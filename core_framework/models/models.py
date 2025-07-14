"""
Models Helper Functions Module
==============================

This module provides common helper functions that assist in the generation of model class instances
for the core automation framework. These functions provide convenient factory methods and path
generation utilities for working with deployment details, packages, actions, and state information.

The functions in this module serve as a bridge between command-line arguments and the structured
model objects used throughout the core automation system.

Functions
---------
get_artefact_key : function
    Get the artefacts key in the S3 bucket for deployment details
get_artefacts_path : function
    Get the artefacts path with optional S3 formatting
get_packages_path : function
    Get the packages path in the storage system
get_files_path : function
    Get the files path in the storage system
generate_task_payload : function
    Create a TaskPayload object from command line arguments
generate_package_details : function
    Create a PackageDetails object from deployment details and arguments
generate_deployment_details_from_stack : function
    Generate DeploymentDetails objects from stack configuration
generate_deployment_details : function
    Create a DeploymentDetails object from command line arguments
generate_action_details : function
    Create an ActionDetails object from deployment details and arguments
generate_state_details : function
    Create a StateDetails object from deployment details and arguments

Examples
--------
Generate deployment details from arguments::

    >>> dd = generate_deployment_details(
    ...     client="my-client",
    ...     portfolio="my-portfolio",
    ...     app="my-app"
    ... )

Get artefacts path::

    >>> path = get_artefacts_path(dd, "deploy.yaml")
    >>> print(path)  # artefacts/my-portfolio/my-app/main/1.0.0/deploy.yaml

Create action details::

    >>> action_details = generate_action_details(dd, task="deploy")
"""

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
    scope: str | None = None,
) -> str:
    """
    Get the artefacts key in the core automation S3 bucket for the deployment details.

    This function generates S3 keys for artefacts storage following the hierarchical
    path structure: artefacts/portfolio/app/branch/build/<name>

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object containing the deployment context.
    name : str | None, optional
        The name of the artefacts file or sub-folder. If None, returns the directory path.
    scope : str | None, optional
        The scope override for the artefacts path. If None, uses the deployment's scope.
        Valid values: "portfolio", "app", "branch", "build".

    Returns
    -------
    str
        The S3 key path to the artefacts location with forward slashes.

    Examples
    --------
    Get artefacts directory key::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        >>> key = get_artefact_key(dd)
        >>> print(key)  # artefacts/ecom/web/main/1.0

    Get specific file key::

        >>> key = get_artefact_key(dd, "deploy.yaml")
        >>> print(key)  # artefacts/ecom/web/main/1.0/deploy.yaml

    Override scope::

        >>> key = get_artefact_key(dd, "app-config.yaml", scope="app")
        >>> print(key)  # artefacts/ecom/web/app-config.yaml

    Notes
    -----
    This function is a convenience wrapper around get_artefacts_path() with s3=True.
    The returned path uses forward slashes suitable for S3 keys.
    """
    return get_artefacts_path(deployment_details, name, scope, True)


def get_artefacts_path(
    deployment_details: DeploymentDetails,
    name: str | None = None,
    scope: str | None = None,
    s3: bool = False,
) -> str:
    """
    Get the artefacts path in the core automation storage system.

    This function generates paths for artefacts storage that can be used for both
    S3 and local filesystem storage depending on the s3 parameter.

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object containing the deployment context.
    name : str | None, optional
        The name of the artefacts file or directory. If None, returns the directory path.
    scope : str | None, optional
        The scope override for the artefacts path. If None, uses the deployment's scope.
        Valid values: "portfolio", "app", "branch", "build".
    s3 : bool, optional
        If True, forces forward slashes for S3 compatibility. If False, uses OS-dependent
        path separators. Default is False.

    Returns
    -------
    str
        The path to the artefacts location in the specified format.

    Examples
    --------
    Get local filesystem path::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        >>> path = get_artefacts_path(dd, "deploy.yaml")
        >>> print(path)  # artefacts/ecom/web/main/1.0/deploy.yaml (or artefacts\\ecom\\web\\main\\1.0\\deploy.yaml on Windows)

    Get S3-compatible path::

        >>> path = get_artefacts_path(dd, "deploy.yaml", s3=True)
        >>> print(path)  # artefacts/ecom/web/main/1.0/deploy.yaml

    Override scope::

        >>> path = get_artefacts_path(dd, "config.yaml", scope="app")
        >>> print(path)  # artefacts/ecom/web/config.yaml

    Notes
    -----
    This function delegates to the deployment_details.get_object_key() method
    with the OBJ_ARTEFACTS constant.
    """
    return deployment_details.get_object_key(OBJ_ARTEFACTS, name, scope, s3)


