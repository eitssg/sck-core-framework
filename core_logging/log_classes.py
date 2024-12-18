"""
This module is the Core-Automation logging module providing a custom logger that can log messages as
JSON objects, status messages, and trace messages.
"""

from typing import Any

from datetime import datetime
import io
import json
import logging
import os
from collections import OrderedDict
from ruamel import yaml

from logging import NOTSET, FATAL, WARN, CRITICAL, DEBUG, INFO, WARNING, ERROR

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Custom log levels not supported by the logging module
MSG = 70
STATUS = 60
TRACE = 5

# In the logging object, all levels exist, here are some custom ones:
logging.addLevelName(MSG, "MSG")
logging.addLevelName(FATAL, "FATAL")
logging.addLevelName(WARN, "WARN")
logging.addLevelName(STATUS, "STATUS")
logging.addLevelName(TRACE, "TRACE")

# Attributes of the log message when the output is set to JSON
LOG_DETAILS: str = "Details"
""" \\- "Details" """
LOG_STATUS: str = "Status"
""" \\- "Status" """
LOG_MESSAGE: str = "Message"
""" \\- "Message" """
LOG_REASON: str = "Reason"
""" \\- "Reason" """
LOG_RESOURCE: str = "Resource"
""" \\- "Resource" """
LOG_TIMESTAMP: str = "Timestamp"
""" \\- "Timestamp" """
LOG_TYPE: str = "Type"
""" \\- "Type" """
LOG_SCOPE: str = "Scope"
""" \\- "Scope" """

# Attributes for the extra: Mapping[str, object] parameter when calling the log methods
L_STATUS_LABEL: str = "status_label"
""" \\- "status_label" """
L_STATUS: str = "status"
""" \\- "status" """
L_REASON: str = "reason"
""" \\- "reason" """
L_MESSAGE: str = "message"
""" \\- "message" """
L_DETAILS: str = "details"
""" \\- "details" """
L_TYPE: str = "type"
""" \\- "type" """
L_SCOPE: str = "scope"
""" \\- "scope" """
L_IDENTITY: str = "identity"
""" \\- "identity" """
L_PRN: str = "prn"
""" \\- "prn" """


class CoreLogFormatter(logging.Formatter):
    """Base Class for the CoreLogJsonFormatter and CoreLogTextFormatter classes."""

    def __init__(self, fmt: str, datefmt: str):
        """
        Initialize the formatter with the specified format and date format.

        Args:
            fmt (str): Message Format
            datefmt (str): Datetime Format
        """
        super().__init__(fmt, datefmt)

    def format_datetime(self, t: datetime, date_format: str | None = None) -> str:
        """
        Formates a datetime object to a string using the specified format.  If no format is specified, the default format is used.

        The default format is "%Y-%m-%d %H:%M:%S" if date_format is None.

        Args:
            t (datetime): The datetime object to format.
            date_format (str | None, optional): The date format to use. Defaults to None.

        Returns:
            str: The formatted date string.
        """
        return t.strftime(date_format or DEFAULT_DATE_FORMAT)

    def formatTime(
        self, record: logging.LogRecord, date_format: str | None = None
    ) -> str:  # NOSONAR: python:S100
        """
        Exracts the "created" field from the logging.LogRecord object and converts it to a datetime object.
        to be used as the timestamp of the log message.

        If date_format is not specified, the default format is used.

        Args:
            record (logging.LogRecord): The log record object.
            date_format (str | None, optional): The format to use for the datetime. Defaults to None.

        Returns:
            str: The formatted datatime string.
        """
        t = datetime.fromtimestamp(record.created)
        return self.format_datetime(t, date_format or self.datefmt)


