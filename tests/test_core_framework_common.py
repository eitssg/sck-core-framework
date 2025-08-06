"""
This module is to test the core framework common utilities.

The functions to test are in the file "core_framework/common.py"

the import is:

import core_framework as util

All functions in 'core_framework.common' are exposed in "core_framwork.__init__" so that
they can be imported directly from the core_framework module.  This is to allow for a more
standard import style across the core automation framework.

this has become the standard 'style' for importing the core automation framework.

Perhaps in the future, I'll call it "import core_framwork as core" or
"import core_framework as cf" but for now, it is util.

"""

from botocore.exceptions import ProfileNotFound
from decimal import Decimal
import tempfile
import io
import os
from datetime import datetime, date, time
import pytest
from unittest.mock import patch
import core_framework as util

from core_framework.models import (
    TaskPayload,
    DeploymentDetails,
    PackageDetails,
    DeploySpec,
    ActionSpec,
)

from core_framework.constants import (
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
    SCOPE_PORTFOLIO,
    ENV_SCOPE,
    ENV_CLIENT,
    ENV_BUCKET_REGION,
    ENV_DOCUMENT_BUCKET_NAME,
    ENV_UI_BUCKET_NAME,
    ENV_ARTEFACT_BUCKET_NAME,
    ENV_AUTOMATION_TYPE,
    ENV_PORTFOLIO,
    ENV_APP,
    ENV_BRANCH,
    ENV_BUILD,
    ENV_AUTOMATION_ACCOUNT,
    ENV_ORGANIZATION_ID,
    ENV_ORGANIZATION_NAME,
    ENV_ORGANIZATION_ACCOUNT,
    ENV_ORGANIZATION_EMAIL,
    ENV_IAM_ACCOUNT,
    ENV_AUDIT_ACCOUNT,
    ENV_SECURITY_ACCOUNT,
    ENV_NETWORK_ACCOUNT,
    ENV_DOMAIN,
    ENV_CDK_DEFAULT_ACCOUNT,
    ENV_CDK_DEFAULT_REGION,
    ENV_CONSOLE,
    ENV_USE_S3,
    ENV_LOCAL_MODE,
    ENV_LOG_AS_JSON,
    ENV_CONSOLE_LOG,
    ENV_LOG_LEVEL,
    ENV_ENFORCE_VALIDATION,
    ENV_AWS_PROFILE,
    ENV_VOLUME,
    ENV_CLIENT_NAME,
    ENV_LOG_DIR,
    ENV_DELIVERED_BY,
    ENV_AWS_REGION,
    ENV_CLIENT_REGION,
    ENV_MASTER_REGION,
    ENV_AUTOMATION_REGION,
    ENV_DYNAMODB_REGION,
    ENV_DYNAMODB_HOST,
    ENV_AUTOMATION_ACCOUNT,
    ENV_INVOKER_LAMBDA_ARN,
    ENV_INVOKER_LAMBDA_NAME,
    ENV_INVOKER_LAMBDA_REGION,
    ENV_START_RUNNER_LAMBDA_ARN,
    ENV_API_HOST_URL,
    ENV_API_LAMBDA_ARN,
    ENV_API_LAMBDA_NAME,
    ENV_EXECUTE_LAMBDA_ARN,
    ENV_PROJECT,
    ENV_BIZAPP,
    ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN,
    ENV_COMPONENT_COMPILER_LAMBDA_ARN,
    ENV_CORRELATION_ID,
    ENV_ENVIRONMENT,
    V_INTERACTIVE,
    V_DEPLOYSPEC,
    V_PIPELINE,
    V_SERVICE,
    V_LOCAL,
    V_DEFAULT_REGION,
    V_EMPTY,
)


@pytest.fixture
def mock_stdout():
    with patch("sys.stdout", new_callable=io.StringIO) as mock:
        yield mock


@pytest.fixture
def prn():
    return "prn:example"


def test_get_identity():

    try:
        # requird to instantiate the DeploymentDetails class
        os.environ["CLIENT"] = "example_client"

        input_data = {
            "portfolio": "portfolio",
            "app": "app",
            "branch": "branch-very-long-name",
            "build": "build",
        }

        data = DeploymentDetails.from_arguments(**input_data)

        identity = data.get_identity()

        # Branch should be a "short" name (20 characters or less)
        assert identity == "prn:portfolio:app:branch-very-long-nam:build"
    except Exception as e:
        print(e)
        assert False, e


def test_get_configuration_bucket_name():

    bucket_name = util.generate_bucket_name("Example_Client", "Example_Branch", "scope-")

    assert bucket_name == "scope-example_client-core-automation-example_branch"

    bucket_name = util.get_bucket_name("baskets")

    assert bucket_name == "baskets-core-automation-ap-southeast-1"

    bucket_name = util.get_bucket_name()

    client = util.get_client()
    if client:
        assert bucket_name == f"{client}-core-automation-ap-southeast-1"
    else:
        assert bucket_name == "core-automation-master"


def test_generate_branch_short_name():
    # Test with a normal branch name
    assert util.generate_branch_short_name("feature/new-feature") == "feature-new-feature"

    # Test with a branch name containing uppercase letters
    assert util.generate_branch_short_name("Feature/New-Feature") == "feature-new-feature"

    # Test with a branch name containing special characters
    assert util.generate_branch_short_name("feature/new@feature!") == "feature-new-feature"

    # Test with a branch name that is exactly 20 characters long, but if the last character is a hyphen, it's stripped
    assert util.generate_branch_short_name("feature/new-feature-1234") == "feature-new-feature"

    # Test with a branch name that is longer than 20 characters
    assert util.generate_branch_short_name("feature/new-feature-1234567890") == "feature-new-feature"

    # Test with a branch name containing trailing hyphens
    assert util.generate_branch_short_name("feature/new-feature-") == "feature-new-feature"

    # Test with a branch name containing only special characters
    assert util.generate_branch_short_name("@@@@") == ""

    # Test with a branch name containing only digits
    assert util.generate_branch_short_name("1234567890") == "1234567890"

    # Test with an empty branch name
    assert util.generate_branch_short_name("") == ""

    # Test with None as the branch name
    assert util.generate_branch_short_name(None) is None


def test_generate_task_payload():
    # Define the input parameters
    task = "deploy"
    kwargs = {
        "force": True,
        "dry_run": False,
        "client": "example_client",
        "portfolio": "example_portfolio",
        "app": "example_app",
        "branch": "main_branch",
        "build": "build-123",
        "environment": "dev",
        "data_center": "sin",
        "component": "example_component",
        "automation_type": "deployspec",
        "mode": "local",
    }

    # Generate the task payload
    payload = TaskPayload.from_arguments(task=task, **kwargs)
    payload.package.deployspec = None

    # Assert the payload contains the expected values
    assert payload.task == task
    assert payload.force == kwargs["force"]
    assert payload.dry_run == kwargs["dry_run"]
    assert payload.type == kwargs["automation_type"]

    deployspec_data = []

    # Add more assertions for identity, deployment, and package details
    identity_details = "prn:example_portfolio:example_app:main-branch:build-123"
    deployment_details = DeploymentDetails.from_arguments(**kwargs)
    package_details = PackageDetails.from_arguments(
        deployment_details=deployment_details,
        deployspec=deployspec_data,
        **kwargs,
    )

    assert payload.identity == identity_details
    assert payload.deployment_details == deployment_details
    assert payload.package == package_details

    assert package_details.temp_dir is not None


def test_split_portfolio():

    # this is a specialized function that assume the PRN portfolio is in the format of "company-group-department-bizapp"
    # Company    is a Gitlab Group or GitHub Organization
    # Group      is a Gitlab Group or GitHub Group
    # Department is a Gitlab Group or GitHub Group
    # bizapp     is a Jira Project Code or Gitlab Group or GitHub project/group

    results = util.split_portfolio("company-group-department-bizapp")

    assert results == ("company", "group", "department", "bizapp")

    results = util.split_portfolio("group-department-bizapp")

    assert results == (None, "group", "department", "bizapp")

    results = util.split_portfolio("department-bizapp")

    assert results == (None, None, "department", "bizapp")

    results = util.split_portfolio("bizapp")

    assert results == (None, None, None, "bizapp")


def test_split_branch():

    result = util.split_branch("branch-dc")

    assert result == ("branch", "dc")

    result = util.split_branch("branch")

    assert result == ("branch", "use")