def get_packages_path(
    deployment_details: DeploymentDetails,
    name: str | None = None,
    scope: str | None = None,
    s3: bool = False,
) -> str:
    """
    Get the packages path in the core automation storage system.

    This function generates paths for packages storage following the hierarchical
    path structure: packages/portfolio/app/branch/build/<name>

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object containing the deployment context.
    name : str | None, optional
        The name of the packages file or directory. If None, returns the directory path.
    scope : str | None, optional
        The scope override for the packages path. If None, uses the deployment's scope.
        Valid values: "portfolio", "app", "branch", "build".
    s3 : bool, optional
        If True, forces forward slashes for S3 compatibility. If False, uses OS-dependent
        path separators. Default is False.

    Returns
    -------
    str
        The path to the packages location in the specified format.

    Examples
    --------
    Get packages directory path::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        >>> path = get_packages_path(dd)
        >>> print(path)  # packages/ecom/web/main/1.0

    Get specific package path::

        >>> path = get_packages_path(dd, "app-package.zip")
        >>> print(path)  # packages/ecom/web/main/1.0/app-package.zip

    Get S3-compatible path::

        >>> path = get_packages_path(dd, "package.zip", s3=True)
        >>> print(path)  # packages/ecom/web/main/1.0/package.zip

    Notes
    -----
    This function delegates to the deployment_details.get_object_key() method
    with the OBJ_PACKAGES constant.
    """
    return deployment_details.get_object_key(OBJ_PACKAGES, name, scope, s3)


def get_files_path(
    deployment_details: DeploymentDetails,
    name: str | None = None,
    scope: str | None = None,
    s3: bool = False,
) -> str:
    """
    Get the files path in the core automation storage system.

    This function generates paths for files storage following the hierarchical
    path structure: files/portfolio/app/branch/build/<name>

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object containing the deployment context.
    name : str | None, optional
        The name of the file or directory. If None, returns the directory path.
    scope : str | None, optional
        The scope override for the files path. If None, uses the deployment's scope.
        Valid values: "portfolio", "app", "branch", "build".
    s3 : bool, optional
        If True, forces forward slashes for S3 compatibility. If False, uses OS-dependent
        path separators. Default is False.

    Returns
    -------
    str
        The path to the files location in the specified format.

    Examples
    --------
    Get files directory path::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        >>> path = get_files_path(dd)
        >>> print(path)  # files/ecom/web/main/1.0

    Get specific file path::

        >>> path = get_files_path(dd, "config.json")
        >>> print(path)  # files/ecom/web/main/1.0/config.json

    Override scope to app level::

        >>> path = get_files_path(dd, "app-config.json", scope="app")
        >>> print(path)  # files/ecom/web/app-config.json

    Notes
    -----
    This function delegates to the deployment_details.get_object_key() method
    with the OBJ_FILES constant.
    """
    return deployment_details.get_object_key(OBJ_FILES, name, scope, s3)


def generate_task_payload(**kwargs) -> TaskPayload:
    """
    Create a TaskPayload object from command line arguments.

    This function serves as a factory method to create TaskPayload instances
    from keyword arguments typically derived from command line input.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments containing task payload parameters. These are typically
        derived from command line arguments and can include:
        - client (str): Client identifier
        - portfolio (str): Portfolio name
        - app (str): Application name
        - branch (str): Branch name
        - build (str): Build identifier
        - component (str): Component name
        - task (str): Task name
        - Additional parameters as supported by TaskPayload.from_arguments()

    Returns
    -------
    TaskPayload
        A TaskPayload object initialized with the provided arguments.

    Examples
    --------
    Create task payload from command line args::

        >>> args = {
        ...     "client": "my-client",
        ...     "portfolio": "ecommerce",
        ...     "app": "web-app",
        ...     "task": "deploy"
        ... }
        >>> payload = generate_task_payload(**args)
        >>> print(payload.task)  # deploy

    Create with minimal arguments::

        >>> payload = generate_task_payload(task="build")

    Notes
    -----
    This function delegates to TaskPayload.from_arguments() for the actual
    object creation and validation.
    """
    return TaskPayload.from_arguments(**kwargs)


