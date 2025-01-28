""" AWS Helper functions that provide Automation Role switching for all deployment functions and Lambda's """

from typing import Any
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

from .cache import InsecureEnclave

store = InsecureEnclave()


def transform_stack_parameter_dict(keyvalues: dict[str, str]) -> dict[str, str]:
    rv = {}
    if len(keyvalues):
        for key, value in keyvalues.items():
            rv[key] = value
    return rv


def transform_stack_parameter_hash(keyvalues: dict[str, str]) -> list[dict[str, str]]:
    """
    Translate a basic dictionary into CloudFormation stack paramters object

    Input:  { "Name": "My Name" }

    Output: [{"ParameterKey": "Name", "ParameterValue: "My Name"}]

    Args:
        keyvalues (dict[str, str]): Simple Key/Value Pairs

    Returns:
        list[dict[str, str]]: List of Parameters to be passed to Cloudformation stack actions.

    """
    return __transform_keyvalues_to_array(keyvalues, "ParameterKey", "ParameterValue")


def transform_tag_hash(keyvalues: dict[str, str]) -> list[dict[str, str]]:
    """
    Tranlate a basic dictionary into a list of Tags values that can be applied
    to CloudFormation Resources:

    Input:  { "Name": "My Name" }

    Output:

    """
    return __transform_keyvalues_to_array(keyvalues, "Key", "Value")


def get_session_key(session: Session) -> str | None:
    prefix = util.get_automation_scope() or "ca-"
    return f"{prefix}{session.profile_name}-{session.region_name}"


def get_session(**kwargs) -> Session:

    region = kwargs.get("region", util.get_region())
    profile_name = kwargs.get("aws_profile", util.get_aws_profile())
    session_token = kwargs.get("session_token", kwargs.get("sessionToken", None))

    # the store key is generated from the profile and region
    prefix = util.get_automation_scope() or "ca"
    key = f"{prefix}{profile_name}-{region}"

    session = store.retrieve_session(key)

    if session is None:
        session = boto3.session.Session(
            region_name=region,
            profile_name=profile_name,
            aws_session_token=session_token,
        )
        store.store_session(key, session, ttl=300)  # 5 minutes

    return session


def get_session_credentials(**kwargs) -> dict | None:
    """
    REturns the credentials information for the current session/role that has been assumed.
    If no role assumed, then this is the user's credentials.

    Returns:
        dict: A dictionary with the following keys:
            - AccessKeyId
            - SecretAccessKey
            - SessionToken
    """
    session = get_session(**kwargs)
    credentials = session.get_credentials()

    if credentials:
        frozen_credentials = credentials.get_frozen_credentials()
        if frozen_credentials:
            # ALWAYS expire defauult credentials
            creds = {
                "AccessKeyId": frozen_credentials.access_key,
                "SecretAccessKey": frozen_credentials.secret_key,
                "SessionToken": frozen_credentials.token,
            }
            return creds

    return None


def login_to_aws(auth: dict[str, str], **kwargs) -> dict[str, str] | None:

    role = kwargs.get("role", None)

    sts_client = get_session(**kwargs).client(
        "sts",
        aws_access_key_id=auth["AccessKeyId"],
        aws_secret_access_key=auth["SecretAccessKey"],
        aws_session_token=auth["SessionToken"],
        config=__get_client_config(),
    )

    try:

        result = sts_client.assume_role(
            RoleArn=role, RoleSessionName="AssumeRoleSession1"
        )

    except ClientError as e:
        log.error("Failed to get identity: {}", e)
        return None

    return result["Credentials"]


def get_role_credentials(role: str) -> dict[str, Any]:
    return store.retrieve_data(role) or {}


def __get_client_config() -> Config:

    http_proxy = os.getenv("HTTP_PROXY", os.getenv("http_proxy", None))
    https_proxy = os.getenv("HTTPS_PROXY", os.getenv("https_proxy", None))
    if http_proxy and not https_proxy:
        https_proxy = http_proxy
    elif https_proxy and not http_proxy:
        http_proxy = https_proxy

    if http_proxy and https_proxy:
        proxy_definition = {"http": http_proxy, "https": https_proxy}
    else:
        proxy_definition = None

    return Config(
        proxies=proxy_definition,
        connect_timeout=15,
        read_timeout=15,
        retries=dict(max_attempts=10),
    )