def test_get_artefacts_path():

    task_payload = util.generate_task_payload(
        task="deploy",
        client="example_client",
        portfolio="example_portfolio",
        app="example_app",
        branch="main_branch",
        build="build-123",
        environment="dev",
        data_center="sin",
        component="example_component",
        automation_type="deployspec",
    )

    path = util.get_artefacts_path(task_payload.deployment_details)

    # standard path separator is colon
    assert path == os.path.sep.join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
        ]
    )

    path = util.get_artefacts_path(task_payload.deployment_details, s3=True)

    # S3 paths are slashes not semi-colons
    assert path == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
        ]
    )

    path = util.get_artefacts_path(task_payload.deployment_details, "bubbles", s3=False)

    # Add another path component 'bubbles' to the end
    assert path == os.path.sep.join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "bubbles",
        ]
    )

    path = util.get_artefacts_path(task_payload.deployment_details, "bubbles", s3=True)

    # Add another path component 'bubbles' to the end
    assert path == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "bubbles",
        ]
    )


def test_get_packages_path():

    task_payload = util.generate_task_payload(
        task="deploy",
        client="example_client",
        portfolio="example_portfolio",
        app="example_app",
        branch="main_branch",
        build="build-123",
        environment="dev",
        data_center="sin",
        component="example_component",
        automation_type="deployspec",
    )

    path = util.get_packages_path(task_payload.deployment_details)

    # standard path separator is colon
    assert path == os.path.sep.join(["packages", "example_portfolio", "example_app", "main-branch", "build-123"])

    path = util.get_packages_path(task_payload.deployment_details, s3=True)

    # S3 paths are slashes not semi-colons
    assert path == "/".join(["packages", "example_portfolio", "example_app", "main-branch", "build-123"])

    path = util.get_packages_path(task_payload.deployment_details, "bubbles", s3=False)

    # Add another path component 'bubbles' to the end
    assert path == os.path.sep.join(
        [
            "packages",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "bubbles",
        ]
    )

    path = util.get_packages_path(task_payload.deployment_details, "bubbles", s3=True)

    # Add another path component 'bubbles' to the end
    assert path == "/".join(
        [
            "packages",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "bubbles",
        ]
    )


def test_get_files_path():

    task_payload = util.generate_task_payload(
        task="deploy",
        client="example_client",
        portfolio="example_portfolio",
        app="example_app",
        branch="main_branch",
        build="build-123",
        environment="dev",
        data_center="sin",
        component="example_component",
        automation_type="deployspec",
    )

    path = util.get_files_path(task_payload.deployment_details)

    # standard path separator is semi-colon
    assert path == os.path.sep.join(["files", "example_portfolio", "example_app", "main-branch", "build-123"])

    path = util.get_files_path(task_payload.deployment_details, s3=True)

    # S3 paths are slashes not semi-colons
    assert path == "/".join(["files", "example_portfolio", "example_app", "main-branch", "build-123"])

    path = util.get_files_path(task_payload.deployment_details, "bubbles", s3=False)

    # Add another path component 'bubbles' to the end
    assert path == os.path.sep.join(
        [
            "files",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "bubbles",
        ]
    )

    path = util.get_files_path(task_payload.deployment_details, "bubbles", s3=True)

    # Add another path component 'bubbles' to the end
    assert path == "/".join(
        [
            "files",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "bubbles",
        ]
    )


def test_get_artefact_key():

    deployment_details = util.generate_deployment_details(
        client="example_client",
        portfolio="example_portfolio",
        app="example_app",
        branch="main_branch",
        build="build-123",
        environment="dev",
        data_center="sin",
        component="example_component",
    )

    name = "artefact_name"

    deployment_details.scope = SCOPE_BUILD
    key = util.get_artefact_key(deployment_details, name)

    assert key == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "build-123",
            "artefact_name",
        ]
    )

    deployment_details.scope = SCOPE_BRANCH
    key = util.get_artefact_key(deployment_details, name)

    assert key == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "artefact_name",
        ]
    )

    deployment_details.scope = SCOPE_APP
    key = util.get_artefact_key(deployment_details, name)

    assert key == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "artefact_name",
        ]
    )

    deployment_details.scope = SCOPE_PORTFOLIO
    key = util.get_artefact_key(deployment_details, name)

    assert key == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "artefact_name",
        ]
    )


def test_generate_deployment_details_from_stack():

    kwargs = {
        "force": True,
        "dry_run": False,
        "client": "example_client",
        "portfolio": "example_portfolio",
        "app": "example_app",
        "branch": "main_branch",
        "build": "build-123",
        "environment": "dev",
        "data_center": "sin",
        "component": "example_component",
        "automation_type": "deployspec",
        "stacks": [
            {
                "stack_file": "template.yaml",
                "stack_name": "example_stack",
                "accounts": ["example_account"],
                "regions": ["example_region"],
                "stack_policy": "stack_policy",
            }
        ],
    }

    deplayment_details = util.generate_deployment_details_from_stack(**kwargs)

    assert len(deplayment_details) == 1

    dd = deplayment_details[0]

    assert dd.client == "example_client"
    assert dd.portfolio == "example_portfolio"

    assert dd.stack_file == "template.yaml"
    assert dd.app == "example_stack"
    assert dd.branch == "example_region"
    assert dd.branch_short_name == "example-region"

    assert dd.build == "build-123"
    assert dd.environment == "dev"
    assert dd.data_center == "sin"
    assert dd.component == "example_component"


def test_get_prn_and_alt():

    result = util.get_prn("portfolio", "app", "branch", "build", "component", SCOPE_BUILD)

    assert result == "portfolio:app:branch:build"

    result = util.get_prn("portfolio", "app", "branch", "build", "component", SCOPE_COMPONENT)

    assert result == "portfolio:app:branch:build:component"

    result = util.get_prn_alt("portfolio", "app", "branch", "build", "component", SCOPE_BUILD)

    assert result == "portfolio-app-branch-build"


def test_get_prn_scope():

    prn = "prn:portfolio:app:branch:build"

    result = util.get_prn_scope(prn)

    assert result == SCOPE_BUILD

    prn = "prn:portfolio:app:branch"

    result = util.get_prn_scope(prn)

    assert result == SCOPE_BRANCH

    prn = "prn:portfolio:app"

    result = util.get_prn_scope(prn)

    assert result == SCOPE_APP

    prn = "prn:portfolio"

    result = util.get_prn_scope(prn)

    assert result == SCOPE_PORTFOLIO


def test_is_local_mode():

    if "LOCAL_MODE" in os.environ:
        del os.environ["LOCAL_MODE"]

    assert util.is_local_mode() is False

    os.environ["LOCAL_MODE"] = "true"

    assert util.is_local_mode() is True

    os.environ["LOCAL_MODE"] = "false"

    assert util.is_local_mode() is False


def test_split_prn():

    result = util.split_prn("prn:portfolio:app:branch:build:component")
    assert result == (
        "portfolio",
        "app",
        "branch",
        "build",
        "component",
    ), "Should split PRN into its components"

    result = util.split_prn("prn:portfolio:app:branch:build")
    assert result == (
        "portfolio",
        "app",
        "branch",
        "build",
        None,
    ), "Should handle missing component in PRN"

    result = util.split_prn("prn:portfolio:app:branch")
    assert result == (
        "portfolio",
        "app",
        "branch",
        None,
        None,
    ), "Should handle missing build and component in PRN"
    result = util.split_prn("prn:portfolio:app")
    assert result == (
        "portfolio",
        "app",
        None,
        None,
        None,
    ), "Should handle missing branch, build, and component in PRN"
    result = util.split_prn("prn:portfolio")
    assert result == (
        "portfolio",
        None,
        None,
        None,
        None,
    ), "Should handle missing app, branch, build, and component in PRN"
    with pytest.raises(ValueError, match="PRN must start with 'prn:'"):
        util.split_prn("invalid:prn:format")


