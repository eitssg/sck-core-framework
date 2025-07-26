"""
This module is the Core-Automation logging module providing a custom logger that can log messages as
JSON objects, status messages, and trace messages.
"""

from typing import Any

from datetime import datetime
import json
import logging
from collections import OrderedDict
import textwrap

from logging import NOTSET, FATAL, WARN, CRITICAL, DEBUG, INFO, WARNING, ERROR

import core_framework as util

# Default formats for the log messages
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
""":const DEFAULT_DATE_FORMAT: The default format for dates in log messages."""
DEFAULT_LOG_FORMAT = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
""":const DEFAULT_LOG_FORMAT: The default format for log messages."""

# Custom log levels not supported by the logging module
MSG = 70
""":const MSG: Custom log level for simple messages."""
STATUS = 60
""":const STATUS: Custom log level for status updates."""
TRACE = 5
""":const TRACE: Custom log level for detailed trace messages."""

# In the logging object, all levels exist, here are some custom ones:
logging.addLevelName(MSG, "MSG")
logging.addLevelName(FATAL, "FATAL")
logging.addLevelName(WARN, "WARN")
logging.addLevelName(STATUS, "STATUS")
logging.addLevelName(TRACE, "TRACE")

# Attributes of the log message when the output is set to JSON
LOG_DETAILS = "Details"
""":const LOG_DETAILS: Key for the 'Details' field in a JSON log entry."""
LOG_STATUS = "Status"
""":const LOG_STATUS: Key for the 'Status' field in a JSON log entry."""
LOG_MESSAGE = "Message"
""":const LOG_MESSAGE: Key for the 'Message' field in a JSON log entry."""
LOG_REASON = "Reason"
""":const LOG_REASON: Key for the 'Reason' field in a JSON log entry."""
LOG_RESOURCE = "Resource"
""":const LOG_RESOURCE: Key for the 'Resource' field in a JSON log entry."""
LOG_TIMESTAMP = "Timestamp"
""":const LOG_TIMESTAMP: Key for the 'Timestamp' field in a JSON log entry."""
LOG_TYPE = "Type"
""":const LOG_TYPE: Key for the 'Type' field in a JSON log entry."""
LOG_SCOPE = "Scope"
""":const LOG_SCOPE: Key for the 'Scope' field in a JSON log entry."""

# Future - Not in use yet
ENV_LOG_GROUP = "LOG_GROUP"
""":const ENV_LOG_GROUP: Environment variable for the log group name."""
ENV_LOG_STREAM = "LOG_STREAM"
""":const ENV_LOG_STREAM: Environment variable for the log stream name."""

# Attributes for the extra: Mapping[str, object] parameter when calling the log methods
L_STATUS_LABEL = "status_label"
""":const L_STATUS_LABEL: Key for the 'status_label' extra parameter."""
L_STATUS = "status"
""":const L_STATUS: Key for the 'status' extra parameter."""
L_REASON = "reason"
""":const L_REASON: Key for the 'reason' extra parameter."""
L_MESSAGE = "message"
""":const L_MESSAGE: Key for the 'message' extra parameter."""
L_DETAILS = "details"
""":const L_DETAILS: Key for the 'details' extra parameter."""
L_TYPE = "type"
""":const L_TYPE: Key for the 'type' extra parameter."""
L_SCOPE = "scope"
""":const L_SCOPE: Key for the 'scope' extra parameter."""
L_IDENTITY = "identity"
""":const L_IDENTITY: Key for the 'identity' extra parameter."""
L_PRN = "prn"
""":const L_PRN: Key for the 'prn' extra parameter."""


