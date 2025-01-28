""" This module provides the log helper functions for the core_logging library. Such as log.debug, log.error, log.warning, log.warn, log.fatal, log.critical, log.info, log.trace, log.message, etc.
"""

import inspect
from threading import local
import os

import logging

from .log_classes import (
    CoreLogger,
    CoreLoggerHandler,
    CoreLogTextFormatter,
    CoreLogJsonFormatter,
    L_IDENTITY,
    DEFAULT_DATE_FORMAT,
    DEFAULT_LOG_FORMAT,
    ENV_LOG_JSON,
    ENV_LOG_LEVEL,
    ENV_LOG_DIR,
    INFO,
)

# Our custom levels were added when the "core_logging.log_classes" module was loaded in the imports above
_log_level: int = logging._nameToLevel.get(os.getenv(ENV_LOG_LEVEL, "INFO"), INFO)

# Override the default logger class to use our custom logger class as methods were added (e.g. trace() and msg() functions).
logging.root = CoreLogger("root", level=_log_level)  # type: ignore
logging.Logger.root = logging.root
logging.setLoggerClass(CoreLogger)

# Please note that Lambda has a time imit nd when it restarts, thread local variables are reset.
_thread_local = local()
_thread_local.default_identity = None
_thread_local.identity = None


def getLevelName(level: int) -> str:
    """
    Return the name of the logging level for the specified level.

    Args:
        level (int): The log level integer value

    Returns:
        str: The string represetation of the logging level
    """
    return logging.getLevelName(level)


def getLevelFromName(level: str) -> int:
    """
    Return the logging level for the name provided.

    Args:
        level (str): The name of the logging level

    Returns:
        int: The logging level integer value
    """
    return logging._nameToLevel.get(level, 0)


def setRootLevel(level: int):
    """
    Set the logging level for the logger.

    Args:
        level (int): The logging level integer value
    """
    logging.root.setLevel(level)


def getRootLevel() -> int:
    """
    Return the current logging level for the logger.

    Returns:
        int: The logging level integer value
    """
    return logging.root.level


def getLevel() -> int:
    """
    Return the current logging level for the log module.

    Returns:
        int: The logging level integer value
    """
    return _log_level


def setLevel(level: int | str):
    """
    Set the logging level for the log module.

    Args:
        level (int): The logging level integer value
    """
    global _log_level

    if isinstance(level, str):
        level = getLevelFromName(level.upper())

    _log_level = level


def setLevelForLogger(name: str, level: int | str):
    """
    Sets the log level for the specified logger.

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

    Args:
        name (str): The logger's name
        level (int): The level that you wish to set

    """
    if isinstance(level, str):
        level = getLevelFromName(level.upper())
    logger = getLogger(name)
    logger.setLevel(level)


def setup(identity: str):
    """
    Initialize the logger with the specified identity.  The identity is a PRN (Pipeline Resource Name) or (Pipeline Reference Name/Number)
    and is in the format of "prn:portfolio:app:branch:build".  The identity is used to identify the source of the log message.

    The identity can actually be any string.  It is not validated.

    Args:
        identity (str): The PRN or identity of the logger.

    """
    _thread_local.default_identity = _thread_local.identity = identity


def set_identity(identity: str):
    """
    Hold an identity for the logger.  This is used to identify the source of the log message.  This value will be used if not specified in the log call

    Args:
        identity (str): The PRN or identity of the logger.
    """

    _thread_local.identity = identity


def get_default_identity() -> str | None:
    """
    Return the threadlocal default identity for the logger.

    Returns:
        str: The thread_local identity or empty string
    """
    return getattr(_thread_local, "default_identity", None)


def get_identity() -> str | None:
    """Return the default identity for the logger.

    This default identity is used to identify the source of the log message and will be used
    if not specified in the log call.

    Returns:
        str: The default identity for the logger.
    """
    return getattr(_thread_local, "identity", get_default_identity())


def clear_identity():
    """Clear both current and default thread-local identity values."""
    if hasattr(_thread_local, "identity"):
        del _thread_local.identity
    if hasattr(_thread_local, "default_identity"):
        del _thread_local.default_identity


def reset_identity():
    """
    Deprecated: use the "getLogger()" method to get a logger with the specified identity..  This method is NOT thread safe.

    Resets the identity to the default identity that was established when the logger was setup with the setup() method.
    """
    _thread_local.identity = get_default_identity()


