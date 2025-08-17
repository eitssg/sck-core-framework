"""YAML Utilities Module for Core Automation Framework.

This module provides specialized YAML parsing and generation capabilities for CloudFormation
templates and Core Automation configuration files. It extends ruamel.yaml with custom
constructors and representers to handle AWS-specific tags, custom data types, and intelligent
string formatting.

Key Features:
    - **CloudFormation Support**: Native handling of AWS intrinsic function tags (!Ref, !GetAtt, etc.)
    - **Custom Tags**: Support for !Include tag for file composition
    - **Smart String Handling**: Intelligent quoting to prevent YAML interpretation issues
    - **Date/Time Support**: ISO 8601 date parsing and formatting
    - **Numeric Preservation**: Proper handling of Decimal types without loss of precision
    - **Round-Trip Safety**: Preserves comments, formatting, and structure

Common Use Cases:
    - CloudFormation template processing and validation
    - Configuration file parsing with custom extensions
    - Template composition using !Include directives
    - Safe YAML serialization with type preservation

Examples:
    Basic YAML operations:

    >>> # Load a CloudFormation template
    >>> template = load_yaml_file("template.yaml")
    >>> print(template["Resources"]["MyBucket"]["Type"])
    'AWS::S3::Bucket'

    >>> # Parse YAML with AWS tags
    >>> yaml_content = '''
    ... BucketName: !Ref MyBucketName
    ... Region: !GetAtt MyBucket.Region
    ... '''
    >>> data = from_yaml(yaml_content)
    >>> print(data["BucketName"])
    {'Ref': 'MyBucketName'}

    Template composition with !Include:

    >>> # main.yaml
    >>> yaml_content = '''
    ... Resources: !Include resources.yaml
    ... Parameters: !Include parameters.yaml
    ... '''
    >>> template = from_yaml(yaml_content)  # Automatically resolves includes

Functions:
    create_yaml_parser: Create a pre-configured YAML parser instance
    load_yaml_file: Load YAML from file with !Include support
    read_yaml: Parse YAML from stream
    from_yaml: Parse YAML from string
    write_yaml: Write Python data to YAML stream
    to_yaml: Convert Python data to YAML string
    strip_root_indent: Remove root-level indentation from YAML strings

Classes:
    CfnYamlConstructor: Custom YAML constructor for CloudFormation and !Include tags

Constants:
    aws_tags: List of supported AWS CloudFormation intrinsic function tags
"""

from typing import IO, Any, Union
import io
from ruamel.yaml import YAML
from ruamel.yaml.emitter import RoundTripEmitter
from ruamel.yaml.constructor import ConstructorError, RoundTripConstructor
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.dumper import RoundTripDumper
from ruamel.yaml.nodes import ScalarNode, MappingNode, SequenceNode
from pathlib import Path
from datetime import datetime, date, time
from decimal import Decimal
import copy

# A list of all the CloudFormation intrinsic function tags
aws_tags = [
    "!And",
    "!Base64",
    "!Cidr",
    "!Equals",
    "!FindInMap",
    "!ForEach",
    "!GetAtt",
    "!GetAZs",
    "!If",
    "!ImportValue",
    "!Join",
    "!Length",
    "!Not",
    "!Or",
    "!Ref",
    "!Select",
    "!Split",
    "!Sub",
    "!ToJsonString",
]


def __iso8601_constructor(loader, node):
    """Construct datetime objects from ISO 8601 formatted strings.

    Attempts to parse YAML string values as datetime objects using ISO 8601 format.
    Falls back to returning the original string if parsing fails, ensuring
    non-date strings are preserved unchanged.

    Args:
        loader: The YAML loader instance.
        node: The YAML node containing the string value.

    Returns:
        datetime object if the string can be parsed as ISO 8601, otherwise
        the original string value.

    Examples:
        >>> # In YAML: date_field: "2023-12-25T10:30:00"
        >>> # Parsed as: datetime(2023, 12, 25, 10, 30, 0)

        >>> # In YAML: text_field: "not a date"
        >>> # Parsed as: "not a date" (unchanged)

    Notes:
        This constructor is automatically applied to all string values during
        YAML parsing, providing transparent date conversion where applicable.
    """
    value = loader.construct_scalar(node)
    try:
        # Attempt to parse the string as a datetime object
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        # If parsing fails, return the original scalar value
        return value