class CoreLogTextFormatter(CoreLogFormatter):
    """Text Formatter for the CoreLogger class that outputs a log message as standard text."""

    def __init__(self, fmt: str, datefmt: str):
        """
        Initializes the formatter with the specified format and date format.

        Args:
            fmt (str): message format
            datefmt (str): datetime format
        """
        super().__init__(fmt, datefmt)
        self.yaml = yaml.YAML(typ="safe")
        self.yaml.default_flow_style = False
        self.yaml.indent(mapping=3, sequence=3, offset=3)
        self.yaml.representer.add_representer(OrderedDict, self.represent_ordereddict)

    @staticmethod
    def represent_ordereddict(dumper: Any, ordered: OrderedDict) -> Any:
        items = dict(ordered)  # translate the OrderedDict into a dict
        return dumper.represent_dict(items)

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the record object into a string.  record.details will be translated to YAML
        format and the generated string will be appended to the end of the.

        Args:
            record (logging.LogRecord): The logger record object

        Returns:
            str: A string to output to the log.
        """
        if hasattr(record, L_SCOPE):
            scope = getattr(record, L_SCOPE)
            if scope:
                record.msg = f"{record.msg} ({scope})"

        data = super().format(record)

        if hasattr(record, L_DETAILS):
            details = getattr(record, L_DETAILS)
            if details and isinstance(details, dict):
                data = data + "\n" + self._dump_ordered_yaml(details)

        return data

    def _dump_ordered_yaml(self, data: dict) -> str:
        s = io.StringIO()
        self.yaml.dump(data, s)
        # Add additional indentation
        indented_yaml = "\n".join("    " + line for line in s.getvalue().splitlines())
        return indented_yaml

    def details(self, record: logging.LogRecord, content: str) -> str:
        """
        Returns a reformatted string based o the content of the log message.

        First, content may be a string with multiple lines.  Each line is formatted and printed to the console.
        such that the message:

        .. code-block:: shell

            this is a test
            of a message
            with multiple
            lines

        Will be output to the log as:

        .. code-block:: shell

            2024-01-01 12:00:00 [root] [INFO] this is a test
            2024-01-01 12:00:00 [root] [INFO] of a message
            2024-01-01 12:00:00 [root] [INFO] with multiple
            2024-01-01 12:00:00 [root] [INFO] lines

        Args:
            record (logging.LogRecord): The logging log recrd object.
            content (str): The text to reformat.

        Returns:
            str: a string of formatted output lines.
        """
        lines = content.split("\n")

        # Remove empty lines from the end of the stream
        while lines and (lines[-1] == "" or lines[-1] is None):
            lines.pop()
        data = ""
        # Format each line and print it on the console
        for line in lines:
            record.msg = line
            data = data + "\n" + super().format(record)
        return data


class CoreLogJsonFormatter(CoreLogFormatter):
    """JSON Formatter for the CoreLogger class that outputs a log message as a JSON object."""

    def __init__(self, text_format: str, datefmt: str):
        """
        Initializes the formatter with the specified format and date format.

        Args:
            text_format (str): Message format
            datefmt (str): datetime format
        """
        super().__init__(text_format, datefmt)

    @staticmethod
    def set_element(
        data: dict, record: logging.LogRecord, key: str, element: str | None = None
    ):
        if element:
            value = getattr(record, element, None)
        if value is None:
            value = getattr(record, key, None)
        if value is not None:
            data[key] = value

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the record object into a JSON string to be output to the log.

        The JSON object will contain the following fields:

        .. code-block:: json

            {
                "Timestamp": "2024-01-01 12:00:00",
                "Type": "INFO",
                "Status": "COMPILE_COMPLETE",
                "Reason": "Compile Complete",
                "Message": "This is a test message",
                "Details": {
                    "prn": "prn:core:automation:master:1.0.0",
                },
                "Scope": "build",
                "Resource": "my-resource-component in the prn"
            }

        The Details field can be any arbitrary dictionary that is passed in the log message.

        Args:
            record (logging.LogRecord): The log record object.

        """
        dtm = self.format_datetime(datetime.fromtimestamp(record.created), self.datefmt)
        data: dict = OrderedDict([(LOG_TIMESTAMP, dtm)])
        self.set_element(data, record, LOG_TYPE, "levelname")
        self.set_element(data, record, LOG_STATUS)
        self.set_element(data, record, LOG_REASON)
        self.set_element(data, record, LOG_MESSAGE, "msg")
        self.set_element(data, record, LOG_DETAILS)
        self.set_element(data, record, LOG_SCOPE)
        self.set_element(data, record, LOG_RESOURCE, "name")
        output = json.dumps(data, default=str)
        return output


