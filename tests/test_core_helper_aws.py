from datetime import datetime, timedelta, timezone
import json
import pytest
from unittest.mock import patch, MagicMock
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
def mock_boto_session(real_aws):

    # if real_aws is true, then do not mock boto3.session.Session

    if real_aws:
        yield MagicMock(), MagicMock()

    else:
        with patch("boto3.session.Session") as mock_boto_session:

            mock_frozen_credentials = MagicMock()
            mock_frozen_credentials.access_key = "mock_access_key"
            mock_frozen_credentials.secret_key = "mock_secret_key"
            mock_frozen_credentials.token = "mock_session_token"

            mock_session_credentials = MagicMock()
            mock_session_credentials.get_frozen_credentials.return_value = (
                mock_frozen_credentials
            )

            mock_client = MagicMock()
            mock_client.get_caller_identity.return_value = {
                "Arn": "arn:aws:iam::123456789012:user/jbarwick",
                "Account": "123456789012",
                "UserId": "jbarwick",
            }

            mock_session = MagicMock()
            mock_session.get_credentials.return_value = mock_session_credentials
            mock_session.client.return_value = mock_client

            mock_boto_session.return_value = mock_session

            yield mock_boto_session, mock_client


@pytest.fixture(autouse=True, scope="function")
def mock_stdout():
    with patch("sys.stdout", new_callable=io.StringIO) as mock:
        yield mock


@pytest.fixture(autouse=True, scope="function")
def reset_awshelper_state():
    # Reset the state of aws between tests
    aws.__session = None
    aws.__credentials = {}


@pytest.fixture
def prn():
    return "prn:example"


@pytest.fixture
def real_aws(pytestconfig):
    return pytestconfig.getoption("--real-aws")


def test_get_identity(mock_boto_session, real_aws):

    if not real_aws:
        mock_client = mock_boto_session[1]
        mock_client.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123456789012:user/jbarwick",
            "UserId": "mock_access_key",
            "Account": "123456789012",
        }

    identity = aws.get_identity()

    assert identity is not None
    assert "Arn" in identity
    assert identity["Arn"].endswith(":user/jbarwick")


def __get_access_key():

    credentials = aws.get_session_credentials()
    return credentials["AccessKeyId"]


def test_get_session(mock_boto_session, real_aws):

    aws.__session = None

    check_value = __get_access_key()

    session = aws.get_session()
    assert session is not None

    credentials = session.get_credentials()

    assert credentials is not None
    creds = credentials.get_frozen_credentials()

    assert creds is not None
    assert creds.access_key == check_value

    assert creds.token is not None


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


def test_invoke_lambda(mock_boto_session, real_aws):

    aws.__session = None

    arn = os.getenv(
        "API_LAMBDA_ARN",
        "arn:aws:lambda:ap-sourtheast-1:123456789012:function:core-invoker",
    )
    payload = {"action": "example:action", "data": {"key": "value"}}

    if not real_aws:
        mock_client = mock_boto_session[1]
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


def test_get_session_credentials(mock_boto_session, real_aws):

    credentials = aws.get_session_credentials()

    if real_aws:
        assert "AccessKeyId" in credentials
        assert "SecretAccessKey" in credentials
        assert "SessionToken" in credentials
    else:
        assert credentials["AccessKeyId"] == "mock_access_key"
        assert credentials["SecretAccessKey"] == "mock_secret_key"
        assert credentials["SessionToken"] == "mock_session_token"


def test_assume_role(mock_boto_session, real_aws):
    if real_aws:
        role = os.getenv("AWS_ROLE_ARN")
        credentials = aws.assume_role(role)
        assert "AccessKeyId" in credentials
        assert "SecretAccessKey" in credentials
        assert "SessionToken" in credentials
    else:

        mock_client = mock_boto_session[1]

        mock_response = {
            "Credentials": {
                "AccessKeyId": "mock_access_key",
                "SecretAccessKey": "mock_secret_key",
                "SessionToken": "mock_session_token",
                "Expiration": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }
        mock_client.assume_role.return_value = mock_response

    role = "arn:aws:iam::123456789012:role/mock-role"
    credentials = aws.assume_role(role)

    assert credentials["AccessKeyId"] == "mock_access_key"
    assert credentials["SecretAccessKey"] == "mock_secret_key"
    assert credentials["SessionToken"] == "mock_session_token"


def test_get_client(mock_boto_session, real_aws):
    if real_aws:
        client = aws.get_client("s3", "us-west-2", None)
        assert client is not None
    else:
        client = aws.get_client("s3", "us-west-2", None)
        assert mock_boto_session[0].called
        assert client is not None


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


if __name__ == "__main__":
    pytest.main()
