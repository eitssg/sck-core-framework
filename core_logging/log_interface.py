"""Core Logging Interface Module providing global logging functions and configuration.

This module serves as the primary interface for the Core Automation logging system,
providing convenient module-level functions that automatically handle logger creation,
identity management, and configuration. It abstracts the complexity of the underlying
logging infrastructure while providing rich metadata support and thread-safe operations.

Key Features:
    - **Global Functions**: Module-level logging functions (debug, info, error, etc.)
    - **Identity Management**: Thread-safe identity tracking for multi-component systems
    - **Automatic Logger Creation**: Dynamic logger instantiation with proper configuration
    - **Environment Configuration**: Automatic setup based on environment variables
    - **Metadata Enrichment**: Automatic caller information and context addition
    - **Multi-Format Support**: Transparent switching between JSON and text output

Architecture:
    The interface provides a simplified API over the CoreLogger infrastructure,
    automatically handling logger creation, formatter selection, and handler
    configuration based on environment settings. All functions use thread-local
    storage for identity management to ensure thread safety.

Thread Safety:
    All logging functions and identity management operations are thread-safe
    through the use of threading.local() for per-thread state management.
    This ensures proper isolation in multi-threaded and Lambda environments.

Environment Variables:
    - LOG_LEVEL: Sets the default logging level (DEBUG, INFO, WARNING, etc.)
    - LOG_AS_JSON: Controls output format (true for JSON, false for text)
    - LOG_DIR: Directory for log file output (optional)
    - CONSOLE_LOG: Enables/disables console output (default: true)
    - LOG_GROUP: Log group name for file organization (optional)
    - LOG_STREAM: Log stream name for file naming (optional)

Usage Patterns:
    The module supports both simple logging calls and rich metadata logging:

    **Simple Logging:**
    Functions like debug(), info(), error() provide direct logging with
    automatic identity resolution and caller information.

    **Identity-Based Logging:**
    Logger identity can be set globally or per-call to organize logs by
    component, service, or operational context.

    **Metadata Logging:**
    All functions accept keyword arguments that are automatically converted
    to structured metadata in the log output.

Integration:
    Designed to work seamlessly with the Core Automation framework while
    providing standalone functionality for any Python application requiring
    structured logging with identity management.
"""

import inspect
from threading import local
import os

import logging
from core_framework.constants import (
    ENV_LOG_LEVEL,
    ENV_LOG_AS_JSON,
    ENV_LOG_DIR,
    ENV_CONSOLE_LOG,
)

from .log_classes import (
    CoreLogger,
    CoreLoggerHandler,
    CoreLogTextFormatter,
    CoreLogJsonFormatter,
    L_IDENTITY,
    DEFAULT_DATE_FORMAT,
    DEFAULT_LOG_FORMAT,
    ENV_LOG_GROUP,
    ENV_LOG_STREAM,
    INFO,
)

# Our custom levels were added when the "core_logging.log_classes" module was loaded in the imports above
_log_level: int = logging._nameToLevel.get(os.getenv(ENV_LOG_LEVEL, "INFO"), INFO)

# Override the default logger class to use our custom logger class as methods were added (e.g. trace() and msg() functions).
logging.root = CoreLogger("root", level=_log_level)  # type: ignore
logging.Logger.root = logging.root
logging.setLoggerClass(CoreLogger)

# Please note that Lambda has a time limit and when it restarts, thread local variables are reset.
_thread_local = local()
_thread_local.default_identity = None
_thread_local.identity = None


def getLevelName(level: int) -> str:
    """Return the textual name for the specified numeric logging level.

    Converts numeric log levels to their string representations for
    display and configuration purposes.

    Args:
        level: The numeric log level value.

    Returns:
        The string name of the logging level (e.g., "DEBUG", "INFO").
    """
    return logging.getLevelName(level)


def getLevelFromName(level: str) -> int:
    """Return the numeric logging level for the specified level name.

    Converts string log level names to their numeric values for
    programmatic level comparison and configuration.

    Args:
        level: The string name of the logging level.

    Returns:
        The numeric log level value, or 0 if the name is not recognized.
    """
    return logging._nameToLevel.get(level, 0)


def setRootLevel(level: int):
    """Set the logging level for the root logger.

    Updates the root logger's level, affecting all loggers that inherit
    from the root unless they have explicitly set levels.

    Args:
        level: The numeric logging level to set.
    """
    logging.root.setLevel(level)


def getRootLevel() -> int:
    """Get the current logging level of the root logger.

    Returns:
        The numeric logging level currently set on the root logger.
    """
    return logging.root.level


def getLevel() -> int:
    """Get the current default logging level for the log module.

    Returns the module-level default log level used for new loggers
    and interface functions.

    Returns:
        The numeric logging level for the module.
    """
    return _log_level


