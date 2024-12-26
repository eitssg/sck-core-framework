""" Module to define some common helper functions that assis in the generation of the model class instances. """

from ..constants import (
    OBJ_ARTEFACTS,
    OBJ_PACKAGES,
    OBJ_FILES,
)

from .deployment_details import DeploymentDetails
from .package_details import PackageDetails
from .action_details import ActionDetails
from .state_details import StateDetails
from .task_payload import TaskPayload


def get_artefact_key(
    deployment_details: DeploymentDetails,
    name: str | None = None,
) -> str:
    """
    Helper function to get the artefacts key in the core automation s3 bucket for the deployment details.

    Example: /artefacts/portfolio/app/branch/build-213/<name>

    Expected to be appended to the end of the s3 bucket name.

    s3://<bucket-name>/artefacts/portfolio/app/branch/build-213/<name>

    Args:
        task_payload (dict): The task payload where the deployment details are stored
        name (str, optional): The name of the artefacts sub-folder, (e.g. /portfolio/app/branch/build-213/<name>)

    Return:
        str: The path to the artefacts in the core automation s3 bucket
    """
    return get_artefacts_path(deployment_details, name, True)


def get_artefacts_path(
    deployment_details: DeploymentDetails,
    name: str | None = None,
    s3: bool = False,
) -> str:
    """
    Helper function to get the artefacts path in the core automation s3 bucket for the task payload.

    Example: artefacts/portfolio/app/branch/build-213/<name>

    Args:
        deployment_details (DeploymentDetails): The deployment details describing the deployment
        name (str, optional): The name of the artefacts folder
        s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

    Return:
        str | None: The path to the artefacts in the core automation s3 bucket
    """
    return deployment_details.get_object_key(OBJ_ARTEFACTS, name, s3)


def get_packages_path(
    deployment_details: DeploymentDetails,
    name: str | None = None,
    s3: bool = False,
) -> str:
    """
    Helper function to get the packages path in the core automation s3 bucket for the task payload.

    Example: packages/portfolio/app/branch/build-213/<name>

    Args:
        deployment_details (DeploymentDetails): The deployment details describing the deployment
        name (str, optional): The name of the artefacts folder
        s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

    Return:
        str: The path to the packages in the core automation s3 bucket
    """
    return deployment_details.get_object_key(OBJ_PACKAGES, name, s3)


def get_files_path(
    deployment_details: DeploymentDetails,
    name: str | None = None,
    s3: bool = False,
) -> str:
    """
    Helper function to get the files path in the core automation s3 bucket for the BUILD scope from the task payload.

    Example: files/portfolio/app/branch/build-213/<name>

    Args:
        deployment_details (DeploymentDetails): The deployment details describing the deployment
        name (str, optional): The name of the artefacts folder
        s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

    Return:
        str: The path to the files in the core automation s3 bucket
    """
    return deployment_details.get_object_key(OBJ_FILES, name, s3)


def generate_task_payload(**kwargs) -> TaskPayload:
    """
    Create a task payload object from the command line arguments

    Args:
        kwargs: The command line arguments dictionary.  User input parameters.

    Returns:
        dict: The task payload object
    """
    return TaskPayload.from_arguments(**kwargs)


def generate_package_details(
    deployment_details: DeploymentDetails, **kwargs
) -> PackageDetails:
    """
    Convert the command line arguments into a PACKAGE object.

    Args:
        deployment_details: The deployment details object
        kwargs: A dictionary containing the extra paramters for package details

    Returns:
        dict: A Package Details object

    """
    kwargs["deployment_details"] = deployment_details
    return PackageDetails.from_arguments(**kwargs)


def generate_deployment_details_from_stack(**kwargs) -> list[DeploymentDetails]:
    """
    Generate a DeploymentDetails object

    Example:

    payload = { "DeploymentDetails": generate_deployment_details(args) }

    Args:
        kwargs: A dictonary containint the deplayment details parameters

    Returns:
        list[dict]: A list of DeploymentDetails objects
    """
    result = []
    stacks = kwargs.get("stacks")
    if not stacks:
        return [DeploymentDetails.from_arguments(**kwargs)]
    for stack in stacks:
        regions = stack.get("regions")
        if not regions:
            continue
        for region in regions:
            kwargs["app"] = stack.get("stack_name")
            kwargs["branch"] = region
            kwargs["stack_file"] = stack.get("stack_file")
            result.append(DeploymentDetails.from_arguments(**kwargs))
    return result


def generate_deployment_details(**kwargs) -> DeploymentDetails:
    """
    Convert the commandline arguments into a DEPLOYMENT_DETAILS object.

    The attributes that should be passed in the kwargs are:
        * client
        * prn

        * portfolio
        * app
        * branch
        * instance or build
        * environment
        * data_center
        * component

    if you suppply a "prn" then it will override all the other values.

    Args:
        kwargs: A dictionary containing the deployment details paremeters

    Returns:
        dict: A DeploymentDetails object
    """
    return DeploymentDetails.from_arguments(**kwargs)


def generate_action_details(deployment_details: DeploymentDetails, **kwargs):
    """
    Generate the action details from the command line arguments

    Args:
        deployment_details: The deployment details object to reference
        kwargs: The command line arguments dictionary.  User input parameters.

    Returns:
        dict: The action details object
    """
    kwargs["deployment_details"] = deployment_details
    return ActionDetails.from_arguments(**kwargs)


def generate_state_details(deploymet_details: DeploymentDetails, **kwargs):
    """
    Generate the state details from the command line arguments

    Args:
        deployment_details: The deployment details object to reference
        kwargs: The command line arguments dictionary.  User input parameters.

    Returns:
        dict: The state details object
    """
    kwargs["deployment_details"] = deploymet_details
    return StateDetails.from_arguments(**kwargs)
