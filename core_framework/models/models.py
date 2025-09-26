"""Models Helper Functions Module for Core Automation Framework.

This module provides common helper functions that assist in the generation of model class instances
for the core automation framework. These functions provide convenient factory methods and path
generation utilities for working with deployment details, packages, actions, and state information.

The functions in this module serve as a bridge between command-line arguments and the structured
model objects used throughout the core automation system.

Key Functions:
    - **Path Generation**: get_artefact_key, get_artefacts_path, get_packages_path, get_files_path
    - **Model Factories**: generate_task_payload, generate_package_details, generate_deployment_details
    - **State Management**: generate_action_details, generate_state_details
    - **Multi-Stack Support**: generate_deployment_details_from_stack

Usage Pattern:
    These helper functions are typically used in command-line tools and automation scripts
    to convert raw arguments into properly structured model objects for the framework.
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
    """Get the artefacts key in the core automation S3 bucket for deployment details.

    This function generates S3 keys for artefacts storage following the hierarchical
    path structure: artefacts/portfolio/app/branch/build/<name>

    Args:
        deployment_details: The deployment details object containing the deployment context.
        name: The name of the artefacts file or sub-folder. If None, returns the directory path.
        scope: The scope override for the artefacts path. If None, uses the deployment's scope.
               Valid values: "portfolio", "app", "branch", "build".

    Returns:
        The S3 key path to the artefacts location with forward slashes.

    Examples::

        dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        key = get_artefact_key(dd)
        print(key)
         'artefacts/ecom/web/main/1.0'

        # Get specific file key
        key = get_artefact_key(dd, "deploy.yaml")
        print(key)
         'artefacts/ecom/web/main/1.0/deploy.yaml'

        # Override scope to app level
        key = get_artefact_key(dd, "app-config.yaml", scope="app")
        print(key)
         'artefacts/ecom/web/app-config.yaml'

    Notes:
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
    """Get the artefacts path in the core automation storage system.

    This function generates paths for artefacts storage that can be used for both
    S3 and local filesystem storage depending on the s3 parameter.

    Args:
        deployment_details: The deployment details object containing the deployment context.
        name: The name of the artefacts file or directory. If None, returns the directory path.
        scope: The scope override for the artefacts path. If None, uses the deployment's scope.
               Valid values: "portfolio", "app", "branch", "build".
        s3: If True, forces forward slashes for S3 compatibility. If False, uses OS-dependent
            path separators.

    Returns:
        The path to the artefacts location in the specified format.

    Examples::

        dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        # Get local filesystem path
        path = get_artefacts_path(dd, "deploy.yaml")
        print(path)
         'artefacts/ecom/web/main/1.0/deploy.yaml'  # or with backslashes on Windows

        # Get S3-compatible path
        path = get_artefacts_path(dd, "deploy.yaml", s3=True)
        print(path)
         'artefacts/ecom/web/main/1.0/deploy.yaml'

        # Override scope to portfolio level
        path = get_artefacts_path(dd, "config.yaml", scope="portfolio")
        print(path)
         'artefacts/ecom/config.yaml'

    Notes:
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
    """Get the packages path in the core automation storage system.

    This function generates paths for packages storage following the hierarchical
    path structure: packages/portfolio/app/branch/build/<name>

    Args:
        deployment_details: The deployment details object containing the deployment context.
        name: The name of the packages file or directory. If None, returns the directory path.
        scope: The scope override for the packages path. If None, uses the deployment's scope.
               Valid values: "portfolio", "app", "branch", "build".
        s3: If True, forces forward slashes for S3 compatibility. If False, uses OS-dependent
            path separators.

    Returns:
        The path to the packages location in the specified format.

    Examples::

        dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        # Get packages directory path
        path = get_packages_path(dd)
        print(path)
         'packages/ecom/web/main/1.0'

        # Get specific package path
        path = get_packages_path(dd, "app-package.zip")
        print(path)
         'packages/ecom/web/main/1.0/app-package.zip'

        # Get S3-compatible path
        path = get_packages_path(dd, "package.zip", s3=True)
        print(path)
         'packages/ecom/web/main/1.0/package.zip'

    Notes:
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
    """Get the files path in the core automation storage system.

    This function generates paths for files storage following the hierarchical
    path structure: files/portfolio/app/branch/build/<name>

    Args:
        deployment_details: The deployment details object containing the deployment context.
        name: The name of the file or directory. If None, returns the directory path.
        scope: The scope override for the files path. If None, uses the deployment's scope.
               Valid values: "portfolio", "app", "branch", "build".
        s3: If True, forces forward slashes for S3 compatibility. If False, uses OS-dependent
            path separators.

    Returns:
        The path to the files location in the specified format.

    Examples::

        dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
        # Get files directory path
        path = get_files_path(dd)
        print(path)
         'files/ecom/web/main/1.0'

        # Get specific file path
        path = get_files_path(dd, "config.json")
        print(path)
         'files/ecom/web/main/1.0/config.json'

        # Override scope to app level
        path = get_files_path(dd, "app-config.json", scope="app")
        print(path)
         'files/ecom/web/app-config.json'

    Notes:
        This function delegates to the deployment_details.get_object_key() method
        with the OBJ_FILES constant.
    """
    return deployment_details.get_object_key(OBJ_FILES, name, scope, s3)


