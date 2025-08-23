"""Core Logging Package for the Core Automation Framework.

This package provides a comprehensive logging system designed specifically for
cloud-native applications, microservices, and automation frameworks. It combines
the power of Python's standard logging with enhanced features for structured
logging, identity management, and multi-format output support.

Key Features:
    - **Structured Logging**: Support for both JSON and human-readable text formats
    - **Identity Management**: Thread-safe identity tracking for multi-component systems
    - **Custom Log Levels**: MSG, STATUS, and TRACE levels beyond standard logging
    - **Metadata Enrichment**: Automatic context addition with caller information
    - **Environment Configuration**: Automatic setup based on environment variables
    - **Cloud Integration**: Optimized for Lambda, containers, and cloud deployments

Architecture:
    The logging system consists of three main layers:

    **Interface Layer (log_interface.py):**
    Global functions that provide simple access to logging functionality with
    automatic logger creation, identity management, and caller information extraction.

    **Core Classes (log_classes.py):**
    Enhanced logging classes including CoreLogger with metadata support,
    formatters for JSON and text output, and handlers for different destinations.

    **Configuration Layer:**
    Environment-driven configuration that adapts logging behavior for different
    deployment contexts (development, staging, production).

Components:
    - **CoreLogger**: Enhanced logger with metadata and identity support
    - **CoreLoggerHandler**: Custom handler for Core Automation message processing
    - **CoreLogTextFormatter**: Human-readable text output with YAML details
    - **CoreLogJsonFormatter**: Structured JSON output for log aggregation
    - **Global Functions**: Module-level logging functions with automatic setup

Log Levels:
    The package supports all standard Python log levels plus custom levels:
    - **TRACE (5)**: Detailed trace information for debugging
    - **DEBUG (10)**: Standard debug information
    - **INFO (20)**: General information messages
    - **WARNING (30)**: Warning messages
    - **ERROR (40)**: Error messages
    - **CRITICAL (50)**: Critical error messages
    - **STATUS (60)**: Status update messages with code and reason
    - **MSG (70)**: Simple high-priority message output

Output Formats:
    **Text Format (Human-Readable):**
    Timestamp [Logger] [Level] Message
        detail_key: detail_value
        nested_key: nested_value

    **JSON Format (Structured):**
    {
        "@timestamp": "2024-01-01T12:00:00.000Z",
        "log.logger": "component.service",
        "log.level": "INFO",
        "message": "Operation completed",
        "context": {"key": "value"}
    }

Environment Variables:
    - **LOG_LEVEL**: Set default logging level (DEBUG, INFO, WARNING, etc.)
    - **LOG_AS_JSON**: Control output format (true for JSON, false for text)
    - **LOG_DIR**: Directory for log file output (optional)
    - **CONSOLE_LOG**: Enable/disable console output (default: true)
    - **LOG_GROUP**: Log group name for file organization
    - **LOG_STREAM**: Log stream name for file naming

Identity Management:
    The logging system uses thread-safe identity management to organize logs
    by component, service, or operational context. Identities follow PRN
    format: prn:portfolio:app:branch:build or custom descriptive strings.

Thread Safety:
    All logging operations are thread-safe using threading.local() for
    per-thread state management. This ensures proper isolation in
    multi-threaded applications and cloud execution environments.

Integration:
    Designed for seamless integration with:
    - AWS Lambda functions and cloud services
    - Container-based deployments with log aggregation
    - Microservice architectures with distributed tracing
    - Development workflows with both human and machine-readable output
    - Monitoring and alerting systems requiring structured logs

Performance:
    The logging system is optimized for high-performance scenarios:
    - Lazy logger creation and caching
    - Efficient formatter selection
    - Minimal overhead for disabled log levels
    - Background processing for expensive operations

Usage Patterns:
    **Simple Logging:**
    ```python
    import core_logging as log
    log.info("Operation completed")
    log.error("Error occurred", exc_info=True)
    ```

    **Identity-Based Logging:**
    ```python
    log.setup("prn:portfolio:app:service:v1")
    log.info("Service started")
    ```

    **Structured Logging:**
    ```python
    log.info("User action", details={"user_id": 123, "action": "login"})
    ```

Extension Points:
    The logging system can be extended with:
    - Custom formatters for specific output requirements
    - Additional handlers for different destinations
    - Custom log levels for specific application needs
    - Integration adapters for external logging services
"""

