"""
AWS Helper functions that provide session management, credential handling, and
role assumption for interacting with AWS services.

This module centralizes the creation of Boto3 sessions and clients, incorporating
a caching layer to reuse sessions and assumed role credentials, which is
particularly effective in AWS Lambda execution environments.
"""

from typing import Any
import datetime
import os
import boto3
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError

import core_framework as util
from core_framework.constants import (
    TR_RESPONSE,
    TR_STATUS,
    CORE_AUTOMATION_SESSION_ID_PREFIX,
)
import core_logging as log
from .cache import InMemoryCache

# This cache is instantiated at the module level, so it persists across
# Lambda invocations within the same execution environment.
store = InMemoryCache()

RETRY_CONFIG: dict[str, Any] = {"max_attempts": 10}


def __transform_keyvalues_to_array(
    keyvalues: dict[str, str] | None, key_key: str, value_key: str
) -> list[dict[str, str]]:
    """
    Transforms a dictionary into a list of key-value pair dictionaries.

    :param keyvalues: The dictionary to transform.
    :type keyvalues: dict[str, str] | None
    :param key_key: The key name to use in the output dictionaries (e.g., 'Key').
    :type key_key: str
    :param value_key: The value name to use in the output dictionaries (e.g., 'Value').
    :type value_key: str
    :return: A list of transformed dictionaries, or an empty list if input is None.
    :rtype: list[dict[str, str]]
    """
    if not keyvalues:
        return []
    return [{key_key: key, value_key: value} for key, value in keyvalues.items()]


def transform_stack_parameter_dict(keyvalues: dict[str, str]) -> dict[str, str]:
    """
    Creates a copy of the input dictionary.

    :param keyvalues: A dictionary of key-value pairs.
    :type keyvalues: dict[str, str]
    :return: A shallow copy of the input dictionary.
    :rtype: dict[str, str]
    """
    rv = {}
    if len(keyvalues):
        for key, value in keyvalues.items():
            rv[key] = value
    return rv


def transform_stack_parameter_hash(keyvalues: dict[str, str]) -> list[dict[str, str]]:
    """
    Translates a dictionary into the CloudFormation stack parameter format.

    :param keyvalues: A dictionary of parameter keys and values.
    :type keyvalues: dict[str, str]
    :return: A list of dictionaries formatted for CloudFormation.
    :rtype: list[dict[str, str]]
    """
    return __transform_keyvalues_to_array(keyvalues, "ParameterKey", "ParameterValue")


def transform_tag_hash(keyvalues: dict[str, str]) -> list[dict[str, str]]:
    """
    Translates a dictionary into the AWS Tag format.

    :param keyvalues: A dictionary of tag keys and values.
    :type keyvalues: dict[str, str]
    :return: A list of dictionaries formatted as AWS Tags.
    :rtype: list[dict[str, str]]
    """
    return __transform_keyvalues_to_array(keyvalues, "Key", "Value")


def get_session_key(session: Session) -> str:
    """
    Generates a unique cache key for a Boto3 session based on its profile and region.

    :param session: The Boto3 session.
    :type session: boto3.session.Session
    :return: A string to be used as a cache key.
    :rtype: str
    """
    prefix = util.get_automation_scope() or "sck-session-"
    return f"{prefix}{session.profile_name}-{session.region_name}"


def get_session(**kwargs) -> Session:
    """
    Retrieves a cached Boto3 session or creates a new one.

    :param kwargs: Optional keyword arguments.
                   `region` (str): The AWS region.
                   `aws_profile` (str): The AWS profile name.
    :return: A Boto3 session object.
    :rtype: boto3.session.Session
    """
    region = kwargs.get("region", util.get_region())
    profile_name = kwargs.get("aws_profile", util.get_aws_profile())
    key = f"sck-session-{profile_name}-{region}"
    session = store.retrieve_session(key)
    if session is None:
        session = boto3.session.Session(region_name=region, profile_name=profile_name)
        store.store_session(key, session)
    return session