def generate_task_payload(**kwargs) -> TaskPayload:
    """Create a TaskPayload object from command line arguments.

    This function serves as a factory method to create TaskPayload instances
    from keyword arguments typically derived from command line input.

    Args:
        **kwargs: Task parameters including:
            - task (str): Task name (required)
            - client (str): Client identifier
            - portfolio (str): Portfolio name
            - app (str): Application name
            - branch (str): Branch name
            - build (str): Build identifier
            - force (bool): Force execution flag
            - dry_run (bool): Dry run mode flag

    Returns:
        TaskPayload: Configured task payload object with deployment details.

    Example:
        >>> payload = generate_task_payload(
        ...     task="deploy",
        ...     client="my-client",
        ...     portfolio="web-services",
        ...     app="frontend"
        ... )
        >>> payload.task
        'deploy'
    """
    return TaskPayload.from_arguments(**kwargs)


def generate_package_details(deployment_details: DeploymentDetails, **kwargs) -> PackageDetails:
    """Create a PackageDetails object from deployment details and additional arguments.

    This function generates PackageDetails objects that describe package locations
    and metadata based on the deployment context.

    Args:
        deployment_details (DeploymentDetails): The deployment details object that
            provides the deployment context.
        **kwargs: Additional keyword arguments for package details including:
            - package_file (str): Name of the package file
            - compile_mode (str): Compilation mode ('full' or 'incremental')
            - bucket_name (str): S3 bucket name override
            - bucket_region (str): S3 bucket region override
            - mode (str): Storage mode ('local' or 'service')

    Returns:
        PackageDetails: Package details object with S3 location and metadata.

    Example:
        >>> dd = DeploymentDetails(portfolio="web", app="frontend", build="1.0")
        >>> pkg = generate_package_details(dd, package_file="app.zip")
        >>> "app.zip" in pkg.key
        True
    """
    kwargs["deployment_details"] = deployment_details
    return PackageDetails.from_arguments(**kwargs)