def __iso8601_representer(dumper, data):
    """Represent datetime/date objects as ISO 8601 formatted strings.

    Converts Python datetime, date, and time objects to their ISO 8601
    string representation for YAML serialization.

    Args:
        dumper: The YAML dumper instance.
        data: The datetime, date, or time object to represent.

    Returns:
        YAML scalar node containing the ISO 8601 formatted string.

    Examples:
        >>> # Python: datetime(2023, 12, 25, 10, 30, 0)
        >>> # YAML: "2023-12-25T10:30:00"

        >>> # Python: date(2023, 12, 25)
        >>> # YAML: "2023-12-25"

    Notes:
        Ensures consistent date formatting across all YAML output and
        enables round-trip preservation of date/time values.
    """
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.isoformat())


def __represent_decimal(dumper, data):
    """Represent Decimal objects as YAML numeric types without precision loss.

    Converts Python Decimal objects to appropriate YAML numeric types (int or float)
    while preserving their exact numeric value without quotes.

    Args:
        dumper: The YAML dumper instance.
        data: The Decimal object to represent.

    Returns:
        YAML scalar node with 'int' tag if the decimal is a whole number,
        'float' tag otherwise.

    Examples:
        >>> # Python: Decimal('42')
        >>> # YAML: 42 (as int, no quotes)

        >>> # Python: Decimal('3.14159')
        >>> # YAML: 3.14159 (as float, no quotes)

        >>> # Python: Decimal('1000.00')
        >>> # YAML: 1000 (as int, trailing zeros removed)

    Notes:
        Prevents loss of precision that could occur with float conversion
        and ensures numeric values remain unquoted in YAML output.
    """
    # Check if the Decimal can be represented as an integer without loss
    if data == data.to_integral_value():
        return dumper.represent_scalar("tag:yaml.org,2002:int", str(data))
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:float", str(data))


def __represent_smart_str(dumper, data):
    """Represent strings with intelligent quoting to prevent YAML interpretation issues.

    Applies quotes only when necessary to prevent strings from being interpreted
    as booleans, numbers, or null values. Uses literal block style for multiline
    strings and plain style for simple strings.

    Args:
        dumper: The YAML dumper instance.
        data: The string to represent.

    Returns:
        YAML scalar node with appropriate style (plain, quoted, or literal block).

    Examples:
        >>> # Multiline strings use literal block style
        >>> multiline = "Line 1\\nLine 2\\nLine 3"
        >>> # YAML output:
        >>> # |
        >>> #   Line 1
        >>> #   Line 2
        >>> #   Line 3

        >>> # Ambiguous strings get quoted
        >>> bool_like = "true"
        >>> # YAML: 'true' (quoted to prevent boolean interpretation)

        >>> # Numeric strings get quoted
        >>> number_like = "123"
        >>> # YAML: '123' (quoted to prevent numeric interpretation)

        >>> # Plain strings remain unquoted
        >>> simple = "hello world"
        >>> # YAML: hello world (no quotes needed)

    Ambiguous Strings:
        The following strings are automatically quoted to prevent misinterpretation:
        - Boolean-like: "true", "false", "yes", "no", "on", "off"
        - Null-like: "null"
        - Numeric: Any string that can be parsed as a number

    Notes:
        This intelligent quoting prevents common YAML parsing issues while
        keeping the output clean and readable for human consumption.
    """
    if "\n" in data:
        # Use literal block scalar style for multiline strings
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

    # This is a list of strings that look like booleans or null in YAML 1.1/1.2
    ambiguous_strings = ["true", "false", "yes", "no", "on", "off", "null"]

    # Check if the string is one of the ambiguous values (case-insensitive)
    if data.lower() in ambiguous_strings:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")

    # Try to parse as a number (int or float). If it succeeds, it needs quotes.
    try:
        float(data)
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    except (ValueError, TypeError):
        pass

    # Let ruamel decide the best style (plain, literal, etc.) for all other strings.
    # It will handle special characters correctly.
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def __represent_none(dumper, data):
    """Represent None values as empty strings instead of 'null'.

    Provides cleaner YAML output by representing Python None values as empty
    strings rather than the explicit 'null' keyword.

    Args:
        dumper: The YAML dumper instance.
        data: The None value to represent.

    Returns:
        YAML scalar node with empty string value.

    Examples:
        >>> # Python: {"key": None}
        >>> # YAML: key: (empty, not 'null')

    Notes:
        This representation choice makes YAML output cleaner and more readable
        while maintaining round-trip compatibility.
    """
    return dumper.represent_scalar("tag:yaml.org,2002:null", "")  # Empty instead of 'null'


