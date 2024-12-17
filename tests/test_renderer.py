import os
import yaml
import pytest
from unittest.mock import patch, MagicMock
from core_renderer import Jinja2Renderer


@pytest.fixture
def mock_boto_session():
    with patch("boto3.session.Session") as mock_boto_session:

        mock_frozen_credentials = MagicMock()
        mock_frozen_credentials.access_key = "mock_access_key"
        mock_frozen_credentials.secret_key = "mock_secret_key"
        mock_frozen_credentials.token = "mock_session_token"

        yield mock_boto_session


def convert_line_endings(text: str) -> str:
    """
    Convert all line endings in the given text to the OS default line endings.
    """
    return text.replace("\n", os.linesep)


def get_sample_facts():
    try:
        # Get the filename in the same directory as this script file
        fn = os.path.join(os.path.dirname(__file__), "sample_facts.yaml")

        with open(fn, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        assert False, str(e)


@pytest.mark.asyncio
async def test_render():

    # Get the folder path of this running test script
    current_path = os.path.dirname(os.path.realpath(__file__))

    template_path = os.path.join(current_path, "templates")
    renderer = Jinja2Renderer(template_path)

    context = get_sample_facts()

    try:
        file_folder = ""

        os.environ["DEBUG "] = "True"
        os.environ["TEMPLATE_DEBUG "] = "False"

        result = renderer.render_files(file_folder, context)
        assert result is not None

        data = result["test_render.yaml.j2"]
        data = convert_line_endings(data)
        print(data)

    except Exception as e:
        assert False, str(e)
