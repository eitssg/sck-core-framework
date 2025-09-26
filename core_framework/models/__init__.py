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

    1. **Planning Phase**: DeploySpec and ActionResource define what to deploy
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
    - ActionResource: Individual action definition with dependencies and parameters
    - ActionSpec: Base parameter model for action configuration

**Utility Functions:**
    - Path resolution for artifacts, packages, and files
    - Artifact key generation for unique identification
    - Model factory functions for consistent object creation

Examples::::


    # Returns: Basic model usage:

    # Returns: from core_framework.models import ActionResource, DeploySpec
    # Returns: >>>
    # Create an action specification
    # Returns: action = ActionResource(
    # Returns: name="deploy-app",
    # Returns: kind="AWS::CreateStack",
    # Returns: params={
    # Returns: "stack_name": "my-application",
    # Returns: "template": "templates/app.yaml"
    # Returns: }
    # Returns: )

    # Create deployment specification
    # Returns: deploy_spec = DeploySpec(actions=[action])
    # Returns: print(len(deploy_spec))
    # Returns: 1

    # Returns: Using generator functions:

    # Returns: from core_framework.models import generate_task_payload
    # Returns: >>>
    # Generate complete task payload
    # Returns: payload = generate_task_payload(
    # Returns: action_resource=action,
    # Returns: deployment_id="deploy-123",
    # Returns: account="123456789012",
    # Returns: region="us-east-1"
    # Returns: )

    # Returns: Path and artifact utilities:

    # Returns: from core_framework.models import get_artefacts_path, get_artefact_key
    # Returns: >>>
    # Resolve artifact paths
    # Returns: artifacts_path = get_artefacts_path("my-portfolio", "my-app")
    # Returns: >>>
    # Generate unique artifact keys
    # Returns: key = get_artefact_key("deploy-123", "stack-outputs.json")

Integration Points:
    These models integrate with all Core Automation components:

    - **core-execute**: Uses TaskPayload and ActionResource for execution
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
    ...     DeploySpec, ActionResource, ActionSpec,
    ...
    ...     # Utility Functions
    ...     get_artefacts_path, generate_task_payload
    ... )
"""

from .task_payload import TaskPayload
from .file_details import FileDetails
from .deployment_details import DeploymentDetails
from .package_details import PackageDetails
from .action_details import ActionDetails
from .state_details import StateDetails
from .deploy_spec import DeploySpec
from .action_resource import ActionResource, ActionMetadata, ActionSpec
from .action_hook import HookResourceParameters, HookResource

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
    "FileDetails",
    "ActionMetadata",
    "PackageDetails",
    "ActionDetails",
    "StateDetails",
    # Specification Models
    "DeploySpec",
    "ActionResource",
    "ActionSpec",
    "HookResourceParameters",
    "HookResource",
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
    "ActionResource",
    "ActionSpec",
    "ActionMetadata",
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

    Examples::

        categories = get_model_categories()
        print(categories["core_models"])
        # Returns: ['TaskPayload', 'DeploymentDetails', 'PackageDetails', ...]

        # Check what specification models are available
        spec_models = categories["specification_models"]
        print("DeploySpec" in spec_models)
        # Returns: True
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

    Examples::

        models = get_all_models()
        print(len(models))
        # Returns: 8
        print("ActionResource" in models)
        # Returns: True
    """
    return CORE_MODELS + SPECIFICATION_MODELS


def get_all_functions() -> list[str]:
    """Get a list of all available utility and generator functions.

    Returns:
        List of all function names available in this module.

    Examples::

        functions = get_all_functions()
        print("generate_task_payload" in functions)
        # Returns: True
        print("get_artefacts_path" in functions)
        # Returns: True
    """
    return UTILITY_FUNCTIONS + GENERATOR_FUNCTIONS