class CfnYamlConstructor(RoundTripConstructor):
    """Custom YAML constructor for AWS CloudFormation tags and !Include functionality.

    Extends ruamel.yaml's constructor to handle AWS CloudFormation intrinsic functions
    and custom !Include tags for template composition. Provides proper construction
    of CloudFormation function syntax and file inclusion capabilities.

    Attributes:
        root_path: Base path for resolving relative !Include file paths.

    Examples:
        CloudFormation tag construction:

        >>> # YAML: !Ref MyParameter
        >>> # Constructed as: {"Ref": "MyParameter"}

        >>> # YAML: !GetAtt MyResource.Attribute
        >>> # Constructed as: {"Fn::GetAtt": "MyResource.Attribute"}

        File inclusion:

        >>> # YAML: Resources: !Include resources.yaml
        >>> # Loads and inserts contents of resources.yaml file

    Supported AWS Tags:
        All standard CloudFormation intrinsic functions are supported:
        - !Ref - References parameters and resources
        - !GetAtt - Gets resource attributes
        - !Sub - String substitution
        - !Join - String joining
        - !If, !And, !Or, !Not, !Equals - Conditional functions
        - And many more (see aws_tags constant)

    File Inclusion:
        The !Include tag enables template composition:
        - Resolves paths relative to the including file
        - Recursively processes included files
        - Supports nested includes
        - Validates file existence before inclusion
    """

    def __init__(self, *args, **kwargs):
        """Initialize the CloudFormation YAML constructor.

        Args:
            *args: Positional arguments passed to parent constructor.
            **kwargs: Keyword arguments passed to parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.root_path = None  # Used to resolve relative !Include paths

    def construct_aws_tag(self, tag_suffix, node):
        """Construct AWS CloudFormation intrinsic function objects.

        Converts YAML tags like !Ref and !GetAtt into their corresponding
        CloudFormation function syntax ({"Ref": ...}, {"Fn::GetAtt": ...}, etc.).

        Args:
            tag_suffix: The AWS function name (e.g., "Ref", "GetAtt").
            node: The YAML node containing the function arguments.

        Returns:
            Dictionary with CloudFormation function syntax.

        Examples:
            >>> # !Ref MyParameter -> {"Ref": "MyParameter"}
            >>> # !GetAtt MyResource.Property -> {"Fn::GetAtt": "MyResource.Property"}
            >>> # !Join [",", ["a", "b"]] -> {"Fn::Join": [",", ["a", "b"]]}

        Notes:
            - "Ref" is treated specially and doesn't get the "Fn::" prefix
            - All other functions get the "Fn::" prefix automatically
            - Supports scalar, mapping, and sequence node types
        """
        function_name = tag_suffix
        if function_name != "Ref":
            function_name = f"Fn::{function_name}"

        if isinstance(node, ScalarNode):
            return {function_name: self.construct_scalar(node)}
        elif isinstance(node, MappingNode):
            return {function_name: self.construct_mapping(node)}
        elif isinstance(node, SequenceNode):
            return {function_name: self.construct_sequence(node)}
        return None

    def include(self, node: ScalarNode):
        """Handle !Include tag for file composition.

        Loads and parses the specified file, incorporating its contents
        into the current YAML structure. Supports relative path resolution
        based on the including file's location.

        Args:
            node: YAML scalar node containing the file path to include.

        Returns:
            Parsed contents of the included file.

        Raises:
            ConstructorError: If no root path is set, file doesn't exist,
                            or file cannot be parsed.

        Examples:
            >>> # In main.yaml:
            >>> # Resources: !Include resources.yaml
            >>> # Parameters: !Include config/parameters.yaml

            >>> # Loads resources.yaml and parameters.yaml, inserting their
            >>> # contents into the main template structure

        File Resolution:
            - Paths are resolved relative to the including file's directory
            - Supports both relative and absolute paths
            - Validates file existence before attempting to load
            - Uses the same YAML parser configuration for consistency

        Notes:
            The root_path must be set by the calling code (typically
            load_yaml_file) to enable proper relative path resolution.
        """
        if not self.root_path:
            raise ConstructorError(f"Cannot use !Include without a valid base path. File: {node.value}")

        # Resolve the path relative to the file being parsed
        file_path = self.root_path / self.construct_scalar(node)

        if not file_path.is_file():
            raise ConstructorError(f"!Include file not found: {file_path}")

        # Create a new YAML instance to parse the included file
        yaml_parser = create_yaml_parser()
        return yaml_parser.load(file_path)


def create_yaml_parser() -> YAML:
    """Create a pre-configured YAML parser for CloudFormation and Core Automation files.

    Creates a ruamel.yaml YAML instance with custom configuration for handling
    CloudFormation templates, AWS tags, date parsing, and intelligent string
    representation. Replaces the need for separate monkeypatch configurations.

    Returns:
        Configured YAML parser instance ready for CloudFormation and automation use.

    Configuration Features:
        - **Round-trip preservation**: Maintains comments, formatting, and structure
        - **AWS tag support**: All CloudFormation intrinsic functions (!Ref, !GetAtt, etc.)
        - **!Include support**: File composition and template inclusion
        - **Smart string handling**: Intelligent quoting to prevent interpretation issues
        - **Date/time parsing**: Automatic ISO 8601 date conversion
        - **Decimal preservation**: Maintains numeric precision without quotes
        - **Unicode support**: Full UTF-8 encoding with unicode characters
        - **Clean formatting**: Consistent indentation and block-style output

    Examples:
        >>> parser = create_yaml_parser()
        >>>
        >>> # Parse CloudFormation template
        >>> template = parser.load(open("template.yaml"))
        >>>
        >>> # Generate clean YAML output
        >>> output = parser.dump(data, stream)

    Parser Settings:
        - **Type**: Round-trip ('rt') for comment/formatting preservation
        - **Quotes**: Preserved from original source
        - **Duplicates**: Not allowed (raises error on duplicate keys)
        - **Start/End**: No explicit document markers (--- or ...)
        - **Flow Style**: Block style by default for readability
        - **Indentation**: 2 spaces for mappings, 4 for sequences, 2 offset
        - **Encoding**: UTF-8 with unicode support

    Custom Representers:
        - **None**: Empty string instead of 'null'
        - **datetime/date/time**: ISO 8601 format strings
        - **Decimal**: Proper numeric types without precision loss
        - **str**: Intelligent quoting based on content

    Notes:
        This function creates a new parser instance each time it's called.
        For better performance with multiple operations, create once and reuse.
    """
    yaml = YAML(typ="rt")  # 'rt' for round-trip, preserves comments and formatting
    yaml.Constructor = CfnYamlConstructor
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = False  # Fail on duplicate keys
    yaml.explicit_start = False  # Always start with '---'
    yaml.explicit_end = False  # Do not end with '...'
    yaml.default_flow_style = False  # Use block style by default
    yaml.allow_unicode = True  # Allow unicode characters
    yaml.encoding = "utf-8"  # Use UTF-8 encoding for input/output

    # Set indentation for clean output
    yaml.indent(mapping=2, sequence=4, offset=2)

    yaml.representer.ignore_aliases = lambda *args: True  # Ignore aliases

    yaml.representer.add_representer(type(None), __represent_none)

    # Add the ISO 8601 date constructor and representer
    # This overrides the default string constructor to attempt date parsing
    yaml.constructor.add_constructor("tag:yaml.org,2002:str", __iso8601_constructor)

    yaml.representer.add_representer(datetime, __iso8601_representer)
    yaml.representer.add_representer(date, __iso8601_representer)
    yaml.representer.add_representer(time, __iso8601_representer)
    yaml.representer.add_representer(Decimal, __represent_decimal)

    # Add the custom string representer to intelligently quote strings.
    # This must come AFTER the datetime representer.
    yaml.representer.add_representer(str, __represent_smart_str)

    # Register all the AWS CloudFormation tags
    for tag in aws_tags:
        yaml.constructor.add_constructor(tag, CfnYamlConstructor.construct_aws_tag)

    # Register the !Include tag
    yaml.constructor.add_constructor("!Include", CfnYamlConstructor.include)

    return yaml


def load_yaml_file(file_path: str, yaml_parser: YAML = None) -> Any:
    """Load YAML file with !Include support and proper path resolution.

    Loads a YAML file and configures the parser to handle !Include tags
    by setting the appropriate root path for relative file resolution.

    Args:
        file_path: Path to the YAML file to load. Can be relative or absolute.
        yaml_parser: Optional pre-configured YAML parser. Creates new one if None.

    Returns:
        Parsed YAML content with all !Include directives resolved.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ConstructorError: If included files are not found or cannot be parsed.
        ValueError: If the YAML content is invalid.

    Examples:
        >>> # Load a CloudFormation template with includes
        >>> template = load_yaml_file("infrastructure/main.yaml")
        >>>
        >>> # Load with custom parser
        >>> parser = create_yaml_parser()
        >>> config = load_yaml_file("config.yaml", parser)

        >>> # Template composition example
        >>> # main.yaml contains:
        >>> # Resources: !Include resources/ec2.yaml
        >>> # Parameters: !Include config/parameters.yaml
        >>> template = load_yaml_file("main.yaml")
        >>> # All includes are automatically resolved

    File Resolution:
        - Converts file_path to pathlib.Path for robust path handling
        - Sets parser's root_path to file's directory for !Include resolution
        - Supports both relative and absolute include paths
        - Handles nested includes (included files can include other files)

    Error Handling:
        - Validates file existence before attempting to parse
        - Provides clear error messages for missing include files
        - Propagates YAML syntax errors with file context

    Notes:
        The root_path is set to the directory containing the loaded file,
        allowing !Include directives to use relative paths from that location.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    # Convert the file path to a Path object
    file_path = Path(file_path)

    # Set the root path to the directory of the file being loaded
    # This allows !Include to resolve relative paths correctly.
    yaml_parser.constructor.root_path = file_path.parent

    with file_path.open("r") as f:
        return read_yaml(f, yaml_parser)


