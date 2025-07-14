from datetime import datetime, timezone
import json
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import core_helper.aws as aws
import os
import io

from core_framework.constants import TR_RESPONSE, TR_STATUS


@pytest.fixture
def mock_identity():
    return {
        "Arn": "arn:aws:iam::123456789012:user/jbarwick",
        "UserId": "AIDAJDPLRKLG7UEXAMPLE",
        "Account": "123456789012",
    }


@pytest.fixture
def mock_client():


@pytest.fixture
def mock_session(mock_client):

    with patch("boto3.session.Session") as mock_boto_session:

        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123456789012:user/jbarwick",
            "UserId": "AIDAJDPLRKLG7UEXAMPLE",
            "Account": "123456789012",
        }

        mock_frozen_credentials = MagicMock()
        mock_frozen_credentials.access_key = "mock_access_key"
        mock_frozen_credentials.secret_key = "mock_secret_key"
        mock_frozen_credentials.token = "mock_session_token"

        mock_session_credentials = MagicMock()
        mock_session_credentials.get_frozen_credentials.return_value = (
            mock_frozen_credentials
        )

        mock_session = MagicMock()
        mock_session.get_credentials.return_value = mock_session_credentials
        mock_session.client.return_value = mock_client

        mock_boto_session.return_value = mock_session

        yield mock_boto_session


@pytest.fixture(autouse=True, scope="function")
def mock_stdout():
    with patch("sys.stdout", new_callable=io.StringIO) as mock:
        yield mock


@pytest.fixture
def prn():
    return "prn:example"


def test_get_identity(mock_session):

    identity = aws.get_identity()

    assert identity is not None
    assert "Arn" in identity
    assert identity["Arn"].endswith(":user/jbarwick")


def test_get_identity_client_error(mock_session):

    with patch("core_helper.aws.sts_client") as mock_sts:
        mock_sts.side_effect = ClientError(
            error_response={"Error": {"Code": "Test", "Message": "fail"}},
            operation_name="GetCallerIdentity",
        )
        assert aws.get_identity() is None


def test_get_session(mock_session):

    creds = aws.get_session_credentials()
    if not creds:
        assert False, "Credentials are None"

    assert creds["AccessKeyId"] == "mock_access_key"
    assert creds["SecretAccessKey"] == "mock_secret_key"
    assert creds["SessionToken"] == "mock_session_token"

    session = aws.get_session()

    assert session is not None
    assert mock_session.called

    assert (
        session.get_credentials().get_frozen_credentials().access_key
        == "mock_access_key"
    )
    assert (
        session.get_credentials().get_frozen_credentials().secret_key
        == "mock_secret_key"
    )
    assert (
        session.get_credentials().get_frozen_credentials().token == "mock_session_token"
    )