def assume_role(**kwargs) -> dict[str, str] | None:
    """
    Assume a role using the current session credentials and get the credentials.

    If the role is None, the function will return the current session credentials.

    Args:
        role (str | None, optional): A role to assume. Defaults to None.

    Returns:
        dict[str, str] | None: credetials object containing AccessKeyId, SecretAccessKey, and SessionToken.
    """

    role = kwargs.get("role", None)

    if role is None:
        return get_session_credentials()

    credentials = store.retrieve_data(role)
    if credentials:
        return credentials

    try:
        # Assume the role if no role credentials exist or existing credentials have expired

        session = get_session(**kwargs)

        key = get_session_key(session)

        # Generate a unique session name if not provided
        session_name = f"{CORE_AUTOMATION_SESSION_ID_PREFIX}-{key}"

        # Assume / re-assume the role to get new credentials
        log.debug("Assuming role [{}] session namae [{}]", role, session_name)

        client = session.client("sts", config=__get_client_config())

        sts_response = client.assume_role(RoleArn=role, RoleSessionName=session_name)
        if (
            sts_response["ResponseMetadata"]["HTTPStatusCode"] == 200
            and "Credentials" in sts_response
        ):
            credentials = sts_response["Credentials"]
            if isinstance(credentials, dict):
                store.store_data(role, credentials, ttl=300)  # 5 minutes
                return credentials

    except ClientError as e:
        log.error("Failed to assume role {}: {}", role, e)

    return get_session_credentials()


def get_identity(
    token: str | None = None, role: str | None = None
) -> dict[str, str] | None:
    """Assume the specified role and return the user information along with the credentials"""
    try:
        if role:
            client = sts_client(session_token=token, role=role)
            credentials = get_role_credentials(role)
        else:
            client = sts_client(session_token=token)
            response = client.get_session_token()
            credentials = response.get("Credentials")

        if not credentials:
            return None

        identity = client.get_caller_identity()

        response = {
            "UserId": identity["UserId"],
            "Account": identity["Account"],
            "Arn": identity["Arn"],
            "AccessKeyId": credentials["AccessKeyId"],
            "SecretAccessKey": credentials["SecretAccessKey"],
            "SessionToken": credentials["SessionToken"],
            "Expiration": credentials["Expiration"],
        }

        return response

    except ClientError as e:
        log.error("Failed to get identity: {}", e)
        return None


def get_session_token() -> dict | None:
    """
    Get the current session token from the AWS credentials.

    Returns:
        str: The session token, or None if the token is not available.
    """
    credentials = get_session_credentials()
    if credentials:
        session_token = credentials.get("SessionToken")
        if session_token:
            return credentials
        client = sts_client()
        response = client.get_session_token()
        credentials["SessionToken"] = response.get("Credentials", {}).get(
            "SessionToken"
        )
        return credentials

    return None


def get_client(service, **kwargs) -> Any:

    session = get_session(**kwargs)

    # you better have "role" paramter in kwargs!
    credentials = assume_role(**kwargs)

    if credentials is None:
        client = session.client(service, config=__get_client_config())
    else:
        client = session.client(
            service,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            config=__get_client_config(),
        )
    return client


def get_client_credentials(client: Any) -> dict[str, str] | None:
    """
    Retrieve the credentials details from a Boto3 client.

    Args:
        client (Any): The Boto3 client.

    Returns:
        dict: A dictionary with the following keys:
            - AccessKeyId
            - SecretAccessKey
            - SessionToken
    """
    credentials = client._request_signer._credentials
    if credentials:
        frozen_credentials = credentials.get_frozen_credentials()
        if frozen_credentials:
            creds = {
                "AccessKeyId": frozen_credentials.access_key,
                "SecretAccessKey": frozen_credentials.secret_key,
                "SessionToken": frozen_credentials.token,
            }
            return creds

    return None


def sts_client(**kwargs) -> Any:
    return get_client("sts", **kwargs)


def cfn_client(**kwargs) -> Any:
    return get_client("cloudformation", **kwargs)


def cloudwatch_client(**kwargs) -> Any:
    return get_client("cloudwatch", **kwargs)


def cloudfront_client(**kwargs) -> Any:
    return get_client("cloudfront", **kwargs)


