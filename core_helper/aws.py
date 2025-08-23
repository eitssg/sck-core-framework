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


def get_session_key(session: Session) -> str:
    """Generate a unique cache key for a Boto3 session.

    Creates a cache key based on the session's profile and region for
    use in the session caching system.

    Args:
        session: The Boto3 session to generate a key for.

    Returns:
        A string cache key combining automation scope, profile, and region.
    """
    prefix = util.get_automation_scope() or "sck-session-"
    return f"{prefix}{session.profile_name}-{session.region_name}"


def get_session(**kwargs) -> Session:
    """Retrieve a cached Boto3 session or create a new one.

    Manages session creation and caching to improve performance by reusing
    sessions across function calls within the same execution environment.

    Args:
        **kwargs: Optional keyword arguments.
            region (str): The AWS region for the session.
            aws_profile (str): The AWS profile name to use.

    Returns:
        A Boto3 session object, either from cache or newly created.
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
        return {
            "AccessKeyId": frozen_creds.access_key,
            "SecretAccessKey": frozen_creds.secret_key,
            "SessionToken": frozen_creds.token,
        }
    return None


def login_to_aws(auth: dict[str, str], **kwargs) -> dict[str, Any] | None:
    """Log into AWS using username and password credentials with MFA support.

    Authenticates a user with username/password and handles MFA challenges
    if required. Supports both Cognito User Pools and direct IAM user
    authentication.

    Args:
        auth: A dictionary containing authentication credentials:
            - 'username' (str, required): The username for authentication
            - 'password' (str, required): The password for authentication
            - 'mfa_code' (str, optional): The MFA code if completing MFA challenge
            - 'session' (str, optional): The session token from MFA challenge
        **kwargs: Keyword arguments including:
            - 'user_pool_id' (str): Cognito User Pool ID (if using Cognito)
            - 'client_id' (str): Cognito Client ID (if using Cognito)
            - 'role' (str): The ARN of the IAM role to assume after authentication
            Other optional arguments are passed to get_session().

    Returns:
        A dictionary containing either:
        - Successful auth: {'status': 'authenticated', 'credentials': {...}}
        - MFA required: {'status': 'mfa_required', 'session': '...', 'challenge_type': '...'}
        - Error: {'status': 'error', 'message': '...'}
        or None if authentication fails completely.

    Raises:
        ValueError: If required parameters are missing.

    Notes:
        This function supports both Cognito User Pools and direct IAM user authentication.
        For Cognito, provide user_pool_id and client_id in kwargs.
        For IAM users, the function will attempt direct STS authentication.
    """
    log.trace(
        "Entering login_to_aws", details={"username": auth.get("username", "unknown")}
    )

    username = auth.get("username")
    password = auth.get("password")
    mfa_code = auth.get("mfa_code")
    session_token = auth.get("session")

    if not username or not password:
        log.trace("Missing username or password in login_to_aws")
        raise ValueError("Username and password are required for login_to_aws")

    # Check if we're using Cognito or direct IAM authentication
    user_pool_id = kwargs.get("user_pool_id")
    client_id = kwargs.get("client_id")

    if user_pool_id and client_id:
        log.trace(
            "Using Cognito authentication", details={"user_pool_id": user_pool_id}
        )
        return _authenticate_with_cognito(auth, user_pool_id, client_id, **kwargs)
    else:
        log.trace("Using direct IAM authentication")
        return _authenticate_with_iam(auth, **kwargs)


def _authenticate_with_cognito(
    auth: dict[str, str], user_pool_id: str, client_id: str, **kwargs
) -> dict[str, Any] | None:
    """Authenticate a user using AWS Cognito User Pools.

    Handles the complete Cognito authentication flow including initial
    authentication, MFA challenges, and credential retrieval through
    Cognito Identity Pools.

    Args:
        auth: Authentication credentials dictionary containing username, password,
            and optionally mfa_code and session token.
        user_pool_id: The Cognito User Pool ID for authentication.
        client_id: The Cognito Client ID for the application.
        **kwargs: Additional arguments including identity_pool_id and role for
            credential retrieval and role assumption.

    Returns:
        Authentication result dictionary with status, credentials, and tokens,
        or None if authentication fails.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError

        session = get_session(**kwargs)
        cognito_client = session.client("cognito-idp")

        username = auth.get("username")
        password = auth.get("password")
        mfa_code = auth.get("mfa_code")
        session_token = auth.get("session")

        log.trace("Attempting Cognito authentication", details={"username": username})

        if session_token and mfa_code:
            # Responding to MFA challenge
            log.trace("Responding to MFA challenge")
            response = cognito_client.respond_to_auth_challenge(
                ClientId=client_id,
                ChallengeName="SOFTWARE_TOKEN_MFA",
                Session=session_token,
                ChallengeResponses={
                    "USERNAME": username,
                    "SOFTWARE_TOKEN_MFA_CODE": mfa_code,
                },
            )
        else:
            # Initial authentication
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": username, "PASSWORD": password},
            )

        # Check if MFA is required
        if response.get("ChallengeName") == "SOFTWARE_TOKEN_MFA":
            log.trace("MFA challenge required")
            return {
                "status": "mfa_required",
                "session": response["Session"],
                "challenge_type": "SOFTWARE_TOKEN_MFA",
                "message": "Please provide your MFA code",
            }

        # Check if authentication was successful
        if "AuthenticationResult" in response:
            log.trace("Cognito authentication successful")
            auth_result = response["AuthenticationResult"]

            # Get temporary AWS credentials using the ID token
            cognito_identity_client = session.client("cognito-identity")
            identity_pool_id = kwargs.get("identity_pool_id")

            if identity_pool_id:
                # Get identity ID
                identity_response = cognito_identity_client.get_id(
                    IdentityPoolId=identity_pool_id,
                    Logins={
                        f"cognito-idp.{session.region_name}.amazonaws.com/{user_pool_id}": auth_result[
                            "IdToken"
                        ]
                    },
                )

                # Get temporary credentials
                credentials_response = cognito_identity_client.get_credentials_for_identity(
                    IdentityId=identity_response["IdentityId"],
                    Logins={
                        f"cognito-idp.{session.region_name}.amazonaws.com/{user_pool_id}": auth_result[
                            "IdToken"
                        ]
                    },
                )

                credentials = credentials_response["Credentials"]

                # Assume role if specified
                role_arn = kwargs.get("role")
                if role_arn:
                    log.trace(
                        "Assuming role after Cognito authentication",
                        details={"role": role_arn},
                    )
                    role_creds = _assume_role_with_credentials(
                        credentials, role_arn, **kwargs
                    )
                    if role_creds:
                        credentials = role_creds

                log.trace("Cognito authentication and credential retrieval successful")
                return {
                    "status": "authenticated",
                    "credentials": {
                        "AccessKeyId": credentials["AccessKeyId"],
                        "SecretAccessKey": credentials["SecretKey"],
                        "SessionToken": credentials["SessionToken"],
                        "Expiration": credentials["Expiration"],
                    },
                    "tokens": {
                        "access_token": auth_result["AccessToken"],
                        "id_token": auth_result["IdToken"],
                        "refresh_token": auth_result.get("RefreshToken"),
                    },
                }
            else:
                log.trace("No identity pool ID provided, returning tokens only")
                return {
                    "status": "authenticated",
                    "tokens": {
                        "access_token": auth_result["AccessToken"],
                        "id_token": auth_result["IdToken"],
                        "refresh_token": auth_result.get("RefreshToken"),
                    },
                }

        log.trace("Cognito authentication failed - unexpected response")
        return {
            "status": "error",
            "message": "Authentication failed - unexpected response from Cognito",
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        log.trace("Cognito authentication failed", details={"error_code": error_code})

        if error_code == "NotAuthorizedException":
            return {"status": "error", "message": "Invalid username or password"}
        elif error_code == "CodeMismatchException":
            return {"status": "error", "message": "Invalid MFA code"}
        elif error_code == "ExpiredCodeException":
            return {"status": "error", "message": "MFA code has expired"}
        else:
            return {"status": "error", "message": f"Authentication failed: {str(e)}"}
    except Exception as e:
        log.trace("Cognito authentication error", details={"error": str(e)})
        log.error("Cognito authentication error: {}", e)
        return {"status": "error", "message": f"Authentication error: {str(e)}"}


def _authenticate_with_iam(auth: dict[str, str], **kwargs) -> dict[str, Any] | None:
    """Authenticate using direct IAM user credentials with MFA support.

    Uses the provided username/password as IAM access keys and attempts
    to authenticate with AWS STS. Supports MFA challenges using virtual
    MFA devices.

    Args:
        auth: Authentication credentials dictionary containing:
            - 'username' (str): The IAM Access Key ID
            - 'password' (str): The IAM Secret Access Key
            - 'mfa_code' (str, optional): The MFA code if completing MFA challenge
            - 'mfa_serial' (str, optional): The MFA device serial number
        **kwargs: Additional arguments including:
            - 'role' (str, optional): Role ARN to assume after authentication
            - 'mfa_serial' (str, optional): MFA device serial number

    Returns:
        Authentication result dictionary with status, credentials, and identity
        information, or None if authentication fails.
    """
    try:
        session = get_session(**kwargs)

        access_key_id = auth.get("username")
        secret_access_key = auth.get("password")
        mfa_code = auth.get("mfa_code")
        mfa_serial = auth.get("mfa_serial") or kwargs.get("mfa_serial")

        log.trace(
            "Attempting IAM authentication",
            details={"access_key_id": access_key_id[:10] + "..."},
        )

        # Create STS client with IAM credentials
        sts_client = session.client(
            "sts",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=__get_client_config(),
        )

        # First, try to get caller identity to validate credentials
        try:
            log.trace("Validating IAM credentials with get_caller_identity")
            identity = sts_client.get_caller_identity()
            log.trace(
                "IAM credentials validated successfully",
                details={
                    "user_id": identity.get("UserId"),
                    "account": identity.get("Account"),
                    "arn": identity.get("Arn"),
                },
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            log.trace(
                "IAM credential validation failed", details={"error_code": error_code}
            )

            if error_code == "InvalidUserID.NotFound":
                return {"status": "error", "message": "Invalid access key ID"}
            elif error_code == "SignatureDoesNotMatch":
                return {"status": "error", "message": "Invalid secret access key"}
            elif error_code == "TokenRefreshRequired":
                return {"status": "error", "message": "Token refresh required"}
            else:
                return {
                    "status": "error",
                    "message": f"Authentication failed: {str(e)}",
                }

        # Check if MFA is required by attempting to get session token
        try:
            log.trace("Attempting to get session token")

            # If MFA code is provided, use it
            if mfa_code:
                if not mfa_serial:
                    # Try to determine MFA serial from the user ARN
                    user_arn = identity.get("Arn")
                    if user_arn and ":user/" in user_arn:
                        username = user_arn.split(":user/")[1]
                        account_id = identity.get("Account")
                        mfa_serial = f"arn:aws:iam::{account_id}:mfa/{username}"
                        log.trace(
                            "Inferred MFA serial", details={"mfa_serial": mfa_serial}
                        )

                if not mfa_serial:
                    return {
                        "status": "error",
                        "message": "MFA serial number required when providing MFA code",
                    }

                log.trace(
                    "Getting session token with MFA", details={"mfa_serial": mfa_serial}
                )
                session_response = sts_client.get_session_token(
                    SerialNumber=mfa_serial, TokenCode=mfa_code
                )
            else:
                # Try without MFA first
                log.trace("Getting session token without MFA")
                session_response = sts_client.get_session_token()

            session_credentials = session_response["Credentials"]
            log.trace("Session token obtained successfully")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            log.trace(
                "Session token request failed", details={"error_code": error_code}
            )

            if error_code == "AccessDenied":
                # This likely means MFA is required
                if not mfa_code:
                    log.trace("MFA required for session token")

                    # Try to get MFA devices for the user
                    try:
                        # Create IAM client to list MFA devices
                        iam_client_instance = session.client(
                            "iam",
                            aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key,
                            config=__get_client_config(),
                        )

                        # Get username from ARN
                        user_arn = identity.get("Arn")
                        if user_arn and ":user/" in user_arn:
                            username = user_arn.split(":user/")[1]

                            mfa_devices = iam_client_instance.list_mfa_devices(
                                UserName=username
                            )
                            if mfa_devices["MFADevices"]:
                                mfa_device = mfa_devices["MFADevices"][0]
                                mfa_serial = mfa_device["SerialNumber"]

                                log.trace(
                                    "MFA device found",
                                    details={"mfa_serial": mfa_serial},
                                )

                                return {
                                    "status": "mfa_required",
                                    "mfa_serial": mfa_serial,
                                    "challenge_type": "TOTP",
                                    "message": "Please provide your MFA code",
                                }

                        return {
                            "status": "error",
                            "message": "MFA is required but no MFA devices found",
                        }

                    except ClientError as iam_error:
                        log.trace(
                            "Failed to list MFA devices",
                            details={"error": str(iam_error)},
                        )
                        return {
                            "status": "mfa_required",
                            "challenge_type": "TOTP",
                            "message": "MFA is required. Please provide mfa_code and mfa_serial parameters.",
                        }
                else:
                    return {
                        "status": "error",
                        "message": "Invalid MFA code or MFA serial number",
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get session token: {str(e)}",
                }

        # At this point we have valid session credentials
        final_credentials = {
            "AccessKeyId": session_credentials["AccessKeyId"],
            "SecretAccessKey": session_credentials["SecretAccessKey"],
            "SessionToken": session_credentials["SessionToken"],
            "Expiration": session_credentials["Expiration"],
        }

        # If a role is specified, assume it
        role_arn = kwargs.get("role")
        if role_arn:
            log.trace(
                "Assuming role after IAM authentication", details={"role": role_arn}
            )
            role_credentials = _assume_role_with_credentials(
                final_credentials, role_arn, **kwargs
            )
            if role_credentials:
                final_credentials = role_credentials
                log.trace("Role assumption successful")
            else:
                log.trace("Role assumption failed, using session credentials")

        log.trace("IAM authentication completed successfully")
        return {
            "status": "authenticated",
            "credentials": final_credentials,
            "identity": {
                "user_id": identity.get("UserId"),
                "account": identity.get("Account"),
                "arn": identity.get("Arn"),
            },
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        log.trace("IAM authentication failed", details={"error_code": error_code})

        if error_code == "InvalidUserID.NotFound":
            return {"status": "error", "message": "Invalid access key ID"}
        elif error_code == "SignatureDoesNotMatch":
            return {"status": "error", "message": "Invalid secret access key"}
        elif error_code == "AccessDenied":
            return {
                "status": "error",
                "message": "Access denied - check your credentials and permissions",
            }
        else:
            return {"status": "error", "message": f"Authentication failed: {str(e)}"}
    except Exception as e:
        log.trace("IAM authentication error", details={"error": str(e)})
        log.error("IAM authentication error: {}", e)
        return {"status": "error", "message": f"Authentication error: {str(e)}"}


def _assume_role_with_credentials(
    credentials: dict[str, Any], role_arn: str, **kwargs
) -> dict[str, Any] | None:
    """Assume a role using provided credentials.

    Takes existing credentials and uses them to assume a different IAM role,
    returning the new temporary credentials for the assumed role.

    Args:
        credentials: The credentials to use for role assumption containing
            AccessKeyId, SecretKey, and SessionToken.
        role_arn: The ARN of the role to assume.
        **kwargs: Additional arguments passed to session creation.

    Returns:
        The assumed role credentials dictionary, or None if assumption failed.
    """
    try:
        session = get_session(**kwargs)

        sts_client = session.client(
            "sts",
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretKey"],
            aws_session_token=credentials["SessionToken"],
            config=__get_client_config(),
        )

        session_name = (
            f"{CORE_AUTOMATION_SESSION_ID_PREFIX}-login-{util.get_current_timestamp()}"
        )

        log.trace(
            "Assuming role with credentials",
            details={"role_arn": role_arn, "session_name": session_name},
        )

        result = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)

        log.trace(
            "Role assumption successful",
            details={
                "role_arn": role_arn,
                "access_key_id": result["Credentials"]["AccessKeyId"][:10] + "...",
            },
        )

        return result["Credentials"]

    except ClientError as e:
        log.trace(
            "Role assumption failed", details={"role_arn": role_arn, "error": str(e)}
        )
        log.error("Failed to assume role {}: {}", role_arn, e)
        return None


def get_role_credentials(role: str) -> dict[str, Any] | None:
    """Retrieve cached credentials for a specific role.

    Args:
        role: The ARN of the role to retrieve credentials for.

    Returns:
        A dictionary containing the cached credentials, or None if not found.
    """
    return store.retrieve_data(role)


def clear_role_credentials(role: str) -> None:
    """Clear cached credentials for a specific role.

    Args:
        role: The ARN of the role to clear credentials for.
    """
    store.clear_data(role)


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


def assume_role(**kwargs) -> dict[str, str] | None:
    """Assume an IAM role and return temporary credentials.

    Attempts to assume the specified IAM role using cached credentials when
    available. Falls back to base session credentials if no role is provided
    or if role assumption fails.

    Args:
        **kwargs: Optional keyword arguments including:
            role (str): The ARN of the role to assume.
            role_arn (str): Alternative parameter name for role ARN.
            Role (str): Alternative parameter name for role ARN.
            RoleArn (str): Alternative parameter name for role ARN.

    Returns:
        A dictionary of credentials containing AccessKeyId, SecretAccessKey,
        SessionToken, and Expiration, or None if credential retrieval fails.
    """
    role_arn = (
        kwargs.get("role")
        or kwargs.get("role_arn")
        or kwargs.get("Role")
        or kwargs.get("RoleArn")
    )
    if not role_arn:
        return get_session_credentials()

    credentials = store.retrieve_data(role_arn)
    if credentials:
        return credentials

    try:
        session = get_session(**kwargs)

        session_name = (
            f"{CORE_AUTOMATION_SESSION_ID_PREFIX}-{util.get_current_timestamp()}"
        )
        log.debug("Assuming role [{}] with session name [{}]", role_arn, session_name)
        # Call the STS client with the session and role ARN directy instead of sts_client() to avoid recursion
        client = session.client("sts", **kwargs, config=__get_client_config())
        response = client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
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
    """Create a Boto3 client, using assumed role credentials if a role is provided.

    Creates AWS service clients with automatic credential management, using
    assumed role credentials when a role is specified in kwargs.

    Args:
        service_name: The name of the AWS service (e.g., 's3', 'sts', 'ec2').
        **kwargs: Optional keyword arguments including 'role' for role assumption
            and other parameters passed to the Boto3 client constructor.

    Returns:
        An initialized Boto3 client for the specified service.
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
    endpoint = util.get_cognito_endpoint("http://localhjost:4566")
    return get_client("cognito-idp", **kwargs, endpoint_url=endpoint)


def get_resource(service_name: str, **kwargs) -> Any:
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
    kwargs["region"] = kwargs.get("region", util.get_dynamodb_region())
    return get_resource("dynamodb", **kwargs)


def invoke_lambda(
    arn: str, request_payload: dict[str, Any], **kwargs
) -> dict[str, Any]:
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
    """Generate a basic authorization context for AWS service access.

    Creates a standard context dictionary used for authorization in
    AWS service interactions within the Core Automation framework.

    Returns:
        A dictionary containing default authorization context with
        DeliveredBy and AuthorizationToken fields.
    """
    return {"DeliveredBy": "user", "AuthorizationToken": "temp cred auth token id"}


def grant_assume_role_permission(
    user_name: str, role_name: str, account_id: str, **kwargs
) -> None:
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
