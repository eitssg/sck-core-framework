from pydantic import ValidationError
import pytest
import os

import core_framework as util
from core_framework.constants import ENV_LOCAL_MODE

from core_framework.models import (
    ActionSpec,
    TaskPayload,
    DeploymentDetails,
    DeploySpec,
    ActionSpec,
    PackageDetails,
)


@pytest.fixture
def setup_enivornment_variables():

    # Before proceeding we need to set up the environment variables for reasonable defaults in the models

    pass


@pytest.fixture
def runtime_arguments():

    arguments = {
        "task": "deploy",
        "client": "my-client",
        "portfolio": "my-portfolio",
        "app": "my-app",
        "branch": "my-branch",
        "build": "my-build",
        "mode": "local",
        "scope": "portfolio",
        "environment": "dev",
        "data_center": "us-east-1",
        "bucket_region": "specified_region",
    }

    return arguments


@pytest.fixture
def deployspec_sample():

    # Get the path of this current script file
    data_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(data_path, "deployspec_yaml", "deployspec.yaml")

    deployspec = util.load_yaml_file(
        file_path
    )  # Load the YAML file to ensure it exists

    return deployspec


def test_action_model():

    sample_action = {
        "Label": "my-action",
        "Type": "AWS::CreateUser",
        "Params": {
            "StackName": "my-action-cloudformation-stack",
            "Account": "123456789012",
            "Region": "us-east-1",
        },
        "Scope": "build",
    }

    action = ActionSpec(**sample_action)

    assert action is not None


def test_task_payload_model(runtime_arguments):

    os.environ[ENV_LOCAL_MODE] = "true"

    try:
        task_payload = TaskPayload.from_arguments(**runtime_arguments)

        assert task_payload is not None

        assert task_payload.task == "deploy"

        assert task_payload.identity == "prn:my-portfolio:my-app:my-branch:my-build"

        assert (
            task_payload.actions.bucket_name
            == "my-client-core-automation-specified_region"
        )

        assert task_payload.actions.bucket_region == "specified_region"

        assert (
            task_payload.actions.key
            == f"artefacts{os.path.sep}my-portfolio{os.path.sep}deploy.actions"
        )

        assert (
            task_payload.package.bucket_name
            == "my-client-core-automation-specified_region"
        )

        assert task_payload.package.bucket_region == "specified_region"

        assert (
            task_payload.package.key
            == f"packages{os.path.sep}my-portfolio{os.path.sep}package.zip"
        )

        assert task_payload.deployment_details.client == "my-client"

        assert task_payload.deployment_details.scope == "portfolio"

        assert task_payload.deployment_details.environment == "dev"

        assert task_payload.deployment_details.data_center == "us-east-1"

        assert task_payload.package.bucket_region == "specified_region"

        assert task_payload.state.bucket_region == "specified_region"

        assert (
            task_payload.state.key
            == f"artefacts{os.path.sep}my-portfolio{os.path.sep}deploy.state"
        )

        assert task_payload.flow_control is None

        assert task_payload.type == "pipeline"

    except ValidationError as e:
        print(e.errors())
        assert False, str(e)
    except Exception as e:
        print(e)
        assert False, str(e)


def test_deployment_details_model(runtime_arguments):

    try:
        deployment_details = DeploymentDetails.from_arguments(**runtime_arguments)

        assert deployment_details is not None

        assert deployment_details.scope == "portfolio"
    except ValidationError as e:
        print(e.errors())
        assert False, str(e)
    except Exception as e:
        print(e)
        assert False, str(e)


def test_package_details_model(runtime_arguments):

    try:
        package_details = PackageDetails.from_arguments(**runtime_arguments)

        assert package_details is not None

        assert (
            package_details.bucket_name == "my-client-core-automation-specified_region"
        )

        assert package_details.bucket_region == "specified_region"

        # The scope is "portfolio"

        assert (
            package_details.key
            == f"packages{os.path.sep}my-portfolio{os.path.sep}package.zip"
        )

    except ValidationError as e:
        print(e.erros())
        assert False, str(e)
    except Exception as e:
        print(e)
        assert False, str(e)


def test_deploy_spec_model(deployspec_sample):

    action_spec = ActionSpec(**deployspec_sample[0])

    assert action_spec is not None

    assert action_spec.label == "test1-create-user"

    assert action_spec.type == "create_user"

    deploy_spec = DeploySpec(actions=deployspec_sample)

    assert deploy_spec is not None

    assert isinstance(deploy_spec.action_specs, list)

    assert len(deploy_spec.action_specs) == 6

    assert deploy_spec.action_specs[5].label == "test1-delete-change-set"

    data = deploy_spec.model_dump(by_alias=True)

    assert "Actions" in data, "Expected 'actions' to be present in model_dump"
    assert isinstance(data["Actions"], list), "Expected 'Actions' to be a list"
    assert len(data["Actions"]) == 6, "Expected 6 actions in the model_dump"

    # Ensure pascal case in the cascaded dump
    assert "Name" in data["Actions"][0], "Expected 'Name' to be present in action"


def test_action_spec_model_dump(deployspec_sample):

    action_spec = ActionSpec(**deployspec_sample[0])

    data = action_spec.model_dump(by_alias=True)

    assert "Name" in data, "Expected 'Name' to be present in model_dump"
    assert "Kind" in data, "Expected 'Kind' to be present in model_dump"
    assert "Params" in data, "Expected 'Params' to be present in model_dump"
    assert "Scope" in data, "Expected 'Scope' to be present in model_dump"

    assert data["Name"] == "test1-create-user"

    assert "Action" not in data, "Expected 'action' to be excluded from model_dump"

    data = action_spec.model_dump(by_alias=False)

    assert "name" in data, "Expected 'name' to be present in model_dump"
    assert "kind" in data, "Expected 'kind' to be present in model_dump"
    assert "params" in data, "Expected 'params' to be present in model_dump"
    assert "scope" in data, "Expected 'scope' to be present in model_dump"

    assert data["name"] == "test1-create-user"


def test_action_spec_validation():
    try:

        action_spec = ActionSpec(
            **{
                "Label": "test-action",
                "Type": "AWS::CreateUser",
                "DependsOn": {},
                "Params": {
                    "StackName": "test-stack",
                },
            }
        )

        # Should have a validation error on DependsOn since it is not a valid type
        assert False, "Expected validation error for DependsOn field"

    except ValidationError as e:
        assert (
            e.errors() is not None
        ), "Expected validation error for non-existent action"


def test_action_spec_validation_invalid_scope():
    try:
        action_spec = ActionSpec(
            **{
                "Label": "test-action",
                "Type": "AWS::CreateUser",
                "Scope": "invalid_scope",
                "Params": {
                    "StackName": "test-stack",
                },
            }
        )
        # Should have a validation error on Scope since it is not a valid value
        assert False, "Expected validation error for invalid scope"
    except ValidationError as e:
        assert (
            e.errors() is not None
        ), "Expected validation error for invalid scope value"


def test_action_spec_model(deployspec_sample):

    sample_action_spec = deployspec_sample[0]

    action_spec = ActionSpec(**sample_action_spec)

    assert action_spec is not None

    # TODO: Add more tests for the DeploySpec model