def ec2_client(**kwargs) -> Any:
    return get_client("ec2", **kwargs)


def ecr_client(**kwargs) -> Any:
    return get_client("ecr", **kwargs)


def elb_client(**kwargs) -> Any:
    return get_client("elb", **kwargs)


def elbv2_client(**kwargs) -> Any:
    return get_client("elbv2", **kwargs)


def iam_client(**kwargs) -> Any:
    return get_client("iam", **kwargs)


def kms_client(**kwargs) -> Any:
    return get_client("kms", **kwargs)


def lambda_client(**kwargs) -> Any:
    return get_client("lambda", **kwargs)


def rds_client(**kwargs) -> Any:
    return get_client("rds", **kwargs)


def s3_client(**kwargs) -> Any:
    return get_client("s3", **kwargs)


def org_client(**kwargs) -> Any:
    return get_client("organizations", **kwargs)


def step_functions_client(**kwargs) -> Any:
    return get_client("stepfunctions", **kwargs)


def r53_client(**kwargs) -> Any:
    return get_client("route53", **kwargs)


def get_resource(service, **kwargs) -> Any:

    session = get_session(**kwargs)

    credentials = assume_role(**kwargs)

    if credentials is None:
        resource = session.resource(
            service,
            config=Config(
                connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
            ),
        )
    else:
        resource = session.resource(
            service,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            config=Config(
                connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
            ),
        )
    return resource


def s3_resource(**kwargs) -> Any:
    return get_resource("s3", **kwargs)


def dynamodb_resource(**kwargs) -> Any:
    region = kwargs.get("region", util.get_dynamodb_region())
    kwargs["region"] = region
    return get_resource("dynamodb", **kwargs)


def invoke_lambda(
    arn: str, request_payload: dict[str, Any], **kwargs
) -> dict[str, Any]:

    kwargs["region"] = kwargs.get("region", arn.split(":")[3])

    client = lambda_client(**kwargs)

    log.trace(
        "Invoking Lambda", details={"FunctionName": arn, "Payload": request_payload}
    )

    try:

        request = util.to_json(request_payload)
        response = client.invoke(FunctionName=arn, Payload=request)

    except Exception as e:

        log.warn("Failed to invoke FunctionName={}, e={}", arn, e)

        return {
            TR_STATUS: "error",
            TR_RESPONSE: "Failed to invoke Lambda - {}".format(e),
        }

    status_code = int(response.get("StatusCode")) if "StatusCode" in response else 0

    if "Payload" in response:
        raw_data = response.get("Payload").read()
        decoded_data = raw_data.decode("utf-8")

    response_payload = util.from_json(decoded_data) if decoded_data else None

    function_error: str | None = response.get("FunctionError", None)

    # Build the detaisl for the log message
    details: dict[str, Any] = {"StatusCode": status_code, "Payload": response_payload}

    if function_error is not None:
        details["FunctionError"] = function_error

    # Log the details
    log.trace("Lambda invoked response: ", details=details)

    if status_code < 200 or status_code >= 300:
        log.error("Lambda invocation failed (status code {})", status_code)
        status = "error"

    elif function_error is not None:
        log.error(
            "The invoked Lambda encountered an error ({})",
            function_error,
            details=response_payload,
        )
        status = "error"

    else:
        status = "ok"

    log.debug(
        "Invoked Lambda: status ({})",
        status,
        details={"FunctionName": arn, "Payload": response_payload},
    )

    return {TR_STATUS: status, TR_RESPONSE: response_payload}


def __transform_keyvalues_to_array(
    keyvalues: dict[str, str], key_key: str, value_key: str
) -> list[dict[str, str]]:

    if keyvalues is None:
        return None

    return [{key_key: key, value_key: value} for key, value in keyvalues.items()]


def generate_context() -> dict:
    """
    This should be used to begin an authorization_context to provide
    access tokens and temporary credentials for boto3 aws service access

    """
    return {"DeliveredBy": "user", "AuthorizationToken": "temp cred auth token id"}