def test_split_portfolio():
    try:
        util.split_portfolio("a-b-c-d-e")
        assert False, "Should raise ValueError for invalid portfolio string"
    except ValueError as e:
        assert (
            str(e) == 'Portfolio should have 1 to 4 segments separated by a dash "-"'
        ), "Should raise ValueError for invalid portfolio string"
    result = util.split_portfolio("company-group-department-bizapp")
    assert result == (
        "company",
        "group",
        "department",
        "bizapp",
    ), "Should split portfolio into its components"
    result = util.split_portfolio("group-department-bizapp")
    assert result == (
        None,
        "group",
        "department",
        "bizapp",
    ), "Should handle missing company"
    result = util.split_portfolio("department-bizapp")
    assert result == (None, None, "department", "bizapp"), "Should handle missing group"
    result = util.split_portfolio("bizapp")
    assert result == (None, None, None, "bizapp"), "Should handle only bizapp"
    # pass empty string as portfolio string should result in exception and expect the ValueError to return "Portfolio name must be specified."
    try:
        util.split_portfolio("")
        assert False, "Should raise ValueError for empty portfolio string"
    except ValueError as e:
        assert str(e) == "Portfolio name must be specified.", "Should raise ValueError for empty portfolio string"

    try:
        util.split_portfolio(None)
        assert False, "Should raise ValueError for None portfolio string"
    except ValueError as e:
        assert str(e) == "Portfolio name must be specified.", "Should raise ValueError for None portfolio string"


def test_split_branch():
    result = util.split_branch("branch-dc")
    assert result == ("branch", "dc"), "Should split branch into name and data center"
    result = util.split_branch("branch")
    assert result == ("branch", "use"), "Should default region/data-center to 'use'"
    result = util.split_branch("branch", "rdc")
    assert result == ("branch", "rdc"), "Should use provided region/data-center"
    result = util.split_branch(None)
    assert result == (
        "master",
        "use",
    ), "Should return 'master' for branch and 'use' for region when None is provided"


def test_get_prn():

    prn = util.get_prn("portfolio", "app", "branch", "build", "component", SCOPE_PORTFOLIO)

    assert prn == "portfolio", "PRN should match the expected format for SCOPE_PORTFOLIO"

    prn = util.get_prn("portfolio", "app", "branch", "build", "component", SCOPE_APP)

    assert prn == "portfolio:app", "PRN should match the expected format for SCOPE_APP"

    prn = util.get_prn("portfolio", "app", "branch", "build", "component", SCOPE_BRANCH)

    assert prn == "portfolio:app:branch", "PRN should match the expected format for SCOPE_BRANCH"

    prn = util.get_prn(
        portfolio="portfolio",
        app="app",
        branch="branch",
        build="build",
        component="component",
        scope=SCOPE_BUILD,
        delim=",",
    )

    assert prn == "portfolio,app,branch,build", "PRN should match the expected format"

    prn = util.get_prn(
        portfolio="portfolio",
        app="app",
        branch="branch",
        build="build",
        component="component",
        scope=SCOPE_COMPONENT,
    )

    assert prn == "portfolio:app:branch:build:component", "PRN should match the expected format"

    prn = util.get_prn(portfolio="portfolio", app="app", branch="branch", build="build")

    assert prn == "portfolio:app:branch:build", "PRN should match the expected format"

    prn = util.get_prn(portfolio="portfolio", app="app", branch="branch")

    assert prn == "portfolio:app:branch", "PRN should match the expected format"

    prn = util.get_prn(portfolio="portfolio", app="app")

    assert prn == "portfolio:app", "PRN should match the expected format"

    prn = util.get_prn(portfolio="portfolio")

    assert prn == "portfolio", "PRN should match the expected format"


def test_generate_bucket_name():

    os.environ[ENV_SCOPE] = "test_scope-"
    os.environ[ENV_CLIENT] = "default_client"
    os.environ[ENV_BUCKET_REGION] = "test_region"

    # Test that the bucket name is generated correctly with all parameters.

    bucket_name = util.generate_bucket_name(client="example_client", scope_prefix="scope-", region="example_region")

    assert bucket_name == "scope-example_client-core-automation-example_region", "1 - Bucket name should match the expected format"

    # Test that the default region is used if not specified.  Scope prefix comes from menvironment
    # variable "SCOPE" and a dash will be added automatically

    bucket_name = util.generate_bucket_name(client="test")

    assert (
        bucket_name == "test_scope-test-core-automation-test_region"
    ), "2 - Bucket name should match the expected format with default scoope and region from env variables"

    # Test that the default region is used if not specified.  Scope prefix will be set to blank

    bucket_name = util.generate_bucket_name(client="test", scope_prefix="")

    assert (
        bucket_name == "test-core-automation-test_region"
    ), "3 - Bucket name should match the expected format with default scoope and region from env variables"

    # test that the default client is used if not specified.  Kill the scope and to eliminate scope prefix

    del os.environ[ENV_SCOPE]

    bucket_name = util.generate_bucket_name()

    assert (
        bucket_name == "default_client-core-automation-test_region"
    ), "4 - Bucket name should match the expected format with the no scope, client and test region from env variables"


def test_get_bucket_name():

    os.environ[ENV_BUCKET_REGION] = "ap-southeast-1"
    os.environ[ENV_SCOPE] = "test-scope-"
    os.environ[ENV_CLIENT] = "test-client"

    bucket_name = util.get_bucket_name(client="example_client", region="example_region")
    assert (
        bucket_name == "test-scope-example_client-core-automation-example_region"
    ), "1 - Bucket name should match the expected format"

    # Test with defaults

    os.environ[ENV_SCOPE] = ""
    os.environ[ENV_BUCKET_REGION] = ""
    bucket_name = util.get_bucket_name()
    assert (
        bucket_name == "test-client-core-automation-ap-southeast-1"
    ), "2 - Bucket name should match the expected format with default client and region"


def test_get_document_bucket_name():

    os.environ[ENV_BUCKET_REGION] = "example_region"
    os.environ[ENV_SCOPE] = "example_scope-"
    os.environ[ENV_DOCUMENT_BUCKET_NAME] = "core-document-bucket-us-east-1"
    os.environ[ENV_CLIENT] = "example_client"

    bucket_name = util.get_document_bucket_name()

    assert bucket_name == "core-document-bucket-us-east-1", "1 - Document bucket name should match the expected format"

    os.environ[ENV_DOCUMENT_BUCKET_NAME] = ""

    bucket_name = util.get_document_bucket_name()

    assert (
        bucket_name == "example_scope-example_client-core-automation-example_region"
    ), "2 - Document bucket name should match the expected format with scope and region from env variables"


def test_get_ui_bucket_name():

    os.environ[ENV_BUCKET_REGION] = "example_region"
    os.environ[ENV_SCOPE] = "example_scope-"
    os.environ[ENV_UI_BUCKET_NAME] = "core-ui-bucket-us-east-1"
    os.environ[ENV_CLIENT] = "example_client"

    bucket_name = util.get_ui_bucket_name()

    assert bucket_name == "core-ui-bucket-us-east-1", "1 - UI bucket name should match the expected format"

    os.environ[ENV_UI_BUCKET_NAME] = ""

    bucket_name = util.get_ui_bucket_name()

    assert (
        bucket_name == "example_scope-example_client-core-automation-example_region"
    ), "2 - UI bucket name should match the expected format with scope and region from env variables"


def test_get_artefact_bucket_name():
    os.environ[ENV_BUCKET_REGION] = "example_region"
    os.environ[ENV_SCOPE] = "example_scope-"
    os.environ[ENV_ARTEFACT_BUCKET_NAME] = "core-artefact-bucket-us-east-1"
    os.environ[ENV_CLIENT] = "example_client"

    bucket_name = util.get_artefact_bucket_name()

    assert bucket_name == "core-artefact-bucket-us-east-1", "1 - Artefact bucket name should match the expected format"

    os.environ[ENV_ARTEFACT_BUCKET_NAME] = ""

    bucket_name = util.get_artefact_bucket_name()

    assert (
        bucket_name == "example_scope-example_client-core-automation-example_region"
    ), "2 - Artefactr bucket name should match the expected format with scope and region from env variables"


def test_get_artefact_bucket_region():

    os.environ[ENV_BUCKET_REGION] = "ap-southeast-1"

    region = util.get_artefact_bucket_region()
    assert region == "ap-southeast-1", "1 - Artefact bucket region should match the expected format"


def test_get_prn_alt():

    prn = util.get_prn_alt(
        portfolio="portfolio",
        app="app",
        branch="branch",
        build="build",
        component="component",
        scope=SCOPE_BUILD,
    )

    assert prn == "portfolio-app-branch-build", "PRN Alt should match the expected format for SCOPE_BUILD"

    prn = util.get_prn_alt(
        portfolio="portfolio",
        app="app",
        branch="branch",
        build="build",
        component="component",
        scope=SCOPE_COMPONENT,
    )

    assert prn == "portfolio-app-branch-build-component", "PRN Alt should match the expected format for SCOPE_COMPONENT"


