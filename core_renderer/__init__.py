"""Core Renderer Package for Template Processing and Infrastructure as Code Generation.

This package provides a comprehensive Jinja2-based template rendering system specifically
designed for the Core Automation framework. It enables powerful template processing
capabilities for AWS CloudFormation, Terraform, configuration files, and other
infrastructure as code resources.

Key Features:
    - **Multi-Source Templates**: Support for file system and dictionary-based template loading
    - **AWS Integration**: Custom Jinja2 filters for AWS resource naming, tagging, and ARNs
    - **Context-Aware Rendering**: Automatic integration with Core Automation deployment context
    - **Infrastructure as Code**: Optimized for CloudFormation and Terraform template generation
    - **Cross-Platform Support**: Consistent behavior across Windows and Unix file systems
    - **Batch Processing**: Efficient rendering of entire template directories

Architecture:
    The core renderer is built around the Jinja2Renderer class which provides multiple
    rendering modes and integrates seamlessly with Core Automation's deployment pipeline.
    Custom filters extend Jinja2's capabilities with AWS-specific functionality and
    deployment context awareness.

Components:
    **Jinja2Renderer**: Main rendering engine with support for:
    - String template rendering for dynamic content generation
    - Object rendering for complex data structure templating
    - File rendering from file system or dictionary sources
    - Batch file rendering for entire template directories
    - JSON rendering with template variable resolution

    **Custom Filters**: Extensive collection of AWS and deployment-specific filters:
    - aws_tags: Generate AWS tag lists from deployment context
    - docker_image: Construct ECR image names with registry URIs
    - ip_rules: Create security group rules from specifications
    - split_cidr: Split CIDR blocks for VPC subnet planning
    - And many more for comprehensive infrastructure templating

Use Cases:
    **CloudFormation Templates:**
    Generate AWS CloudFormation templates with dynamic resource names, tags,
    and configurations based on deployment context.

    **Terraform Configurations:**
    Create Terraform configuration files with consistent naming and tagging
    across multiple environments and deployment stages.

    **Configuration Management:**
    Render application configuration files, scripts, and deployment artifacts
    with environment-specific values and settings.

    **Multi-Environment Deployments:**
    Support for portfolio, application, branch, and build-scoped resources
    with automatic context-aware naming and tagging.

Integration:
    The renderer integrates with Core Automation's deployment pipeline to provide:
    - Automatic deployment context injection (portfolio, app, branch, build)
    - Consistent resource naming across AWS services
    - Environment-specific configuration management
    - Security rule generation and network planning
    - Cross-stack reference management

Template Sources:
    **File System Templates:**
    Load templates from directory structures for organized project layouts
    with hierarchical template organization and inheritance.

    **Dictionary Templates:**
    Use embedded or dynamically generated templates for scenarios requiring
    runtime template composition or distributed template storage.

Performance:
    The rendering system is optimized for:
    - Large template directories with efficient batch processing
    - Complex nested data structures with recursive rendering
    - Memory-efficient processing of template hierarchies
    - Minimal overhead for simple string template operations

Error Handling:
    Comprehensive error handling with:
    - Strict undefined variable checking for reliable template validation
    - Clear error messages for template debugging and development
    - Graceful handling of missing templates and invalid configurations
    - Support for development and production error reporting modes

Thread Safety:
    The renderer is designed for safe concurrent use in multi-threaded
    environments including serverless functions and container deployments.
"""

from .renderer import Jinja2Renderer

__all__ = ["Jinja2Renderer"]

# Package metadata for documentation and introspection
__version__ = "1.0.0"
__package_name__ = "Core Renderer"
__description__ = "Jinja2 template rendering system for infrastructure as code"