def generate_package_details(
    deployment_details: DeploymentDetails, **kwargs
) -> PackageDetails:
    """
    Create a PackageDetails object from deployment details and additional arguments.

    This function generates PackageDetails objects that describe package locations
    and metadata based on the deployment context.

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object that provides the deployment context.
    **kwargs : dict
        Additional keyword arguments for package details. These can include:
        - package_name (str): Name of the package
        - package_version (str): Version of the package
        - package_type (str): Type of package (e.g., "zip", "tar.gz")
        - bucket_name (str): S3 bucket name override
        - bucket_region (str): S3 bucket region override
        - Additional parameters as supported by PackageDetails.from_arguments()

    Returns
    -------
    PackageDetails
        A PackageDetails object initialized with the deployment context and
        additional parameters.

    Examples
    --------
    Create package details from deployment::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", build="1.0")
        >>> pkg = generate_package_details(dd, package_name="web-app.zip")
        >>> print(pkg.package_name)  # web-app.zip

    Create with custom package type::

        >>> pkg = generate_package_details(
        ...     dd, 
        ...     package_name="app-bundle.tar.gz",
        ...     package_type="tar.gz"
        ... )

    Notes
    -----
    The deployment_details parameter is automatically added to the kwargs
    before calling PackageDetails.from_arguments().
    """
    kwargs["deployment_details"] = deployment_details
    return PackageDetails.from_arguments(**kwargs)


def generate_deployment_details_from_stack(**kwargs) -> list[DeploymentDetails]:
    """
    Generate multiple DeploymentDetails objects from stack configuration.

    This function creates DeploymentDetails objects based on stack configuration
    that specifies multiple stacks and regions. It's useful for multi-region
    or multi-stack deployments.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments that must include:
        - stacks (list): List of stack configurations, each containing:
            - stack_name (str): Name of the stack
            - regions (list): List of regions for the stack
            - stack_file (str): CloudFormation template file
        - Other deployment parameters (client, portfolio, etc.)

    Returns
    -------
    list[DeploymentDetails]
        A list of DeploymentDetails objects, one for each stack/region combination.
        If no stacks are provided, returns a single DeploymentDetails object.

    Examples
    --------
    Generate from stack configuration::

        >>> stacks_config = {
        ...     "client": "my-client",
        ...     "portfolio": "ecommerce",
        ...     "stacks": [
        ...         {
        ...             "stack_name": "web-app",
        ...             "regions": ["us-east-1", "us-west-2"],
        ...             "stack_file": "web-app.yaml"
        ...         },
        ...         {
        ...             "stack_name": "database",
        ...             "regions": ["us-east-1"],
        ...             "stack_file": "database.yaml"
        ...         }
        ...     ]
        ... }
        >>> deployments = generate_deployment_details_from_stack(**stacks_config)
        >>> print(len(deployments))  # 3 (web-app in 2 regions + database in 1 region)

    Handle case with no stacks::

        >>> deployments = generate_deployment_details_from_stack(
        ...     client="my-client",
        ...     portfolio="ecommerce"
        ... )
        >>> print(len(deployments))  # 1

    Notes
    -----
    - Each stack/region combination creates a separate DeploymentDetails object
    - The stack_name is used as the app name in the resulting DeploymentDetails
    - The region is used as the branch name in the resulting DeploymentDetails
    - If no stacks are provided, a single DeploymentDetails object is created
    """
    result = []
    stacks = kwargs.get("stacks")
    if not stacks:
        return [DeploymentDetails.from_arguments(**kwargs)]
    
    for stack in stacks:
        regions = stack.get("regions", [])
        if not regions:
            continue
        
        for region in regions:
            # Create a copy of kwargs to avoid modifying the original
            stack_kwargs = kwargs.copy()
            stack_kwargs["app"] = stack.get("stack_name")
            stack_kwargs["branch"] = region
            stack_kwargs["stack_file"] = stack.get("stack_file")
            result.append(DeploymentDetails.from_arguments(**stack_kwargs))
    
    return result


