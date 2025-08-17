"""Core Automation Logging Module with Custom JSON and Text Formatters.

This module provides a comprehensive logging system specifically designed for the
Core Automation framework. It supports both JSON and text output formats, custom
log levels for status and trace messages, and enhanced metadata handling for
structured logging in cloud environments.

Key Features:
    - **Dual Format Support**: JSON and text formatters for different environments
    - **Custom Log Levels**: MSG, STATUS, and TRACE levels beyond standard logging
    - **Metadata Enrichment**: Automatic context addition with scope and identity
    - **Template Processing**: Placeholder replacement with overflow handling
    - **Structured Output**: Consistent formatting for monitoring and analysis
    - **Stack Depth Awareness**: Proper source location tracking through custom stack levels

Components:
    - **CoreLogFormatter**: Base formatter with common functionality
    - **CoreLogTextFormatter**: Human-readable text output with YAML details
    - **CoreLogJsonFormatter**: Structured JSON output for log aggregation
    - **CoreLoggerHandler**: Custom handler for special message processing
    - **CoreLogger**: Enhanced logger with metadata and identity support

Integration:
    Designed to work seamlessly with cloud logging systems, monitoring tools,
    and the Core Automation framework's configuration and utility modules.

Log Levels:
    - **TRACE (5)**: Detailed trace information for debugging
    - **DEBUG (10)**: Standard debug information
    - **INFO (20)**: General information messages
    - **WARNING (30)**: Warning messages
    - **ERROR (40)**: Error messages
    - **CRITICAL (50)**: Critical error messages
    - **STATUS (60)**: Status update messages with code and reason
    - **MSG (70)**: Simple message output

Output Formats:
    The module supports two output formats controlled by environment configuration:
    - **Text Format**: Human-readable with YAML-formatted details
    - **JSON Format**: Structured output compatible with log aggregation systems

Thread Safety:
    All formatters and loggers are designed for safe concurrent access in
    multi-threaded environments and cloud execution contexts.
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
    """Base formatter class for Core Automation logging with common functionality.

    Provides shared functionality for both JSON and text formatters including
    datetime formatting, placeholder replacement, and metadata handling. This
    base class ensures consistent behavior across different output formats.

    The formatter handles template processing where messages can contain {}
    placeholders that are replaced with values from the args tuple, with
    proper overflow handling for unused arguments.

    Attributes:
        Inherits from logging.Formatter with enhanced functionality for
        template processing and metadata enrichment.
    """

    def __init__(self, fmt: str, datefmt: str):
        """Initialize the formatter with the specified format and date format.

        Args:
            fmt: Message format string for log output formatting.
            datefmt: Datetime format string for timestamp formatting.
        """
        super().__init__(fmt, datefmt)

    def format_datetime(self, t: datetime, date_format: str | None = None) -> str:
        """Format a datetime object to a string using the specified format.

        Provides consistent datetime formatting across all formatters with
        fallback to default format when none is specified.

        Args:
            t: The datetime object to format.
            date_format: The date format to use. If None, uses DEFAULT_DATE_FORMAT.

        Returns:
            The formatted date string in the specified format.
        """
        return t.strftime(date_format or DEFAULT_DATE_FORMAT)

    def formatTime(self, record: logging.LogRecord, date_format: str | None = None) -> str:  # NOSONAR: python:S100
        """Extract the created timestamp from LogRecord and convert to datetime string.

        Converts the timestamp from the log record to a formatted datetime string
        using either the specified format or the formatter's default date format.

        Args:
            record: The log record object containing the timestamp.
            date_format: The format to use for the datetime. If None, uses
                        the formatter's datefmt or DEFAULT_DATE_FORMAT.

        Returns:
            The formatted datetime string.
        """
        t = datetime.fromtimestamp(record.created)
        return self.format_datetime(t, date_format or self.datefmt)

    def formatMessage(self, record) -> str:
        """Format the message from a log record using the parent formatter.

        Delegates to the parent class formatMessage method while maintaining
        compatibility with the enhanced Core Automation logging features.

        Args:
            record: The log record containing the message to format.

        Returns:
            The formatted message string.
        """
        return super().formatMessage(record)

    @staticmethod
    def replace_holders(message: str, args) -> tuple[str, tuple]:
        """Replace {} placeholders in the message with values from the args tuple.

        Processes template strings by replacing {} placeholders with corresponding
        values from the args tuple. Handles cases where there are more or fewer
        placeholders than arguments gracefully.

        Args:
            message: The message string containing {} placeholders.
            args: Tuple of values to replace the placeholders with.

        Returns:
            A tuple containing the processed message string and any unused
            arguments from the args tuple.

        Behavior:
            - If more placeholders than args: Empty strings fill missing args
            - If more args than placeholders: Extra args returned as unused
            - If no args provided: Returns message unchanged with empty unused tuple
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
        """Add or update the details property on the log record.

        Merges additional detail data into the log record's details attribute,
        creating the attribute if it doesn't exist or updating it if it does.
        Used by formatters to enrich log records with metadata.

        Args:
            record: The log record object to modify.
            data: Dictionary of data to add to the record's details.

        Behavior:
            - Creates details attribute if it doesn't exist
            - Merges dict data into existing details if both are dicts
            - Replaces details completely if data is not a dict
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
    """Text formatter for human-readable log output with YAML details formatting.

    Produces human-readable log output with optional YAML-formatted detail
    sections. Designed for development environments and situations where
    logs need to be easily readable by humans rather than processed by
    automated systems.

    The formatter handles multi-line content by splitting it across multiple
    log entries, each with proper timestamp and metadata. Detail dictionaries
    are formatted as indented YAML for improved readability.

    Output Format:
        Standard log lines follow the pattern:
        TIMESTAMP [LOGGER] [LEVEL] MESSAGE

        When details are present, they are appended as indented YAML:
        TIMESTAMP [LOGGER] [LEVEL] MESSAGE
            key1: value1
            key2: value2
    """

    def __init__(self, text_format: str | None = None, datefmt: str | None = None):
        """Initialize the text formatter with format and date format strings.

        Args:
            text_format: Message format string. If None, uses standard format:
                        "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
            datefmt: Datetime format string. If None, uses DEFAULT_DATE_FORMAT.
        """
        if not text_format:
            text_format = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
        if not datefmt:
            datefmt = DEFAULT_DATE_FORMAT

        super().__init__(text_format, datefmt)

    @staticmethod
    def represent_ordereddict(dumper: Any, ordered: OrderedDict) -> Any:
        """Convert an OrderedDict to a regular dict for YAML dumping.

        Provides compatibility with YAML dumpers that may not handle
        OrderedDict objects directly by converting them to standard
        dictionaries while preserving content.

        Args:
            dumper: The YAML dumper instance.
            ordered: The OrderedDict to convert.

        Returns:
            Dictionary representation suitable for YAML dumping.
        """
        items = dict(ordered)  # translate the OrderedDict into a dict
        return dumper.represent_dict(items)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record into a human-readable text string.

        Processes the log record by handling placeholder replacement, status
        message formatting, scope addition, and detail formatting. The output
        is designed for human readability with proper indentation and structure.

        Args:
            record: The log record object to format.

        Returns:
            Formatted text string ready for output to console or file.

        Processing Steps:
            1. Normalize record.args to tuple format
            2. Handle STATUS level message formatting with status and reason
            3. Process placeholder replacement in message
            4. Extract details from first dict argument if present
            5. Add scope information to message if available
            6. Format base message using parent formatter
            7. Append YAML-formatted details if present
        """
        # If for some reason record.args is not a tuple, make it one.  This happens if the original
        # tuple had only one element that is also a list (or dictionary)
        if not isinstance(record.args, tuple):
            record.args = (record.args,)

        if record.levelno == STATUS and hasattr(record, "status") and hasattr(record, "reason"):
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
            if details and (isinstance(details, dict) or isinstance(details, OrderedDict) or isinstance(details, list)):
                data = data + "\n" + self._indent_yaml(details)

        return data

    def _indent_yaml(self, data: dict, indent=4) -> str:
        """Convert data to indented YAML string for readable detail formatting.

        Converts dictionary, OrderedDict, or list data to YAML format and
        indents it consistently for inclusion in log output. Used to make
        detail data human-readable while maintaining structure.

        Args:
            data: The data to format as YAML (dict, OrderedDict, or list).
            indent: Number of spaces to indent each line. Defaults to 4.

        Returns:
            Indented YAML string representation of the data.
        """
        yaml_str = util.to_yaml(data).rstrip("\n")
        return textwrap.indent(yaml_str, " " * indent)

    def details(self, record: logging.LogRecord, content: str) -> str:
        """Format multi-line content into separate log entries with timestamps.

        Takes content with multiple lines and formats each line as a separate
        log entry with full timestamp and metadata. Useful for formatting
        large blocks of text or command output while maintaining log structure.

        Args:
            record: The log record object containing metadata.
            content: Multi-line text content to format.

        Returns:
            Formatted string with each line as a separate log entry.

        Behavior:
            - Splits content on newline characters
            - Removes empty lines from the end
            - Formats each line as a complete log entry
            - Preserves timestamp and metadata for each line
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
    """JSON formatter for structured log output compatible with log aggregation systems.

    Produces structured JSON log entries that can be easily parsed by log
    aggregation systems, monitoring tools, and automated analysis systems.
    Each log entry is a complete JSON object with standardized field names
    and consistent structure.

    The formatter creates JSON objects with fields optimized for cloud logging
    systems and includes metadata like timestamps, source locations, and
    custom context information. Field names follow common conventions for
    compatibility with popular logging platforms.

    JSON Structure:
        Each log entry contains standardized fields including timestamp,
        logger information, level, message content, and optional metadata
        like scope, file location, and custom context data.
    """

    def __init__(self, text_format: str | None = None, datefmt: str | None = None):
        """Initialize the JSON formatter with format and date format strings.

        Args:
            text_format: Message format string (maintained for compatibility).
                        Defaults to standard format if None.
            datefmt: Datetime format string (used for internal processing).
                    Defaults to DEFAULT_DATE_FORMAT if None.

        Notes:
            The text_format parameter is maintained for compatibility but JSON
            output uses a fixed structure rather than template-based formatting.
        """
        if not text_format:
            text_format = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
        if not datefmt:
            datefmt = DEFAULT_DATE_FORMAT

        super().__init__(text_format, datefmt)

    @staticmethod
    def set_element(data: dict, record: logging.LogRecord, key: str, alternate: str | None = None):
        """Add an element to the JSON data dictionary if it exists in the log record.

        Conditionally adds fields to the JSON output by checking for their
        presence in the log record. Supports alternate field names for
        flexibility in field mapping and backwards compatibility.

        Args:
            data: The dictionary to add the element to.
            record: The log record object to extract the element from.
            key: The primary key to add to the data dictionary.
            alternate: Alternative record attribute name to check if primary
                      key is not found. Defaults to None.

        Behavior:
            - Checks alternate attribute first if provided
            - Falls back to primary key if alternate not found
            - Only adds to data dict if value is not None
            - Maintains original key name in output regardless of source
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
        """Format the log record into a structured JSON string.

        Creates a comprehensive JSON object containing all relevant log
        information including timestamp, logger details, message content,
        and metadata. The output follows standardized field naming conventions
        for compatibility with log aggregation systems.

        Args:
            record: The log record object to format.

        Returns:
            JSON string representation of the log record.

        JSON Fields:
            - @timestamp: ISO 8601 timestamp with millisecond precision
            - log.logger: Logger name
            - log.level: Log level name
            - status: Status code for STATUS level messages
            - reason: Reason text for STATUS level messages
            - message: The formatted log message
            - scope: Scope context if available
            - file: Source filename
            - line: Source line number
            - function: Source function name
            - context: Additional details and metadata

        Processing Steps:
            1. Normalize record.args to tuple format
            2. Handle STATUS level message composition
            3. Process placeholder replacement
            4. Extract details from arguments
            5. Add scope to message if present
            6. Create JSON structure with timestamp
            7. Populate fields conditionally based on record content
        """
        # If for some reason record.args is not a tuple, make it one.  This happens if the original
        # tuple had only one element that is also a list (or dictionary)
        if not isinstance(record.args, tuple):
            record.args = (record.args,)

        if record.levelno == STATUS and hasattr(record, "status") and hasattr(record, "reason"):
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
    """Custom logging handler for Core Automation with special message processing.

    Provides specialized handling for Core Automation log messages with support
    for both JSON and text formatters. The handler manages formatter selection
    and message emission with proper handling of custom log levels and metadata.

    The handler works with CoreLogFormatter subclasses to provide consistent
    output formatting regardless of the chosen output format. It handles the
    special processing requirements of the Core Automation logging system.

    Formatter Selection:
        The choice between JSON and text formatters is typically controlled
        by environment configuration, allowing the same logging code to
        produce different output formats based on deployment context.
    """

    formatter: CoreLogFormatter

    def __init__(self, name: str, **kwargs):
        """Initialize a new Core Logger Handler instance.

        Creates a handler with the specified name and optional level setting.
        The handler can be configured with various options through kwargs.

        Args:
            name: The name of the handler for identification.
            **kwargs: Additional keyword arguments including:
                     level: Log level for the handler (defaults to NOTSET).

        Notes:
            The level can be passed in kwargs and will be extracted automatically.
            Other kwargs are available for future extension.
        """
        super().__init__(level=kwargs.get("level", NOTSET))
        self.name = name

    def emit(self, record) -> None:
        """Emit the log message using the configured formatter.

        Processes the log record through the configured formatter and outputs
        the result. Provides special handling for different message types and
        ensures proper formatting regardless of the formatter type.

        Args:
            record: The log record object to emit.

        Behavior:
            - Uses configured formatter if available
            - Falls back to basic message output if no formatter is set
            - Handles STATUS messages with special processing
            - Outputs to stdout using print for simplicity
        """
        if self.formatter:
            print(self.formatter.format(record))
        else:
            print(record.getMessage())


