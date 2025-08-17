"""Core Automation Framework - Main Module.

This is the primary module for the Core Automation Framework, providing a unified interface
to all framework functionality including data models, utilities, configuration management,
and infrastructure automation tools. It serves as the single entry point for all Core
Automation operations.

Key Features:
    - **Unified API**: Single import point for all framework functionality
    - **Configuration Management**: Environment-aware configuration and settings
    - **Data Models**: Complete set of Pydantic models for automation workflows
    - **Utility Functions**: Path resolution, artifact management, and data processing
    - **PRN System**: Portfolio Resource Name generation and validation
    - **YAML/JSON Support**: Intelligent parsing and serialization with CloudFormation support
    - **AWS Integration**: Built-in AWS service configuration and resource management

Architecture Overview:
    The framework is organized into several key subsystems:

    **Data Models & Serialization:**
    - Pydantic models for type-safe data handling
    - JSON/YAML serialization with CloudFormation support
    - Model generators for consistent object creation

    **Configuration System:**
    - Environment variable-based configuration
    - AWS account and region management
    - Multi-environment deployment support

    **Portfolio Resource Names (PRN):**
    - Hierarchical naming convention for resources
    - Validation and generation functions
    - Component identification and extraction

    **Utility Functions:**
    - Path resolution for artifacts and packages
    - Data merging and manipulation
    - AWS client configuration and management

Common Usage Patterns:

**Basic Configuration:**

    >>> import core_framework as cf
    >>>
    >>> # Get current environment configuration
    >>> env = cf.get_environment()
    >>> region = cf.get_region()
    >>> account = cf.get_automation_account()

**Data Model Usage:**

    >>> # Generate deployment artifacts
    >>> task_payload = cf.generate_task_payload(
    ...     action_spec=action,
    ...     deployment_id="deploy-123"
    ... )
    >>>
    >>> # Work with paths and artifacts
    >>> artifacts_path = cf.get_artefacts_path("portfolio", "app")
    >>> artifact_key = cf.get_artefact_key("deploy-123", "outputs.json")

**PRN Operations:**

    >>> # Generate Portfolio Resource Names
    >>> portfolio_prn = cf.generate_portfolio_prn("my-portfolio")
    >>> app_prn = cf.generate_app_prn("my-portfolio", "my-app")
    >>>
    >>> # Validate and extract PRN components
    >>> is_valid = cf.validate_app_prn(app_prn)
    >>> portfolio = cf.extract_portfolio(app_prn)

**YAML/JSON Processing:**

    >>> # CloudFormation template processing
    >>> template = cf.load_yaml_file("template.yaml")
    >>> clean_yaml = cf.to_yaml(template)
    >>>
    >>> # Configuration file handling
    >>> config = cf.from_json(json_string)
    >>> cf.write_yaml(config, output_stream)

Module Categories:

**Configuration Functions:**
    Environment, AWS account, region, and service configuration management.

**Data Models:**
    Type-safe Pydantic models for deployment workflows and state management.

**Utility Functions:**
    Path resolution, data processing, and infrastructure helper functions.

**PRN System:**
    Portfolio Resource Name generation, validation, and component extraction.

**Serialization:**
    JSON and YAML processing with CloudFormation and custom tag support.

Integration with Core Automation:
    This module integrates with all Core Automation components:

    - **core-execute**: Action execution with TaskPayload and ActionSpec
    - **core-runner**: Deployment orchestration with DeploySpec processing
    - **core-api**: REST API operations with model serialization
    - **core-db**: Database operations with model persistence
    - **core-cli**: Command-line interface with configuration functions

Examples:
    Complete workflow example:

    >>> import core_framework as cf
    >>>
    >>> # 1. Get environment configuration
    >>> env = cf.get_environment()
    >>> account = cf.get_automation_account()
    >>> region = cf.get_region()
    >>>
    >>> # 2. Generate PRNs for resources
    >>> portfolio = "my-portfolio"
    >>> app = "web-app"
    >>> branch = "feature-auth"
    >>>
    >>> portfolio_prn = cf.generate_portfolio_prn(portfolio)
    >>> app_prn = cf.generate_app_prn(portfolio, app)
    >>> branch_prn = cf.generate_branch_prn(portfolio, app, branch)
    >>>
    >>> # 3. Create deployment specification
    >>> action = ActionSpec(
    ...     name="deploy-infrastructure",
    ...     kind="AWS::CreateStack",
    ...     params={
    ...         "account": account,
    ...         "region": region,
    ...         "stack_name": f"{cf.branch_short_name(branch)}-infrastructure"
    ...     }
    ... )
    >>>
    >>> # 4. Generate task payload for execution
    >>> payload = cf.generate_task_payload(
    ...     action_spec=action,
    ...     deployment_id=f"deploy-{cf.get_current_timestamp_short()}"
    ... )
    >>>
    >>> # 5. Process and serialize
    >>> yaml_output = cf.to_yaml(payload.model_dump())

Error Handling:
    All functions include proper error handling and validation:

    - Configuration functions return None or defaults for missing values
    - Validation functions raise ValueError for invalid inputs
    - Serialization functions handle encoding and format errors gracefully
    - Path functions validate existence and permissions where applicable

Version: 0.0.11-pre.8+11ddda5
"""