def generate_deployment_details(**kwargs) -> DeploymentDetails:
    """
    Create a DeploymentDetails object from command line arguments.

    This function serves as a factory method to create DeploymentDetails instances
    from keyword arguments typically derived from command line input.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments containing deployment details parameters. These can include:
        - client (str): Client identifier
        - prn (str): Complete PRN to parse (overrides other parameters)
        - portfolio (str): Portfolio name
        - app (str): Application name
        - branch (str): Branch name
        - build (str): Build identifier or instance
        - component (str): Component name
        - environment (str): Environment name
        - data_center (str): Data center location
        - scope (str): Deployment scope override
        - tags (dict): Resource tags
        - stack_file (str): CloudFormation template file
        - delivered_by (str): Delivery person or system

    Returns
    -------
    DeploymentDetails
        A DeploymentDetails object initialized with the provided arguments.

    Examples
    --------
    Create from individual parameters::

        >>> dd = generate_deployment_details(
        ...     client="my-client",
        ...     portfolio="ecommerce",
        ...     app="web-app",
        ...     branch="main",
        ...     build="1.2.3"
        ... )

    Create from PRN (overrides other values)::

        >>> dd = generate_deployment_details(
        ...     client="my-client",
        ...     prn="prn:ecommerce:web-app:main:1.2.3"
        ... )

    Create with minimal arguments::

        >>> dd = generate_deployment_details(
        ...     portfolio="ecommerce",
        ...     app="web-app"
        ... )

    Notes
    -----
    - If a PRN is provided, it overrides all other deployment hierarchy parameters
    - Missing parameters are populated with defaults from the utility functions
    - This function delegates to DeploymentDetails.from_arguments() for object creation
    """
    return DeploymentDetails.from_arguments(**kwargs)


def generate_action_details(deployment_details: DeploymentDetails, **kwargs) -> ActionDetails:
    """
    Create an ActionDetails object from deployment details and additional arguments.

    This function generates ActionDetails objects that describe action file locations
    and metadata based on the deployment context.

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object that provides the deployment context.
    **kwargs : dict
        Additional keyword arguments for action details. These can include:
        - task (str): Task name to generate action file from
        - action_file (str): Specific action file name
        - key (str): Direct S3 key specification
        - bucket_name (str): S3 bucket name override
        - bucket_region (str): S3 bucket region override
        - version_id (str): S3 object version ID
        - content_type (str): MIME type of the action file
        - mode (str): Storage mode (V_LOCAL or V_SERVICE)
        - Additional parameters as supported by ActionDetails.from_arguments()

    Returns
    -------
    ActionDetails
        An ActionDetails object initialized with the deployment context and
        additional parameters.

    Examples
    --------
    Create action details from task name::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", build="1.0")
        >>> action = generate_action_details(dd, task="deploy")
        >>> print(action.key)  # artefacts/ecom/web/.../deploy.actions

    Create with explicit action file::

        >>> action = generate_action_details(dd, action_file="custom.actions")

    Create with direct key specification::

        >>> action = generate_action_details(dd, key="custom/path/actions.yaml")

    Notes
    -----
    The deployment_details parameter is automatically added to the kwargs
    before calling ActionDetails.from_arguments().
    """
    kwargs["deployment_details"] = deployment_details
    return ActionDetails.from_arguments(**kwargs)


def generate_state_details(deployment_details: DeploymentDetails, **kwargs) -> StateDetails:
    """
    Create a StateDetails object from deployment details and additional arguments.

    This function generates StateDetails objects that describe state file locations
    and metadata based on the deployment context.

    Parameters
    ----------
    deployment_details : DeploymentDetails
        The deployment details object that provides the deployment context.
    **kwargs : dict
        Additional keyword arguments for state details. These can include:
        - state_file (str): Specific state file name
        - key (str): Direct S3 key specification
        - bucket_name (str): S3 bucket name override
        - bucket_region (str): S3 bucket region override
        - version_id (str): S3 object version ID
        - content_type (str): MIME type of the state file
        - mode (str): Storage mode (V_LOCAL or V_SERVICE)
        - Additional parameters as supported by StateDetails.from_arguments()

    Returns
    -------
    StateDetails
        A StateDetails object initialized with the deployment context and
        additional parameters.

    Examples
    --------
    Create state details with default settings::

        >>> dd = DeploymentDetails(portfolio="ecom", app="web", build="1.0")
        >>> state = generate_state_details(dd)

    Create with custom state file::

        >>> state = generate_state_details(dd, state_file="custom-state.json")

    Create with direct key specification::

        >>> state = generate_state_details(dd, key="custom/path/state.json")

    Notes
    -----
    The deployment_details parameter is automatically added to the kwargs
    before calling StateDetails.from_arguments().
    """
    kwargs["deployment_details"] = deployment_details
    return StateDetails.from_arguments(**kwargs)