def generate_deployment_details_from_stack(**kwargs) -> list[DeploymentDetails]:
    """Generate DeploymentDetails objects from multi-stack configuration.

    This function creates multiple DeploymentDetails objects from a configuration
    that specifies multiple stacks and regions. It's useful for multi-region
    or multi-stack deployments.

    Args:
        **kwargs: Keyword arguments that must include:
            - stacks (list): List of stack configurations, each containing:
                - stack_name (str): Name of the stack
                - regions (list): List of regions for the stack
                - stack_file (str): CloudFormation template file
            - client (str): Client identifier
            - portfolio (str): Portfolio name
            - build (str): Build identifier
            - Any other deployment parameters

    Returns:
        list[DeploymentDetails]: List of DeploymentDetails objects, one for each
            stack/region combination. If no stacks are provided, returns a single
            DeploymentDetails object.

    Example:
        >>> config = {
        ...     "client": "web-team",
        ...     "portfolio": "ecommerce",
        ...     "stacks": [
        ...         {"stack_name": "frontend", "regions": ["us-east-1"], "stack_file": "web.yaml"}
        ...     ]
        ... }
        >>> deployments = generate_deployment_details_from_stack(**config)
        >>> len(deployments)
        1
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
    """Create a DeploymentDetails object from command line arguments.

    This function serves as a factory method to create DeploymentDetails instances
    from keyword arguments typically derived from command line input.

    Args:
        **kwargs: Keyword arguments containing deployment details parameters including:
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

    Returns:
        DeploymentDetails: A DeploymentDetails object initialized with the provided arguments.

    Note:
        If a PRN is provided, it overrides all other deployment hierarchy parameters.
        Missing parameters are populated with defaults from the utility functions.

    Example:
        >>> dd = generate_deployment_details(
        ...     client="web-team",
        ...     portfolio="ecommerce",
        ...     app="frontend",
        ...     branch="main",
        ...     build="v1.2.0"
        ... )
        >>> dd.portfolio
        'ecommerce'
    """
    return DeploymentDetails.from_arguments(**kwargs)


def generate_action_details(deployment_details: DeploymentDetails, **kwargs) -> ActionDetails:
    """Create an ActionDetails object from deployment details and additional arguments.

    This function generates ActionDetails objects that describe action file locations
    and metadata based on the deployment context.

    Args:
        deployment_details: The deployment details object that provides the deployment context.
        **kwargs: Additional keyword arguments for action details. These can include:
                 - **File Specification**:
                     - task (str): Task name to generate action file from
                     - action_file (str): Specific action file name
                     - key (str): Direct S3 key specification
                 - **Storage Parameters**:
                     - bucket_name (str): S3 bucket name override
                     - bucket_region (str): S3 bucket region override
                     - version_id (str): S3 object version ID
                     - content_type (str): MIME type of the action file
                     - mode (str): Storage mode ('local' or 'service')
                 - **Additional Parameters**: Any other parameters supported by ActionDetails.from_arguments()

    Returns:
        An ActionDetails object initialized with the deployment context and additional parameters.

    Examples::

        dd = DeploymentDetails(portfolio="ecom", app="web", build="1.0")
        # Create action details from task name
        action = generate_action_details(dd, task="deploy")
        print("deploy.actions" in action.key)
         True

        # Create with explicit action file
        action = generate_action_details(dd, action_file="custom.actions")
        print("custom.actions" in action.key)
         True

        # Create with direct key specification
        action = generate_action_details(dd, key="custom/path/actions.yaml")
        print(action.key)
         'custom/path/actions.yaml'

        # Create with storage mode override
        action = generate_action_details(
        dd,
        task="deploy",
        mode="local",
        bucket_name="/var/automation"
        )
        print(action.mode)
         'local'

    Notes:
        The deployment_details parameter is automatically added to the kwargs
        before calling ActionDetails.from_arguments().
    """
    kwargs["deployment_details"] = deployment_details
    return ActionDetails.from_arguments(**kwargs)


def generate_state_details(deployment_details: DeploymentDetails, **kwargs) -> StateDetails:
    """Create a StateDetails object from deployment details and additional arguments.

    This function generates StateDetails objects that describe state file locations
    and metadata based on the deployment context.

    Args:
        deployment_details: The deployment details object that provides the deployment context.
        **kwargs: Additional keyword arguments for state details. These can include:
                 - **File Specification**:
                     - task (str): Task name to generate state file from
                     - state_file (str): Specific state file name
                     - key (str): Direct S3 key specification
                 - **Storage Parameters**:
                     - bucket_name (str): S3 bucket name override
                     - bucket_region (str): S3 bucket region override
                     - version_id (str): S3 object version ID
                     - content_type (str): MIME type of the state file
                     - mode (str): Storage mode ('local' or 'service')
                 - **Additional Parameters**: Any other parameters supported by StateDetails.from_arguments()

    Returns:
        A StateDetails object initialized with the deployment context and additional parameters.

    Examples::

        dd = DeploymentDetails(portfolio="ecom", app="web", build="1.0")
        # Create state details with default settings
        state = generate_state_details(dd)
        print("artefacts" in state.key)
         True

        # Create with task name for state file
        state = generate_state_details(dd, task="deploy")
        print("deploy.state" in state.key)
         True

        # Create with custom state file
        state = generate_state_details(dd, state_file="custom-state.json")
        print("custom-state.json" in state.key)
         True

        # Create with direct key specification
        state = generate_state_details(dd, key="custom/path/state.json")
        print(state.key)
         'custom/path/state.json'

        # Create with storage parameters
        state = generate_state_details(
        dd,
        task="deploy",
        mode="service",
        bucket_name="deployment-bucket"
        )
        print(state.mode)
         'service'

    Notes:
        The deployment_details parameter is automatically added to the kwargs
        before calling StateDetails.from_arguments().
    """
    kwargs["deployment_details"] = deployment_details
    return StateDetails.from_arguments(**kwargs)
