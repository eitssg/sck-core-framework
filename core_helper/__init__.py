"""Core Helper Modules for AWS Operations and Development Utilities.

This package provides essential helper modules that simplify common tasks in the
Core Automation framework, particularly focusing on AWS service interactions,
caching mechanisms, and development utilities. The helpers are designed to work
seamlessly with the core framework while providing standalone functionality.

Key Modules:
    - **aws**: AWS session management, authentication, and service client creation
    - **cache**: Thread-safe in-memory caching with sliding TTL for performance optimization
    - **magic**: S3 emulation for local development and testing without AWS infrastructure

Architecture:
    The helper modules follow a layered approach where higher-level operations
    build upon lower-level utilities:

    **AWS Operations:**
    - Session and credential management with automatic caching
    - Multi-factor authentication support for Cognito and IAM users
    - Role assumption with credential chaining and automatic refresh
    - Service client factory with proxy and retry configuration

    **Caching System:**
    - Thread-safe operations for multi-threaded and Lambda environments
    - Sliding TTL that extends expiration on access to keep active items fresh
    - Background cleanup to prevent memory leaks in long-running processes
    - Specialized methods for AWS sessions and credential storage

    **Development Tools:**
    - Drop-in S3 replacement for local development and testing
    - Transparent switching between real AWS and local filesystem storage
    - API-compatible emulation maintaining boto3 interface patterns
    - Streaming support with proper resource management

Integration with Core Framework:
    All helper modules integrate deeply with the core_framework configuration
    system, automatically adapting behavior based on environment settings:

    - **Environment Detection**: Automatic switching between development and production modes
    - **Configuration Driven**: Behavior controlled via environment variables and settings
    - **Lambda Optimized**: Default timeouts and caching aligned with AWS Lambda limits
    - **Multi-Environment**: Support for local, staging, and production deployments

Common Usage Patterns:

**AWS Service Access:**
    The aws module provides centralized service client creation with automatic
    credential management and role assumption capabilities.

**Performance Optimization:**
    The cache module enables efficient reuse of expensive operations like
    session creation and credential retrieval across multiple function calls.

**Local Development:**
    The magic module allows complete local development without requiring AWS
    infrastructure, automatically switching based on configuration.

Thread Safety:
    All helper modules are designed for safe concurrent access in multi-threaded
    environments and AWS Lambda execution contexts. Proper locking mechanisms
    ensure data integrity during parallel operations.

Error Handling:
    Comprehensive error handling with graceful degradation:
    - AWS credential failures fall back to base session credentials
    - Cache operations handle expiration and cleanup automatically
    - S3 emulation provides consistent error responses matching AWS behavior

Performance Considerations:
    - Session and credential caching minimizes AWS API calls
    - Background cleanup prevents memory leaks in long-running processes
    - Lazy loading and streaming reduce memory usage for large operations
    - Configurable timeouts and retry logic for robust AWS interactions

Development vs Production:
    The helpers automatically adapt to different environments:
    - **Development**: Uses local filesystem, mock services, and debug logging
    - **Production**: Uses real AWS services with optimized caching and error handling
    - **Testing**: Provides consistent interfaces for both local and cloud testing

Extension Points:
    The helper modules can be extended for custom use cases:
    - Custom authentication providers for aws module
    - Additional cache storage backends for cache module
    - Custom storage providers for magic module emulation

Dependencies:
    - **boto3**: AWS SDK for Python (for real AWS operations)
    - **botocore**: Low-level AWS service access (configuration and errors)
    - **pydantic**: Data validation and settings management
    - **threading**: Thread safety and background operations
    - **core_framework**: Configuration and utility functions

Version Compatibility:
    The helper modules are designed to work with:
    - Python 3.8+ (f-strings, type hints, dataclasses)
    - boto3 1.20+ (modern session and client interfaces)
    - AWS Lambda runtime environments
    - Multi-threaded applications and frameworks

Security Considerations:
    - Credentials are handled securely with automatic cleanup
    - Session tokens have appropriate TTL and expiration handling
    - Role assumption follows AWS security best practices
    - Local storage uses appropriate file permissions and cleanup
"""

