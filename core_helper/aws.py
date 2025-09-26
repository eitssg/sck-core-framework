"""AWS Helper Functions for Session Management and Credential Handling.

This module centralizes the creation of Boto3 sessions and clients, incorporating
a caching layer to reuse sessions and assumed role credentials. It provides
session management, credential handling, and role assumption capabilities that
are particularly effective in AWS Lambda execution environments.

Key Features:
    - **Session Caching**: Reuses Boto3 sessions across function invocations
    - **Role Assumption**: Automated IAM role assumption with credential caching
    - **Multi-Authentication**: Supports Cognito and direct IAM authentication
    - **MFA Support**: Handles multi-factor authentication workflows
    - **Client Factory**: Centralized AWS service client creation
    - **Credential Management**: Secure handling of temporary and permanent credentials
    - **Error Handling**: Comprehensive error handling for AWS operations

Authentication Methods:
    - **Cognito User Pools**: Username/password authentication with MFA support
    - **IAM Users**: Direct IAM user authentication with MFA support
    - **Role Assumption**: Cross-account and cross-role credential switching
    - **Session Tokens**: Temporary credential generation and management

Caching Strategy:
    - Sessions are cached by profile and region combination
    - Role credentials are cached by role ARN with automatic expiration
    - Cache persists across Lambda invocations within same execution environment
    - Automatic cache invalidation for expired credentials

Integration:
    - Integrates with core_framework configuration system
    - Supports proxy configuration via environment variables
    - Compatible with AWS Lambda execution environment
    - Works with local development and production environments
"""

from typing import Any, Dict
import os
import boto3
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.response import StreamingBody


import core_framework as util

import core_logging as log
from .cache import InMemoryCache
from .aws_models import AwsCredentials

# This cache is instantiated at the module level, so it persists across
# Lambda invocations within the same execution environment.
store = InMemoryCache()

RETRY_CONFIG: dict[str, Any] = {"max_attempts": 10}
LAMBDA_FUNCTION_NAME_REGEX = r"(arn:(aws[a-zA-Z-]*)?:lambda:)?([a-z]{2}(-gov)?-[a-z]+-\d{1}:)?(\d{12}:)?(function:)?([a-zA-Z0-9-_\.]+)(:(\$LATEST|[a-zA-Z0-9-_]+))?"


def __transform_keyvalues_to_array(keyvalues: dict[str, str] | None, key_key: str, value_key: str) -> list[dict[str, str]]:
    """Transform a dictionary into a list of key-value pair dictionaries.

    Converts a standard Python dictionary into AWS API format where each
    key-value pair becomes a dictionary with specified key names.

    Args:
        keyvalues: The dictionary to transform. Can be None.
        key_key: The key name to use for dictionary keys (e.g., 'Key').
        value_key: The key name to use for dictionary values (e.g., 'Value').

    Returns:
        A list of transformed dictionaries, or an empty list if input is None.
    """
    if not keyvalues:
        return []
    return [{key_key: key, value_key: value} for key, value in keyvalues.items()]


def transform_stack_parameter_dict(keyvalues: dict[str, str]) -> dict[str, str]:
    """Create a copy of the input dictionary.

    Args:
        keyvalues: A dictionary of key-value pairs.

    Returns:
        A shallow copy of the input dictionary.
    """
    rv = {}
    if len(keyvalues):
        for key, value in keyvalues.items():
            rv[key] = value
    return rv


def transform_stack_parameter_hash(keyvalues: dict[str, str]) -> list[dict[str, str]]:
    """Translate a dictionary into CloudFormation stack parameter format.

    Converts a standard dictionary into the format expected by CloudFormation
    APIs for stack parameters.

    Args:
        keyvalues: A dictionary of parameter keys and values.

    Returns:
        A list of dictionaries formatted for CloudFormation with 'ParameterKey'
        and 'ParameterValue' fields.
    """
    return __transform_keyvalues_to_array(keyvalues, "ParameterKey", "ParameterValue")