def get_invoke_response():

    data = json.dumps(
        {
            "status": "success",
            "data": {"key": "value"},
            "code": 200,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return io.BytesIO(data.encode("utf-8"))


def test_invoke_lambda(mock_session):

    arn = os.getenv(
        "API_LAMBDA_ARN",
        "arn:aws:lambda:ap-sourtheast-1:123456789012:function:core-invoker",
    )
    payload = {"action": "example:action", "data": {"key": "value"}}

    mock_client = mock_session.return_value.client.return_value

    mock_client.invoke.return_value = {
        "StatusCode": 200,
        "Payload": get_invoke_response(),
    }

    result = aws.invoke_lambda(arn, payload)

    assert result is not None
    assert TR_STATUS in result
    assert result[TR_STATUS] == "ok"
    assert TR_RESPONSE in result
    assert "status" in result[TR_RESPONSE]
    assert result[TR_RESPONSE]["status"] == "success"
    assert "data" in result[TR_RESPONSE]
    assert result[TR_RESPONSE]["data"] == {"key": "value"}
    assert "code" in result[TR_RESPONSE]
    assert result[TR_RESPONSE]["code"] == 200


def test_get_session_credentials(mock_session):

    credentials = aws.get_session_credentials()

    if not credentials:
        assert False, "Credentials are None"

    assert credentials["AccessKeyId"] == "mock_access_key"
    assert credentials["SecretAccessKey"] == "mock_secret_key"
    assert credentials["SessionToken"] == "mock_session_token"


def test_get_session_credentials_client_error(mock_boto_session):

    session = aws.get_session()
    # Change the value of the MagicMock mock_boto_session get_credentials to return None
    session.get_credentials.return_value = None

    assert aws.get_session_credentials() is None


def test_assume_role(mock_session):

    mock_response = {
        "Credentials": {
            "AccessKeyId": "mock_access_key",
            "SecretAccessKey": "mock_secret_key",
            "SessionToken": "mock_session_token",
        },
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    mock_client.assume_role.return_value = mock_response

    role = "arn:aws:iam::123456789012:role/mock-role"
    credentials = aws.assume_role(role=role)

    if not credentials:
        assert False, "Credentials are None"

    credentials = aws.assume_role()

    if not credentials:
        assert False, "Credentials are None.  Should have come from store"

    assert credentials["AccessKeyId"] == "mock_access_key"
    assert credentials["SecretAccessKey"] == "mock_secret_key"
    assert credentials["SessionToken"] == "mock_session_token"

    creds = aws.get_role_credentials(role)

    assert creds is not None
    assert creds["AccessKeyId"] == "mock_access_key"
    assert creds["SecretAccessKey"] == "mock_secret_key"
    assert creds["SessionToken"] == "mock_session_token"


def test_get_client__config():
    from core_helper.aws import __get_client_config, RETRY_CONFIG

    one = "http://proxy.example.com:8080"
    two = "https://proxy.example.com:8080"

    os.environ["HTTP_PROXY"] = one
    os.environ["HTTPS_PROXY"] = two

    # Clear any existing environment variables to ensure test isolation

    def do_the_test(p1, p2):
        config = aws.__get_client_config()

        assert config is not None

        # Check default values
        assert config.proxies == {"http": p1, "https": p2}
        assert config.read_timeout == 15
        assert config.connect_timeout == 15
        assert config.retries == RETRY_CONFIG

    do_the_test(one, two)

    del os.environ["HTTPS_PROXY"]

    do_the_test(one, one)

    del os.environ["HTTP_PROXY"]

    os.environ["HTTPS_PROXY"] = two

    do_the_test(two, two)

    del os.environ["HTTPS_PROXY"]

    config = aws.__get_client_config()

    assert config is not None
    assert config.proxies == None
    assert config.read_timeout == 15
    assert config.connect_timeout == 15
    assert config.retries == RETRY_CONFIG


def test_login_to_aws(mock_boto_session, mock_client):

    session = aws.get_session()

    assume_role = MagicMock()
    assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "role_mock_access_key",
            "SecretAccessKey": "role_mock_secret_key",
            "SessionToken": "role_mock_session_token",
        },
    }
    mock_client.assume_role = assume_role
    session.return_value.client.return_value = mock_client

    auth = {
        "AccessKeyId": "mock_access_key",
        "SecretAccessKey": "mock_secret_key",
        "SessionToken": "mock_session_token",
    }
    result = aws.login_to_aws(auth)

    assert result is not None

    assert "AccessKeyId" in result and result["AccessKeyId"] == "role_mock_access_key"
    assert (
        "SecretAccessKey" in result
        and result["SecretAccessKey"] == "role_mock_secret_key"
    )
    assert (
        "SessionToken" in result and result["SessionToken"] == "role_mock_session_token"
    )


def test_login_to_aws_client_error(mock_boto_session, mock_client):

    session = aws.get_session()
    mock_client.assume_role.side_effect = ClientError(
        error_response={"Error": {"Code": "Test", "Message": "fail"}},
        operation_name="AssumeRole",
    )
    session.return_value.client.return_value = mock_client

    auth = {
        "AccessKeyId": "mock_access_key",
        "SecretAccessKey": "mock_secret_key",
        "SessionToken": "mock_session_token",
    }
    result = aws.login_to_aws(auth, role="abc")
    assert result is None


def test_get_client(mock_boto_session):

    client = aws.get_client("s3", region="us-west-2")

    assert client is not None
    assert mock_boto_session.called


def test_transform_stack_parameter_hash():
    keyvalues = {"Key1": "Value1", "Key2": "Value2"}
    result = aws.transform_stack_parameter_hash(keyvalues)
    expected = [
        {"ParameterKey": "Key1", "ParameterValue": "Value1"},
        {"ParameterKey": "Key2", "ParameterValue": "Value2"},
    ]
    assert result == expected


def test_transform_tag_hash():
    keyvalues = {"Key1": "Value1", "Key2": "Value2"}
    result = aws.transform_tag_hash(keyvalues)
    expected = [{"Key": "Key1", "Value": "Value1"}, {"Key": "Key2", "Value": "Value2"}]
    assert result == expected


def test_transform_stack_parameter_dict():

    assert aws.transform_stack_parameter_dict({}) == {}
    assert aws.transform_stack_parameter_dict({"A": "B"}) == {"A": "B"}


if __name__ == "__main__":
    pytest.main()