def setLevel(level: int | str):
    """Set the default logging level for the log module.

    Updates the module-level default log level that will be applied
    to new loggers and interface functions.

    Args:
        level: The logging level as either a numeric value or string name.
    """
    global _log_level

    if isinstance(level, str):
        level = getLevelFromName(level.upper())

    _log_level = level


def setLevelForLogger(name: str, level: int | str):
    """Set the log level for a specific named logger.

    Allows fine-grained control over logging levels for individual
    loggers, enabling different verbosity levels for different components.

    Args:
        name: The name/identity of the logger to configure.
        level: The logging level as either a numeric value or string name.

    Notes:
        This enables selective debugging where specific components can
        have different log levels while maintaining overall system logging
        configuration.
    """
    if isinstance(level, str):
        level = getLevelFromName(level.upper())
    logger = getLogger(name)
    logger.setLevel(level)


def setup(identity: str):
    """Initialize the logging system with a default identity.

    Establishes a default identity for the current thread that will be
    used for all subsequent logging calls unless explicitly overridden.
    The identity helps organize logs by component or operational context.

    Args:
        identity: The default identity string, typically in PRN format
                 (e.g., "prn:portfolio:app:branch:build") but can be any
                 descriptive string.

    Notes:
        This function sets both the default identity and current identity
        for the thread. The identity is stored in thread-local storage
        to ensure thread safety in multi-threaded environments.
    """
    _thread_local.default_identity = _thread_local.identity = identity


def set_identity(identity: str):
    """Set the current logging identity for the thread.

    Updates the current thread's logging identity without changing the
    default identity. This allows temporary identity changes that can
    be reset back to the default.

    Args:
        identity: The identity string to use for subsequent logging calls.

    Notes:
        The identity is used to identify the source of log messages and
        organize logs by component, service, or operational context.
        This setting is thread-local and does not affect other threads.
    """
    _thread_local.identity = identity


def get_default_identity() -> str | None:
    """Get the default identity established during logging setup.

    Returns the default identity that was set when the logging system
    was initialized with the setup() function.

    Returns:
        The default identity string, or None if setup() has not been called.

    Notes:
        The default identity serves as a fallback when no specific identity
        is provided for logging calls.
    """
    return getattr(_thread_local, "default_identity", None)


def get_identity() -> str | None:
    """Get the current logging identity for the thread.

    Returns the currently active identity for the thread, falling back
    to the default identity if no current identity is set.

    Returns:
        The current thread identity, default identity, or None if neither
        has been set.

    Notes:
        This function checks the current identity first, then falls back
        to the default identity to ensure consistent identity resolution.
    """
    return getattr(_thread_local, "identity", get_default_identity())


def clear_identity():
    """Clear both current and default thread-local identity values.

    Removes all identity information from the current thread, causing
    subsequent logging calls to use automatic identity resolution based
    on caller information.

    Notes:
        After calling this function, logging calls will derive identity
        from module and function names unless explicitly provided.
    """
    if hasattr(_thread_local, "identity"):
        del _thread_local.identity
    if hasattr(_thread_local, "default_identity"):
        del _thread_local.default_identity


def reset_identity():
    """Reset the current identity to the default identity.

    Restores the current thread identity to the default identity that
    was established during setup.

    Notes:
        This function is deprecated. Use getLogger() with a specific
        identity instead for better thread safety and explicit control.

    Deprecated:
        Use getLogger() method to get a logger with the specified identity.
        This method is NOT thread safe.
    """
    _thread_local.identity = get_default_identity()


def get_logger_identity(**kwargs: dict) -> str:
    """Extract or determine the logger identity from various sources.

    Attempts to find an appropriate identity for logging by checking
    kwargs parameters and falling back to automatic identity generation
    from caller information.

    Args:
        **kwargs: Keyword arguments that may contain identity information.
                 Supports 'identity', 'prn', 'module', and 'function' keys.

    Returns:
        The resolved identity string, using the following priority:
        1. 'identity' from kwargs
        2. Current thread identity
        3. Generated from module.function
        4. "unknown" as final fallback

    Notes:
        The function looks for 'identity' or 'prn' in kwargs but only
        'identity' is removed from kwargs to avoid mutation side effects.
        The 'prn' key is preserved for backward compatibility.
    """
    module = kwargs.get("module", None)
    function = kwargs.get("function", None)
    identity = get_identity() or f"{module}.{function}" or "unknown"
    return str(kwargs.get(L_IDENTITY, identity))