class CoreLoggerHandler(logging.Handler):
    """
    This is the core logging handler that does special things with messages and arguments.

    There are two types of formatters used by this handler.  The CoreLogJsonFormatter and the CoreLogTextFormatter.

    Which formatter is used is determined by the LOG_AS_JSON environment variable.  If it's set to 'true' (case insensitive),
    then the CoreLogJsonFormatter is used.

    """

    formatter: CoreLogFormatter

    def __init__(self, name: str, **kwargs):
        """
        Initialize a new instance of the CoreLoggerHandler class.

        You can pass level in kwargs as the following is executed:

        .. code-block:: python

            level = kwargs.get("level", NOTSET)

        Args:
            name (str): The name of the handler.
            **kwargs: Additional keyword arguments to pass to the handler.
        """

        super().__init__(level=kwargs.get("level", NOTSET))

        self.name = name

        date_fmt = kwargs.get("datefmt", DEFAULT_DATE_FORMAT)
        msg_fmt = kwargs.get(
            "fmt", "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
        )

        # default logging to text formatter unless LOG_AS_JSON is set to true
        if os.environ.get("LOG_AS_JSON", "false").lower() == "true":
            self.formatter = CoreLogJsonFormatter(msg_fmt, date_fmt)
        else:
            self.formatter = CoreLogTextFormatter(msg_fmt, date_fmt)

    def emit(self, record) -> None:
        """
        Emit the log message to the console.  This is the method that is called by the logging framework to output the log message.

        This is almost identicl to the standard emit() however there is some special handling for STATUS messages.

        Args:
            record (dict): The log record object.
        """
        try:
            # If for some reason record.args is not a tuple, make it one.  This happens if the original
            # tuple had only one element that is also a list (or dictionary)
            if not isinstance(record.args, tuple):
                record.args = (record.args,)

            if record.levelno == STATUS:
                record.msg = f"{record.status} {record.reason}"

            # The user can send an list of replacement values if the "msg" contains "%s"
            # place_holders.
            record.msg, record.args = self.replace_holders(record.msg, record.args)

            # The FIRST argument after the replacement values goes into "details".  But ONLY
            # if it's a dictionary.  Else skip it.
            if len(record.args) > 0 and isinstance(record.args[0], dict):
                self.add_details(record, record.args[0])
                record.args = record.args[1:]

            # fix the message if it exists.  The "msg" was modified if it had replacement %s characters.
            if self.formatter:
                print(self.formatter.format(record))
            else:
                print(record.getMessage())

        except Exception as e:
            print(f"Error writing to log file: {str(e)}")

    @staticmethod
    def replace_holders(message: str, args: tuple[Any]) -> tuple[str, tuple]:
        """
        Replace the %s place holders in the message with the values in the args tuple.  If there are more values in the args tuple
        than there are %s place holders in the message, then the remaining values are returned in a list.

        Args:
            message (str): The message to replace the place holders in.
            args (tuple): The values to replace the place holders with.

        Returns:
            tuple: A tuple of the message and a list of unused values.
        """
        if message and args and len(args) > 0:
            unused_values = []
            for value in args:
                if "%s" in message:
                    message = (
                        message.replace("%s", str(value), 1)
                        if value
                        else message.replace("%s", "", 1)
                    )
                else:
                    unused_values.append(value)
        else:
            unused_values = list(args)
        return message, tuple(unused_values)

    @staticmethod
    def add_details(record: logging.LogRecord, data: dict) -> None:
        """
        Add the "Details" property to the fields.  This is called by the emit() method.

        Args:
            record (logging.LogRecord): The log record object.
            data (dict): The dictionary of data to add to the record object.

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


class CoreLogger(logging.Logger):
    """
    CoreLogger is a special logger that is designed to work with the standard python logger but provides some additional features.

    Feetures include the ability to log messages as JSON objects, the ability to log status messages, and the ability to log trace messages.

    The primary feature of this logger is that it overrides all logging methods (log.debug, log.info, log.error, etc) and accepts a \\*\\*kwargs
    argument that will be used to determne the identity of the logger.

    The flow looks like:

    log.info("This is a message", identity="my-identity")

        1.  identity = kwargs.get("identity", None)
        2.  logger = logging.getLogger(idendity)
        3.  logger.info("This is a message", \\*\\*kwargs)

    Pretty simple. The magic is in the handler and is set in the contructor of this class. If you want more handlers, you will
    need to add them after you instantiate the logger with getLogger()

    See CoreLoggerHandler for more information.

    """

    def __init__(self, name: str, level: int = NOTSET):
        """
        Initialize the logger with the specified name and level.  Also tells the logging framework to use the CoreLoggerHandler class for all handlers.

        Args:
            name (_type_): _description_
            level (_type_, optional): _description_. Defaults to NOTSET.
        """
        super().__init__(name, level=level)
        self.propagate = False
        self.handlers = [CoreLoggerHandler(name, level=level)]

    def setLevel(self, level: int | str) -> None:
        """
        Special function to set the level of the logger and all of the handlers.

        Args:
            level (int): The loglevel to set
        """
        super().setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)

    def core_log(
        self, level: int, message: str | dict | None, args: tuple, **kwargs
    ) -> None:
        """
        This is a duplicate of logging.Logger._log() but the signature differs with the default by removing fixed parameters
        and replacing them with \\*\\*kwargs so we can convert both the message and the kwargs to extra data allowing the caller
        to submit arbitrary meta-data in the call to the logger.

        The message can have replacement strings %s symbol in the string and pass (args) tuples to replace the %s symbols.

            Examples:

            .. code-block:: python

                log.debug("This is a %s message", "test")
                log.debug("This is a %s message", "test", details={"key": "value"}, identity="my-identity")

        Args:
            level (int): The loglevel
            message (str): The message to log.
            args (tuple): A list of replacement values for the message.
            **kwargs: Elements to add to the log.record as exta data.

        """
        exc_info = kwargs.pop("exec_info", None)
        extra = kwargs.pop("extra", {})
        stack_info = kwargs.pop("stack_info", False)
        stacklevel = kwargs.pop("stacklevel", 1)

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

        super()._log(level, message, args, exc_info, extra, stack_info, stacklevel)

    def msg(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """
        Outputs a simple message to the log in the 'MSG' level.

        Args:
            message (Any): The message to output.
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        self.core_log(MSG, message, args, **kwargs)

    def status(self, code: str | int, reason: str, *args: Any, **kwargs: Any) -> None:
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
        """
        Log a message with severity 'TRACE'.

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if self.isEnabledFor(TRACE):
            self.core_log(TRACE, message, args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'DEBUG'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.debug("Houston, we have a %s", "thorny problem", exc_info=True)

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if self.isEnabledFor(DEBUG):
            self.core_log(DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.info("Houston, we have a %s", "notable problem", exc_info=True)

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if self.isEnabledFor(INFO):
            self.core_log(INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'WARNING'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.warning("Houston, we have a %s", "bit of a problem", exc_info=True)

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if self.isEnabledFor(WARNING):
            self.core_log(WARNING, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.error("Houston, we have a %s", "major problem", exc_info=True)

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if self.isEnabledFor(ERROR):
            self.core_log(ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.critical("Houston, we have a %s", "major disaster", exc_info=True)

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if self.isEnabledFor(CRITICAL):
            self.core_log(CRITICAL, msg, args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """
        Log 'msg % args' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "We have a %s", "mysterious problem", exc_info=True)

        Args:
            message (str): The message to output
            *args: Additional arguments to replace in the message.
            **kwargs: Additional keyword arguments to pass to the logger.
        """
        if not isinstance(level, int):
            raise TypeError("level must be an integer")

        if self.isEnabledFor(level):
            self.core_log(level, msg, args, **kwargs)