# Import all public interfaces from helper modules
from .aws import (
    # Session and credential management
    get_session,
    get_session_credentials,
    get_session_token,
    assume_role,
    get_identity,
    get_role_credentials,
    clear_role_credentials,
    # Authentication functions
    login_to_aws,
    # Data transformation utilities
    transform_stack_parameter_dict,
    transform_stack_parameter_hash,
    transform_tag_hash,
    # Client factory functions
    get_client,
    get_resource,
    # Service-specific clients
    sts_client,
    s3_client,
    cfn_client,
    cloudwatch_client,
    cloudfront_client,
    ec2_client,
    ecr_client,
    elb_client,
    elbv2_client,
    iam_client,
    kms_client,
    lambda_client,
    rds_client,
    org_client,
    step_functions_client,
    r53_client,
    cognito_client,
    # Service-specific resources
    s3_resource,
    dynamodb_resource,
    # Lambda and service invocation
    invoke_lambda,
    # IAM permission management
    grant_assume_role_permission,
    revoke_assume_role_permission,
    # Context and utility functions
    generate_context,
)

from .cache import (
    # Cache class and constants
    InMemoryCache,
    DEFAULT_TTL,
)

from .magic import (
    # S3 emulation classes
    FileStreamingBody,
    MagicObject,
    MagicBucket,
    MagicS3Client,
    SeekableStreamWrapper,
)

__all__ = [
    # AWS Session and Credential Management
    "get_session",
    "get_session_credentials",
    "get_session_token",
    "assume_role",
    "get_identity",
    "get_role_credentials",
    "clear_role_credentials",
    # Authentication
    "login_to_aws",
    # Data Transformation
    "transform_stack_parameter_dict",
    "transform_stack_parameter_hash",
    "transform_tag_hash",
    # Client and Resource Factories
    "get_client",
    "get_resource",
    # AWS Service Clients
    "sts_client",
    "s3_client",
    "cfn_client",
    "cloudwatch_client",
    "cloudfront_client",
    "ec2_client",
    "ecr_client",
    "elb_client",
    "elbv2_client",
    "iam_client",
    "kms_client",
    "lambda_client",
    "rds_client",
    "org_client",
    "step_functions_client",
    "r53_client",
    "cognito_client",
    # AWS Service Resources
    "s3_resource",
    "dynamodb_resource",
    # Service Operations
    "invoke_lambda",
    # IAM Management
    "grant_assume_role_permission",
    "revoke_assume_role_permission",
    # Utilities
    "generate_context",
    # Caching
    "InMemoryCache",
    "DEFAULT_TTL",
    # S3 Emulation
    "FileStreamingBody",
    "MagicObject",
    "MagicBucket",
    "MagicS3Client",
    "SeekableStreamWrapper",
]

# Categorized function lists for documentation and IDE assistance

#: AWS session and credential management functions
AWS_SESSION_FUNCTIONS = [
    "get_session",
    "get_session_credentials",
    "get_session_token",
    "assume_role",
    "get_identity",
    "get_role_credentials",
    "clear_role_credentials",
]

#: Authentication and login functions
AUTHENTICATION_FUNCTIONS = [
    "login_to_aws",
]

#: Data transformation and formatting utilities
DATA_TRANSFORMATION_FUNCTIONS = [
    "transform_stack_parameter_dict",
    "transform_stack_parameter_hash",
    "transform_tag_hash",
]

#: AWS service client creation functions
CLIENT_FACTORY_FUNCTIONS = [
    "get_client",
    "get_resource",
    "sts_client",
    "s3_client",
    "cfn_client",
    "cloudwatch_client",
    "cloudfront_client",
    "ec2_client",
    "ecr_client",
    "elb_client",
    "elbv2_client",
    "iam_client",
    "kms_client",
    "lambda_client",
    "rds_client",
    "org_client",
    "step_functions_client",
    "r53_client",
    "cognito_client",
    "s3_resource",
    "dynamodb_resource",
]

#: Service operation and invocation functions
SERVICE_OPERATION_FUNCTIONS = [
    "invoke_lambda",
    "generate_context",
]

#: IAM permission and role management functions
IAM_MANAGEMENT_FUNCTIONS = [
    "grant_assume_role_permission",
    "revoke_assume_role_permission",
]

#: Caching system components
CACHING_COMPONENTS = [
    "InMemoryCache",
    "DEFAULT_TTL",
]