def test_get_automation_scope():

    os.environ[ENV_SCOPE] = "test_scope-"

    scope = util.get_automation_scope()
    assert scope == "test_scope-", "1 - Automation scope should match the expected format with scope from env variables"

    del os.environ[ENV_SCOPE]

    scope = util.get_automation_scope()
    assert scope == "", "2 - Automation scope should be empty if ENV_SCOPE is not set"


def test_get_automation_type():

    os.environ[ENV_AUTOMATION_TYPE] = V_DEPLOYSPEC

    automation_type = util.get_automation_type()
    assert automation_type == V_DEPLOYSPEC, "1 - Automation type should match the expected format with default deployspec"

    del os.environ[ENV_AUTOMATION_TYPE]

    automation_type = util.get_automation_type()
    assert automation_type == V_PIPELINE, "2 - Automation type should be pipeline if ENV_AUTOMATION_TYPE is not set"


def test_get_portfolio():

    os.environ[ENV_PORTFOLIO] = "default_portfolio"

    portfolio = util.get_portfolio()

    assert portfolio == "default_portfolio", "1 - Portfolio should match the expected format with default portfolio"

    del os.environ[ENV_PORTFOLIO]

    portfolio = util.get_app()
    assert portfolio is None, "2 - Portfolio should be empty if ENV_PORTFOLIO is not set"


def test_get_app():

    os.environ[ENV_APP] = "default_app"

    app = util.get_app()

    assert app == "default_app", "1 - App should match the expected format with default portfolio"

    del os.environ[ENV_APP]

    app = util.get_app()

    assert app is None, "2 - App should be empty if ENV_PORTFOLIO is not set"


def test_get_branch():

    os.environ[ENV_BRANCH] = "default_branch"

    branch = util.get_branch()

    assert branch == "default_branch", "1 - Branch should match the expected format with default portfolio"

    # Per requirements, make sure None is returned if ENV_BRANCH is not set

    del os.environ[ENV_BRANCH]

    branch = util.get_branch()

    assert branch is None, "2 - Branch should be empty if ENV_PORTFOLIO is not set"


def test_get_build():

    os.environ[ENV_BUILD] = "default_build"

    build = util.get_build()

    assert build == "default_build", "1 - Build should match the expected format with default portfolio"

    # Per requirements, make sure None is returned if ENV_BUILD is not set

    del os.environ[ENV_BUILD]

    build = util.get_build()

    assert build is None, "2 - Build should be empty if ENV_PORTFOLIO is not set"


def test_get_provisioning_role_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"

    role_arn = util.get_provisioning_role_arn(account="456789012345")

    assert (
        role_arn == "arn:aws:iam::456789012345:role/PipelineProvisioning"
    ), "Provisioning role ARN should match the expected format"

    # Test with default account from environment variable if one is not provided

    role_arn = util.get_provisioning_role_arn()

    assert (
        role_arn == "arn:aws:iam::123456789012:role/PipelineProvisioning"
    ), "Provisioning role ARN should match the expected format"


def test_get_automation_api_role_arn():
    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"

    role_arn = util.get_automation_api_role_arn(account="456789012345")
    assert (
        role_arn == "arn:aws:iam::456789012345:role/CoreAutomationApiRead"
    ), "Automation API role ARN should match the expected format"
    role_arn = util.get_automation_api_role_arn(write=True)
    assert (
        role_arn == "arn:aws:iam::123456789012:role/CoreAutomationApiWrite"
    ), "Automation API write role ARN should match the expected format"
    del os.environ[ENV_AUTOMATION_ACCOUNT]
    role_arn = util.get_automation_api_role_arn()
    assert role_arn is None, "Automation API role ARN should be None if ENV_AUTOMATION_ACCOUNT is not set"


def test_get_organization_id():

    os.environ[ENV_ORGANIZATION_ID] = "o-1234567890"

    org_id = util.get_organization_id()
    assert org_id == "o-1234567890", "Organization ID should match the expected format with default organization ID"

    del os.environ[ENV_ORGANIZATION_ID]
    org_id = util.get_organization_id()
    assert org_id is None, "Organization ID should be empty if ENV_ORGANIZATION_ID is not set"


def test_get_organization_name():

    os.environ[ENV_ORGANIZATION_NAME] = "default_organization"

    org_name = util.get_organization_name()
    assert org_name == "default_organization", "Organization name should match the expected format with default organization name"

    # Per requirements, make sure None is returned if ENV_ORGANIZATION_NAME is not set

    del os.environ[ENV_ORGANIZATION_NAME]

    org_name = util.get_organization_name()

    assert org_name is None, "Organization name should be empty if ENV_ORGANIZATION_NAME is not set"


def test_get_organization_account():

    os.environ[ENV_ORGANIZATION_ACCOUNT] = "123456789012"
    org_account = util.get_organization_account()
    assert org_account == "123456789012", "Organization account should match the expected format with default organization account"
    # Per requirements, make sure None is returned if ENV_ORGANIZATION_ACCOUNT is not set
    del os.environ[ENV_ORGANIZATION_ACCOUNT]
    org_account = util.get_organization_account()
    assert org_account is None, "Organization account should be empty if ENV_ORGANIZATION_ACCOUNT is not set"


def test_get_organization_email():

    os.environ[ENV_ORGANIZATION_EMAIL] = "mail"

    email = util.get_organization_email()
    assert email == "mail", "Organization email should be None if not set"

    del os.environ[ENV_ORGANIZATION_EMAIL]

    email = util.get_organization_email()
    assert email is None, "Organization email should be None if ENV_ORGANIZATION_EMAIL is not set"


def test_get_iam_account():

    os.environ[ENV_IAM_ACCOUNT] = "123456789012"

    iam_account = util.get_iam_account()
    assert iam_account == "123456789012", "IAM account should be None if not set"

    del os.environ[ENV_IAM_ACCOUNT]
    iam_account = util.get_iam_account()
    assert iam_account is None, "IAM account should be None if ENV_IAM_ACCOUNT is not set"


def test_get_audit_account():

    os.environ[ENV_AUDIT_ACCOUNT] = "123456789012"

    audit_account = util.get_audit_account()
    assert audit_account == "123456789012", "Audit account should be None if not set"

    del os.environ[ENV_AUDIT_ACCOUNT]
    audit_account = util.get_audit_account()
    assert audit_account is None, "Audit account should be None if ENV_AUDIT_ACCOUNT is not set"


def test_get_security_account():

    os.environ[ENV_SECURITY_ACCOUNT] = "123456789012"

    security_account = util.get_security_account()
    assert security_account == "123456789012", "Security account should be None if not set"

    del os.environ[ENV_SECURITY_ACCOUNT]
    security_account = util.get_security_account()
    assert security_account is None, "Security account should be None if ENV_SECURITY_ACCOUNT is not set"


def test_get_domain():

    os.environ[ENV_DOMAIN] = "example.com"

    domain = util.get_domain()
    assert domain == "example.com", "Domain should match the expected format with default domain"

    del os.environ[ENV_DOMAIN]
    domain = util.get_domain()
    assert domain == "example.com", "Domain should be None if ENV_DOMAIN is not set"


def test_get_network_account():

    os.environ[ENV_NETWORK_ACCOUNT] = "123456789012"

    network_account = util.get_network_account()
    assert network_account == "123456789012", "Network account should match the expected format with default network account"

    del os.environ[ENV_NETWORK_ACCOUNT]
    network_account = util.get_network_account()
    assert network_account is None, "Network account should be None if ENV_NETWORK_ACCOUNT is not set"


def test_get_cdk_default_account():

    os.environ[ENV_CDK_DEFAULT_ACCOUNT] = "123456789012"

    account = util.get_cdk_default_account()
    assert account == "123456789012", "CDK default account should match the expected format with default account"

    del os.environ[ENV_CDK_DEFAULT_ACCOUNT]
    account = util.get_cdk_default_account()
    assert account is None, "CDK default account should be None if ENV_CDK_DEFAULT_ACCOUNT is not set"


def test_get_cdk_default_region():

    os.environ[ENV_CDK_DEFAULT_REGION] = "us-east-1"

    region = util.get_cdk_default_region()
    assert region == "us-east-1", "CDK default region should match the expected format with default region"

    del os.environ[ENV_CDK_DEFAULT_REGION]
    region = util.get_cdk_default_region()
    assert region is None, "CDK default region should be None if ENV_CDK_DEFAULT_REGION is not set"


