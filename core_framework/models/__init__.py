"""Core Automation Framework Data Models Module.

This module provides all data models, utilities, and generators used throughout the
Core Automation framework for infrastructure deployment, task orchestration, and
state management. It serves as the central hub for all model-related functionality.

Key Components:
    - **Core Models**: Primary data structures for deployment orchestration
    - **Specification Models**: Action and deployment specification definitions
    - **Utility Functions**: Path resolution and artifact management
    - **Generator Functions**: Factory methods for creating model instances

Architecture Overview:
    The models are designed to support the complete Core Automation workflow:

    1. **Planning Phase**: DeploySpec and ActionSpec define what to deploy
    2. **Execution Phase**: TaskPayload carries execution context
    3. **Tracking Phase**: DeploymentDetails and ActionDetails track progress
    4. **State Phase**: StateDetails manages persistent state
    5. **Packaging Phase**: PackageDetails handles artifact management

Model Categories:

**Core Data Models:**
    - TaskPayload: Complete execution context for automation tasks
    - DeploymentDetails: Deployment metadata and tracking information
    - PackageDetails: Artifact and package management information
    - ActionDetails: Individual action execution tracking and results
    - StateDetails: Persistent state management and variable storage

**Specification Models:**
    - DeploySpec: Collection of actions defining a complete deployment
    - ActionSpec: Individual action definition with dependencies and parameters
    - ActionParams: Base parameter model for action configuration

**Utility Functions:**
    - Path resolution for artifacts, packages, and files
    - Artifact key generation for unique identification
    - Model factory functions for consistent object creation

Examples:
    Basic model usage:

    >>> from core_framework.models import ActionSpec, DeploySpec
    >>>
    >>> # Create an action specification
    >>> action = ActionSpec(
    ...     name="deploy-app",
    ...     kind="AWS::CreateStack",
    ...     params={
    ...         "stack_name": "my-application",
    ...         "template": "templates/app.yaml"
    ...     }
    ... )

    >>> # Create deployment specification
    >>> deploy_spec = DeploySpec(actions=[action])
    >>> print(len(deploy_spec))
    1

    Using generator functions:

    >>> from core_framework.models import generate_task_payload
    >>>
    >>> # Generate complete task payload
    >>> payload = generate_task_payload(
    ...     action_spec=action,
    ...     deployment_id="deploy-123",
    ...     account="123456789012",
    ...     region="us-east-1"
    ... )

    Path and artifact utilities:

    >>> from core_framework.models import get_artefacts_path, get_artefact_key
    >>>
    >>> # Resolve artifact paths
    >>> artifacts_path = get_artefacts_path("my-portfolio", "my-app")
    >>>
    >>> # Generate unique artifact keys
    >>> key = get_artefact_key("deploy-123", "stack-outputs.json")

Integration Points:
    These models integrate with all Core Automation components:

    - **core-execute**: Uses TaskPayload and ActionSpec for execution
    - **core-runner**: Processes DeploySpec and tracks deployment progress
    - **core-api**: Serializes/deserializes all models for API operations
    - **core-db**: Persists DeploymentDetails, ActionDetails, and StateDetails
    - **core-cli**: Uses models for command-line interaction and validation

Design Principles:
    - **Pydantic-based**: All models use Pydantic for validation and serialization
    - **Type Safety**: Full type hints and validation for IDE support
    - **Serialization**: JSON/YAML serialization with alias support
    - **Backward Compatibility**: Deprecated field handling with warnings
    - **Extensibility**: Base classes and composition for custom extensions

Imports:
    All models and utilities are available through this module:

    >>> from core_framework.models import (
    ...     # Core Models
    ...     TaskPayload, DeploymentDetails, PackageDetails,
    ...     ActionDetails, StateDetails,
    ...
    ...     # Specification Models
    ...     DeploySpec, ActionSpec, ActionParams,
    ...
    ...     # Utility Functions
    ...     get_artefacts_path, generate_task_payload
    ... )
"""

from .task_payload import TaskPayload
from .deployment_details import DeploymentDetails
from .package_details import PackageDetails
from .action_details import ActionDetails
from .state_details import StateDetails
from .deploy_spec import DeploySpec
from .action_spec import ActionSpec, ActionParams

from .models import (
    get_artefacts_path,
    get_packages_path,
    get_files_path,
    get_artefact_key,
    generate_package_details,
    generate_task_payload,
    generate_deployment_details_from_stack,
    generate_deployment_details,
    generate_action_details,
)

__all__ = [
    # Core Data Models
    "TaskPayload",
    "DeploymentDetails",
    "PackageDetails",
    "ActionDetails",
    "StateDetails",
    # Specification Models
    "DeploySpec",
    "ActionSpec",
    "ActionParams",
    # Path Utilities
    "get_artefacts_path",
    "get_packages_path",
    "get_files_path",
    "get_artefact_key",
    # Model Generators
    "generate_package_details",
    "generate_task_payload",
    "generate_deployment_details_from_stack",
    "generate_deployment_details",
    "generate_action_details",
]

# Model Categories for Documentation and IDE Assistance

#: Core data models for deployment execution and tracking
CORE_MODELS = [
    "TaskPayload",
    "DeploymentDetails",
    "PackageDetails",
    "ActionDetails",
    "StateDetails",
]

#: Specification models for defining deployments and actions
SPECIFICATION_MODELS = [
    "DeploySpec",
    "ActionSpec",
    "ActionParams",
]

#: Utility functions for path resolution and artifact management
UTILITY_FUNCTIONS = [
    "get_artefacts_path",
    "get_packages_path",
    "get_files_path",
    "get_artefact_key",
]

#: Factory functions for generating model instances
GENERATOR_FUNCTIONS = [
    "generate_package_details",
    "generate_task_payload",
    "generate_deployment_details_from_stack",
    "generate_deployment_details",
    "generate_action_details",
]


def get_model_categories() -> dict[str, list[str]]:
    """Get categorized lists of available models and functions.

    Returns:
        Dictionary mapping category names to lists of available items.

    Examples:
        >>> categories = get_model_categories()
        >>> print(categories["core_models"])
        ['TaskPayload', 'DeploymentDetails', 'PackageDetails', ...]

        >>> # Check what specification models are available
        >>> spec_models = categories["specification_models"]
        >>> print("DeploySpec" in spec_models)
        True
    """
    return {
        "core_models": CORE_MODELS,
        "specification_models": SPECIFICATION_MODELS,
        "utility_functions": UTILITY_FUNCTIONS,
        "generator_functions": GENERATOR_FUNCTIONS,
    }


def get_all_models() -> list[str]:
    """Get a list of all available model classes.

    Returns:
        List of all model class names available in this module.

    Examples:
        >>> models = get_all_models()
        >>> print(len(models))
        8
        >>> print("ActionSpec" in models)
        True
    """
    return CORE_MODELS + SPECIFICATION_MODELS


def get_all_functions() -> list[str]:
    """Get a list of all available utility and generator functions.

    Returns:
        List of all function names available in this module.

    Examples:
        >>> functions = get_all_functions()
        >>> print("generate_task_payload" in functions)
        True
        >>> print("get_artefacts_path" in functions)
        True
    """
    return UTILITY_FUNCTIONS + GENERATOR_FUNCTIONS
