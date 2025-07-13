import os
import pytest
from unittest.mock import patch, MagicMock
from core_renderer import Jinja2Renderer
import core_framework as util
import jinja2
import traceback
import ruamel.yaml as yaml


@pytest.fixture
def mock_boto_session():
    with patch("boto3.session.Session") as mock_boto_session:

        mock_frozen_credentials = MagicMock()
        mock_frozen_credentials.access_key = "mock_access_key"
        mock_frozen_credentials.secret_key = "mock_secret_key"
        mock_frozen_credentials.token = "mock_session_token"

        mock_credentials = MagicMock()
        mock_credentials.get_frozen_credentials.return_value = mock_frozen_credentials

        mock_boto_session.return_value.get_credentials.return_value = mock_credentials

        yield mock_boto_session


def convert_to_unix_line_endings(text: str) -> str:
    """
    Convert all line endings in the given text to the OS default line endings.
    """

    # Ensure that the line endings are in Unix format
    return text.replace("\r\n", "\n").replace("\r", "\n")


@pytest.fixture
def contexts():
    try:
        # Get the filename in the same directory as this script file
        fn = os.path.join(os.path.dirname(__file__), "sample_facts.yaml")

        with open(fn, "r") as f:
            return util.read_yaml(f)

    except FileNotFoundError:
        raise FileNotFoundError(f"Sample facts file not found: {fn}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")
    except Exception as e:
        assert False, str(e)


@pytest.fixture
def filter_template():
    try:
        # Get the filters template file and return its content
        fn = os.path.join(
            os.path.dirname(__file__), "templates", "test_filters.yaml.j2"
        )
        with open(fn, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {fn}")
    except Exception as e:
        assert False, str(e)


@pytest.mark.asyncio
async def test_render(contexts):

    # Get the folder path of this running test script
    current_path = os.path.dirname(os.path.realpath(__file__))

    template_path = os.path.join(current_path, "templates")
    renderer = Jinja2Renderer(template_path)

    try:
        file_folder = ""

        os.environ["DEBUG "] = "True"
        os.environ["TEMPLATE_DEBUG "] = "False"

        result = renderer.render_files(file_folder, contexts)
        assert result is not None

        yaml_data = result["test_filters.yaml.j2"]

        # Convert it back to test Roundtrip
        data = util.from_yaml(yaml_data)

        assert data is not None

        yaml_data = result["test_render.yaml.j2"]

        # Convert it back to test Roundtrip
        data = util.from_yaml(yaml_data)

        assert data is not None

    except jinja2.exceptions.TemplateError as e:
        # This catches specific Jinja2 errors (Syntax, Undefined variable, etc.)
        # and provides much more context than a generic exception.
        error_details = f"Jinja2 Template Error: {e.__class__.__name__}\n"
        if hasattr(e, "name") and e.name:
            error_details += f"  File: {e.name}\n"
        if hasattr(e, "lineno"):
            error_details += f"  Line: {e.lineno}\n"
        error_details += f"  Message: {e.message}"
        assert False, error_details
    except Exception as e:
        # For any other type of error, print the full stack trace
        print(e)
        traceback.print_exc()
        assert False, "An unexpected, non-Jinja2 error occurred during rendering."