class CoreLogFormatter(logging.Formatter):
    """Base Class for the CoreLogJsonFormatter and CoreLogTextFormatter classes."""

    def __init__(self, fmt: str, datefmt: str):
        """Initialize the formatter with the specified format and date format.

        :param fmt: Message Format.
        :type fmt: str
        :param datefmt: Datetime Format.
        :type datefmt: str
        """
        super().__init__(fmt, datefmt)

    def format_datetime(self, t: datetime, date_format: str | None = None) -> str:
        """Formats a datetime object to a string using the specified format.

        If no format is specified, the default format is used.
        The default format is "%Y-%m-%d %H:%M:%S" if date_format is None.

        :param t: The datetime object to format.
        :type t: datetime
        :param date_format: The date format to use. Defaults to None.
        :type date_format: str or None, optional
        :return: The formatted date string.
        :rtype: str
        """
        return t.strftime(date_format or DEFAULT_DATE_FORMAT)

    def formatTime(
        self, record: logging.LogRecord, date_format: str | None = None
    ) -> str:  # NOSONAR: python:S100
        """Extracts the "created" field from the LogRecord and converts it to a datetime string.

        If date_format is not specified, the default format is used.

        :param record: The log record object.
        :type record: logging.LogRecord
        :param date_format: The format to use for the datetime. Defaults to None.
        :type date_format: str or None, optional
        :return: The formatted datetime string.
        :rtype: str
        """
        t = datetime.fromtimestamp(record.created)
        return self.format_datetime(t, date_format or self.datefmt)

    def formatMessage(self, record) -> str:
        """Formats the message from a record.

        :param record: The log record.
        :return: The formatted message.
        :rtype: str
        """
        return super().formatMessage(record)

    @staticmethod
    def replace_holders(message: str, args) -> tuple[str, tuple]:
        """Replace the {} place holders in the message with the values in the args tuple.

        If there are more values in the args tuple than there are {} place holders
        in the message, then the remaining values are returned in a tuple.

        :param message: The message to replace the place holders in.
        :type message: str
        :param args: The values to replace the place holders with.
        :type args: tuple
        :return: A tuple of the message and a tuple of unused values.
        :rtype: tuple
        """
        if args:
            count = message.count("{}")
            # If there are more "{}" strings than there are values in the args tuple, then we need to add empty strings to args
            if count > len(args):
                args = args + tuple([""] * (count - len(args)))
            # Replace the "{}" strings with the values in the args tuple
            message = message.format(*args)
            # Return the message and any unused values in the args tuple
            unused_values = args[count:]
        else:
            unused_values = ()
        return message, unused_values

    @staticmethod
    def add_details(record: logging.LogRecord, data: dict) -> None:
        """Add the "Details" property to the fields.

        This is called by the emit() method.

        :param record: The log record object.
        :type record: logging.LogRecord
        :param data: The dictionary of data to add to the record object.
        :type data: dict
        """
        if hasattr(record, L_DETAILS):
            details = getattr(record, L_DETAILS)
        else:
            details = {}
        if isinstance(data, dict):
            details.update(data)
        else:
            details = data
        setattr(record, L_DETAILS, details)