def get_renderer_info() -> dict[str, any]:
    """Get comprehensive information about the Core Renderer package.

    Returns:
        Dictionary containing package capabilities, supported features,
        template sources, and integration information.
    """
    return {
        "name": __package_name__,
        "version": __version__,
        "description": __description__,
        "main_class": "Jinja2Renderer",
        "template_sources": [
            "File system directories",
            "Dictionary-based templates",
            "String templates",
            "JSON templates with variable resolution",
        ],
        "rendering_modes": [
            "String rendering for simple templates",
            "Object rendering for complex data structures",
            "File rendering from configured sources",
            "Batch directory rendering",
            "JSON rendering with parsing",
        ],
        "custom_filters": [
            "AWS resource management (aws_tags, docker_image, image_id)",
            "Security rules (ip_rules, iam_rules, parse_port_spec)",
            "Network operations (split_cidr, subnet planning)",
            "Data transformation (lookup, extract, ensure_list)",
            "String utilities (shorten_unique, regex_replace)",
            "Date and formatting (format_date, to_json, to_yaml)",
        ],
        "integration_features": [
            "Core Automation deployment context",
            "AWS CloudFormation optimization",
            "Terraform configuration support",
            "Cross-platform file handling",
            "Environment-specific rendering",
        ],
        "supported_formats": [
            "CloudFormation YAML/JSON",
            "Terraform HCL configurations",
            "Shell scripts and automation",
            "Configuration files (YAML, JSON, INI)",
            "Documentation and README files",
        ],
        "deployment_contexts": [
            "Portfolio-scoped resources",
            "Application-scoped resources",
            "Branch-scoped resources",
            "Build-scoped resources",
            "Environment-scoped resources",
            "Component-scoped resources",
        ],
        "aws_integrations": [
            "Resource naming conventions",
            "Tag standardization",
            "Security group rules",
            "IAM policy generation",
            "ECR image references",
            "CloudFormation outputs",
        ],
        "thread_safety": "Full thread safety for concurrent rendering",
        "error_handling": "Strict undefined checking with clear error messages",
        "performance": "Optimized for batch processing and large template sets",
    }


def get_template_best_practices() -> dict[str, list[str]]:
    """Get best practices for template development with Core Renderer.

    Returns:
        Dictionary organized by category containing best practice recommendations
        for effective template development and deployment.
    """
    return {
        "template_organization": [
            "Use descriptive file names with .j2 or .jinja2 extensions",
            "Organize templates in logical directory hierarchies",
            "Separate base templates from environment-specific overrides",
            "Use template inheritance for common patterns",
            "Group related templates by service or component type",
        ],
        "variable_management": [
            "Use descriptive variable names following naming conventions",
            "Leverage deployment context variables (portfolio, app, branch, build)",
            "Validate required variables with default values or error handling",
            "Document template variables in header comments",
            "Use consistent variable naming across template sets",
        ],
        "filter_usage": [
            "Use aws_tags filter for consistent resource tagging",
            "Apply docker_image filter for ECR image references",
            "Use ip_rules and iam_rules for security configurations",
            "Leverage split_cidr for VPC and subnet planning",
            "Apply ensure_list for robust parameter handling",
        ],
        "error_prevention": [
            "Test templates with various input combinations",
            "Use strict undefined checking during development",
            "Validate generated CloudFormation/Terraform syntax",
            "Include error handling for optional template sections",
            "Document template requirements and constraints",
        ],
        "performance_optimization": [
            "Minimize complex filter chains in loops",
            "Cache rendered results for repeated template operations",
            "Use batch rendering for multiple related templates",
            "Optimize template structure for rendering efficiency",
            "Profile template rendering for large-scale deployments",
        ],
        "security_considerations": [
            "Validate and sanitize external input variables",
            "Use secure defaults for sensitive configurations",
            "Apply least-privilege principles in generated IAM policies",
            "Avoid hardcoded credentials or sensitive values",
            "Use parameter files for environment-specific secrets",
        ],
    }


# Export metadata for runtime introspection
__renderer_info__ = get_renderer_info()
__template_best_practices__ = get_template_best_practices()