from .merge import deep_copy, deep_merge_in_place, deep_merge, set_nested
from .models import (
    get_artefacts_path,
    get_files_path,
    get_packages_path,
    get_artefact_key,
    generate_task_payload,
    generate_package_details,
    generate_deployment_details_from_stack,
    generate_deployment_details,
)
from .common import (
    split_prn,
    split_branch,
    split_portfolio,
    get_automation_region,
    get_cdk_default_account,
    get_cdk_default_region,
    get_prn,
    get_prn_alt,
    get_region,
    get_client,
    get_client_name,
    get_client_region,
    get_storage_volume,
    get_log_dir,
    get_log_level,
    get_temp_dir,
    get_delivered_by,
    get_aws_profile,
    get_aws_region,
    get_automation_scope,
    get_automation_account,
    get_iam_account,
    get_audit_account,
    get_security_account,
    get_network_account,
    get_domain,
    get_organization_id,
    get_organization_name,
    get_organization_account,
    get_organization_email,
    get_api_lambda_name,
    get_api_lambda_arn,
    get_api_host_url,
    get_invoker_lambda_arn,
    get_invoker_lambda_name,
    get_invoker_lambda_region,
    get_execute_lambda_arn,
    get_start_runner_lambda_arn,
    get_deployspec_compiler_lambda_arn,
    get_component_compiler_lambda_arn,
    get_dynamodb_host,
    get_dynamodb_region,
    get_bucket_region,
    get_bucket_name,
    get_document_bucket_name,
    get_ui_bucket_name,
    get_step_function_arn,
    get_artefact_bucket_name,
    get_artefact_bucket_region,
    get_provisioning_role_arn,
    get_automation_api_role_arn,
    get_environment,
    get_correlation_id,
    get_mode,
    get_automation_type,
    get_portfolio,
    get_app,
    get_branch,
    get_build,
    get_project,
    get_bizapp,
    get_console_mode,
    get_master_region,
    get_current_timestamp,
    get_current_timestamp_short,
    get_cognito_endpoint,
    generate_branch_short_name,
    generate_bucket_name,
    get_valid_mimetypes,
    is_local_mode,
    is_use_s3,
    is_enforce_validation,
    is_json_log,
    is_console_log,
    is_json_mimetype,
    is_yaml_mimetype,
    is_zip_mimetype,
    to_json,
    from_json,
    read_json,
    write_json,
    pascal_case_to_snake_case,
    snake_case_to_pascal_case,
)
from .yaml.yaml_utils import (
    to_yaml,
    from_yaml,
    read_yaml,
    write_yaml,
    create_yaml_parser,
    load_yaml_file,
)

# retrieve the version of the package dynamically
__version__ = "0.0.11-pre.8+11ddda5"

# import everything from prn_utils
from .prn_utils import (
    get_prn_scope,
    validate_item_prn,
    validate_portfolio_prn,
    validate_app_prn,
    validate_branch_prn,
    validate_build_prn,
    validate_component_prn,
    generate_portfolio_prn,
    generate_app_prn,
    generate_branch_prn,
    generate_build_prn,
    generate_component_prn,
    branch_short_name,
    extract_app,
    extract_portfolio,
    extract_branch,
    extract_build,
    extract_component,
    extract_portfolio_prn,
    extract_app_prn,
    extract_branch_prn,
    extract_build_prn,
    extract_component_prn,
)