def test_get_console_mode():
    os.environ[ENV_CONSOLE] = V_INTERACTIVE

    console_mode = util.get_console_mode()
    assert console_mode == V_INTERACTIVE, "Console mode allowed value is V_INTERACTIVE or None"

    del os.environ[ENV_CONSOLE]
    console_mode = util.get_console_mode()
    assert console_mode is None, "Console mode should be None if ENV_CONSOLE_MODE is not set"


def test_is_use_s3():

    os.environ[ENV_LOCAL_MODE] = "true"
    os.environ[ENV_USE_S3] = "true"

    use_s3 = util.is_use_s3()
    assert use_s3 is True, "Use S3 should be True if ENV_USE_S3 is set to 'true' and LOCAL_MODE is true"

    os.environ[ENV_USE_S3] = "false"
    use_s3 = util.is_use_s3()
    assert use_s3 is False, "Use S3 should be False if ENV_USE_S3 is set to 'false' and LOCAL_MODE is true"

    del os.environ[ENV_USE_S3]
    del os.environ[ENV_LOCAL_MODE]

    use_s3 = util.is_use_s3()
    assert use_s3 is True, "Use S3 should be True if ENV_USE_S3 is not set and LOCAL_MODE is not set"

    # if LOCAL_MODE is set to true, use_s3 is forced to True
    os.environ[ENV_USE_S3] = "false"
    os.environ[ENV_LOCAL_MODE] = "false"

    use_s3 = util.is_use_s3()

    assert use_s3 is True, "Use S3 should always be True if LOCAL_MODE false"


def test_is_json_log():

    os.environ[ENV_LOG_AS_JSON] = "true"
    use_json_log = util.is_json_log()
    assert use_json_log is True, "JSON log should be True if ENV_JSON_LOG is set to 'true'"

    del os.environ[ENV_LOG_AS_JSON]
    use_json_log = util.is_json_log()
    assert use_json_log is False, "JSON log should be False if ENV_JSON_LOG is not set"


def test_is_console_log():

    os.environ[ENV_CONSOLE_LOG] = "true"
    console_log = util.is_console_log()
    assert console_log is True, "Console log should be True if ENV_CONSOLE_LOG is set to 'true'"

    del os.environ[ENV_CONSOLE_LOG]
    console_log = util.is_console_log()
    assert console_log is False, "Console log should be False if ENV_CONSOLE_LOG is not set"


def test_get_log_level():

    os.environ[ENV_LOG_LEVEL] = "DEBUG"
    log_level = util.get_log_level()
    assert log_level == "DEBUG", "Log level should match the expected format with default log level"

    del os.environ[ENV_LOG_LEVEL]
    log_level = util.get_log_level()
    assert log_level == "INFO", "Log level should be INFO if ENV_LOG_LEVEL is not set"


def test_is_local_mode():

    os.environ[ENV_LOCAL_MODE] = "true"
    local_mode = util.is_local_mode()
    assert local_mode is True, "Local mode should be True if ENV_LOCAL_MODE is set to 'true'"

    del os.environ[ENV_LOCAL_MODE]
    local_mode = util.is_local_mode()
    assert local_mode is False, "Local mode should be False if ENV_LOCAL_MODE is not set"


def test_get_storage_volume():

    os.environ[ENV_LOCAL_MODE] = "true"

    expected_volume = "/var/data/log/test_volume"
    os.environ[ENV_VOLUME] = expected_volume

    volume = util.get_storage_volume()
    assert volume == expected_volume, "Storage volume should match the expected format with default volume"

    # If local mode is true, and the ENV_VOLUME is not set, it should return the current working directory appended with 'local'
    current_dir = os.getcwd()
    expected_volume = os.path.join(current_dir, "local")

    del os.environ[ENV_VOLUME]
    volume = util.get_storage_volume()
    assert volume == expected_volume, f"Storage volume should be {expected_volume} if ENV_VOLUME is not set"

    # if local mode is false, the volume should be the URL to the S3 regional service where we will PUT the data
    region = util.get_bucket_region()
    expected_volume = f"https://s3-{region}.amazonaws.com"

    os.environ[ENV_LOCAL_MODE] = "false"
    volume = util.get_storage_volume()
    assert volume == expected_volume, "Storage volume should be None if ENV_LOCAL_MODE is not set or is set to false"


def test_get_temp_dir():

    folder = os.path.join("tmp", "test_temp_dir")
    os.environ["TEMP_DIR"] = folder
    path = os.path.join("var", "tmp", "data")

    expected_temp_dir = os.path.join(folder, path)

    temp_dir = util.get_temp_dir(path)
    assert temp_dir == expected_temp_dir, f"1 - Expected {expected_temp_dir}, but got {temp_dir}"

    del os.environ["TEMP_DIR"]
    os.environ["TEMP"] = folder

    temp_dir = util.get_temp_dir(path)
    assert temp_dir == expected_temp_dir, f"2 - Expected {expected_temp_dir}, but got {temp_dir}"

    folder = tempfile.gettempdir()
    del os.environ["TEMP"]
    expected_temp_dir = os.path.join(folder, path)

    temp_dir = util.get_temp_dir(path)
    assert temp_dir == expected_temp_dir, f"3 - Expected {expected_temp_dir}, but got {temp_dir}"


def test_get_mode():

    os.environ[ENV_LOCAL_MODE] = "true"

    mode = util.get_mode()
    assert mode == V_LOCAL, f"Mode should be '{V_LOCAL}' if local mode"

    os.environ[ENV_LOCAL_MODE] = "false"
    mode = util.get_mode()
    assert mode == V_SERVICE, f"Mode should be '{V_SERVICE}' if not local mode"


def test_is_enforce_validation():

    os.environ[ENV_ENFORCE_VALIDATION] = "false"

    enforce_validation = util.is_enforce_validation()
    assert enforce_validation is False, "Enforce validation should be False if ENV_ENFORCE_VALIDATION is set to 'false'"

    del os.environ[ENV_ENFORCE_VALIDATION]
    enforce_validation = util.is_enforce_validation()
    assert enforce_validation is True, "Enforce validation should be True if ENV_ENFORCE_VALIDATION is not set"


def test_get_client():

    os.environ[ENV_CLIENT] = "example_client"
    os.environ[ENV_AWS_PROFILE] = "default_profile"

    client = util.get_client()
    assert client == "example_client", "Client should match the expected format with default client"

    del os.environ[ENV_CLIENT]
    client = util.get_client()
    assert client == "default_profile", "Client should be 'default_profile' if ENV_CLIENT is not set and an AWS profile is set"

    del os.environ[ENV_AWS_PROFILE]
    client = util.get_client()
    assert client is None, "Client should be None if ENV_CLIENT and ENV_AWS_PROFILE are not set"


def test_get_client_name():

    os.environ[ENV_CLIENT_NAME] = "example_client_name"
    client_name = util.get_client_name()
    assert client_name == "example_client_name", "Client name should match the expected format with default client name"

    del os.environ[ENV_CLIENT_NAME]

    client_name = util.get_client_name()
    assert client_name is None, "Client name should be None if ENV_CLIENT_NAME is not set"


def test_get_log_dir():

    os.environ[ENV_LOG_DIR] = "example_log_dir"

    log_dir = util.get_log_dir()
    assert log_dir == "example_log_dir", "Log directory should match the expected format with default log directory"

    del os.environ[ENV_LOG_DIR]

    expected_log_dir = os.path.join(os.getcwd(), "local", "logs")
    log_dir = util.get_log_dir()
    assert log_dir == expected_log_dir, "Log directory should be None if ENV_LOG_DIR is not set"


def test_get_delivered_by():

    os.environ[ENV_DELIVERED_BY] = "example_delivered_by"

    delivered_by = util.get_delivered_by()
    assert delivered_by == "example_delivered_by", "Delivered by should match the expected format with default delivered by"

    del os.environ[ENV_DELIVERED_BY]

    delivered_by = util.get_delivered_by()
    assert delivered_by == "automation", "Delivered by should be None if ENV_DELIVERED_BY is not set"


def test_get_aws_profile():

    os.environ[ENV_CLIENT] = "client"  ## this profile is not in the AWS credentials file
    os.environ[ENV_AWS_PROFILE] = "example_aws_profile"  ## this profile is not in the AWS credentials file

    aws_profile = util.get_aws_profile()
    assert aws_profile == "default", "1 - AWS profile should match the expected format with default AWS profile"

    del os.environ[ENV_AWS_PROFILE]

    aws_profile = util.get_aws_profile()
    assert aws_profile == "default", "2 - AWS profile should be None if ENV_AWS_PROFILE is not set"