def transform_tag_hash(keyvalues: dict[str, str]) -> list[dict[str, str]]:
    """Translate a dictionary into AWS Tag format.

    Converts a standard dictionary into the format expected by AWS APIs
    for resource tags.

    Args:
        keyvalues: A dictionary of tag keys and values.

    Returns:
        A list of dictionaries formatted as AWS Tags with 'Key' and 'Value' fields.
    """
    return __transform_keyvalues_to_array(keyvalues, "Key", "Value")


def set_user_context(user_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Set the user context for AWS operations in the current thread.

    Checks if user context already exists and only updates if needed.
    This optimization prevents unnecessary cache operations for the same user.

    Args:
        user_id: Unique identifier for the user (from JWT sub claim)
        credentials: AWS credentials from JWT token

    Returns:
        The user context dict (either existing or newly set)
    """
    # Check if context already exists for this user
    existing_context = store.get_user_context()

    if existing_context and existing_context.get("user_id") == user_id:
        # Check if credentials have changed (token refresh scenario)
        existing_creds = existing_context.get("credentials", {})
        if existing_creds.get("AccessKeyId") == credentials.get("AccessKeyId"):
            log.debug(
                "User context already current - no update needed",
                details={"user_id": user_id},
            )
            return existing_context

    # Set new or updated user context
    new_context = {"user_id": user_id, "credentials": credentials}

    store.set_user_context(user_id, credentials)

    log.debug(
        "Set user context for AWS session management",
        details={
            "user_id": user_id,
            "access_key": credentials.get("AccessKeyId", "")[:10] + "...",
            "updated": existing_context is not None,
        },
    )

    return new_context


def get_user_context() -> Dict[str, Any] | None:
    """Get the current user context for the thread.

    Returns:
        The user context dict containing user_id and credentials, or None if not set
    """
    return store.get_user_context()


def clear_user_context() -> None:
    """Clear the current user context for the thread."""
    store.clear_user_context()
    log.debug("Cleared user context")


def get_session(
    *,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    aws_session_token=None,
    region_name=None,
    profile_name=None,
    aws_account_id=None,
    **kwargs,
) -> Session:
    """Retrieve a cached Boto3 session or create a new one.

    Now automatically uses user context from JWT credentials when available.

    Args:
        role_arn: Optional ARN of the IAM role to assume after session creation
        aws_access_key_id: Optional AWS access key ID for session
        aws_secret_access_key: Optional AWS secret access key for session
        aws_session_token: Optional AWS session token for temporary credentials
        region_name: Optional AWS region for session
        profile_name: Optional AWS CLI profile name for session
        aws_account_id: Optional AWS account ID for cross-account role assumption
        **kwargs: Additional keyword arguments passed to boto3.session.Session

    Returns:
        A Boto3 Session object, either cached or newly created.
    """

    if not region_name:
        region_name = kwargs.get("region", util.get_region())
    if not profile_name:
        profile_name = kwargs.get("aws_profile", util.get_aws_profile())

    # Get user context (set by handler from JWT)
    user_context = get_user_context()

    if user_context:
        credentials: Dict[str, str] = user_context.get("credentials")
        if not aws_access_key_id and credentials:
            aws_access_key_id = credentials.get("AccessKeyId")
            aws_secret_access_key = credentials.get("SecretAccessKey")
            aws_session_token = credentials.get("SessionToken")

    def gen_key() -> str:
        key_parts = [
            "sck-session",
            profile_name,
            region_name,
            aws_access_key_id or "x",
            (aws_secret_access_key[:8] if aws_secret_access_key else "x"),
            (aws_session_token[:16] if aws_session_token else "x"),
            aws_account_id or "x",
        ]
        return "-".join(key_parts)

    key = gen_key()

    cached_session = store.retrieve_session(key)
    if cached_session:
        log.debug(f"Retrieved cached user session: {key}")
        return cached_session

    # Create the session
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=region_name,
        profile_name=profile_name,
        aws_account_id=aws_account_id,
    )

    if not aws_access_key_id:
        credentials = session.get_credentials()
        if credentials:
            frozen_creds = credentials.get_frozen_credentials()
            aws_access_key_id = frozen_creds.access_key
            aws_secret_access_key = frozen_creds.secret_key
            aws_session_token = frozen_creds.token

    if not user_context or user_context.get("user_id") is None:
        store.set_user_context(
            aws_access_key_id,
            {
                "AccessKeyId": aws_access_key_id,
                "SecretAccessKey": aws_secret_access_key,
                "SessionToken": aws_session_token,
            },
        )

    # Did credentials change?  Generate new key if so
    key = gen_key()

    store.store_session(key, session)

    return session


def get_session_credentials(**kwargs) -> AwsCredentials | None:
    """Return the credentials from the current base session.

    Retrieves the base credentials from the session, which are either from
    an IAM user or the instance/task role, before any role assumption.

    Args:
        **kwargs: Optional arguments passed to get_session.

    Returns:
        A dictionary containing AccessKeyId, SecretAccessKey, and SessionToken,
        or None if credentials cannot be retrieved.
    """
    session = get_session(**kwargs)
    credentials = session.get_credentials()
    if credentials:
        frozen_creds = credentials.get_frozen_credentials()
        return AwsCredentials.model_validate(
            {
                "AccessKeyId": frozen_creds.access_key,
                "SecretAccessKey": frozen_creds.secret_key,
                "SessionToken": frozen_creds.token,
            }
        )
    return None


def get_role_credentials(role_arn: str) -> AwsCredentials | None:
    """Retrieve cached credentials for a specific role.

    Args:
        role: The ARN of the role to retrieve credentials for.

    Returns:
        A dictionary containing the cached credentials, or None if not found.
    """
    return AwsCredentials.model_validate(store.retrieve_user_credentials(role_arn))


def __get_client_config() -> Config:
    """Create a Botocore Config object with standard proxy and retry settings.

    Configures the client with proxy settings from environment variables
    and standard retry configuration for robust AWS API interactions.

    Returns:
        A configured botocore.config.Config object with proxy and retry settings.
    """
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    proxy_definition = None
    if not http_proxy and https_proxy:
        http_proxy = https_proxy
    if not https_proxy and http_proxy:
        https_proxy = http_proxy
    if http_proxy:
        proxy_definition = {"http": http_proxy, "https": https_proxy}
    return Config(
        proxies=proxy_definition,
        connect_timeout=15,
        read_timeout=15,
        retries=RETRY_CONFIG,
    )


def assume_role(*, role_arn: str = None, **kwargs) -> AwsCredentials:
    """Assume an IAM role and return temporary credentials. Fallback to return session credentials."""

    if not role_arn:
        role_arn = kwargs.pop("RoleArn", None)

    if not role_arn:
        return get_session_credentials(**kwargs)

    # Check user-specific cached credentials first
    user_context = get_user_context()
    if user_context:
        cached_credentials = store.retrieve_user_credentials(role_arn)
        if cached_credentials:
            log.debug("Retrieved cached user role credentials", details={"user_id": user_context["user_id"], "role": role_arn})
            return AwsCredentials.model_validate(cached_credentials)

    try:
        session = get_session(**kwargs)
        session_name = f"Pipeline-{util.get_current_timestamp()}"

        # get_session will set a user_context.
        user_context = get_user_context()

        log.debug("Assuming role for user", details={"role_arn": role_arn, "session_name": session_name})

        client = session.client("sts", config=__get_client_config())
        response = client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)

        credentials = response.get("Credentials")
        if credentials:
            # Cache credentials for this user and role
            if user_context:
                store.store_user_credentials(credentials, role_arn)
                log.debug("Cached new user role credentials", details={"user_id": user_context["user_id"], "role": role_arn})
            else:
                # Fall back to old caching method
                store.store_data(role_arn, credentials)

            return AwsCredentials.model_validate(credentials)

    except Exception as e:
        log.error("Failed to assume role {}: {}. Falling back to base credentials.", role_arn, e)

    # Fallback to base credentials if assumption fails
    return get_session_credentials(**kwargs)


def get_identity(role_arn: str | None = None, **kwargs) -> dict[str, Any] | None:
    """Get the caller identity and credentials for the current session or assumed role.

    Combines the output of the STS GetCallerIdentity API call with the active
    credentials. If a role ARN is provided, attempts to assume that role first.

    Args:
        role: The ARN of the IAM role to assume before getting the identity.
            If None, returns the identity of the base session credentials.
        **kwargs: Optional arguments passed to the session and client creators.

    Returns:
        A dictionary containing the caller's identity (UserId, Account, Arn)
        and the corresponding credentials, or None on failure.
    """
    try:
        credentials = assume_role(role_arn=role_arn, **kwargs)

        if not credentials:
            log.error("Could not retrieve credentials for get_identity.")
            return None

        client = sts_client(
            aws_access_key_id=credentials.get("AccessKeyId"),
            aws_secret_access_key=credentials.get("SecretAccessKey"),
            aws_session_token=credentials.get("SessionToken"),
            config=__get_client_config(),
        )
        identity = client.get_caller_identity()

        # Build a new response dictionary, preserving the original API contract.
        # This combines identity information with the retrieved credentials.
        response = {
            "UserId": identity.get("UserId"),
            "Account": identity.get("Account"),
            "Arn": identity.get("Arn"),
            "AccessKeyId": credentials.get("AccessKeyId"),
            "SecretAccessKey": credentials.get("SecretAccessKey"),
            "SessionToken": credentials.get("SessionToken"),
            "Expiration": credentials.get("Expiration"),
        }

        return response

    except ClientError as e:
        log.error("Failed to get identity for role [{}]: {}", role_arn, e)
        return None


def get_session_token(**kwargs) -> AwsCredentials | None:
    """Ensure the current session has temporary credentials with a session token.

    Generates temporary credentials if the base credentials are long-term IAM
    user credentials. If the base credentials already have a session token,
    they are returned as-is.

    Args:
        **kwargs: Optional arguments passed to the underlying session and client creators.

    Returns:
        A dictionary containing temporary credentials with AccessKeyId,
        SecretAccessKey, SessionToken, and Expiration, or None if credentials
        cannot be obtained.

    Notes:
        The returned credentials are always temporary credentials with a SessionToken,
        either from the existing session or newly generated via STS GetSessionToken.
    """
    credentials = get_session_credentials(**kwargs)
    if not credentials:
        return None

    # If a session token already exists, return the credentials as-is
    session_token = credentials.session_token
    if session_token:
        return credentials

    # If no token exists, these are likely long-term credentials.
    # Call STS GetSessionToken to get temporary credentials.
    try:
        client = sts_client(**kwargs)  # Pass kwargs for consistency
        response = client.get_session_token()

        # Return the complete new credentials structure from STS
        new_credentials = response.get("Credentials")
        if new_credentials:
            return AwsCredentials.model_validate(new_credentials)
        else:
            log.error("STS GetSessionToken returned no credentials")
            return None

    except ClientError as e:
        log.error("Failed to get session token: {}", e)
        return None


def get_client(service_name: str, *, role_arn: str | None = None, **kwargs) -> Any:
    """Create a Boto3 client, using assumed role credentials if a role is provided.

    Creates AWS service clients with automatic credential management, using
    assumed role credentials when a role is specified in kwargs.

    Args:
        service_name: The name of the AWS service (e.g., 's3', 'sts', 'ec2').
        **kwargs: Optional keyword arguments including 'role' for role assumption
            and other parameters passed to the Boto3 client constructor.
            - aws_access_key_id (str): AWS access Key
            - aws_secret_access_key (str): AWS secret Key
            - aws_session_token (str): AWS session Token
            - region_name (str): AWS region
            - aws_profile (str): AWS profile name
            - aws_account_id (str): AWS account ID
            - role_arn (str): If supplied, will do an assume_role and cache the session

    Returns:
        An initialized Boto3 client for the specified service.
    """

    if not role_arn:
        role_arn = kwargs.pop("RoleArn", None)

    if role_arn:
        # These credentials should be cached.  Assume role will check cache first.

        credentials = assume_role(role_arn=role_arn, **kwargs)

        # Remove any direct credentials from kwargs to avoid conflicts.  We've assumed a role!
        if "aws_access_key_id" in kwargs:
            del kwargs["aws_access_key_id"]
        if "aws_secret_access_key" in kwargs:
            del kwargs["aws_secret_access_key"]
        if "aws_session_token" in kwargs:
            del kwargs["aws_session_token"]

        # Get the session for the assumed role credentials
        session = get_session(
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token,
            **kwargs,
        )
    else:
        # No role to assume, use base session
        session = get_session(**kwargs)

    # Get the session for the current user and his credentials else create a new one
    return session.client(service_name, config=__get_client_config())


# Convenience functions for creating specific clients
def sts_client(**kwargs) -> Any:
    """Create a Boto3 STS client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 STS client.
    """
    return get_client("sts", **kwargs)


def s3_client(**kwargs) -> Any:
    """Create a Boto3 S3 client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 S3 client.
    """
    return get_client("s3", **kwargs)


def cfn_client(**kwargs) -> Any:
    """Create a Boto3 CloudFormation client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 CloudFormation client.
    """
    return get_client("cloudformation", **kwargs)


def cloudwatch_client(**kwargs) -> Any:
    """Create a Boto3 CloudWatch client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 CloudWatch client.
    """
    return get_client("cloudwatch", **kwargs)


def cloudfront_client(**kwargs) -> Any:
    """Create a Boto3 CloudFront client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 CloudFront client.
    """
    return get_client("cloudfront", **kwargs)


def ec2_client(**kwargs) -> Any:
    """Create a Boto3 EC2 client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 EC2 client.
    """
    return get_client("ec2", **kwargs)


def ecr_client(**kwargs) -> Any:
    """Create a Boto3 ECR client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 ECR client.
    """
    return get_client("ecr", **kwargs)


def elb_client(**kwargs) -> Any:
    """Create a Boto3 ELB client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 ELB client.
    """
    return get_client("elb", **kwargs)


def elbv2_client(**kwargs) -> Any:
    """Create a Boto3 ELBv2 client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 ELBv2 client.
    """
    return get_client("elbv2", **kwargs)


def iam_client(**kwargs) -> Any:
    """Create a Boto3 IAM client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 IAM client.
    """
    return get_client("iam", **kwargs)


def kms_client(**kwargs) -> Any:
    """Create a Boto3 KMS client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 KMS client.
    """
    return get_client("kms", **kwargs)


def lambda_client(**kwargs) -> Any:
    """Create a Boto3 Lambda client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 Lambda client.
    """
    return get_client("lambda", **kwargs)


def rds_client(**kwargs) -> Any:
    """Create a Boto3 RDS client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 RDS client.
    """
    return get_client("rds", **kwargs)


def org_client(**kwargs) -> Any:
    """Create a Boto3 Organizations client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 Organizations client.
    """
    return get_client("organizations", **kwargs)


def step_functions_client(**kwargs) -> Any:
    """Create a Boto3 Step Functions client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 Step Functions client.
    """
    return get_client("stepfunctions", **kwargs)


def r53_client(**kwargs) -> Any:
    """Create a Boto3 Route53 client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 Route53 client.
    """
    return get_client("route53", **kwargs)


def cognito_client(**kwargs) -> Any:
    """Create a Boto3 Cognito client with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 Cognito client with endpoint configuration.
    """
    endpoint = util.get_cognito_endpoint("http://localhost:4566")
    return get_client("cognito-idp", **kwargs, endpoint_url=endpoint)


def get_resource(service_name: str, *, role_arn: str | None, **kwargs) -> Any:
    """Create a Boto3 resource, using assumed role credentials if a role is provided.

    Creates AWS service resources with automatic credential management, using
    assumed role credentials when a role is specified in kwargs.

    Args:
        service_name: The name of the AWS service resource (e.g., 's3', 'dynamodb').
        **kwargs: Optional keyword arguments including 'role' for role assumption
            and other parameters passed to the Boto3 resource constructor.

    Returns:
        An initialized Boto3 resource for the specified service.
    """

    if not role_arn:
        role_arn = kwargs.pop("RoleArn", None)

    if role_arn:
        # These credentials should be cached.  Assume role will check cache first.
        credentials = assume_role(role_arn=role_arn, **kwargs)

        if "aws_access_key_id" in kwargs:
            del kwargs["aws_access_key_id"]
        if "aws_secret_access_key" in kwargs:
            del kwargs["aws_secret_access_key"]
        if "aws_session_token" in kwargs:
            del kwargs["aws_session_token"]

        # Get the session for the assumed role credentials
        session = get_session(
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token,
            **kwargs,
        )
    else:
        # No role to assume, use base session
        session = get_session(**kwargs)

    return session.resource(service_name, config=__get_client_config())


def s3_resource(**kwargs) -> Any:
    """Create a Boto3 S3 resource with automatic credential management.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption.

    Returns:
        An initialized Boto3 S3 resource.
    """
    return get_resource("s3", **kwargs)


def dynamodb_resource(**kwargs) -> Any:
    """Create a Boto3 DynamoDB resource with automatic credential management.

    Automatically configures the region using the DynamoDB region from
    configuration if not specified in kwargs.

    Args:
        **kwargs: Optional keyword arguments including 'role' for role assumption
            and 'region' for DynamoDB region override.

    Returns:
        An initialized Boto3 DynamoDB resource.
    """
    return get_resource("dynamodb", **kwargs)


def invoke_lambda(arn: str, request_payload: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Invoke an AWS Lambda function and return its response.

    Invokes the specified Lambda function with the provided payload and
    returns a standardized response containing the invocation status and result.

    Args:
        arn: The ARN of the Lambda function to invoke.
        request_payload: The JSON-serializable payload to send to the function.
        **kwargs: Optional arguments passed to the lambda_client including
            'role' for role assumption and 'region' for client region.

    Returns:
        A dictionary containing the status and response from the Lambda:
        - {'status': 'ok', 'response': {...}} for successful invocations
        - {'status': 'error', 'response': '...'} for failed invocations
    """

    # get a cient in the region where the lambda is located
    kwargs["region_name"] = kwargs.get("region_name") or arn.split(":")[3]
    client = get_client("lambda", **kwargs)

    log.trace("Invoking Lambda", details={"FunctionName": arn, "Payload": request_payload})
    try:
        response: Dict[str, Any] = client.invoke(FunctionName=arn, Payload=util.to_json(request_payload))

        payload_stream: StreamingBody = response.get("Payload")
        payload_bytes = payload_stream.read()

        response_payload = util.from_json(payload_bytes.decode("utf-8"))

        status_code = response.get("StatusCode", 0)
        function_error = response.get("FunctionError")

        if status_code < 200 or status_code >= 300 or function_error:
            log.error(
                "Lambda invocation failed",
                details={
                    "StatusCode": status_code,
                    "FunctionError": function_error,
                    "Payload": response_payload,
                },
            )
            return {"Status": "error", "Response": response_payload}

        return {"Status": "ok", "Response": response_payload}

    except Exception as e:
        log.warn("Failed to invoke FunctionName={}: {}", arn, e)
        return {"Status": "error", "Response": f"Failed to invoke Lambda - {e}"}


def generate_context() -> dict:
    """Generate a basic authorization context for AWS service access.

    Creates a standard context dictionary used for authorization in
    AWS service interactions within the Core Automation framework.

    Returns:
        A dictionary containing default authorization context with
        DeliveredBy and AuthorizationToken fields.
    """
    return {"DeliveredBy": "user", "AuthorizationToken": "temp cred auth token id"}


def grant_assume_role_permission(user_name: str, role_name: str, account_id: str, **kwargs) -> None:
    """Grant a user permission to assume a specific role.

    Modifies the user's inline IAM policy to add the role to the list of
    allowed resources for the sts:AssumeRole action. Also updates the role's
    trust policy to allow the user to assume it.

    Args:
        user_name: The IAM user to grant the permission to.
        role_name: The name of the role the user should be able to assume.
        account_id: The AWS account ID where the role is defined.
        **kwargs: Optional arguments passed to the iam_client.
    """
    policy_name = "AssumeRolePolicy"
    client = iam_client(**kwargs)
    try:
        existing_policy = client.get_user_policy(UserName=user_name, PolicyName=policy_name)
        policy_document = existing_policy["PolicyDocument"]
    except client.exceptions.NoSuchEntityException:
        policy_document = {"Version": "2012-10-17", "Statement": []}

    assume_role_statement = next(
        (stmt for stmt in policy_document["Statement"] if stmt.get("Action") == "sts:AssumeRole"),
        None,
    )
    if not assume_role_statement:
        assume_role_statement = {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [],
        }
        policy_document["Statement"].append(assume_role_statement)

    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    if role_arn not in assume_role_statement.get("Resource", []):
        assume_role_statement["Resource"].append(role_arn)

    client.put_user_policy(
        UserName=user_name,
        PolicyName=policy_name,
        PolicyDocument=util.to_json(policy_document),
    )

    role = client.get_role(RoleName=role_name)
    trust_policy = role["Role"]["AssumeRolePolicyDocument"]
    user_arn = f"arn:aws:iam::{account_id}:user/{user_name}"
    if not any(stmt["Principal"].get("AWS") == user_arn for stmt in trust_policy["Statement"] if stmt["Effect"] == "Allow"):
        trust_policy["Statement"].append(
            {
                "Effect": "Allow",
                "Principal": {"AWS": user_arn},
                "Action": "sts:AssumeRole",
            }
        )
        client.update_assume_role_policy(RoleName=role_name, PolicyDocument=util.to_json(trust_policy))


def revoke_assume_role_permission(user_name: str, role_name: str, account_id: str, **kwargs) -> None:
    """Revoke a user's permission to assume a specific role.

    Removes the role from the user's sts:AssumeRole policy and removes
    the user from the role's trust policy.

    Args:
        user_name: The IAM user to revoke the permission from.
        role_name: The name of the role to revoke access to.
        account_id: The AWS account ID where the role is defined.
        **kwargs: Optional arguments passed to the iam_client.
    """
    client = iam_client(**kwargs)
    policy_name = "AssumeRolePolicy"
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    try:
        response = client.get_user_policy(UserName=user_name, PolicyName=policy_name)
        policy_document = response["PolicyDocument"]
        assume_role_statement = next(
            (stmt for stmt in policy_document["Statement"] if stmt.get("Action") == "sts:AssumeRole"),
            None,
        )
        if assume_role_statement and role_arn in assume_role_statement.get("Resource", []):
            assume_role_statement["Resource"].remove(role_arn)
            if not assume_role_statement["Resource"]:
                policy_document["Statement"].remove(assume_role_statement)

            if not policy_document["Statement"]:
                client.delete_user_policy(UserName=user_name, PolicyName=policy_name)
            else:
                client.put_user_policy(
                    UserName=user_name,
                    PolicyName=policy_name,
                    PolicyDocument=util.to_json(policy_document),
                )
    except client.exceptions.NoSuchEntityException:
        log.debug(
            "Policy {} not found for user {}, nothing to revoke.",
            policy_name,
            user_name,
        )

    try:
        role = client.get_role(RoleName=role_name)
        trust_policy = role["Role"]["AssumeRolePolicyDocument"]
        user_arn = f"arn:aws:iam::{account_id}:user/{user_name}"
        original_statement_count = len(trust_policy["Statement"])
        trust_policy["Statement"] = [stmt for stmt in trust_policy["Statement"] if stmt.get("Principal", {}).get("AWS") != user_arn]
        if len(trust_policy["Statement"]) < original_statement_count:
            client.update_assume_role_policy(RoleName=role_name, PolicyDocument=util.to_json(trust_policy))
    except client.exceptions.NoSuchEntityException:
        log.debug("Role {} not found, nothing to update in trust policy.", role_name)
    except Exception as e:
        log.error("Error updating trust policy for role {}: {}", role_name, e)


def clear_role_credentials(role_arn: str) -> None:
    """Clear cached credentials for a specific role.

    Args:
        role_arn: The ARN of the role to clear cached credentials for.
    """
    store.clear_user_credentials(role_arn)