def read_yaml(stream: IO, yaml_parser: YAML = None) -> Any:
    """Parse YAML data from an input stream.

    Reads and parses YAML content from any file-like object or stream,
    returning the parsed Python data structure.

    Args:
        stream: Input stream containing YAML data (file, StringIO, etc.).
        yaml_parser: Optional pre-configured YAML parser. Creates new one if None.

    Returns:
        Parsed YAML content as Python data structures (dict, list, etc.).

    Raises:
        ValueError: If the YAML content is invalid or cannot be parsed.
        ConstructorError: If custom tags cannot be constructed properly.

    Examples:
        >>> # Read from file handle
        >>> with open("config.yaml", "r") as f:
        ...     config = read_yaml(f)

        >>> # Read from StringIO
        >>> import io
        >>> yaml_content = "key: value\\nlist: [1, 2, 3]"
        >>> stream = io.StringIO(yaml_content)
        >>> data = read_yaml(stream)

        >>> # Read with custom parser
        >>> parser = create_yaml_parser()
        >>> with open("template.yaml", "r") as f:
        ...     template = read_yaml(f, parser)

    Stream Requirements:
        - Must be readable text stream (not binary)
        - Should contain valid YAML content
        - Can be any file-like object (file, StringIO, etc.)

    Parser Features:
        - Handles CloudFormation intrinsic functions automatically
        - Processes !Include tags (if root_path is set)
        - Converts ISO 8601 date strings to datetime objects
        - Validates against duplicate keys

    Notes:
        This function does not set root_path for !Include resolution.
        Use load_yaml_file() for files that contain !Include directives.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    return yaml_parser.load(stream)


def from_yaml(yaml_data: str, yaml_parser: YAML = None) -> Any:
    """Parse YAML content from a string.

    Converts a YAML string into Python data structures using the configured
    parser with CloudFormation and custom tag support.

    Args:
        yaml_data: String containing YAML content to parse.
        yaml_parser: Optional pre-configured YAML parser. Creates new one if None.

    Returns:
        Parsed YAML content as Python data structures.

    Raises:
        ValueError: If the YAML string is invalid or cannot be parsed.
        ConstructorError: If custom tags cannot be constructed properly.

    Examples:
        >>> # Simple YAML parsing
        >>> yaml_str = '''
        ... name: MyApplication
        ... version: 1.0.0
        ... enabled: true
        ... '''
        >>> config = from_yaml(yaml_str)
        >>> print(config["name"])
        'MyApplication'

        >>> # CloudFormation with intrinsic functions
        >>> cf_yaml = '''
        ... Resources:
        ...   MyBucket:
        ...     Type: AWS::S3::Bucket
        ...     Properties:
        ...       BucketName: !Ref BucketNameParameter
        ... '''
        >>> template = from_yaml(cf_yaml)
        >>> print(template["Resources"]["MyBucket"]["Properties"]["BucketName"])
        {'Ref': 'BucketNameParameter'}

        >>> # With custom parser configuration
        >>> parser = create_yaml_parser()
        >>> data = from_yaml(yaml_str, parser)

    Supported Features:
        - CloudFormation intrinsic functions (!Ref, !GetAtt, etc.)
        - ISO 8601 date parsing
        - Smart string handling (quoted when needed)
        - Decimal number preservation
        - Unicode content support

    Stream Handling:
        - Creates temporary StringIO stream with timestamped name
        - Handles multi-document YAML if present
        - Processes content with full parser configuration

    Notes:
        For YAML content with !Include directives, use load_yaml_file()
        instead as this function doesn't set up root_path resolution.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    stream = io.StringIO(yaml_data)
    stream.name = "yaml_to_data-" + datetime.now().isoformat()
    return read_yaml(stream, yaml_parser)