__all__ = [
    # Data Manipulation Utilities
    "deep_copy",
    "deep_merge_in_place",
    "deep_merge",
    "set_nested",
    # Path and Artifact Management
    "get_artefacts_path",
    "get_files_path",
    "get_packages_path",
    "get_artefact_key",
    # Model Generators
    "generate_task_payload",
    "generate_package_details",
    "generate_deployment_details_from_stack",
    "generate_deployment_details",
    # PRN Parsing and Manipulation
    "split_prn",
    "split_branch",
    "split_portfolio",
    # Configuration and Environment
    "get_prn",
    "get_prn_alt",
    "get_region",
    "get_master_region",
    "get_domain",
    "get_client",
    "get_client_name",
    "get_client_region",
    "get_storage_volume",
    "get_log_dir",
    "get_log_level",
    "get_temp_dir",
    "get_delivered_by",
    "get_aws_profile",
    "get_aws_region",
    "get_iam_account",
    "get_automation_scope",
    "get_automation_account",
    "get_automation_region",
    "get_audit_account",
    "get_security_account",
    "get_network_account",
    "get_organization_id",
    "get_organization_name",
    "get_organization_account",
    "get_organization_email",
    # Name and Resource Generation
    "generate_branch_short_name",
    "generate_bucket_name",
    "get_cognito_endpoint",
    # AWS Lambda Functions
    "get_api_lambda_name",
    "get_api_lambda_arn",
    "get_api_host_url",
    "get_invoker_lambda_arn",
    "get_invoker_lambda_name",
    "get_invoker_lambda_region",
    "get_execute_lambda_arn",
    "get_start_runner_lambda_arn",
    "get_deployspec_compiler_lambda_arn",
    "get_component_compiler_lambda_arn",
    "get_automation_api_role_arn",
    # AWS Storage and Infrastructure
    "get_dynamodb_host",
    "get_dynamodb_region",
    "get_bucket_region",
    "get_bucket_name",
    "get_document_bucket_name",
    "get_ui_bucket_name",
    "get_step_function_arn",
    "get_artefact_bucket_name",
    "get_artefact_bucket_region",
    "get_provisioning_role_arn",
    # Deployment Context
    "get_environment",
    "get_correlation_id",
    "get_mode",
    "get_automation_type",
    "get_portfolio",
    "get_app",
    "get_branch",
    "get_build",
    "get_project",
    "get_bizapp",
    "get_console_mode",
    "get_current_timestamp",
    # Validation and Type Checking
    "get_valid_mimetypes",
    "is_local_mode",
    "is_use_s3",
    "is_enforce_validation",
    "is_json_log",
    "is_console_log",
    "is_json_mimetype",
    "is_yaml_mimetype",
    "is_zip_mimetype",
    # JSON Serialization
    "to_json",
    "from_json",
    "read_json",
    "write_json",
    # YAML Serialization
    "to_yaml",
    "from_yaml",
    "read_yaml",
    "write_yaml",
    "create_yaml_parser",
    "load_yaml_file",
    # PRN System - Validation
    "get_prn_scope",
    "validate_item_prn",
    "validate_portfolio_prn",
    "validate_app_prn",
    "validate_branch_prn",
    "validate_build_prn",
    "validate_component_prn",
    # PRN System - Generation
    "generate_portfolio_prn",
    "generate_app_prn",
    "generate_branch_prn",
    "generate_build_prn",
    "generate_component_prn",
    # PRN System - Extraction and Parsing
    "branch_short_name",
    "extract_app",
    "extract_portfolio",
    "extract_branch",
    "extract_build",
    "extract_component",
    "extract_portfolio_prn",
    "extract_app_prn",
    "extract_branch_prn",
    "extract_build_prn",
    "extract_component_prn",
    "pascal_case_to_snake_case",
    "snake_case_to_pascal_case",
]


# Categorized function lists for documentation and IDE assistance

#: Data manipulation and merging utilities
DATA_UTILITIES = [
    "deep_copy",
    "deep_merge_in_place",
    "deep_merge",
    "set_nested",
]

#: Path resolution and artifact management functions
PATH_UTILITIES = [
    "get_artefacts_path",
    "get_files_path",
    "get_packages_path",
    "get_artefact_key",
]

#: Model factory and generation functions
MODEL_GENERATORS = [
    "generate_task_payload",
    "generate_package_details",
    "generate_deployment_details_from_stack",
    "generate_deployment_details",
    "pascal_case_to_snake_case",
    "snake_case_to_pascal_case",
]

#: Environment and configuration retrieval functions
CONFIGURATION_FUNCTIONS = [
    "get_environment",
    "get_region",
    "get_automation_account",
    "get_aws_profile",
    "get_domain",
    "get_organization_id",
    "get_correlation_id",
    "get_mode",
]