from .log_interface import (
    getLogger,
    setLevel,
    getLevel,
    setup,
    get_identity,
    set_identity,
    reset_identity,
    msg,
    status,
    trace,
    debug,
    error,
    warning,
    warn,
    fatal,
    critical,
    info,
    getLevelName,
)
from .log_classes import (
    CoreLogger,
    CoreLoggerHandler,
    MSG,
    STATUS,
    TRACE,
    LOG_TYPE,
    LOG_STATUS,
    LOG_MESSAGE,
    LOG_REASON,
    LOG_RESOURCE,
    LOG_TIMESTAMP,
    LOG_DETAILS,
    L_STATUS_LABEL,
    L_STATUS,
    L_REASON,
    L_MESSAGE,
    L_DETAILS,
    L_IDENTITY,
    L_TYPE,
    L_SCOPE,
    DEFAULT_DATE_FORMAT,
)
from logging import NOTSET, INFO, WARNING, ERROR, CRITICAL, DEBUG

__all__ = [
    # Core logging classes
    "CoreLogger",
    "CoreLoggerHandler",
    # Custom log levels
    "MSG",
    "STATUS",
    "TRACE",
    # Standard log levels
    "DEBUG",
    "ERROR",
    "WARNING",
    "CRITICAL",
    "INFO",
    "NOTSET",
    # JSON output field names
    "LOG_TYPE",
    "LOG_STATUS",
    "LOG_MESSAGE",
    "LOG_REASON",
    "LOG_RESOURCE",
    "LOG_TIMESTAMP",
    "LOG_DETAILS",
    # Extra parameter keys for kwargs
    "L_STATUS_LABEL",
    "L_STATUS",
    "L_REASON",
    "L_MESSAGE",
    "L_DETAILS",
    "L_IDENTITY",
    "L_TYPE",
    "L_SCOPE",
    # Formatting utilities
    "DEFAULT_DATE_FORMAT",
    # Logger management functions
    "getLogger",
    "setLevel",
    "getLevel",
    "setup",
    # Identity management functions
    "get_identity",
    "set_identity",
    "reset_identity",
    # Logging functions
    "msg",
    "status",
    "trace",
    "debug",
    "error",
    "fatal",
    "warning",
    "warn",
    "critical",
    "info",
    "getLevelName",
]

# Categorized exports for documentation and discovery

#: Core logging infrastructure classes
LOGGING_CLASSES = [
    "CoreLogger",
    "CoreLoggerHandler",
]

#: Custom log levels for Core Automation
CUSTOM_LOG_LEVELS = [
    "MSG",  # Level 70 - High priority messages
    "STATUS",  # Level 60 - Status updates with code/reason
    "TRACE",  # Level 5  - Detailed trace information
]

#: Standard Python logging levels
STANDARD_LOG_LEVELS = [
    "CRITICAL",  # Level 50 - Critical errors
    "ERROR",  # Level 40 - Error conditions
    "WARNING",  # Level 30 - Warning conditions
    "INFO",  # Level 20 - General information
    "DEBUG",  # Level 10 - Debug information
    "NOTSET",  # Level 0  - No level set
]

#: JSON output field names for structured logging
JSON_FIELD_NAMES = [
    "LOG_TYPE",  # Type field in JSON output
    "LOG_STATUS",  # Status field in JSON output
    "LOG_MESSAGE",  # Message field in JSON output
    "LOG_REASON",  # Reason field in JSON output
    "LOG_RESOURCE",  # Resource field in JSON output
    "LOG_TIMESTAMP",  # Timestamp field in JSON output
    "LOG_DETAILS",  # Details field in JSON output
]

#: Extra parameter keys for kwargs in logging calls
EXTRA_PARAMETER_KEYS = [
    "L_STATUS_LABEL",  # Status label for legacy compatibility
    "L_STATUS",  # Status code for status messages
    "L_REASON",  # Reason text for status messages
    "L_MESSAGE",  # Message content override
    "L_DETAILS",  # Additional details dictionary
    "L_IDENTITY",  # Logger identity override
    "L_TYPE",  # Type classification
    "L_SCOPE",  # Scope context information
]

#: Formatting and utility functions
FORMATTING_UTILITIES = [
    "DEFAULT_DATE_FORMAT",  # Default datetime format string
]

#: Logger management and configuration functions
LOGGER_MANAGEMENT = [
    "getLogger",  # Get or create logger instance
    "setLevel",  # Set default log level
    "getLevel",  # Get current log level
    "setup",  # Initialize logging with identity
    "getLevelName",  # Convert level number to name
]

#: Identity management functions for multi-component systems
IDENTITY_MANAGEMENT = [
    "get_identity",  # Get current thread identity
    "set_identity",  # Set current thread identity
    "reset_identity",  # Reset to default identity (deprecated)
]

#: Logging functions organized by severity level
LOGGING_FUNCTIONS = [
    # High priority output
    "msg",  # Level 70 - Always visible messages
    "status",  # Level 60 - Status with code and reason
    # Standard severity levels
    "critical",  # Level 50 - Critical errors
    "fatal",  # Level 50 - Fatal errors (alias for critical)
    "error",  # Level 40 - Error conditions
    "warning",  # Level 30 - Warning conditions
    "warn",  # Level 30 - Warning conditions (alias)
    "info",  # Level 20 - General information
    "debug",  # Level 10 - Debug information
    "trace",  # Level 5  - Detailed trace information
]