class CoreLogTextFormatter(CoreLogFormatter):
    """Text Formatter for the CoreLogger class that outputs a log message as standard text."""

    def __init__(self, text_format: str | None = None, datefmt: str | None = None):
        """Initializes the formatter with the specified format and date format.

        :param text_format: message format.
        :type text_format: str, optional
        :param datefmt: datetime format.
        :type datefmt: str, optional
        """
        if not text_format:
            text_format = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
        if not datefmt:
            datefmt = DEFAULT_DATE_FORMAT

        super().__init__(text_format, datefmt)

    @staticmethod
    def represent_ordereddict(dumper: Any, ordered: OrderedDict) -> Any:
        """Represents an OrderedDict as a dict for YAML dumping.

        :param dumper: The YAML dumper.
        :type dumper: Any
        :param ordered: The OrderedDict to represent.
        :type ordered: OrderedDict
        :return: The dictionary representation.
        :rtype: Any
        """
        items = dict(ordered)  # translate the OrderedDict into a dict
        return dumper.represent_dict(items)

    def format(self, record: logging.LogRecord) -> str:
        """Formats the record object into a string.

        ``record.details`` will be translated to YAML format and the generated
        string will be appended to the end of the message.

        :param record: The logger record object.
        :type record: logging.LogRecord
        :return: A string to output to the log.
        :rtype: str
        """
        # If for some reason record.args is not a tuple, make it one.  This happens if the original
        # tuple had only one element that is also a list (or dictionary)
        if not isinstance(record.args, tuple):
            record.args = (record.args,)

        if (
            record.levelno == STATUS
            and hasattr(record, "status")
            and hasattr(record, "reason")
        ):
            record.msg = f"{record.status} {record.reason}"

        # The user can send a list of replacement values if the "msg" contains "{}"
        # place_holders.
        record.msg, record.args = self.replace_holders(record.msg, record.args)

        if len(record.args) > 0 and isinstance(record.args[0], dict):
            self.add_details(record, record.args[0])
            record.args = record.args[1:]

        if hasattr(record, L_SCOPE):
            scope = getattr(record, L_SCOPE)
            if scope:
                record.msg = f"{record.msg} ({scope})"

        data = super().format(record)

        if hasattr(record, L_DETAILS):
            details = getattr(record, L_DETAILS)
            if details and (
                isinstance(details, dict)
                or isinstance(details, OrderedDict)
                or isinstance(details, list)
            ):
                data = data + "\n" + self._indent_yaml(details)

        return data

    def _indent_yaml(self, data: dict, indent=4) -> str:
        """Indents a dictionary as a YAML string.

        :param data: The dictionary to format.
        :type data: dict
        :param indent: The number of spaces to indent. Defaults to 4.
        :type indent: int, optional
        :return: The indented YAML string.
        :rtype: str
        """
        yaml_str = util.to_yaml(data).rstrip("\n")
        return textwrap.indent(yaml_str, " " * indent)

    def details(self, record: logging.LogRecord, content: str) -> str:
        """Returns a reformatted string based on the content of the log message.

        First, content may be a string with multiple lines. Each line is formatted
        and printed to the console. For example, the message:

        .. code-block:: text

            this is a test
            of a message
            with multiple
            lines

        Will be output to the log as:

        .. code-block:: text

            2024-01-01 12:00:00 [root] [INFO] this is a test
            2024-01-01 12:00:00 [root] [INFO] of a message
            2024-01-01 12:00:00 [root] [INFO] with multiple
            2024-01-01 12:00:00 [root] [INFO] lines

        :param record: The logging log record object.
        :type record: logging.LogRecord
        :param content: The text to reformat.
        :type content: str
        :return: a string of formatted output lines.
        :rtype: str
        """
        lines = content.split("\n")

        # Remove empty lines from the end of the stream
        while lines and (lines[-1] == "" or lines[-1] is None):
            lines.pop()
        data = ""
        # Format each line and print it to the console
        for line in lines:
            record.msg = line
            data = data + "\n" + super().format(record)
        return data


class CoreLogJsonFormatter(CoreLogFormatter):
    """JSON Formatter for the CoreLogger class that outputs a log message as a JSON object."""

    def __init__(self, text_format: str | None = None, datefmt: str | None = None):
        """Initializes the formatter with the specified format and date format.

        :param text_format: Message format.
        :type text_format: str, optional
        :param datefmt: datetime format.
        :type datefmt: str, optional
        """
        if not text_format:
            text_format = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
        if not datefmt:
            datefmt = DEFAULT_DATE_FORMAT

        super().__init__(text_format, datefmt)

    @staticmethod
    def set_element(
        data: dict, record: logging.LogRecord, key: str, alternate: str | None = None
    ):
        """Adds an element to the data dictionary if it exists in the record object.

        :param data: The dictionary to add the element to.
        :type data: dict
        :param record: The log record object to extract the element from.
        :type record: logging.LogRecord
        :param key: The key to add to the data dictionary.
        :type key: str
        :param alternate: An alternate key to use if the primary key does not exist. Defaults to None.
        :type alternate: str or None, optional
        """
        value = None

        # If the alternate exists, use it
        if alternate:
            value = getattr(record, alternate, None)

        # If the alternate doesn't exist, try the key
        if value is None:
            value = getattr(record, key, None)

        # If the value is not None, add it to the data dictionary
        if value is not None:
            data[key] = value

    def format(self, record: logging.LogRecord) -> str:
        """Formats the record object into a JSON string to be output to the log.

        The JSON object will contain the following fields:

        .. code-block:: json

            {
                "@timestamp": "2024-01-01T12:00:00.000Z",
                "log.logger": "my-logger",
                "log.level": "INFO",
                "status": "COMPILE_COMPLETE",
                "reason": "Compile Complete",
                "message": "This is a test message",
                "scope": "build",
                "file": "test.py",
                "line": 10,
                "function": "my_function",
                "context": {
                    "prn": "prn:core:automation:master:1.0.0"
                }
            }

        :param record: The log record object.
        :type record: logging.LogRecord
        :return: The formatted JSON string.
        :rtype: str
        """
        # If for some reason record.args is not a tuple, make it one.  This happens if the original
        # tuple had only one element that is also a list (or dictionary)
        if not isinstance(record.args, tuple):
            record.args = (record.args,)

        if (
            record.levelno == STATUS
            and hasattr(record, "status")
            and hasattr(record, "reason")
        ):
            record.msg = f"{record.status} {record.reason}"

        # The user can send a list of replacement values if the "msg" contains "{}"
        # place_holders.
        record.msg, record.args = self.replace_holders(record.msg, record.args)

        if len(record.args) > 0 and isinstance(record.args[0], dict):
            self.add_details(record, record.args[0])
            record.args = record.args[1:]

        if hasattr(record, L_SCOPE):
            scope = getattr(record, L_SCOPE)
            if scope:
                record.msg = f"{record.msg} ({scope})"

        timestamp = datetime.fromtimestamp(record.created)
        json_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        data: dict = OrderedDict([("@timestamp", json_timestamp)])

        self.set_element(data, record, "log.logger", "name")
        self.set_element(data, record, "log.level", "levelname")
        self.set_element(data, record, "status", "status")
        self.set_element(data, record, "reason", "reason")
        self.set_element(data, record, "message", "msg")
        self.set_element(data, record, "scope", "scope")
        self.set_element(data, record, "file", "filename")
        self.set_element(data, record, "line", "lineno")
        self.set_element(data, record, "function", "funcName")
        self.set_element(data, record, "context", "details")

        output = json.dumps(data, default=str)

        return output