def test_get_aws_region():

    os.environ[ENV_AWS_REGION] = "us-west-2"

    aws_region = util.get_aws_region()
    assert aws_region == "us-west-2", "1 - AWS region should match the expected format with default AWS region"

    del os.environ[ENV_AWS_REGION]

    # throw and exception ProfileNotrFound if the boto3.session.Session is called
    # Will cause get_aws_profile to return the 'default' profile
    with patch(
        "core_framework.common.boto3.session.Session",
        side_effect=ProfileNotFound(profile="none"),
    ):
        aws_profile = util.get_aws_region()
        assert (
            aws_profile is V_DEFAULT_REGION
        ), f"2 - AWS profile should be '{V_DEFAULT_REGION}' if there is an error getting the AWS profile"

    with patch("core_framework.common.boto3.session.Session") as mock_session:
        mock_session.return_value.region_name = "us-west-2"
        aws_region = util.get_aws_region()
        assert (
            aws_region == "us-west-2"
        ), "3 - AWS region should match the expected format with default AWS region from boto3 session"


def test_get_client_region():

    os.environ[ENV_CLIENT_REGION] = "us-west-2"

    client_region = util.get_client_region()
    assert client_region == "us-west-2", "1 - Client region should match the expected format with default client region"

    del os.environ[ENV_CLIENT_REGION]

    # if not specified, it will be the default region from the AWS profile
    client_region = util.get_client_region()
    assert (
        client_region is not None
    ), "2 - Client region should not be None if ENV_CLIENT_REGION is not set as it comes from the AWS profile"


def test_get_master_region():

    os.environ[ENV_MASTER_REGION] = "us-west-2"

    master_region = util.get_master_region()
    assert master_region == "us-west-2", "1 - Master region should match the expected format with default master region"

    del os.environ[ENV_MASTER_REGION]

    # if not specified, it will be the default region from the AWS profile
    master_region = util.get_master_region()
    assert (
        master_region is not None
    ), "2 -Master region should not be None if ENV_MASTER_REGION is not set as it comes from the AWS profile"


def test_get_region():

    os.environ[ENV_AWS_REGION] = "us-west-2"
    region = util.get_region()
    assert region == "us-west-2", "1 -Region should match the expected format with default region"

    del os.environ[ENV_AWS_REGION]
    region = util.get_region()
    assert region is not None, "2 - Region should not be None if ENV_REGION is not set as it comes from the AWS profile"


def test_get_automation_region():

    os.environ[ENV_AUTOMATION_REGION] = "us-west-2"

    automation_region = util.get_automation_region()
    assert automation_region == "us-west-2", "1 - Automation region should match the expected format with default automation region"

    del os.environ[ENV_AUTOMATION_REGION]

    # if not specified, it will be the default region from the AWS profile
    automation_region = util.get_automation_region()
    assert (
        automation_region is not None
    ), "2  Automation region should not be None if ENV_AUTOMATION_REGION is not set as it comes from the AWS profile"


def test_get_bucket_region():

    os.environ[ENV_BUCKET_REGION] = "us-west-2"

    bucket_region = util.get_bucket_region()
    assert bucket_region == "us-west-2", "1 - Bucket region should match the expected format with default bucket region"

    del os.environ[ENV_BUCKET_REGION]

    # if not specified, it will be the default region from the AWS profile
    bucket_region = util.get_bucket_region()
    assert (
        bucket_region is not None
    ), "2 - Bucket region should not be None if ENV_BUCKET_REGION is not set as it comes from the AWS profile"


def test_get_dynamodb_region():

    os.environ[ENV_DYNAMODB_REGION] = "us-west-2"

    dynamodb_region = util.get_dynamodb_region()
    assert dynamodb_region == "us-west-2", "1 - DynamoDB region should match the expected format with default DynamoDB region"

    del os.environ[ENV_DYNAMODB_REGION]

    # if not specified, it will be the default region from the AWS profile
    dynamodb_region = util.get_dynamodb_region()
    assert (
        dynamodb_region is not None
    ), "2 - DynamoDB region should not be None if ENV_DYNAMODB_REGION is not set as it comes from the AWS profile"


def test_get_invoker_lambda_region():

    os.environ[ENV_INVOKER_LAMBDA_REGION] = "us-west-2"

    invoker_lambda_region = util.get_invoker_lambda_region()
    assert (
        invoker_lambda_region == "us-west-2"
    ), "1 - Invoker Lambda region should match the expected format with default Invoker Lambda region"

    del os.environ[ENV_INVOKER_LAMBDA_REGION]

    # if not specified, it will be the default region from the AWS profile
    invoker_lambda_region = util.get_invoker_lambda_region()
    assert (
        invoker_lambda_region is not None
    ), "2 - Invoker Lambda region should not be None if ENV_INVOKER_LAMBDA_REGION is not set as it comes from the AWS profile"


def test_get_automation_account():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"

    automation_account = util.get_automation_account()
    assert (
        automation_account == "123456789012"
    ), "1 - Automation account should match the expected format with default automation account"

    del os.environ[ENV_AUTOMATION_ACCOUNT]

    # if not specified, it will be the default account from the AWS profile
    automation_account = util.get_automation_account()
    assert automation_account is None, "2 - Automation account should be None if ENV_AUTOMATION_ACCOUNT is not set"


def test_get_dynamodb_host():

    os.environ[ENV_DYNAMODB_HOST] = "dynamodb.us-west-2.amazonaws.com"

    dynamodb_host = util.get_dynamodb_host()
    assert (
        dynamodb_host == "dynamodb.us-west-2.amazonaws.com"
    ), "1 - DynamoDB host should match the expected format with default DynamoDB host"

    del os.environ[ENV_DYNAMODB_HOST]

    # if not specified, it will be the default host from the AWS profile
    dynamodb_host = util.get_dynamodb_host()
    assert (
        dynamodb_host is not None
    ), "2 - DynamoDB host should not be None if ENV_DYNAMODB_HOST is not set as it comes from the AWS profile"


def test_get_step_function_arn():

    account = "123456789012"
    region = util.get_region()

    os.environ[ENV_AUTOMATION_ACCOUNT] = account  # Must be set to get the ARN
    os.environ[ENV_LOCAL_MODE] = "true"

    arn = util.get_step_function_arn()

    assert (
        arn == f"arn:aws:states:{region}:local:execution:stateMachineName:CoreAutomationRunner"
    ), "1 - Step Function ARN should match the expected format with default Step Function ARN"

    # default value for LOCAL_MODE is false
    del os.environ[ENV_LOCAL_MODE]

    arn = util.get_step_function_arn()

    assert (
        arn == f"arn:aws:states:{region}:{account}:stateMachine:CoreAutomationRunner"
    ), "2 - Step Function ARN should match the expected format with default Step Function ARN when LOCAL_MODE is not set or is false"


def test_get_invoker_lambda_name():

    os.environ[ENV_INVOKER_LAMBDA_NAME] = "example_invoker_lambda"
    invoker_lambda_name = util.get_invoker_lambda_name()
    assert (
        invoker_lambda_name == "example_invoker_lambda"
    ), "1 - Invoker Lambda name should match the expected format with default invoker lambda name"

    del os.environ[ENV_INVOKER_LAMBDA_NAME]
    invoker_lambda_name = util.get_invoker_lambda_name()
    assert (
        invoker_lambda_name == "core-automation-invoker"
    ), "2 - Invoker Lambda name should be 'core-automation-invoker' if ENV_INVOKER_LAMBDA_NAME is not set"


def test_get_api_lambda_name():

    os.environ[ENV_API_LAMBDA_NAME] = "example_api_lambda"
    api_lambda_name = util.get_api_lambda_name()
    assert (
        api_lambda_name == "example_api_lambda"
    ), "1 - API Lambda name should match the expected format with default API lambda name"

    del os.environ[ENV_API_LAMBDA_NAME]
    api_lambda_name = util.get_api_lambda_name()
    assert (
        api_lambda_name == "core-automation-api"
    ), "2 - API Lambda name should be 'core-automation-api' if ENV_API_LAMBDA_NAME is not set"


def test_get_api_lambda_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"  ## Must be set to get the ARN

    os.environ[ENV_API_LAMBDA_ARN] = "arn:aws:lambda:us-west-2:123456789012:function:example_api_lambda"
    api_lambda_arn = util.get_api_lambda_arn()
    assert (
        api_lambda_arn == "arn:aws:lambda:us-west-2:123456789012:function:example_api_lambda"
    ), "1 - API Lambda ARN should match the expected format with default API lambda ARN"

    del os.environ[ENV_API_LAMBDA_ARN]
    api_lambda_arn = util.get_api_lambda_arn()
    assert (
        api_lambda_arn == "arn:aws:lambda:ap-southeast-1:123456789012:function:core-automation-api"
    ), "2 - API Lambda ARN should be None if ENV_API_LAMBDA_ARN is not set"