def get_logging_categories() -> dict[str, list[str]]:
    """Get categorized lists of available logging functionality.

    Returns:
        Dictionary mapping category names to lists of available functions,
        classes, and constants organized by purpose.

    Categories:
        - classes: Core logging infrastructure classes
        - levels_custom: Custom log levels for Core Automation
        - levels_standard: Standard Python logging levels
        - json_fields: Field names for JSON structured output
        - extra_keys: Parameter keys for metadata in logging calls
        - formatting: Datetime formatting utilities
        - management: Logger creation and configuration functions
        - identity: Identity management for multi-component systems
        - functions: Logging functions organized by severity
    """
    return {
        "classes": LOGGING_CLASSES,
        "levels_custom": CUSTOM_LOG_LEVELS,
        "levels_standard": STANDARD_LOG_LEVELS,
        "json_fields": JSON_FIELD_NAMES,
        "extra_keys": EXTRA_PARAMETER_KEYS,
        "formatting": FORMATTING_UTILITIES,
        "management": LOGGER_MANAGEMENT,
        "identity": IDENTITY_MANAGEMENT,
        "functions": LOGGING_FUNCTIONS,
    }


def get_level_hierarchy() -> dict[str, int]:
    """Get the complete log level hierarchy with numeric values.

    Returns:
        Dictionary mapping level names to their numeric values, including
        both standard Python levels and custom Core Automation levels.

    Level Hierarchy:
        MSG (70) > STATUS (60) > CRITICAL (50) > ERROR (40) >
        WARNING (30) > INFO (20) > DEBUG (10) > TRACE (5) > NOTSET (0)
    """
    return {
        "MSG": 70,  # High priority messages
        "STATUS": 60,  # Status updates with code/reason
        "CRITICAL": 50,  # Critical system errors
        "ERROR": 40,  # Error conditions
        "WARNING": 30,  # Warning conditions
        "INFO": 20,  # General information
        "DEBUG": 10,  # Debug information
        "TRACE": 5,  # Detailed trace information
        "NOTSET": 0,  # No level set (inherit from parent)
    }


def get_package_info() -> dict[str, any]:
    """Get comprehensive information about the Core Logging package.

    Returns:
        Dictionary containing package metadata, capabilities, configuration
        options, and usage information for documentation and discovery.
    """
    categories = get_logging_categories()
    levels = get_level_hierarchy()

    return {
        "name": "Core Logging Package",
        "description": "Comprehensive logging system for cloud-native applications",
        "version": "1.0.0",
        "features": [
            "Structured logging with JSON and text formats",
            "Thread-safe identity management",
            "Custom log levels (MSG, STATUS, TRACE)",
            "Automatic metadata enrichment",
            "Environment-driven configuration",
            "Cloud and container optimization",
        ],
        "output_formats": {
            "text": "Human-readable with YAML details",
            "json": "Structured JSON for log aggregation",
        },
        "log_levels": levels,
        "environment_variables": {
            "LOG_LEVEL": "Default logging level (DEBUG, INFO, WARNING, etc.)",
            "LOG_AS_JSON": "Output format control (true/false)",
            "LOG_DIR": "Directory for log file output",
            "CONSOLE_LOG": "Enable console output (default: true)",
            "LOG_GROUP": "Log group for file organization",
            "LOG_STREAM": "Log stream for file naming",
        },
        "categories": list(categories.keys()),
        "total_exports": len(__all__),
        "classes": len(LOGGING_CLASSES),
        "functions": len(LOGGING_FUNCTIONS + LOGGER_MANAGEMENT + IDENTITY_MANAGEMENT),
        "constants": len(
            CUSTOM_LOG_LEVELS
            + STANDARD_LOG_LEVELS
            + JSON_FIELD_NAMES
            + EXTRA_PARAMETER_KEYS
        ),
        "thread_safety": "Full thread safety with threading.local()",
        "cloud_integration": [
            "AWS Lambda optimized",
            "Container logging support",
            "Log aggregation compatibility",
            "Monitoring system integration",
        ],
        "use_cases": [
            "Microservice logging with identity tracking",
            "Development with human-readable output",
            "Production with structured JSON logging",
            "Cloud deployments with centralized logging",
            "Multi-threaded applications with safe logging",
        ],
    }


# Module metadata for introspection and documentation
__logging_categories__ = get_logging_categories()
__level_hierarchy__ = get_level_hierarchy()
__package_info__ = get_package_info()

# Package version and compatibility information
__version__ = "1.0.0"
__python_requires__ = ">=3.8"
__framework_integration__ = "core_framework"
