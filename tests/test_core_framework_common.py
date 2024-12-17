import io
import os

from core_framework.models import TaskPayload, DeploymentDetails, PackageDetails, DeploySpec

import pytest
from unittest.mock import patch
import core_framework as util

from core_framework.constants import (
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
    SCOPE_PORTFOLIO,
)

from core_framework.models import (
    TaskPayload,
    DeploymentDetails,
    PackageDetails,
    DeploySpec,
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

    bucket_name = util.generate_bucket_name(
        "Example_Client", "Example_Branch", "scope-"
    )

    assert bucket_name == "scope-example_client-core-automation-example_branch"

    bucket_name = util.get_bucket_name("baskets")

    assert bucket_name == "baskets-core-automation-master"

    bucket_name = util.get_bucket_name()

    client = util.get_client()
    if client:
        assert bucket_name == f"{client}-core-automation-master"
    else:
        assert bucket_name == "core-automation-master"


def test_generate_branch_short_name():
    # Test with a normal branch name
    assert (
        util.generate_branch_short_name("feature/new-feature") == "feature-new-feature"
    )

    # Test with a branch name containing uppercase letters
    assert (
        util.generate_branch_short_name("Feature/New-Feature") == "feature-new-feature"
    )

    # Test with a branch name containing special characters
    assert (
        util.generate_branch_short_name("feature/new@feature!") == "feature-new-feature"
    )

    # Test with a branch name that is exactly 20 characters long, but if the last character is a hyphen, it's stripped
    assert (
        util.generate_branch_short_name("feature/new-feature-1234")
        == "feature-new-feature"
    )

    # Test with a branch name that is longer than 20 characters
    assert (
        util.generate_branch_short_name("feature/new-feature-1234567890")
        == "feature-new-feature"
    )

    # Test with a branch name containing trailing hyphens
    assert (
        util.generate_branch_short_name("feature/new-feature-") == "feature-new-feature"
    )

    # Test with a branch name containing only special characters
    assert util.generate_branch_short_name("@@@@") == ""

    # Test with a branch name containing only digits
    assert util.generate_branch_short_name("1234567890") == "1234567890"

    # Test with an empty branch name
    assert util.generate_branch_short_name("") == ""

    # Test with None as the branch name
    assert util.generate_branch_short_name(None) == ""


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
    payload.Package.DeploySpec = DeploySpec(actions=[])

    # Assert the payload contains the expected values
    assert payload.Task == task
    assert payload.Force == kwargs["force"]
    assert payload.DryRun == kwargs["dry_run"]
    assert payload.Type == kwargs["automation_type"]

    deployspec_data = []

    # Add more assertions for identity, deployment, and package details
    identity_details = "prn:example_portfolio:example_app:main-branch:build-123"
    deployment_details = DeploymentDetails.from_arguments(**kwargs)
    package_details = PackageDetails.from_arguments(
        deployment_details=deployment_details,
        deployspec=deployspec_data,
        **kwargs,
    )

    assert payload.Identity == identity_details
    assert payload.DeploymentDetails == deployment_details
    assert payload.Package == package_details

    assert package_details.TempDir is not None


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
        tasik="deploy",
        client="example_client",
        portfolio="example_portfolio",
        app="example_app",
        branch="main_branch",
        build="build-123",
        environment="dev",
        datacenter="sin",
        component="example_component",
        automation_type="deployspec",
    )

    path = util.get_artefacts_path(task_payload.DeploymentDetails)

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

    path = util.get_artefacts_path(task_payload.DeploymentDetails, s3=True)

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

    path = util.get_artefacts_path(task_payload.DeploymentDetails, "bubbles", s3=False)

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

    path = util.get_artefacts_path(task_payload.DeploymentDetails, "bubbles", s3=True)

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
        datacenter="sin",
        component="example_component",
        automation_type="deployspec",
    )

    path = util.get_packages_path(task_payload.DeploymentDetails)

    # standard path separator is colon
    assert path == os.path.sep.join(
        ["packages", "example_portfolio", "example_app", "main-branch", "build-123"]
    )

    path = util.get_packages_path(task_payload.DeploymentDetails, s3=True)

    # S3 paths are slashes not semi-colons
    assert path == "/".join(
        ["packages", "example_portfolio", "example_app", "main-branch", "build-123"]
    )

    path = util.get_packages_path(task_payload.DeploymentDetails, "bubbles", s3=False)

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

    path = util.get_packages_path(task_payload.DeploymentDetails, "bubbles", s3=True)

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
        datacenter="sin",
        component="example_component",
        automation_type="deployspec",
    )

    path = util.get_files_path(task_payload.DeploymentDetails)

    # standard path separator is semi-colon
    assert path == os.path.sep.join(
        ["files", "example_portfolio", "example_app", "main-branch", "build-123"]
    )

    path = util.get_files_path(task_payload.DeploymentDetails, s3=True)

    # S3 paths are slashes not semi-colons
    assert path == "/".join(
        ["files", "example_portfolio", "example_app", "main-branch", "build-123"]
    )

    path = util.get_files_path(task_payload.DeploymentDetails, "bubbles", s3=False)

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

    path = util.get_files_path(task_payload.DeploymentDetails, "bubbles", s3=True)

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

    generate_deployment = util.generate_deployment_details(
        client="example_client",
        portfolio="example_portfolio",
        app="example_app",
        branch="main_branch",
        build="build-123",
        environment="dev",
        datacenter="sin",
        component="example_component",
    )

    name = "artefact_name"

    key = util.get_artefact_key(generate_deployment, name, SCOPE_BUILD)

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

    key = util.get_artefact_key(generate_deployment, name, SCOPE_BRANCH)

    assert key == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "main-branch",
            "artefact_name",
        ]
    )

    key = util.get_artefact_key(generate_deployment, name, SCOPE_APP)

    assert key == "/".join(
        [
            "artefacts",
            "example_portfolio",
            "example_app",
            "artefact_name",
        ]
    )

    key = util.get_artefact_key(generate_deployment, name, SCOPE_PORTFOLIO)

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
        "datacenter": "sin",
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

    assert dd.Client == "example_client"
    assert dd.Portfolio == "example_portfolio"

    assert dd.StackFile == "template.yaml"
    assert dd.App == "example_stack"
    assert dd.Branch == "example_region"
    assert dd.BranchShortName == "example-region"

    assert dd.Build == "build-123"
    assert dd.Environment == "dev"
    assert dd.DataCenter == "sin"
    assert dd.Component == "example_component"


def test_get_prn_and_alt():

    result = util.get_prn(
        "portfolio", "app", "branch", "build", "component", SCOPE_BUILD
    )

    assert result == "portfolio:app:branch:build"

    result = util.get_prn(
        "portfolio", "app", "branch", "build", "component", SCOPE_COMPONENT
    )

    assert result == "portfolio:app:branch:build:component"

    result = util.get_prn_alt(
        "portfolio", "app", "branch", "build", "component", SCOPE_BUILD
    )

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


if __name__ == "__main__":
    pytest.main()