def test_get_api_host_url():

    os.environ[ENV_API_HOST_URL] = "https://api.example.com"
    api_host_url = util.get_api_host_url()
    assert api_host_url == "https://api.example.com", "1 - API host URL should match the expected format with default API host URL"

    del os.environ[ENV_API_HOST_URL]
    api_host_url = util.get_api_host_url()
    assert api_host_url is None, "2 - API host URL should be None if ENV_API_HOST_URL is not set"


def test_get_invoker_lambda_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"  # Must be set to get the ARN

    os.environ[ENV_INVOKER_LAMBDA_ARN] = "arn:aws:lambda:us-west-2:123456789012:function:example_invoker_lambda"
    invoker_lambda_arn = util.get_invoker_lambda_arn()
    assert (
        invoker_lambda_arn == "arn:aws:lambda:us-west-2:123456789012:function:example_invoker_lambda"
    ), "1 - Invoker Lambda ARN should match the expected format with default invoker lambda ARN"

    del os.environ[ENV_INVOKER_LAMBDA_ARN]
    invoker_lambda_arn = util.get_invoker_lambda_arn()
    assert (
        invoker_lambda_arn == "arn:aws:lambda:ap-southeast-1:123456789012:function:core-automation-invoker"
    ), "2 - Invoker Lambda ARN should be None if ENV_INVOKER_LAMBDA_ARN is not set"


def test_get_execute_lambda_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"  # Must be set to get the ARN

    os.environ[ENV_EXECUTE_LAMBDA_ARN] = "arn:aws:lambda:us-west-2:123456789012:function:example_execute_lambda"
    execute_lambda_arn = util.get_execute_lambda_arn()
    assert (
        execute_lambda_arn == "arn:aws:lambda:us-west-2:123456789012:function:example_execute_lambda"
    ), "1 - Execute Lambda ARN should match the expected format with default execute lambda ARN"
    del os.environ[ENV_EXECUTE_LAMBDA_ARN]
    execute_lambda_arn = util.get_execute_lambda_arn()
    assert (
        execute_lambda_arn == "arn:aws:lambda:ap-southeast-1:123456789012:function:core-automation-execute"
    ), "2 - Execute Lambda ARN should be None if ENV_EXECUTE_LAMBDA_ARN is not set"


def test_get_start_runner_lambda_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"  # Must be set to get the ARN

    os.environ[ENV_START_RUNNER_LAMBDA_ARN] = "arn:aws:lambda:us-west-2:123456789012:function:example_start_runner_lambda"
    start_runner_lambda_arn = util.get_start_runner_lambda_arn()
    assert (
        start_runner_lambda_arn == "arn:aws:lambda:us-west-2:123456789012:function:example_start_runner_lambda"
    ), "1 - Start Runner Lambda ARN should match the expected format with default start runner lambda ARN"
    del os.environ[ENV_START_RUNNER_LAMBDA_ARN]
    start_runner_lambda_arn = util.get_start_runner_lambda_arn()
    assert (
        start_runner_lambda_arn == "arn:aws:lambda:ap-southeast-1:123456789012:function:core-automation-runner"
    ), "2 - Start Runner Lambda ARN should be None if ENV_START_RUNNER_LAMBDA_ARN is not set"


def test_get_project():

    os.environ[ENV_PROJECT] = "example_project"

    project = util.get_project()
    assert project == "example_project", "1 - Project should match the expected format with default project"

    del os.environ[ENV_PROJECT]

    project = util.get_project()
    assert project is None, "2 - Project should be None if ENV_PROJECT is not set"


def test_get_bizapp():

    os.environ[ENV_BIZAPP] = "example_bizapp"

    bizapp = util.get_bizapp()
    assert bizapp == "example_bizapp", "1 - BizApp should match the expected format with default BizApp"

    del os.environ[ENV_BIZAPP]

    bizapp = util.get_bizapp()
    assert bizapp is None, "2 - BizApp should be None if ENV_BIZAPP is not set"


def test_get_deployspec_compiler_lambda_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"  # Must be set to get the ARN

    os.environ[ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN] = (
        "arn:aws:lambda:us-west-2:123456789012:function:example_deployspec_compiler_lambda"
    )
    deployspec_compiler_lambda_arn = util.get_deployspec_compiler_lambda_arn()
    assert (
        deployspec_compiler_lambda_arn == "arn:aws:lambda:us-west-2:123456789012:function:example_deployspec_compiler_lambda"
    ), "1 - DeploySpec Compiler Lambda ARN should match the expected format with default deployspec compiler lambda ARN"

    del os.environ[ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN]
    deployspec_compiler_lambda_arn = util.get_deployspec_compiler_lambda_arn()
    assert (
        deployspec_compiler_lambda_arn == "arn:aws:lambda:ap-southeast-1:123456789012:function:core-automation-deployspec-compiler"
    ), "2 - DeploySpec Compiler Lambda ARN should be None if ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN is not set"


def test_get_component_compiler_lambda_arn():

    os.environ[ENV_AUTOMATION_ACCOUNT] = "123456789012"  # Must be set to get the ARN

    os.environ[ENV_COMPONENT_COMPILER_LAMBDA_ARN] = (
        "arn:aws:lambda:us-west-2:123456789012:function:example_component_compiler_lambda"
    )
    component_compiler_lambda_arn = util.get_component_compiler_lambda_arn()
    assert (
        component_compiler_lambda_arn == "arn:aws:lambda:us-west-2:123456789012:function:example_component_compiler_lambda"
    ), "1 - Component Compiler Lambda ARN should match the expected format with default component compiler lambda ARN"

    del os.environ[ENV_COMPONENT_COMPILER_LAMBDA_ARN]
    component_compiler_lambda_arn = util.get_component_compiler_lambda_arn()
    assert (
        component_compiler_lambda_arn == "arn:aws:lambda:ap-southeast-1:123456789012:function:core-automation-component-compiler"
    ), "2 - Component Compiler Lambda ARN should be None if ENV_COMPONENT_COMPILER_LAMBDA_ARN is not set"


def test_get_correlation_id():

    os.environ[ENV_CORRELATION_ID] = "example_correlation_id"

    correlation_id = util.get_correlation_id()
    assert (
        correlation_id == "example_correlation_id"
    ), "1 - Correlation ID should match the expected format with default correlation ID"

    del os.environ[ENV_CORRELATION_ID]

    correlation_id = util.get_correlation_id()
    assert (
        correlation_id is not None
    ), "2 - Correlation ID should not be None if ENV_CORRELATION_ID is not set.  It should be generated automatically"


def test_get_environment():

    os.environ[ENV_ENVIRONMENT] = "example_environment"

    environment = util.get_environment()
    assert environment == "example_environment", "1 - Environment should match the expected format with default environment"

    del os.environ[ENV_ENVIRONMENT]

    environment = util.get_environment()
    assert environment == "prod", "2 - Environment should default to 'prod' if ENV_ENVIRONMENT is not set"


def test_to_json():

    data = {
        "name": "Test",
        "datetime": datetime(2023, 10, 1, 12, 0),
        "date": date(2023, 10, 1),
        "time": time(12, 0),
        "decimal": Decimal("41.5"),
        "quoted_number": "00000432.1",
        "value": 42.1,
    }

    json_data = util.to_json(data)

    assert isinstance(json_data, str), "JSON data should be a string"
    assert '"name": "Test"' in json_data, "JSON data should contain the name field"
    assert '"date": "2023-10-01"' in json_data, "JSON data should contain the date field"
    assert '"datetime": "2023-10-01T12:00:00"' in json_data, "JSON data should contain the datetime field"
    assert '"time": "12:00:00"' in json_data, "JSON data should contain the time field"
    assert '"decimal": 41.5' in json_data, "JSON data should contain the decimal field"
    assert '"value": 42.1' in json_data, "JSON data should contain the value field"
    assert '"quoted_number": "00000432.1"' in json_data, "JSON data should contain the quoted number field"

    try:
        util.to_json({"uknown_type": set([1, 2, 3])})
        assert False, "to_json should raise TypeError for unsupported types"
    except Exception as e:
        assert isinstance(e, TypeError), "to_json should raise TypeError for unsupported types"

    result = util.to_json(None)
    assert result == V_EMPTY, "to_json should return None if data is None"