def grant_assume_role_permission(
    user_name: str, role_name: str, account_id: str, **kwargs
) -> None:
    """
    This function grants the user the ability to assume the role sepecified in the account
    specified.

    Args:
        user_name (str): The username of the user to grant the permission to
        role_name (str): The name of the role the user should be able to assume
        account_id (str): The account ID where this role is defined
    """
    # Define the policy name
    policy_name = "AssumeRolePolicy"

    client = iam_client(**kwargs)

    # Try to retrieve the existing user policy
    try:
        existing_policy = client.get_user_policy(
            UserName=user_name, PolicyName=policy_name
        )
        policy_document = existing_policy["PolicyDocument"]
    except client.exceptions.NoSuchEntityException:
        # If the policy does not exist, create a new one
        policy_document = {"Version": "2012-10-17", "Statement": []}

    # Ensure the policy has a statement for sts:AssumeRole
    assume_role_statement = next(
        (
            stmt
            for stmt in policy_document["Statement"]
            if stmt["Action"] == "sts:AssumeRole"
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

    # Add the role ARNs to the assume role statement
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    # Bail out if the arn is already in the policy.
    if role_arn in assume_role_statement["Resource"]:
        return

    assume_role_statement["Resource"].append(role_arn)

    # Attach the updated policy to the user
    client.put_user_policy(
        UserName=user_name,
        PolicyName=policy_name,
        PolicyDocument=util.to_json(policy_document),
    )

    # Update the trust policy for each role
    role = client.get_role(RoleName=role_name)
    trust_policy = role["Role"]["AssumeRolePolicyDocument"]

    # Check if the user is already in the trust policy
    user_arn = f"arn:aws:iam::{account_id}:user/{user_name}"
    if not any(
        stmt
        for stmt in trust_policy["Statement"]
        if stmt["Effect"] == "Allow" and stmt["Principal"].get("AWS") == user_arn
    ):
        trust_policy["Statement"].append(
            {
                "Effect": "Allow",
                "Principal": {"AWS": user_arn},
                "Action": "sts:AssumeRole",
            }
        )

    # Update the role's trust policy
    client.update_assume_role_policy(
        RoleName=role_name, PolicyDocument=util.to_json(trust_policy)
    )


def revoke_assume_role_permission(
    user_name: str, role_name: str, account_id: str, **kwargs
):

    client = iam_client(**kwargs)

    # Define the policy name
    policy_name = "AssumeRolePolicy"

    # Try to retrieve the existing user policy
    try:
        existing_policy = client.get_user_policy(
            UserName=user_name, PolicyName=policy_name
        )
        policy_document = existing_policy["PolicyDocument"]

        # Ensure the policy has a statement for sts:AssumeRole
        assume_role_statement = next(
            (
                stmt
                for stmt in policy_document["Statement"]
                if stmt["Action"] == "sts:AssumeRole"
            ),
            None,
        )

        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

        # Bail out if the role is not in the policy
        if (
            not assume_role_statement
            or role_arn not in assume_role_statement["Resource"]
        ):
            return

        assume_role_statement["Resource"].remove(role_arn)

        # Remove the assume role statement if no resources are left
        if not assume_role_statement["Resource"]:
            policy_document["Statement"].remove(assume_role_statement)

        if not policy_document["Statement"]:
            client.delete_user_policy(UserName=user_name, PolicyName=policy_name)
        else:
            # Attach the updated policy to the user
            client.put_user_policy(
                UserName=user_name,
                PolicyName=policy_name,
                PolicyDocument=util.to_json(policy_document),
            )

    except client.exceptions.NoSuchEntityException:
        # If the policy does not exist, there's nothing to revoke.
        return

    try:
        # Update the trust policy for the role
        role = client.get_role(RoleName=role_name)
        trust_policy = role["Role"]["AssumeRolePolicyDocument"]

        # Remove the user from the trust policy
        user_arn = f"arn:aws:iam::{account_id}:user/{user_name}"

        trust_policy["Statement"] = [
            stmt
            for stmt in trust_policy["Statement"]
            if stmt["Action"] != "sts:AssumeRole"
            or stmt["Effect"] != "Allow"
            or stmt.get("Principal", {}).get("AWS") != user_arn
        ]

        # Update the role's trust policy with the new policy
        client.update_assume_role_policy(
            RoleName=role_name, PolicyDocument=util.to_json(trust_policy)
        )
    except Exception as e:
        log.error("Error updating trust policy for role {}: {}", role_name, e)
        return False
