from typing import IO
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
    """
    Tries to construct a datetime object from an ISO 8601 formatted string.
    If it fails, it returns the original string.
    """
    value = loader.construct_scalar(node)
    try:
        # Attempt to parse the string as a datetime object
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        # If parsing fails, return the original scalar value
        return value


def __iso8601_representer(dumper, data):
    """
    Represents a datetime or date object as an ISO 8601 formatted string.
    """
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.isoformat())


def __represent_decimal(dumper, data):
    """
    Represents a Decimal object as a YAML int or float, without quotes,
    to preserve its numeric type in the output.
    """
    # Check if the Decimal can be represented as an integer without loss
    if data == data.to_integral_value():
        return dumper.represent_scalar("tag:yaml.org,2002:int", str(data))
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:float", str(data))


def __represent_smart_str(dumper, data):
    """
    Represents a string, adding quotes only when necessary.
    Quotes are added if the string could be interpreted as a number,
    boolean, or null, or if it contains special YAML characters.
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
    return dumper.represent_scalar("tag:yaml.org,2002:null", "")  # Empty instead of 'null'


class CfnYamlConstructor(RoundTripConstructor):
    """
    Custom constructor for ruamel.yaml to handle AWS CloudFormation tags
    and the !Include tag.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_path = None  # Used to resolve relative !Include paths

    def construct_aws_tag(self, tag_suffix, node):
        """
        Constructs the {'Fn::Tag': ...} or {'Ref': ...} structure.
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
        """
        Handles the !Include tag.
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
    """
    Creates and returns a pre-configured ruamel.yaml.YAML instance
    that can handle AWS CloudFormation templates.

    This replaces the need for the monkeypatch.py script.

    Returns:
        A configured YAML instance.
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


def load_yaml_file(file_path: str, yaml_parser: YAML = None) -> any:
    """
    Helper function to load a YAML file and set the root path for !Include.
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


def read_yaml(stream: IO, yaml_parser: YAML = None) -> any:
    """
    Reads YAML data from a stream and returns the parsed content.
    If no parser is provided, it creates a new one.

    :param stream: An IO stream containing YAML data.
    :return: Parsed YAML content.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    return yaml_parser.load(stream)


def from_yaml(yaml_data: str, yaml_parser: YAML = None) -> any:
    """
    Converts a YAML string to a Python object.
    If no parser is provided, it creates a new one.
    :param yaml_data: A string containing YAML data.
    :return: Parsed YAML content.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    stream = io.StringIO(yaml_data)
    stream.name = "yaml_to_data-" + datetime.now().isoformat()
    return read_yaml(stream, yaml_parser)


def write_yaml(data: any, stream: IO, yaml_parser: YAML = None) -> None:
    """
    Writes Python data to a YAML stream.
    If no parser is provided, it creates a new one.
    :param data: The Python data to write.
    :param stream: An IO stream to write the YAML data to.
    """

    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    if isinstance(data, list):
        yaml_parser.dump(data, stream, transform=lambda s: strip_root_indent(s, yaml_parser.sequence_dash_offset))
    else:
        yaml_parser.dump(data, stream)


def strip_root_indent(stream, indent_size=2):
    lines = stream.splitlines(True)
    stripped_lines = []
    for line in lines:
        if line.startswith(" " * indent_size):
            stripped_lines.append(line[indent_size:])
        else:
            stripped_lines.append(line)
    return "".join(stripped_lines)


def to_yaml(data: any, yaml_parser: YAML = None) -> str:
    """
    Converts Python data to a YAML string.
    If no parser is provided, it creates a new one.
    :param data: The Python data to convert.
    :return: A string containing the YAML representation of the data.
    """
    if not yaml_parser:
        yaml_parser = create_yaml_parser()

    stream = io.StringIO()
    stream.name = "data_to_yaml-" + datetime.now().isoformat()
    write_yaml(data, stream, yaml_parser)
    return stream.getvalue()