def __get_formatter() -> logging.Formatter:
    """Get the appropriate formatter based on environment configuration.

    Creates and returns either a JSON or text formatter depending on
    the LOG_AS_JSON environment variable setting.

    Returns:
        CoreLogJsonFormatter if LOG_AS_JSON is "true", otherwise
        CoreLogTextFormatter for human-readable output.

    Notes:
        The formatter choice affects the output format of all log messages.
        JSON format is suitable for log aggregation systems, while text
        format is better for human readability and development.
    """
    # Get the Core Automation Formatters
    date_fmt = DEFAULT_DATE_FORMAT
    msg_fmt = DEFAULT_LOG_FORMAT

    # default logging to text formatter unless LOG_AS_JSON is set to true
    if os.environ.get(ENV_LOG_AS_JSON, "false").lower() == "true":
        return CoreLogJsonFormatter(msg_fmt, date_fmt)
    else:
        return CoreLogTextFormatter(msg_fmt, date_fmt)


def __get_handlers(name, **kwargs) -> list[logging.Handler]:
    """Create and configure logging handlers based on environment settings.

    Sets up the appropriate handlers for console and/or file output
    based on environment configuration variables.

    Args:
        name: The logger name for handler identification.
        **kwargs: Additional configuration options including:
                 log_group: Custom log group name override.
                 log_stream: Custom log stream name override.

    Returns:
        List of configured logging handlers ready for attachment to loggers.

    Handler Types:
        - Console Handler: Always added if CONSOLE_LOG is true (default)
        - File Handler: Added if LOG_DIR environment variable is set

    File Organization:
        Files are organized as: LOG_DIR/LOG_GROUP/LOG_STREAM.log
        where LOG_GROUP and LOG_STREAM can be overridden via kwargs.
    """
    handlers: list[logging.Handler] = []

    formatter = __get_formatter()

    # Add a console handler
    log_console = os.getenv(ENV_CONSOLE_LOG, "true").lower() == "true"
    if log_console:
        console_hdlr = CoreLoggerHandler(name or "core")
        console_hdlr.setFormatter(formatter)
        handlers.append(console_hdlr)

    # Add a file handler
    log_dir = os.getenv(ENV_LOG_DIR)
    if log_dir:

        # If a LOG GROUP is defined, add it to the folder directory path
        log_group = kwargs.get("log_group", os.getenv(ENV_LOG_GROUP, ""))

        # If a LOG STREAM is defined, set it as the filename
        log_stream = kwargs.get("log_stream", os.getenv(ENV_LOG_STREAM, "core"))

        # Set the filename to the log_dir/log_group/log_stream.log file
        log_file = os.path.join(log_dir, log_group, f"{log_stream}.log")

        os.makedirs(log_dir, exist_ok=True)

        file_hdlr = logging.FileHandler(log_file)
        file_hdlr.setFormatter(formatter)
        handlers.append(file_hdlr)

    return handlers


def getLogger(name: str | None, **kwargs) -> CoreLogger:
    """Get or create a CoreLogger instance with the specified name and configuration.

    Creates a properly configured logger with appropriate handlers and
    formatters based on environment settings. Handles logger caching
    to avoid duplicate handler attachment.

    Args:
        name: The name/identity of the logger. If None, returns the root logger.
        **kwargs: Experimental configuration parameters including:
                 log_stream: Log file name (defaults to "core").
                 log_group: Log directory subfolder (defaults to "").

    Returns:
        A fully configured CoreLogger instance ready for use.

    Notes:
        The function ensures that handlers are only added once per logger
        to prevent duplicate log entries. The logger level is set to the
        current module default level.

        Experimental parameters are subject to change and should be used
        with caution in production environments.
    """
    logger: CoreLogger
    if name is None:
        logger = logging.getLogger()  # type: ignore
    else:
        logger = logging.getLogger(name)  # type: ignore
    if not logger.handlers:
        for handler in __get_handlers(name, **kwargs):
            logger.addHandler(handler)

    logger.setLevel(getLevel())

    return logger


def __get_caller_info():
    """Extract information about the function that called a logging function.

    Inspects the call stack to determine the module, function, filename,
    and line number of the code that initiated the logging call.

    Returns:
        Tuple containing (module_name, function_name, filename, line_number).

    Notes:
        Goes back two frames in the call stack to skip the logging interface
        wrapper and get the actual caller information. Used for automatic
        identity generation and source location tracking.
    """
    frame = inspect.currentframe()
    caller_frame = frame.f_back.f_back  # Go back two frames to get the caller
    module = inspect.getmodule(caller_frame)
    module_name = module.__name__ if module else "Unknown"
    function_name = caller_frame.f_code.co_name
    filename = caller_frame.f_code.co_filename
    lineno = caller_frame.f_lineno
    return module_name, function_name, filename, lineno