def get_logger_identity(**kwargs: dict) -> str:
    """
    Attempts to retrieve the identity from the kwargs parameter.  If it's not found, it will return the default identity.

    The kwargs is NOT expended.  No \\*\\* on the kwargs  We are mutating kwargs and popping off the Identity.

    We may change this behaviour in the future.

    Looking for "identity" or "prn" in kwargs. ("prn" is not popped off)

    Args:
        kwargs (dict): A dictionary of name/value pairs that should have the identity in it.

    Returns:
        str | None: The identity if found, else None
    """
    module = kwargs.get("module", None)
    function = kwargs.get("function", None)
    identity = get_identity() or f"{module}.{function}" or "unknown"
    return str(kwargs.get(L_IDENTITY, identity))


def __get_formatter() -> logging.Formatter:

    # Get the Core Automatin Formatters
    date_fmt = DEFAULT_DATE_FORMAT
    msg_fmt = DEFAULT_LOG_FORMAT

    # default logging to text formatter unless LOG_AS_JSON is set to true
    if os.environ.get(ENV_LOG_JSON, "false").lower() == "true":
        return CoreLogJsonFormatter(msg_fmt, date_fmt)
    else:
        return CoreLogTextFormatter(msg_fmt, date_fmt)


def __get_handlers(name, **kwargs) -> list[logging.Handler]:

    handlers: list[logging.Handler] = []

    formatter = __get_formatter()

    # Add a console handler
    if os.getenv("CONSOLE_LOG", "true").lower() == "true":
        console_hdlr = CoreLoggerHandler(name or "core")
        console_hdlr.setFormatter(formatter)
        handlers.append(console_hdlr)

    # Add a file handler
    log_dir = os.getenv(ENV_LOG_DIR)
    if log_dir:

        # If a LOG GROUP is defined, add it to the folder diretory path
        log_group = kwargs.get("log_group", "")

        # If a LOG STREAM is defined, set it as the filename
        log_stream = kwargs.get("log_stream", "core")

        log_file = os.path.join(log_dir, log_group, f"{log_stream}.log")

        os.makedirs(log_dir, exist_ok=True)
        hdlr = logging.FileHandler(log_file)
        hdlr.setFormatter(formatter)
        handlers.append(hdlr)

    return handlers


def getLogger(name: str | None, **kwargs) -> CoreLogger:
    """
    Return a logging object with the specified name.

    Args:
        name (str | None): The name/identity of the logger
        kwargs (dict): experimental parameters "log_stream" and "log_group".
            * log_stream: The name of the log stream filename.
            * log_group: The name of the log group folder.

    Returns:
        CoreLogger: The logger object
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


def get_caller_info():
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

    Args:
        level (int): The logging level (MSG, STATUS, TRACE, etc.)
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.log(level, message, *args, **kwargs)


def msg(message: str | dict, *args, **kwargs):
    """
    Log a message at the MSG level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.msg(message, *args, **kwargs)


def trace(message: str | dict, *args, **kwargs):
    """
    Log a message at the TRACE level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.trace(message, *args, **kwargs)


def debug(message: str | dict, *args, **kwargs):
    """
    Log a message at the DEBUG level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.debug(message, *args, **kwargs)


def critical(message: str | dict, *args, **kwargs):
    """
    Log a message at the CRITICAL level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.critical(message, *args, **kwargs)


def fatal(message: str | dict, *args, **kwargs):
    """
    Log a message at the FATAL level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.fatal(message, *args, **kwargs)


def error(message: str | dict, *args, **kwargs):
    """
    Log a message at the ERROR level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.error(message, *args, **kwargs)


def info(message: str | dict, *args, **kwargs):
    """
    Log a message at the INFO level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.info(message, *args, **kwargs)


def warn(message: str | dict, *args, **kwargs):
    """
    Log a message at the WARNING level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.warning(message, *args, **kwargs)


def warning(message: str | dict, *args, **kwargs):
    """
    Log a message at the WARNING level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )
    logger.warning(message, *args, **kwargs)


def status(code: str | int, reason: str, *args, **kwargs):
    """
    Log a message at the STATUS level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        code (str): _description_
        reason (str): The status message
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    module_name, function_name, _, _ = get_caller_info()
    logger = getLogger(
        get_logger_identity(module=module_name, function=function_name, **kwargs)
    )

    reason = "" if reason is None else reason

    if code is None:
        code = 200

    logger.status(code, reason, *args, **kwargs)