#: S3 emulation and magic storage components
STORAGE_EMULATION_COMPONENTS = [
    "FileStreamingBody",
    "MagicObject",
    "MagicBucket",
    "MagicS3Client",
    "SeekableStreamWrapper",
]


def get_helper_categories() -> dict[str, list[str]]:
    """Get categorized lists of available helper functions by purpose.

    Returns:
        Dictionary mapping category names to lists of function names.

    Use Cases:
        Discovering available functionality within different helper categories,
        building documentation, and understanding the scope of each helper module.
    """
    return {
        "aws_sessions": AWS_SESSION_FUNCTIONS,
        "authentication": AUTHENTICATION_FUNCTIONS,
        "data_transformation": DATA_TRANSFORMATION_FUNCTIONS,
        "client_factories": CLIENT_FACTORY_FUNCTIONS,
        "service_operations": SERVICE_OPERATION_FUNCTIONS,
        "iam_management": IAM_MANAGEMENT_FUNCTIONS,
        "caching": CACHING_COMPONENTS,
        "storage_emulation": STORAGE_EMULATION_COMPONENTS,
    }


def get_helper_info() -> dict[str, any]:
    """Get comprehensive information about the Core Helper modules.

    Returns:
        Dictionary containing helper metadata, capabilities, and module information.

    Information Included:
        - Module purposes and capabilities
        - Function counts and categorization
        - Integration points with core framework
        - Development vs production behavior differences
        - Performance and security considerations
    """
    categories = get_helper_categories()

    return {
        "name": "Core Helper Modules",
        "description": "Essential helper modules for AWS operations and development utilities",
        "modules": {
            "aws": {
                "purpose": "AWS service interaction and credential management",
                "capabilities": [
                    "Session and credential caching",
                    "Multi-factor authentication support",
                    "Role assumption and credential chaining",
                    "Service client factory with configuration",
                    "Lambda function invocation",
                    "IAM permission management",
                ],
                "function_count": len(
                    AWS_SESSION_FUNCTIONS
                    + AUTHENTICATION_FUNCTIONS
                    + DATA_TRANSFORMATION_FUNCTIONS
                    + CLIENT_FACTORY_FUNCTIONS
                    + SERVICE_OPERATION_FUNCTIONS
                    + IAM_MANAGEMENT_FUNCTIONS
                ),
            },
            "cache": {
                "purpose": "Thread-safe in-memory caching with sliding TTL",
                "capabilities": [
                    "Thread-safe operations for concurrent access",
                    "Sliding TTL that extends on access",
                    "Background cleanup for memory management",
                    "AWS session and credential specialized storage",
                    "Lambda execution environment optimization",
                ],
                "component_count": len(CACHING_COMPONENTS),
            },
            "magic": {
                "purpose": "S3 emulation for local development and testing",
                "capabilities": [
                    "Drop-in replacement for boto3 S3 operations",
                    "Transparent switching between S3 and filesystem",
                    "API-compatible emulation with proper error handling",
                    "Streaming support with resource management",
                    "Metadata generation for local files",
                ],
                "component_count": len(STORAGE_EMULATION_COMPONENTS),
            },
        },
        "integration": {
            "core_framework": "Deep integration with configuration and utilities",
            "environment_aware": "Automatic adaptation to development vs production",
            "lambda_optimized": "Default settings aligned with AWS Lambda limits",
            "thread_safe": "Safe for concurrent access in multi-threaded environments",
        },
        "categories": list(categories.keys()),
        "total_functions": sum(len(funcs) for funcs in categories.values()),
        "aws_services_supported": [
            "STS",
            "S3",
            "CloudFormation",
            "CloudWatch",
            "CloudFront",
            "EC2",
            "ECR",
            "ELB",
            "ELBv2",
            "IAM",
            "KMS",
            "Lambda",
            "RDS",
            "Organizations",
            "Step Functions",
            "Route53",
            "Cognito",
            "DynamoDB",
        ],
        "development_features": [
            "Local S3 emulation",
            "Credential caching for performance",
            "Automatic environment detection",
            "Graceful fallback mechanisms",
            "Comprehensive error handling",
        ],
    }


# Module metadata and discovery helpers
__helper_categories__ = get_helper_categories()
__helper_info__ = get_helper_info()

# Version and compatibility information
__version__ = "1.0.0"
__python_requires__ = ">=3.8"
__aws_sdk_requires__ = "boto3>=1.20.0"