def get_session_credentials(**kwargs) -> dict | None:
    """
    Returns the credentials from the current base session.

    These are the base credentials, either from an IAM user or the instance/task role,
    before any role assumption.

    :param kwargs: Optional arguments passed to `get_session`.
    :return: A dictionary containing AccessKeyId, SecretAccessKey, and SessionToken,
             or None if credentials cannot be retrieved.
    :rtype: dict | None
    """
    session = get_session(**kwargs)
    credentials = session.get_credentials()
    if credentials:
        frozen_creds = credentials.get_frozen_credentials()
        return {
            "AccessKeyId": frozen_creds.access_key,
            "SecretAccessKey": frozen_creds.secret_key,
            "SessionToken": frozen_creds.token,
        }
    return None


def login_to_aws(auth: dict[str, str], **kwargs) -> dict[str, str] | None:
    """
    Logs into AWS using provided authentication credentials and assumes a role.

    :param auth: A dictionary containing AWS credentials with keys 'AccessKeyId',
                 'SecretAccessKey', and 'SessionToken'.
    :type auth: dict[str, str]
    :param kwargs: Optional keyword arguments, including 'role' (str) for the role ARN to assume.
    :return: A dictionary containing the assumed role credentials, or None if assumption fails.
    :rtype: dict[str, str] | None
    """
    role = kwargs.get("role", None)
    if not role:
        log.error("No role specified for login_to_aws")
        return None

    sts_client = get_session(**kwargs).client(
        "sts",
        aws_access_key_id=auth["AccessKeyId"],
        aws_secret_access_key=auth["SecretAccessKey"],
        aws_session_token=auth["SessionToken"],
        config=__get_client_config(),
    )

    try:
        session_name = f"{CORE_AUTOMATION_SESSION_ID_PREFIX}-login-{util.get_timestamp_str()}"

        result = sts_client.assume_role(
            RoleArn=role, RoleSessionName=session_name
        )
    except ClientError as e:
        log.error("Failed to assume role in login_to_aws: {}", e)
        return None

    return result["Credentials"]


def get_role_credentials(role: str) -> dict[str, Any]:
    """
    Retrieves cached credentials for a specific role.

    :param role: The ARN of the role to retrieve credentials for.
    :type role: str
    :return: A dictionary containing the cached credentials, or an empty dict if not found.
    :rtype: dict[str, Any]
    """
    return store.retrieve_data(role) or {}


def __get_client_config() -> Config:
    """
    Creates a Botocore Config object with standard proxy and retry settings.

    :return: A configured botocore.config.Config object.
    :rtype: botocore.config.Config
    """
    http_proxy = os.getenv("HTTP_PROXY", os.getenv("http_proxy"))
    https_proxy = os.getenv("HTTPS_PROXY", os.getenv("https_proxy"))
    proxy_definition = None
    if http_proxy or https_proxy:
        proxy_definition = {"http": http_proxy, "https": https_proxy}
    return Config(
        proxies=proxy_definition,
        connect_timeout=15,
        read_timeout=15,
        retries=RETRY_CONFIG,
    )


def assume_role(**kwargs) -> dict[str, str] | None:
    """
    Assumes an IAM role and returns temporary credentials.

    If a role ARN is provided, it attempts to assume it, using a cache to store
    credentials. If assumption fails or no role is provided, it falls back to
    returning the base session credentials.

    :param kwargs: Optional keyword arguments.
                   `role` (str): The ARN of the role to assume.
    :return: A dictionary of credentials or None.
    :rtype: dict[str, str] | None
    """
    role_arn = kwargs.get("role") or kwargs.get("role_arn")
    if not role_arn:
        return get_session_credentials()

    credentials = store.retrieve_data(role_arn)
    if credentials:
        return credentials

    try:
        session = get_session(**kwargs)
        
        session_name = f"{CORE_AUTOMATION_SESSION_ID_PREFIX}-{util.get_timestamp_str()}"
        log.debug("Assuming role [{}] with session name [{}]", role_arn, session_name)
        # Call the STS client with the session and role ARN directy instead of sts_client() to avoid recursion
        client = session.client("sts", **kwargs, config=__get_client_config())
        response = client.assume_role(
            RoleArn=role_arn, RoleSessionName=session_name
        )
        credentials = response.get("Credentials")
        if credentials:
            store.store_data(role_arn, credentials)
            return credentials
    except ClientError as e:
        log.error(
            "Failed to assume role {}: {}. Falling back to base credentials.",
            role_arn,
            e,
        )

    # Fallback to base credentials if assumption fails
    return get_session_credentials()