class CoreLoggerHandler(logging.Handler):
    """This is the core logging handler that does special things with messages and arguments.

    There are two types of formatters used by this handler: The CoreLogJsonFormatter
    and the CoreLogTextFormatter.

    Which formatter is used is determined by the LOG_AS_JSON environment variable.
    If it's set to 'true' (case insensitive), then the CoreLogJsonFormatter is used.
    """

    formatter: CoreLogFormatter

    def __init__(self, name: str, **kwargs):
        """Initialize a new instance of the CoreLoggerHandler class.

        You can pass level in kwargs as the following is executed:

        .. code-block:: python

            level = kwargs.get("level", NOTSET)

        :param name: The name of the handler.
        :type name: str
        :param kwargs: Additional keyword arguments to pass to the handler.
        :type kwargs: Any
        """
        super().__init__(level=kwargs.get("level", NOTSET))
        self.name = name

    def emit(self, record) -> None:
        """Emit the log message to the console.

        This is the method that is called by the logging framework to output the log message.
        This is almost identical to the standard emit() however there is some special
        handling for STATUS messages.

        :param record: The log record object.
        :type record: logging.LogRecord
        """
        if self.formatter:
            print(self.formatter.format(record))
        else:
            print(record.getMessage())


class CoreLogger(logging.Logger):
    """CoreLogger is a special logger that provides additional features.

    Features include the ability to log messages as JSON objects, the ability to
    log status messages, and the ability to log trace messages.

    The primary feature of this logger is that it overrides all logging methods
    (log.debug, log.info, log.error, etc) and accepts a ``**kwargs``
    argument that will be used to determine the identity of the logger.

    The flow looks like:

    .. code-block:: python

        log.info("This is a message", identity="my-identity")

        # 1. identity = kwargs.get("identity", None)
        # 2. logger = logging.getLogger(identity)
        # 3. logger.info("This is a message", **kwargs)

    The magic is in the handler and is set in the constructor of this class.
    If you want more handlers, you will need to add them after you instantiate
    the logger with getLogger().

    See CoreLoggerHandler for more information.

    :param name: The name of the logger.
    :type name: str
    :param level: The log level. Defaults to NOTSET.
    :type level: int, optional
    """

    def __init__(self, name: str, level: int = NOTSET):
        super().__init__(name, level=level)

    def setLevel(self, level: int | str) -> None:
        """Special function to set the level of the logger and all of its handlers.

        :param level: The loglevel to set.
        :type level: int or str
        """
        super().setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)

    def core_log(
        self, level: int, message: str | dict | None, args: tuple, **kwargs
    ) -> None:
        """This is a duplicate of logging.Logger._log() but with a modified signature.

        It replaces fixed parameters with ``**kwargs`` so we can convert both the
        message and the kwargs to extra data, allowing the caller to submit
        arbitrary meta-data in the call to the logger.

        The message can have replacement strings {} in the string and pass ``args``
        tuples to replace them.

        Examples:

        .. code-block:: python

            log.debug("This is a {} message", "test")
            log.debug("This is a {} message", "test", details={"key": "value"}, identity="my-identity")

        .. warning::

            The current customizations and coding increase the stack_depth of the logger.
            In order to get the correct module and line number of your log message,
            be aware that the default stacklevel is 4.

        :param level: The loglevel.
        :type level: int
        :param message: The message to log.
        :type message: str or dict or None
        :param args: A tuple of replacement values for the message.
        :type args: tuple
        :param kwargs: Elements to add to the log record as extra data.
        :type kwargs: Any
        """
        exc_info = kwargs.pop("exc_info", None)
        extra = kwargs.pop("extra", {})
        stack_info = kwargs.pop("stack_info", False)
        stacklevel = kwargs.pop("stacklevel", 4)

        # If the message is a dictionary, then we need to move the message to the extra data.
        if isinstance(message, dict):
            for k, v in message.items():
                extra[k] = v
                if k.lower() == L_MESSAGE:
                    message = v

        # if the kwargs data contains a message attribute, then we need to move it to the message field overwriting any other message.
        # and move all kwargs to the extra data.
        while len(kwargs) > 0:
            k, v = kwargs.popitem()
            if k.lower() == L_MESSAGE:
                message = v
            else:
                extra[k.lower()] = v

        self._log(level, message, args, exc_info, extra, stack_info, stacklevel)

    def msg(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """Outputs a simple message to the log in the 'MSG' level.

        :param message: The message to output.
        :type message: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        self.core_log(MSG, message, args, **kwargs)

    def status(self, code: str | int, reason: str, *args: Any, **kwargs: Any) -> None:
        """Outputs a status message to the log in the 'STATUS' level.

        Supplying a code and reason will output a message in the following format:
        ``message = f"{code} {reason}"``

        Code and Reason are added as metadata so that JSON formatters can use them individually.

        :param code: The 'code' of the message.
        :type code: str or int
        :param reason: The 'reason' of the message.
        :type reason: str
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(STATUS):
            s = str(code)
            r = reason
            if L_DETAILS in kwargs:
                details = kwargs.get(L_DETAILS)
                if isinstance(details, dict):
                    if LOG_STATUS in details:
                        s = details.pop(LOG_STATUS)
                        if LOG_REASON in details:
                            r = details.pop(LOG_REASON)
            # A hack for some legacy errors
            kwargs[L_STATUS] = kwargs.get(L_STATUS, kwargs.get("status_label", s))
            kwargs[L_REASON] = kwargs.get(L_REASON, r)
            self.core_log(STATUS, None, args, **kwargs)

    def trace(self, message, *args, **kwargs) -> None:
        """Log a message with severity 'TRACE'.

        :param message: The message to output.
        :type message: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(TRACE):
            self.core_log(TRACE, message, args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Log 'msg' with severity 'DEBUG'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g. ``logger.debug("...", exc_info=True)``

        :param msg: The message to output.
        :type msg: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(DEBUG):
            self.core_log(DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log 'msg' with severity 'INFO'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g. ``logger.info("...", exc_info=True)``

        :param msg: The message to output.
        :type msg: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(INFO):
            self.core_log(INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log 'msg' with severity 'WARNING'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g. ``logger.warning("...", exc_info=True)``

        :param msg: The message to output.
        :type msg: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(WARNING):
            self.core_log(WARNING, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log 'msg' with severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g. ``logger.error("...", exc_info=True)``

        :param msg: The message to output.
        :type msg: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(ERROR):
            self.core_log(ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log 'msg' with severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g. ``logger.critical("...", exc_info=True)``

        :param msg: The message to output.
        :type msg: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if self.isEnabledFor(CRITICAL):
            self.core_log(CRITICAL, msg, args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Log 'msg' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g. ``logger.log(level, "...", exc_info=True)``

        :param level: The numeric log level.
        :type level: int
        :param msg: The message to output.
        :type msg: Any
        :param args: Additional arguments to replace in the message.
        :type args: Any
        :param kwargs: Additional keyword arguments to pass to the logger.
        :type kwargs: Any
        """
        if not isinstance(level, int):
            raise TypeError("level must be an integer")

        if self.isEnabledFor(level):
            self.core_log(level, msg, args, **kwargs)
