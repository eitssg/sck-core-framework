from pydantic import ValidationError
import pytest
import os
import yaml

from core_framework.models import (
    ActionDefinition,
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
    app_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(app_path, "sample_deployspec.yaml")
    with open(file_path, "r") as file:
        deployspec = yaml.safe_load(file)

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

    action = ActionDefinition(**sample_action)

    assert action is not None

    # TODO: Add more tests for the DeploySpec model


def test_task_payload_model(runtime_arguments):

    try:
        task_payload = TaskPayload.from_arguments(**runtime_arguments)

        assert task_payload is not None

        assert task_payload.Identity == "prn:my-portfolio:my-app:my-branch:my-build"

        assert task_payload.Actions.BucketName == "my-client-core-automation-master"

        assert task_payload.Actions.BucketRegion == "specified_region"

        assert task_payload.Actions.Key == f"artefacts{os.path.sep}my-portfolio"

        assert task_payload.Package.BucketName == "my-client-core-automation-master"

        assert task_payload.Package.BucketRegion == "specified_region"

        assert task_payload.Package.Key == f"packages{os.path.sep}my-portfolio"

        assert task_payload.DeploymentDetails.Client == "my-client"

        assert task_payload.DeploymentDetails.Scope == "portfolio"

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

        assert deployment_details.Scope == "portfolio"
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

        assert package_details.BucketName == "my-client-core-automation-master"

        assert package_details.BucketRegion == "specified_region"

        # The scope is "portfolio"

        assert package_details.Key == f"packages{os.path.sep}my-portfolio"

    except ValidationError as e:
        print(e.erros())
        assert False, str(e)
    except Exception as e:
        print(e)
        assert False, str(e)


def test_deploy_spec_model(deployspec_sample):

    action1 = deployspec_sample[0]

    action_spec = ActionSpec(**action1)

    assert action_spec is not None

    assert action_spec.label == "test1-create-user"
    assert action_spec.action == "AWS::CreateUser"

    deploy_spec = DeploySpec(actions=deployspec_sample)

    assert deploy_spec is not None

    assert isinstance(deploy_spec.action_specs, list)

    assert len(deploy_spec.action_specs) == 6

    assert deploy_spec.action_specs[5].label == "test1-delete-change-set"


def test_action_spec_model(deployspec_sample):

    sample_action_spec = deployspec_sample[0]

    action_spec = ActionSpec(**sample_action_spec)

    assert action_spec is not None

    # TODO: Add more tests for the DeploySpec model