def get_identity(role: str | None = None, **kwargs) -> dict[str, Any] | None:
    """
    Gets the caller identity and credentials for the current session or an assumed role.

    This function combines the output of the STS GetCallerIdentity API call with the
    active credentials. If a role ARN is provided, it will first attempt to assume
    that role. The credentials and identity of the resulting principal are returned.

    :param role: The ARN of the IAM role to assume before getting the identity.
                 If None, the identity of the base session credentials is returned.
    :type role: str | None
    :param kwargs: Optional arguments passed to the session and client creators.
    :return: A dictionary containing the caller's identity (UserId, Account, Arn)
             and the corresponding credentials, or None on failure.
    :rtype: dict[str, Any] | None
    """
    try:
        kwargs["role"] = role
        credentials = assume_role(**kwargs)

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
        log.error("Failed to get identity for role [{}]: {}", role, e)
        return None


def get_session_token(**kwargs) -> dict | None:
    """
    Ensures the current session has temporary credentials with a session token.

    If the base credentials already have a session token (e.g., from an instance
    role or an assumed role), they are returned as-is. If the base credentials
    are long-term IAM user credentials without a token, this function calls the
    STS GetSessionToken API to generate a new, complete set of temporary credentials.

    :param kwargs: Optional arguments passed to the underlying session and client creators.
    :type kwargs: dict
    :return: A dictionary containing temporary credentials with AccessKeyId,
             SecretAccessKey, SessionToken, and Expiration, or None if credentials
             cannot be obtained.
    :rtype: dict | None

    .. note::
       The returned credentials are always temporary credentials with a SessionToken,
       either from the existing session or newly generated via STS GetSessionToken.
    """
    credentials = get_session_credentials(**kwargs)
    if not credentials:
        return None

    # If a session token already exists, return the credentials as-is
    session_token = credentials.get("SessionToken")
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
            return new_credentials
        else:
            log.error("STS GetSessionToken returned no credentials")
            return None

    except ClientError as e:
        log.error("Failed to get session token: {}", e)
        return None


def get_client(service_name: str, **kwargs) -> Any:
    """
    Creates a Boto3 client, using assumed role credentials if a role is provided.

    :param service_name: The name of the AWS service (e.g., 's3', 'sts').
    :type service_name: str
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 client.
    :rtype: Any
    """
    session = get_session(**kwargs)
    credentials = assume_role(**kwargs)
    if not credentials:
        return session.client(service_name, config=__get_client_config())
    else:
        return session.client(
            service_name,
            aws_access_key_id=credentials.get("AccessKeyId"),
            aws_secret_access_key=credentials.get("SecretAccessKey"),
            aws_session_token=credentials.get("SessionToken"),
            config=__get_client_config(),
        )


# Convenience functions for creating specific clients
def sts_client(**kwargs) -> Any:
    """Creates a Boto3 STS client."""
    return get_client("sts", **kwargs)


def s3_client(**kwargs) -> Any:
    """Creates a Boto3 S3 client."""
    return get_client("s3", **kwargs)


def cfn_client(**kwargs) -> Any:
    """Creates a Boto3 CloudFormation client."""
    return get_client("cloudformation", **kwargs)


def cloudwatch_client(**kwargs) -> Any:
    """
    Creates a Boto3 CloudWatch client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 CloudWatch client.
    :rtype: Any
    """
    return get_client("cloudwatch", **kwargs)