#: AWS service and resource configuration functions
AWS_RESOURCE_FUNCTIONS = [
    "get_api_lambda_arn",
    "get_invoker_lambda_arn",
    "get_execute_lambda_arn",
    "get_dynamodb_host",
    "get_bucket_name",
    "get_step_function_arn",
    "get_provisioning_role_arn",
]

#: Portfolio Resource Name (PRN) system functions
PRN_FUNCTIONS = [
    "generate_portfolio_prn",
    "generate_app_prn",
    "generate_branch_prn",
    "validate_portfolio_prn",
    "validate_app_prn",
    "extract_portfolio",
    "extract_app",
    "extract_branch",
]

#: Data serialization and format handling functions
SERIALIZATION_FUNCTIONS = [
    "to_json",
    "from_json",
    "to_yaml",
    "from_yaml",
    "read_yaml",
    "write_yaml",
    "load_yaml_file",
]

#: Validation and type checking utilities
VALIDATION_FUNCTIONS = [
    "is_local_mode",
    "is_use_s3",
    "is_json_mimetype",
    "is_yaml_mimetype",
    "validate_item_prn",
    "validate_portfolio_prn",
]


def get_function_categories() -> dict[str, list[str]]:
    """Get categorized lists of available functions by purpose.

    Returns:
        Dictionary mapping category names to lists of function names.

    Examples:
        >>> categories = get_function_categories()
        >>> print(categories["configuration"])
        ['get_environment', 'get_region', 'get_automation_account', ...]

        >>> # Check what PRN functions are available
        >>> prn_functions = categories["prn_system"]
        >>> print("generate_app_prn" in prn_functions)
        True

        >>> # Explore AWS resource functions
        >>> aws_funcs = categories["aws_resources"]
        >>> print(len(aws_funcs))
        8
    """
    return {
        "data_utilities": DATA_UTILITIES,
        "path_utilities": PATH_UTILITIES,
        "model_generators": MODEL_GENERATORS,
        "configuration": CONFIGURATION_FUNCTIONS,
        "aws_resources": AWS_RESOURCE_FUNCTIONS,
        "prn_system": PRN_FUNCTIONS,
        "serialization": SERIALIZATION_FUNCTIONS,
        "validation": VALIDATION_FUNCTIONS,
    }


def get_version_info() -> dict[str, str]:
    """Get detailed version information for the framework.

    Returns:
        Dictionary containing version details and metadata.

    Examples:
        >>> version_info = get_version_info()
        >>> print(version_info["version"])
        '0.0.11-pre.8+11ddda5'
        >>> print(version_info["is_prerelease"])
        True
    """
    import re

    version = __version__

    # Parse version components
    version_match = re.match(r"(\d+)\.(\d+)\.(\d+)(-.*)?(\+.*)?", version)

    if version_match:
        major, minor, patch, prerelease, build = version_match.groups()
        return {
            "version": version,
            "major": major,
            "minor": minor,
            "patch": patch,
            "prerelease": prerelease.lstrip("-") if prerelease else None,
            "build": build.lstrip("+") if build else None,
            "is_prerelease": bool(prerelease),
            "is_development": bool(build),
        }
    else:
        return {
            "version": version,
            "major": None,
            "minor": None,
            "patch": None,
            "prerelease": None,
            "build": None,
            "is_prerelease": False,
            "is_development": False,
        }


def get_framework_info() -> dict[str, any]:
    """Get comprehensive information about the Core Automation Framework.

    Returns:
        Dictionary containing framework metadata, capabilities, and configuration.

    Examples:
        >>> info = get_framework_info()
        >>> print(info["name"])
        'Core Automation Framework'
        >>> print(len(info["capabilities"]))
        8
        >>> print(info["function_count"])
        85
    """
    categories = get_function_categories()
    version_info = get_version_info()

    return {
        "name": "Core Automation Framework",
        "version": version_info,
        "description": "Infrastructure automation and deployment orchestration framework",
        "capabilities": [
            "CloudFormation template processing",
            "Multi-environment deployment management",
            "Portfolio Resource Name (PRN) system",
            "AWS service integration",
            "Data model validation and serialization",
            "Configuration management",
            "Artifact and package management",
            "YAML/JSON processing with custom tags",
        ],
        "function_categories": list(categories.keys()),
        "function_count": sum(len(funcs) for funcs in categories.values()),
        "module_count": 6,  # merge, models, common, yaml, prn_utils, __init__
        "supported_formats": ["JSON", "YAML", "CloudFormation"],
        "aws_integration": True,
        "pydantic_models": True,
    }


# Version information and metadata
__version_info__ = get_version_info()
__framework_info__ = get_framework_info()
