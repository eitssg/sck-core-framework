import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_boto_session():
    with patch("boto3.session.Session") as mock_boto_session:

        mock_frozen_credentials = MagicMock()
        mock_frozen_credentials.access_key = "mock_access_key"
        mock_frozen_credentials.secret_key = "mock_secret_key"
        mock_frozen_credentials.token = "mock_session_token"

        yield mock_boto_session