def cloudfront_client(**kwargs) -> Any:
    """
    Creates a Boto3 CloudFront client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 CloudFront client.
    :rtype: Any
    """
    return get_client("cloudfront", **kwargs)


def ec2_client(**kwargs) -> Any:
    """
    Creates a Boto3 EC2 client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 EC2 client.
    :rtype: Any
    """
    return get_client("ec2", **kwargs)


def ecr_client(**kwargs) -> Any:
    """
    Creates a Boto3 ECR client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 ECR client.
    :rtype: Any
    """
    return get_client("ecr", **kwargs)


def elb_client(**kwargs) -> Any:
    """
    Creates a Boto3 ELB client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 ELB client.
    :rtype: Any
    """
    return get_client("elb", **kwargs)


def elbv2_client(**kwargs) -> Any:
    """
    Creates a Boto3 ELBv2 client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 ELBv2 client.
    :rtype: Any
    """
    return get_client("elbv2", **kwargs)


def iam_client(**kwargs) -> Any:
    """Creates a Boto3 IAM client."""
    return get_client("iam", **kwargs)


def kms_client(**kwargs) -> Any:
    """
    Creates a Boto3 KMS client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 KMS client.
    :rtype: Any
    """
    return get_client("kms", **kwargs)


def lambda_client(**kwargs) -> Any:
    """   
    Creates a Boto3 Lambda client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 Lambda client.
    :rtype: Any
    """
    return get_client("lambda", **kwargs)


def rds_client(**kwargs) -> Any:
    """
    Creates a Boto3 RDS client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 RDS client.
    :rtype: Any
    """
    return get_client("rds", **kwargs)


def org_client(**kwargs) -> Any:
    """
    Creates a Boto3 Organizations client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 Organizations client.
    :rtype: Any
    """
    return get_client("organizations", **kwargs)


def step_functions_client(**kwargs) -> Any:
    """
    Creates a Boto3 Step Functions client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 Step Functions client.
    :rtype: Any
    """
    return get_client("stepfunctions", **kwargs)


def r53_client(**kwargs) -> Any:
    """
    Creates a Boto3 Route53 client.
    
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 Route53 client.
    :rtype: Any
    """
    return get_client("route53", **kwargs)


def get_resource(service_name: str, **kwargs) -> Any:
    """
    Creates a Boto3 resource, using assumed role credentials if a role is provided.

    :param service_name: The name of the AWS service resource (e.g., 's3').
    :type service_name: str
    :param kwargs: Optional keyword arguments, including `role` (str).
    :return: An initialized Boto3 resource.
    :rtype: Any
    """
    session = get_session(**kwargs)
    credentials = assume_role(**kwargs)

    if credentials is None:
        return session.resource(service_name, config=__get_client_config())
    else:
        return session.resource(
            service_name,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            config=__get_client_config(),
        )


def s3_resource(**kwargs) -> Any:
    """Creates a Boto3 S3 resource."""
    return get_resource("s3", **kwargs)


def dynamodb_resource(**kwargs) -> Any:
    """Creates a Boto3 DynamoDB resource."""
    kwargs["region"] = kwargs.get("region", util.get_dynamodb_region())
    return get_resource("dynamodb", **kwargs)


def invoke_lambda(
    arn: str, request_payload: dict[str, Any], **kwargs
) -> dict[str, Any]:
    """
    Invokes an AWS Lambda function and returns its response.

    :param arn: The ARN of the Lambda function to invoke.
    :type arn: str
    :param request_payload: The JSON-serializable payload to send to the function.
    :type request_payload: dict[str, Any]
    :param kwargs: Optional arguments passed to the `lambda_client`.
    :return: A dictionary containing the status and response from the Lambda.
    :rtype: dict[str, Any]
    """
    kwargs["region"] = kwargs.get("region") or arn.split(":")[3]
    client = get_client("lambda", **kwargs)
    log.trace(
        "Invoking Lambda", details={"FunctionName": arn, "Payload": request_payload}
    )
    try:
        response = client.invoke(
            FunctionName=arn, Payload=util.to_json(request_payload)
        )
        payload_bytes = response.get("Payload").read()
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
            return {TR_STATUS: "error", TR_RESPONSE: response_payload}

        return {TR_STATUS: "ok", TR_RESPONSE: response_payload}

    except Exception as e:
        log.warn("Failed to invoke FunctionName={}: {}", arn, e)
        return {TR_STATUS: "error", TR_RESPONSE: f"Failed to invoke Lambda - {e}"}