class CoreLogger(logging.Logger):
    """Enhanced logger with metadata support and identity-based routing.

    Provides an advanced logging interface that extends the standard Python
    logger with features specifically designed for the Core Automation
    framework. Supports custom log levels, metadata enrichment, template
    processing, and identity-based logger selection.

    Key Features:
        - Custom log levels (MSG, STATUS, TRACE) beyond standard levels
        - Template processing with {} placeholder replacement
        - Metadata enrichment through kwargs parameters
        - Identity-based logger routing for multi-component systems
        - Automatic scope and context addition
        - Enhanced error information with proper stack level handling

    The logger overrides all standard logging methods to accept additional
    kwargs that are converted to metadata, enabling rich contextual logging
    with minimal code changes.

    Stack Level Handling:
        Due to the custom processing layers, the default stacklevel is set
        to 4 to ensure accurate file and line number reporting in log output.
    """

    def __init__(self, name: str, level: int = NOTSET):
        """Initialize the Core Logger with name and optional level.

        Args:
            name: The name of the logger for identification.
            level: The initial log level. Defaults to NOTSET which inherits
                  from parent loggers.
        """
        super().__init__(name, level=level)

    def setLevel(self, level: int | str) -> None:
        """Set the log level for both the logger and all its handlers.

        Ensures consistent log level across the logger and all attached
        handlers, preventing situations where the logger accepts a message
        but handlers filter it out due to level mismatches.

        Args:
            level: The log level to set (integer constant or string name).
        """
        super().setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)

    def core_log(self, level: int, message: str | dict | None, args: tuple, **kwargs) -> None:
        """Core logging method that processes messages and metadata.

        This is the central logging method that handles all the custom
        processing for Core Automation logging including metadata extraction,
        template processing, and kwargs conversion to extra data.

        Args:
            level: The numeric log level.
            message: The message to log (string, dict, or None).
            args: Tuple of replacement values for message templates.
            **kwargs: Additional metadata and configuration options including:
                     exc_info: Exception information for error logging.
                     extra: Additional fields to add to log record.
                     stack_info: Include stack trace information.
                     stacklevel: Stack depth for source location (default 4).
                     identity: Logger identity for routing.
                     scope: Scope context for the message.
                     details: Additional detail data.

        Processing:
            1. Extracts standard logging kwargs (exc_info, extra, etc.)
            2. Handles dict messages by moving content to extra data
            3. Processes kwargs to extract message and metadata
            4. Calls internal _log method with processed parameters

        Notes:
            The stacklevel default of 4 accounts for the additional layers
            in the custom logging pipeline to ensure accurate source location
            reporting in log output.
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
        """Log a simple message at the MSG level (70).

        Outputs messages at the highest custom level for important
        notifications that should always be visible regardless of
        typical log level settings.

        Args:
            message: The message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata to include in the log record.
        """
        self.core_log(MSG, message, args, **kwargs)

    def status(self, code: str | int, reason: str, *args: Any, **kwargs: Any) -> None:
        """Log a status message with code and reason at the STATUS level (60).

        Outputs structured status messages that combine a status code with
        a descriptive reason. Designed for operational status reporting and
        monitoring integration.

        Args:
            code: The status code (string or integer).
            reason: Descriptive reason text for the status.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including:
                     details: Dict that may contain status and reason overrides.
                     status_label: Alternative status label.

        Message Format:
            The final message follows the pattern: "{code} {reason}"

        Metadata:
            Both code and reason are added as separate metadata fields
            for structured logging systems that can process them individually.
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
        """Log a message with severity TRACE (5).

        Outputs detailed trace information at the lowest custom level for
        fine-grained debugging and development diagnostics.

        Args:
            message: The trace message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata to include in the log record.
        """
        if self.isEnabledFor(TRACE):
            self.core_log(TRACE, message, args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Log message with severity DEBUG (10).

        Standard debug logging with enhanced metadata support for
        development and troubleshooting scenarios.

        Args:
            msg: The debug message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including exc_info for exceptions.
        """
        if self.isEnabledFor(DEBUG):
            self.core_log(DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log message with severity INFO (20).

        Standard informational logging with enhanced metadata support
        for general operational information.

        Args:
            msg: The information message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including exc_info for exceptions.
        """
        if self.isEnabledFor(INFO):
            self.core_log(INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log message with severity WARNING (30).

        Standard warning logging with enhanced metadata support for
        situations that warrant attention but don't stop operation.

        Args:
            msg: The warning message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including exc_info for exceptions.
        """
        if self.isEnabledFor(WARNING):
            self.core_log(WARNING, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log message with severity ERROR (40).

        Standard error logging with enhanced metadata support for
        error conditions that may affect operation.

        Args:
            msg: The error message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including exc_info for exceptions.
        """
        if self.isEnabledFor(ERROR):
            self.core_log(ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log message with severity CRITICAL (50).

        Standard critical logging with enhanced metadata support for
        severe error conditions that may cause system failure.

        Args:
            msg: The critical message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including exc_info for exceptions.
        """
        if self.isEnabledFor(CRITICAL):
            self.core_log(CRITICAL, msg, args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Log message with the specified integer severity level.

        Generic logging method that accepts any numeric log level with
        enhanced metadata support for flexible logging scenarios.

        Args:
            level: The numeric log level (must be an integer).
            msg: The message to output.
            *args: Additional arguments for template replacement.
            **kwargs: Additional metadata including exc_info for exceptions.

        Raises:
            TypeError: If level is not an integer.
        """
        if not isinstance(level, int):
            raise TypeError("level must be an integer")

        if self.isEnabledFor(level):
            self.core_log(level, msg, args, **kwargs)