def log(level: int, message: str | dict, *args, **kwargs):
    """Log a message at the specified numeric level with automatic identity resolution.

    Provides direct access to numeric log levels while handling automatic
    logger creation and identity management.

    Args:
        level: The numeric logging level (TRACE=5, DEBUG=10, INFO=20, etc.).
        message: The message to log, either as a string or dict for structured logging.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 exc_info: Include exception information.
                 details: Additional structured data.

    Notes:
        Automatically determines caller information and creates appropriate
        logger instances. The identity is resolved from kwargs, thread-local
        storage, or generated from caller information.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.log(level, message, *args, **kwargs)


def msg(message: str | dict, *args, **kwargs):
    """Log a message at the MSG level (70) for high-priority output.

    Outputs messages at the highest custom level for important notifications
    that should always be visible regardless of typical log level settings.

    Args:
        message: The message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 scope: Context scope for the message.
                 details: Additional structured data.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.msg(message, *args, **kwargs)


def trace(message: str | dict, *args, **kwargs):
    """Log a message at the TRACE level (5) for detailed debugging.

    Outputs detailed trace information at the lowest custom level for
    fine-grained debugging and development diagnostics.

    Args:
        message: The trace message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 scope: Context scope for the message.
                 details: Additional structured data.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.trace(message, *args, **kwargs)


def debug(message: str | dict, *args, **kwargs):
    """Log a message at the DEBUG level (10) for development information.

    Standard debug logging with enhanced metadata support for development
    and troubleshooting scenarios.

    Args:
        message: The debug message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 exc_info: Include exception information for error debugging.
                 details: Additional structured data.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.debug(message, *args, **kwargs)


def critical(message: str | dict, *args, **kwargs):
    """Log a message at the CRITICAL level (50) for severe errors.

    Standard critical logging with enhanced metadata support for severe
    error conditions that may cause system failure.

    Args:
        message: The critical message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 exc_info: Include exception information for error analysis.
                 details: Additional structured data about the critical condition.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.critical(message, *args, **kwargs)


def fatal(message: str | dict, *args, **kwargs):
    """Log a message at the FATAL level for fatal system errors.

    Alias for critical level logging, providing semantic clarity for
    fatal error conditions that prevent continued operation.

    Args:
        message: The fatal error message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 exc_info: Include exception information for error analysis.
                 details: Additional structured data about the fatal condition.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.fatal(message, *args, **kwargs)


def error(message: str | dict, *args, **kwargs):
    """Log a message at the ERROR level (40) for error conditions.

    Standard error logging with enhanced metadata support for error
    conditions that may affect operation but don't stop execution.

    Args:
        message: The error message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 exc_info: Include exception information for error analysis.
                 details: Additional structured data about the error.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.error(message, *args, **kwargs)


def info(message: str | dict, *args, **kwargs):
    """Log a message at the INFO level (20) for general information.

    Standard informational logging with enhanced metadata support for
    general operational information and status updates.

    Args:
        message: The information message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 scope: Context scope for the message.
                 details: Additional structured data.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.info(message, *args, **kwargs)


def warn(message: str | dict, *args, **kwargs):
    """Log a message at the WARNING level (30) for warning conditions.

    Standard warning logging with enhanced metadata support for situations
    that warrant attention but don't stop operation. Alias for warning().

    Args:
        message: The warning message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 scope: Context scope for the warning.
                 details: Additional structured data about the warning condition.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.warning(message, *args, **kwargs)


def warning(message: str | dict, *args, **kwargs):
    """Log a message at the WARNING level (30) for warning conditions.

    Standard warning logging with enhanced metadata support for situations
    that warrant attention but don't stop operation.

    Args:
        message: The warning message to output, string or dict for structured content.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 scope: Context scope for the warning.
                 details: Additional structured data about the warning condition.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))
    logger.warning(message, *args, **kwargs)


def status(code: str | int, reason: str, *args, **kwargs):
    """Log a structured status message at the STATUS level (60).

    Outputs structured status messages that combine a status code with
    a descriptive reason. Designed for operational status reporting and
    monitoring integration.

    Args:
        code: The status code (string or integer). None defaults to 200.
        reason: Descriptive reason text for the status. None becomes empty string.
        *args: Positional arguments for message template replacement.
        **kwargs: Keyword arguments for metadata enrichment including:
                 identity: Override logger identity for this call.
                 details: Additional structured data that may override code/reason.
                 scope: Context scope for the status.

    Message Format:
        The final message follows the pattern: "{code} {reason}"

    Notes:
        Both code and reason are added as separate metadata fields for
        structured logging systems. The details dict can override these
        values if it contains 'Status' and 'Reason' keys.
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(get_logger_identity(module=module_name, function=function_name, **kwargs))

    reason = "" if reason is None else reason

    if code is None:
        code = 200

    logger.status(code, reason, *args, **kwargs)