def generate_context() -> dict:
    """
    Generates a basic authorization context for AWS service access.

    :return: A dictionary containing default authorization context.
    :rtype: dict
    """
    return {"DeliveredBy": "user", "AuthorizationToken": "temp cred auth token id"}


def grant_assume_role_permission(
    user_name: str, role_name: str, account_id: str, **kwargs
) -> None:
    """
    Grants a user permission to assume a specific role.

    This function modifies the user's inline IAM policy to add the role to the
    list of allowed resources for the `sts:AssumeRole` action. It also updates
    the role's trust policy to allow the user to assume it.

    :param user_name: The IAM user to grant the permission to.
    :type user_name: str
    :param role_name: The name of the role the user should be able to assume.
    :type role_name: str
    :param account_id: The AWS account ID where the role is defined.
    :type account_id: str
    :param kwargs: Optional arguments passed to the `iam_client`.
    """
    policy_name = "AssumeRolePolicy"
    client = iam_client(**kwargs)
    try:
        existing_policy = client.get_user_policy(
            UserName=user_name, PolicyName=policy_name
        )
        policy_document = existing_policy["PolicyDocument"]
    except client.exceptions.NoSuchEntityException:
        policy_document = {"Version": "2012-10-17", "Statement": []}

    assume_role_statement = next(
        (
            stmt
            for stmt in policy_document["Statement"]
            if stmt.get("Action") == "sts:AssumeRole"
        ),
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
    if not any(
        stmt["Principal"].get("AWS") == user_arn
        for stmt in trust_policy["Statement"]
        if stmt["Effect"] == "Allow"
    ):
        trust_policy["Statement"].append(
            {
                "Effect": "Allow",
                "Principal": {"AWS": user_arn},
                "Action": "sts:AssumeRole",
            }
        )
        client.update_assume_role_policy(
            RoleName=role_name, PolicyDocument=util.to_json(trust_policy)
        )


def revoke_assume_role_permission(
    user_name: str, role_name: str, account_id: str, **kwargs
) -> None:
    """
    Revokes a user's permission to assume a specific role.

    This function removes the role from the user's `sts:AssumeRole` policy and
    removes the user from the role's trust policy.

    :param user_name: The IAM user to revoke the permission from.
    :type user_name: str
    :param role_name: The name of the role to revoke access to.
    :type role_name: str
    :param account_id: The AWS account ID where the role is defined.
    :type account_id: str
    :param kwargs: Optional arguments passed to the `iam_client`.
    """
    client = iam_client(**kwargs)
    policy_name = "AssumeRolePolicy"
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    try:
        response = client.get_user_policy(UserName=user_name, PolicyName=policy_name)
        policy_document = response["PolicyDocument"]
        assume_role_statement = next(
            (
                stmt
                for stmt in policy_document["Statement"]
                if stmt.get("Action") == "sts:AssumeRole"
            ),
            None,
        )
        if assume_role_statement and role_arn in assume_role_statement.get(
            "Resource", []
        ):
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
        trust_policy["Statement"] = [
            stmt
            for stmt in trust_policy["Statement"]
            if stmt.get("Principal", {}).get("AWS") != user_arn
        ]
        if len(trust_policy["Statement"]) < original_statement_count:
            client.update_assume_role_policy(
                RoleName=role_name, PolicyDocument=util.to_json(trust_policy)
            )
    except client.exceptions.NoSuchEntityException:
        log.debug("Role {} not found, nothing to update in trust policy.", role_name)
    except Exception as e:
        log.error("Error updating trust policy for role {}: {}", role_name, e)