def test_write_json():
    data = {"name": "Test", "date": datetime(2023, 10, 1, 12, 0), "value": 42.1}
    stream = io.StringIO()
    util.write_json(data, stream)
    json_data = stream.getvalue()
    assert isinstance(json_data, str), "JSON data should be a string"
    assert '"name": "Test"' in json_data, "JSON data should contain the name field"
    assert '"date": "2023-10-01T12:00:00"' in json_data, "JSON data should contain the date field"
    assert '"value": 42.1' in json_data, "JSON data should contain the value field"


def test_from_json():
    json_str = """{
        "name": "Test",
        "date": "2023-10-01T12:00:00",
        "datelist": ["2023-10-01T12:00:00", "2023-10-02T12:00:00"],
        "value": 42.1
    }"""
    data = util.from_json(json_str)
    assert isinstance(data, dict), "Parsed data should be a dictionary"
    assert data["name"] == "Test", "Parsed data should contain the correct name"
    assert data["date"] == datetime(2023, 10, 1, 12, 0), "Parsed data should contain the correct date"
    assert data["value"] == 42.1, "Parsed data should contain the correct value"
    assert data["datelist"] == [
        datetime(2023, 10, 1, 12, 0),
        datetime(2023, 10, 2, 12, 0),
    ], "Parsed data should contain the correct datelist"


def test_read_json():
    stream = io.StringIO(
        """{
        "name": "Test",
        "date": "2023-10-01T12:00:00",
        "value": 42.1}"""
    )
    data = util.read_json(stream)
    assert isinstance(data, dict), "Parsed data should be a dictionary"
    assert data["name"] == "Test", "Parsed data should contain the correct name"
    assert data["date"] == datetime(2023, 10, 1, 12, 0), "Parsed data should contain the correct date"
    assert data["value"] == 42.1, "Parsed data should contain the correct value"


def test_to_yaml():
    data = {
        "name": "Test",
        "datetime": datetime(2023, 10, 1, 12, 0),
        "date": date(2023, 10, 1),
        "time": time(12, 0),
        "datalist": [{"name": "string1", "value": "value1"}, {"name": "string2", "value": "value2"}],
        "value": 42.1,
        "quoted_number": "00000432.1",
        "decimal": Decimal("41.5"),
        "quoted_bool": True,
        "quoted_none": None,
    }
    yaml_data = util.to_yaml(data)
    assert isinstance(yaml_data, str), "YAML data should be a string"
    assert "name: Test" in yaml_data, "YAML data should contain the name field"

    # Date must be in ISO 8601 format surrounded by single quotes
    assert "date: '2023-10-01'" in yaml_data, "YAML data should contain the date field"

    # Datetime must be in ISO 8601 format surrounded by single quotes
    assert "datetime: '2023-10-01T12:00:00'" in yaml_data, "YAML data should contain the date field"
    assert "time: 12:00:00" in yaml_data, "YAML data should contain the time field"
    assert "value: 42.1" in yaml_data, "YAML data should contain the value field"
    assert (
        "datalist:\n  - name: string1\n    value: value1\n  - name: string2\n    value: value2\nvalue: 42.1" in yaml_data
    ), "YAML data should contain the datalist field quoted strings"
    assert "quoted_number: '00000432.1'" in yaml_data, "YAML data should contain the quoted number field"
    assert "decimal: 41.5" in yaml_data, "YAML data should contain the decimal field"


def test_to_yaml_with_top_level_array():
    data = [
        {"name": "Test1", "date": datetime(2023, 10, 1, 12, 0), "value": 42.1},
        {"name": "Test2", "date": datetime(2023, 10, 2, 12, 0), "value": 43.2},
    ]

    test_result = """- name: Test1
  date: '2023-10-01T12:00:00'
  value: 42.1
- name: Test2
  date: '2023-10-02T12:00:00'
  value: 43.2
"""

    yaml_data = util.to_yaml(data)
    assert isinstance(yaml_data, str), "YAML data should be a string"
    assert "- name: Test1" in yaml_data, "YAML data should contain the first item name field"
    assert "- name: Test2" in yaml_data, "YAML data should contain the second item name field"
    assert "date: '2023-10-01T12:00:00'" in yaml_data, "YAML data should contain the first item date field"
    assert "date: '2023-10-02T12:00:00'" in yaml_data, "YAML data should contain the second item date field"
    assert test_result == yaml_data, "YAML data should contain the first item value field"


def test_write_yaml():
    data = {"name": "Test", "date": datetime(2023, 10, 1, 12, 0), "value": 42.1}
    stream = io.StringIO()
    util.write_yaml(data, stream)
    yaml_data = stream.getvalue()

    assert isinstance(yaml_data, str), "YAML data should be a string"
    assert "name: Test" in yaml_data, "YAML data should contain the name field"

    # Date must be in ISO 8601 format surrounded by single quotes
    assert "date: '2023-10-01T12:00:00'" in yaml_data, "YAML data should contain the date field"
    assert "value: 42.1" in yaml_data, "YAML data should contain the value field"


def test_from_yaml():

    # We eare testing the iso8601 date format parsing a string

    data = """
- name: Test
  date: '2023-10-01T12:00:00'
  value: 42.1
"""
    result = util.from_yaml(data)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "Test"
    assert result[0]["date"] == datetime(2023, 10, 1, 12, 0)
    assert result[0]["value"] == 42.1


def test_read_yaml():

    # We are testing the iso8601 date format parsing a string from a stream

    input_stream = io.StringIO(
        """
- name: Test
  date: '2023-10-01T12:00:00'
  value: 42
"""
    )
    result = util.read_yaml(input_stream)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "Test"
    assert result[0]["date"] == datetime(2023, 10, 1, 12, 0)


if __name__ == "__main__":
    pytest.main()


def test_valid_mimetypes():

    valid_mimetypes = util.get_valid_mimetypes()

    assert isinstance(valid_mimetypes, list), "Valid mimetypes should be a list"
    assert len(valid_mimetypes) > 0, "Valid mimetypes list should not be empty"

    for mimetype in valid_mimetypes:
        assert isinstance(mimetype, str), "Each mimetype should be a string"
        assert mimetype, "Mimetype should not be an empty string"

    assert util.is_zip_mimetype("application/zip") is True, "application/zip should be a valid zip mimetype"
    assert (
        util.is_zip_mimetype("application/x-zip-compressed") is True
    ), "application/x-zip-compressed should be a valid zip mimetype"
    assert util.is_zip_mimetype("application/x-zip") is True, "application/x-zip should be a valid zip mimetype"
    assert util.is_zip_mimetype("application/gzip") is False, "application/gzip should not be a valid zip mimetype"
    assert util.is_zip_mimetype("text/plain") is False, "text/plain should not be a valid zip mimetype"
    assert util.is_zip_mimetype("") is False, "Empty string should not be a valid zip mimetype"

    assert util.is_yaml_mimetype("application/x-yaml") is True, "application/x-yaml should be a valid YAML mimetype"
    assert util.is_yaml_mimetype("text/yaml") is True, "text/yaml should be a valid YAML mimetype"
    assert util.is_yaml_mimetype("application/yaml") is True, "application/yaml should be a valid YAML mimetype"
    assert util.is_yaml_mimetype("application/json") is False, "application/json should not be a valid YAML mimetype"
    assert util.is_yaml_mimetype("text/plain") is False, "text/plain should not be a valid YAML mimetype"
    assert util.is_yaml_mimetype("") is False, "Empty string should not be a valid YAML mimetype"

    assert util.is_json_mimetype("application/json") is True, "application/json should be a valid JSON mimetype"
    assert util.is_json_mimetype("application/x-json") is True, "application/x-json should be a valid JSON mimetype"
    assert util.is_json_mimetype("text/json") is True, "text/json should be a valid JSON mimetype"
    assert util.is_json_mimetype("application/x-yaml") is False, "application/x-yaml should not be a valid JSON mimetype"
    assert util.is_json_mimetype("text/plain") is False, "text/plain should not be a valid JSON mimetype"
    assert util.is_json_mimetype("") is False, "Empty string should not be a valid JSON mimetype"


def test_get_timestamp_str():

    with patch("core_framework.common.datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 10, 1, 12, 0, 0)
        timestamp_str = util.get_current_timestamp()
        assert timestamp_str == "2023-10-01T12:00:00", "Timestamp string should match the expected format"
