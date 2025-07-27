"""This module provides the log helper functions for the core_logging library. Such as log.debug, log.error, log.warning, log.warn, log.fatal, log.critical, log.info, log.trace, log.message, etc."""

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
    """
    Return the name of the logging level for the specified level.

    :param level: The log level integer value
    :type level: int
    :return: The string representation of the logging level
    :rtype: str
    """
    return logging.getLevelName(level)


def getLevelFromName(level: str) -> int:
    """
    Return the logging level for the name provided.

    :param level: The name of the logging level
    :type level: str
    :return: The logging level integer value
    :rtype: int
    """
    return logging._nameToLevel.get(level, 0)


def setRootLevel(level: int):
    """
    Set the logging level for the logger.

    :param level: The logging level integer value
    :type level: int
    """
    logging.root.setLevel(level)


def getRootLevel() -> int:
    """
    Return the current logging level for the logger.

    :return: The logging level integer value
    :rtype: int
    """
    return logging.root.level


def getLevel() -> int:
    """
    Return the current logging level for the log module.

    :return: The logging level integer value
    :rtype: int
    """
    return _log_level


def setLevel(level: int | str):
    """
    Set the logging level for the log module.

    :param level: The logging level integer value or string name
    :type level: int | str
    """
    global _log_level

    if isinstance(level, str):
        level = getLevelFromName(level.upper())

    _log_level = level


def setLevelForLogger(name: str, level: int | str):
    """
    Sets the log level for the specified logger.

    :param name: The logger's name
    :type name: str
    :param level: The level that you wish to set
    :type level: int | str

    Example:
        .. code-block:: python

            import core_logging as log

            log.setLevel("WARN")  # Set the default log level to WARN

            # Set the log level for the specified identity to DEBUG
            identity = "prn:portfolio:app:branch:build"
            log.setLevelForLogger(identity, "DEBUG")

            # Log a message for the identity
            log.debug("This is a debug message", identity=identity)

        Outputs the following:

        .. code-block:: console

            2024-12-19 10:21:55 [prn:portfolio:app:branch:build] [DEBUG] This is a debug message
    """
    if isinstance(level, str):
        level = getLevelFromName(level.upper())
    logger = getLogger(name)
    logger.setLevel(level)


def setup(identity: str):
    """
    Initialize the logger with the specified identity.

    The identity is a PRN (Pipeline Resource Name) or (Pipeline Reference Name/Number)
    and is in the format of "prn:portfolio:app:branch:build". The identity is used to
    identify the source of the log message.

    The identity can actually be any string. It is not validated.

    :param identity: The PRN or identity of the logger
    :type identity: str
    """
    _thread_local.default_identity = _thread_local.identity = identity


def set_identity(identity: str):
    """
    Hold an identity for the logger.

    This is used to identify the source of the log message. This value will be used
    if not specified in the log call.

    :param identity: The PRN or identity of the logger
    :type identity: str
    """
    _thread_local.identity = identity


def get_default_identity() -> str | None:
    """
    Return the threadlocal default identity for the logger.

    :return: The thread_local identity or None
    :rtype: str | None
    """
    return getattr(_thread_local, "default_identity", None)


def get_identity() -> str | None:
    """
    Return the default identity for the logger.

    This default identity is used to identify the source of the log message and will be used
    if not specified in the log call.

    :return: The default identity for the logger
    :rtype: str | None
    """
    return getattr(_thread_local, "identity", get_default_identity())


def clear_identity():
    """
    Clear both current and default thread-local identity values.
    """
    if hasattr(_thread_local, "identity"):
        del _thread_local.identity
    if hasattr(_thread_local, "default_identity"):
        del _thread_local.default_identity


def reset_identity():
    """
    Resets the identity to the default identity that was established when the logger was setup with the setup() method.

    .. deprecated::
        Use the "getLogger()" method to get a logger with the specified identity. This method is NOT thread safe.
    """
    _thread_local.identity = get_default_identity()


def get_logger_identity(**kwargs: dict) -> str:
    """
    Attempts to retrieve the identity from the kwargs parameter.

    If it's not found, it will return the default identity.

    The kwargs is NOT expanded. No \\*\\* on the kwargs. We are mutating kwargs and popping off the Identity.

    We may change this behaviour in the future.

    Looking for "identity" or "prn" in kwargs. ("prn" is not popped off)

    :param kwargs: A dictionary of name/value pairs that should have the identity in it
    :type kwargs: dict
    :return: The identity if found, else a fallback identity
    :rtype: str
    """
    module = kwargs.get("module", None)
    function = kwargs.get("function", None)
    identity = get_identity() or f"{module}.{function}" or "unknown"
    return str(kwargs.get(L_IDENTITY, identity))


def __get_formatter() -> logging.Formatter:
    """
    Get the appropriate formatter based on environment configuration.

    :return: The configured formatter (JSON or text)
    :rtype: logging.Formatter
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
    """
    Get the list of handlers for the logger based on environment configuration.

    :param name: The name of the logger
    :type name: str
    :param kwargs: Additional configuration options
    :type kwargs: dict
    :return: List of configured handlers
    :rtype: list[logging.Handler]
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
    """
    Return a logging object with the specified name.

    :param name: The name/identity of the logger
    :type name: str | None
    :param kwargs: Experimental parameters "log_stream" and "log_group"
    :type kwargs: dict
    :return: The logger object
    :rtype: CoreLogger

    .. note::
        Experimental parameters:
        - log_stream: The name of the log stream filename. defaults to "core".
        - log_group: The name of the log group folder. Defaults to "".
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
    """
    Get information about the calling function.

    :return: Tuple of (module_name, function_name, filename, line_number)
    :rtype: tuple[str, str, str, int]
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
    """
    Log a message at the specified level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param level: The logging level (MSG, STATUS, TRACE, etc.)
    :type level: int
    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.log(level, message, *args, **kwargs)


def msg(message: str | dict, *args, **kwargs):
    """
    Log a message at the MSG level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.msg(message, *args, **kwargs)


def trace(message: str | dict, *args, **kwargs):
    """
    Log a message at the TRACE level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.trace(message, *args, **kwargs)


def debug(message: str | dict, *args, **kwargs):
    """
    Log a message at the DEBUG level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.debug(message, *args, **kwargs)


def critical(message: str | dict, *args, **kwargs):
    """
    Log a message at the CRITICAL level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.critical(message, *args, **kwargs)


def fatal(message: str | dict, *args, **kwargs):
    """
    Log a message at the FATAL level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.fatal(message, *args, **kwargs)


def error(message: str | dict, *args, **kwargs):
    """
    Log a message at the ERROR level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.error(message, *args, **kwargs)


def info(message: str | dict, *args, **kwargs):
    """
    Log a message at the INFO level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.info(message, *args, **kwargs)


def warn(message: str | dict, *args, **kwargs):
    """
    Log a message at the WARNING level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.warning(message, *args, **kwargs)


def warning(message: str | dict, *args, **kwargs):
    """
    Log a message at the WARNING level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param message: The message to output
    :type message: str | dict
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.warning(message, *args, **kwargs)


def status(code: str | int, reason: str, *args, **kwargs):
    """
    Log a message at the STATUS level.

    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    :param code: The status code
    :type code: str | int
    :param reason: The status message
    :type reason: str
    :param args: Values used to replace the %s place holders in the message
    :type args: tuple
    :param kwargs: Name/Value pairs that will be added to the output
    :type kwargs: dict
    """
    module_name, function_name, _, _ = __get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )

    reason = "" if reason is None else reason

    if code is None:
        code = 200

    logger.status(code, reason, *args, **kwargs)