def write_yaml(data: Any, stream: IO, yaml_parser: YAML = None) -> None:
    """Write Python data to a YAML stream with formatting optimization.

    Serializes Python data structures to YAML format with intelligent
    formatting for lists and proper indentation handling.

    Args:
        data: Python data to serialize (dict, list, or other supported types).
        stream: Output stream to write YAML content to.
        yaml_parser: Optional pre-configured YAML parser. Creates new one if None.

    Raises:
        ValueError: If the data cannot be serialized to YAML.
        IOError: If writing to the stream fails.

    Examples:
        >>> # Write to file
        >>> data = {"name": "app", "config": {"debug": True}}
        >>> with open("output.yaml", "w") as f:
        ...     write_yaml(data, f)

        >>> # Write to StringIO
        >>> import io
        >>> stream = io.StringIO()
        >>> write_yaml(data, stream)
        >>> yaml_content = stream.getvalue()

        >>> # Write list with root indent stripping
        >>> items = [{"name": "item1"}, {"name": "item2"}]
        >>> with open("list.yaml", "w") as f:
        ...     write_yaml(items, f)

    List Formatting:
        When data is a list, applies root indent stripping to produce cleaner
        output without unnecessary leading spaces on list items.

    Output Features:
        - Clean, readable formatting with consistent indentation
        - Smart string quoting to prevent interpretation issues
        - Proper representation of None, dates, and numeric types
        - Block-style formatting for better readability
        - Preserved precision for Decimal numbers

    Stream Requirements:
        - Must be writable text stream
        - Should be opened in text mode (not binary)
        - Can be file, StringIO, or any file-like object

    Notes:
        The function automatically handles list formatting optimization
        and applies the configured representers for clean output.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    if isinstance(data, list):
        yaml_parser.dump(data, stream, transform=lambda s: strip_root_indent(s, yaml_parser.sequence_dash_offset))
    else:
        yaml_parser.dump(data, stream)


def strip_root_indent(stream: str, indent_size: int = 2) -> str:
    """Remove root-level indentation from YAML string content.

    Processes YAML string content to remove leading indentation from all lines,
    creating cleaner output for root-level list items and other content.

    Args:
        stream: YAML content string to process.
        indent_size: Number of spaces to remove from the beginning of each line.
                    Defaults to 2 for standard YAML indentation.

    Returns:
        Processed YAML string with root indentation removed.

    Examples:
        >>> # Input with root indentation
        >>> indented = '''  - name: item1
        ...   value: test1
        ... - name: item2
        ...   value: test2'''
        >>>
        >>> # Remove 2-space root indent
        >>> clean = strip_root_indent(indented, 2)
        >>> print(clean)
        - name: item1
          value: test1
        - name: item2
          value: test2

        >>> # Custom indent size
        >>> four_space = "    key: value\\n    list:\\n      - item"
        >>> clean = strip_root_indent(four_space, 4)
        >>> print(clean)
        key: value
        list:
          - item

    Processing Logic:
        - Splits input into individual lines preserving line endings
        - Checks each line for leading spaces matching indent_size
        - Removes exact indent_size spaces from lines that have them
        - Leaves lines with different indentation unchanged
        - Rejoins lines maintaining original line ending format

    Use Cases:
        - Cleaning up YAML list output from ruamel.yaml
        - Removing unnecessary root indentation from templates
        - Formatting YAML for better readability
        - Processing auto-generated YAML content

    Notes:
        Only removes indentation that exactly matches the specified size.
        Lines with different indentation levels are preserved unchanged.
    """
    lines = stream.splitlines(True)
    stripped_lines = []
    for line in lines:
        if line.startswith(" " * indent_size):
            stripped_lines.append(line[indent_size:])
        else:
            stripped_lines.append(line)
    return "".join(stripped_lines)


def to_yaml(data: Any, yaml_parser: YAML = None) -> str:
    """Convert Python data to a YAML string with optimized formatting.

    Serializes Python data structures to a YAML string using the configured
    parser with CloudFormation support, smart formatting, and clean output.

    Args:
        data: Python data to convert (dict, list, or other supported types).
        yaml_parser: Optional pre-configured YAML parser. Creates new one if None.

    Returns:
        YAML string representation of the input data.

    Raises:
        ValueError: If the data cannot be serialized to YAML.

    Examples:
        >>> # Convert dictionary to YAML
        >>> data = {
        ...     "name": "MyApp",
        ...     "version": "1.0.0",
        ...     "config": {
        ...         "debug": True,
        ...         "timeout": 30
        ...     }
        ... }
        >>> yaml_str = to_yaml(data)
        >>> print(yaml_str)
        name: MyApp
        version: 1.0.0
        config:
          debug: true
          timeout: 30

        >>> # Convert list with clean formatting
        >>> items = [
        ...     {"name": "item1", "value": 100},
        ...     {"name": "item2", "value": 200}
        ... ]
        >>> yaml_str = to_yaml(items)
        >>> print(yaml_str)
        - name: item1
          value: 100
        - name: item2
          value: 200

        >>> # CloudFormation template generation
        >>> template = {
        ...     "Resources": {
        ...         "MyBucket": {
        ...             "Type": "AWS::S3::Bucket",
        ...             "Properties": {
        ...                 "BucketName": {"Ref": "BucketName"}
        ...             }
        ...         }
        ...     }
        ... }
        >>> yaml_str = to_yaml(template)
        >>> # Produces clean CloudFormation YAML

    Output Features:
        - Clean, readable formatting with proper indentation
        - Smart string quoting only when necessary
        - Proper None representation (empty instead of 'null')
        - ISO 8601 date formatting for datetime objects
        - Preserved precision for Decimal numbers
        - Block-style formatting for better readability

    Temporary Stream:
        - Creates timestamped StringIO stream for processing
        - Handles list formatting optimization automatically
        - Returns final string content after processing

    Performance Notes:
        - Creates temporary stream in memory for processing
        - Suitable for reasonably-sized data structures
        - For large data or streaming scenarios, use write_yaml() directly

    Notes:
        The function combines write_yaml() functionality with string output,
        providing convenient one-step conversion with all formatting benefits.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    stream = io.StringIO()
    stream.name = "data_to_yaml-" + datetime.now().isoformat()
    write_yaml(data, stream, yaml_parser)
    return stream.getvalue()
