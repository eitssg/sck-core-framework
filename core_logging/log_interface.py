""" This module provides the log helper functions for the core_logging library. Such as log.debug, log.error, log.warning, log.warn, log.fatal, log.critical, log.info, log.trace, log.message, etc.
"""

from threading import local
import os

import logging

from .log_classes import CoreLogger, L_IDENTITY, DEFAULT_DATE_FORMAT, INFO, L_PRN

default_level: int = logging._nameToLevel.get(os.getenv("LOG_LEVEL", "INFO"), INFO)

# Override the default logger class to use our custom logger class.
logging.root = CoreLogger(logging.WARNING)  # type: ignore
logging.Logger.root = logging.root
logging.setLoggerClass(CoreLogger)

# Configure logging
logging.basicConfig(
    level=default_level,
    format="%(message)s",
    datefmt=DEFAULT_DATE_FORMAT,
)

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


def getLevel(level: str) -> int:
    """
    Return the logging level for the specified level name.

    Args:
        level (str): The name of the logging level

    Returns:
        int: The logging level integer value
    """
    return logging._nameToLevel.get(level, default_level)


def setup(identity: str):
    """
    Initialize the logger with the specified identity.  The identity is a PRN (Pipeline Resource Name) or (Pipeline Reference Name/Number)
    and is in the format of "prn:portfolio:app:branch:build".  The identity is used to identify the source of the log message.

    The identity can actually be any string.  It is not validated.

    Args:
        identity (str): The PRN or identity of the logger.

    """
    _thread_local.default_identity = identity
    _thread_local.identity = identity


def set_identity(identity: str):
    """
    Hold an identity for the logger.  This is used to identify the source of the log message.  This value will be used if not specified in the log call

    Args:
        identity (str): The PRN or identity of the logger.
    """

    _thread_local.identity = identity


def get_identity() -> str:
    """
    Return the default identity for the logger.  This default identity is used to identify the source of the log message and will be used if not specified in the log call

    :return identity(str):  The default identity for the logger.
    """

    return _thread_local.identity or _thread_local.default_identity or ""


def reset_identity():
    """
    Deprecated: use the "getLogger()" method to get a logger with the specified identity..  This method is NOT thread safe.

    Resets the identity to the default identity that was established when the logger was setup with the setup() method.
    """
    _thread_local.identity = _thread_local.default_identity


def getLogger(name: str | None) -> CoreLogger:
    """
    Return a logging object with the specified name.

    Args:
        name (str | None): The name/identity of the logger

    Returns:
        CoreLogger: The logger object
    """
    logger: CoreLogger
    if name is None:
        logger = logging.getLogger()  # type: ignore
    else:
        logger = logging.getLogger(name)  # type: ignore

    return logger


def get_logger_identity(kwargs: dict) -> str | None:
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
    default_identity = _thread_local.identity or _thread_local.default_identity
    identity = kwargs.pop(L_IDENTITY, kwargs.get(L_PRN, default_identity))
    return identity


def log(level: int, message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the specified level.
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        level (int): The logging level (MSG, STATUS, TRACE, etc.)
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.log(level, message, *args, **kwargs)


def msg(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the MSG level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.msg(message, *args, **kwargs)


def trace(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the TRACE level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.trace(message, *args, **kwargs)


def debug(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the DEBUG level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.debug(message, *args, **kwargs)


def critical(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the CRITICAL level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.critical(message, *args, **kwargs)


def fatal(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the FATAL level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.fatal(message, *args, **kwargs)


def error(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the ERROR level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.error(message, *args, **kwargs)


def info(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the INFO level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.info(message, *args, **kwargs)


def warn(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the WARNING level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.warning(message, *args, **kwargs)


def warning(message: str | dict | None = None, *args, **kwargs):
    """
    Log a message at the WARNING level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        message (Union[str, dict], optional): The message to output. Defaults to None.
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    logger = getLogger(get_logger_identity(kwargs))
    logger.warning(message, *args, **kwargs)


def status(code: str | int | None = None, reason: str | None = None, *args, **kwargs):
    """
    Log a message at the STATUS level
    The log identity is taken from the kwargs parameter if it exists, else it's taken from the _identity variable.

    Args:
        code (str): _description_
        reason (str): The status message
        args (tuple): values used to replace the %s place holders in the message.
        kwargs: Name/Value pairs that will be added to the output. Defaults to None.
    """
    reason = "" if reason is None else reason

    if code is None:
        code = 200

    logger: CoreLogger = getLogger(get_logger_identity(kwargs))
    logger.status(code, reason, *args, **kwargs)
