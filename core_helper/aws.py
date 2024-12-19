""" AWS Helper functions that provide Automation Role switching for all deployment functions and Lambda's """

from typing import Any

import os
import json
import boto3
import uuid

from datetime import datetime, timedelta
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

__credentials: dict = {}
__session = None
__session_id = None


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


def get_session() -> Session:
    global __session, __session_id
    if __session is None:
        __session = (
            boto3.session.Session()
        )  # Use the name we will "patch" with in pytest
        __session_id = str(uuid.uuid4())
    return __session


def get_session_credentials() -> dict | None:
    """
    REturns the credentials information for the current session/role that has been assumed.
    If no role assumed, then this is the user's credentials.

    Returns:
        dict: A dictionary with the following keys:
            - AccessKeyId
            - SecretAccessKey
            - SessionToken
    """
    session = get_session()
    credentials = session.get_credentials()

    if credentials:
        frozen_credentials = credentials.get_frozen_credentials()
        if frozen_credentials:
            return {
                "AccessKeyId": frozen_credentials.access_key,
                "SecretAccessKey": frozen_credentials.secret_key,
                "SessionToken": frozen_credentials.token,
                "Expiration": datetime.fromordinal(
                    1
                ),  # ALWAYS expire defauult credentials
            }
    return None


def login_to_aws(auth: dict[str, str], role: str) -> dict[str, str] | None:

    sts_client = get_session().client(
        "sts",
        aws_access_key_id=auth["AccessKeyId"],
        aws_secret_access_key=auth["SecretAccessKey"],
        aws_session_token=auth["SessionToken"],
    )

    try:

        result = sts_client.assume_role(
            RoleArn=role, RoleSessionName="AssumeRoleSession1"
        )

    except ClientError as e:
        log.error("Failed to get identity: {}", e)
        return None

    return result["Credentials"]


def check_if_user_authorised(auth: dict[str, str] | None, role: str) -> bool:
    """
    Validate the provided AWS credentials and check if they have permissions to assume the specified role.

    Args:
        auth (Dict[str, Any]): User credentials object containing AccessKeyId, SecretAccessKey, and SessionToken.

    Returns:
        bool: True if the credentials are valid and can assume the specified role, False otherwise.
    """
    try:
        if auth is None:
            return True

        auth = get_identity()

        return True  # FIXME Actually authorize the user

        # if 'accountId' not in auth or 'accessKey' not in auth or 'user' not in auth:
        #     raise ValueError('Missing required credentials')

        # return True

    except ClientError as e:
        print(f"Authorization failed: {e}")
        return False


def assume_role(role: str | None = None) -> dict[str, str] | None:
    """
    Assume a role using the current session credentials and get the credentials.

    If the role is None, the function will return the current session credentials.

    Args:
        role (str | None, optional): A role to assume. Defaults to None.

    Returns:
        dict[str, str] | None: credetials object containing AccessKeyId, SecretAccessKey, and SessionToken.
    """
    global __credentials
    global __session_id

    if role is None:
        return get_session_credentials()

    # Generate a unique session name if not provided
    session_name = f"{CORE_AUTOMATION_SESSION_ID_PREFIX}-{__session_id}"

    # Assume the role if no role credentials exist or existing credentials have expired
    if role not in __credentials or __should_renew(__credentials[role]["Expiration"]):

        session = get_session()

        try:
            # Assume / re-assume the role to get new credentials
            log.debug("Assuming IAM Role (role: {})", role)

            client = session.client(
                "sts",
                config=Config(
                    connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
                ),
            )

            sts_response = client.assume_role(
                RoleArn=role, RoleSessionName=session_name
            )
            __credentials[role] = sts_response["Credentials"]

        except ClientError as e:
            log.error("Failed to assume role {}: {}", role, e)
            __credentials[role] = get_session_credentials()

    return __credentials[role]


def get_identity() -> dict[str, str] | None:

    try:
        client = sts_client()

        # Call the get_caller_identity method
        response = client.get_caller_identity()

        return {
            "UserId": response["UserId"],
            "Account": response["Account"],
            "Arn": response["Arn"],
        }
    except ClientError as e:
        log.error("Failed to get identity: {}", e)
        return None


def get_client(service, region: str | None, role: str | None) -> Any:

    session = get_session()

    credentials = assume_role(role)

    if credentials is None:
        client = session.client(
            service,
            region_name=region,
            config=Config(
                connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
            ),
        )
    else:
        client = session.client(
            service,
            region_name=region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            config=Config(
                connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
            ),
        )
    return client


def sts_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("sts", region, role)


def cfn_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("cloudformation", region, role)


def cloudwatch_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("cloudwatch", region, role)


def cloudfront_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("cloudfront", region, role)


def ec2_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("ec2", region, role)


def ecr_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("ecr", region, role)


def elb_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("elb", region, role)


def elbv2_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("elbv2", region, role)


def iam_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("iam", region, role)


def kms_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("kms", region, role)


def lambda_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("lambda", region, role)


def rds_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("rds", region, role)


def s3_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("s3", region, role)


def org_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("organizations", region, role)


def step_functions_client(region: str | None = None, role: str | None = None) -> Any:
    return get_client("stepfunctions", region, role)


def get_resource(service, region: str | None = None, role: str | None = None) -> Any:

    session = get_session()

    credentials = assume_role(role)

    if credentials is None:
        resource = session.resource(
            service,
            region_name=region,
            config=Config(
                connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
            ),
        )
    else:
        resource = session.resource(
            service,
            region_name=region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            config=Config(
                connect_timeout=15, read_timeout=15, retries=dict(max_attempts=10)
            ),
        )
    return resource


def s3_resource(region: str | None = None, role: str | None = None) -> Any:
    return get_resource("s3", region, role)


def dynamodb_resource(region: str | None = None, role: str | None = None) -> Any:
    if not region:
        region = os.environ.get("DYNAMODB_REGION", "us-east-1")
    return get_resource("dynamodb", region, role)


def invoke_lambda(
    arn: str, request_payload: dict[str, Any], role: str | None = None
) -> dict[str, Any]:

    region = arn.split(":")[3]
    client = lambda_client(region, role)

    log.trace(
        "Invoking Lambda", details={"FunctionName": arn, "Payload": request_payload}
    )

    try:

        request = json.dumps(request_payload)
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


# Determine if credentials should be renewed
# Returns true if expiration date has passed or is less than 5 minutes away
def __should_renew(expiration: datetime | None) -> bool:
    if expiration is None:
        return False
    else:
        return (expiration - datetime.now(expiration.tzinfo)) < timedelta(minutes=5)


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
    user_name: str, role_name: str, account_id: str
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

    client = iam_client()

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


def revoke_assume_role_permission(user_name: str, role_name: str, account_id: str):

    client = iam_client()

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
