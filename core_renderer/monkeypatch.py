"""
This library is a few functions that manipulate CloudFormation template files.
"""

from typing import Mapping, Union, Any
import yaml

from yaml.constructor import SafeConstructor
from yaml.representer import BaseRepresenter
from yaml.nodes import ScalarNode, MappingNode, SequenceNode
from yaml.resolver import BaseResolver

from collections import OrderedDict


def construct_aws_fn(
    loader: SafeConstructor, node: Union[ScalarNode, MappingNode, SequenceNode]
) -> dict | None:
    """
    Convert AWS tags (eg. !Ref, !GetAtt) to a map (eg. {Ref: <x>}, {Fn::GetAtt: <x>})

    :param loader:
    :param node:
    :return:
    """
    function_name = node.tag.lstrip("!")

    if function_name != "Ref":
        function_name = "Fn::" + function_name

    try:
        if isinstance(node, ScalarNode):
            return {function_name: loader.construct_scalar(node)}
        elif isinstance(node, MappingNode):
            return {function_name: loader.construct_mapping(node)}
        elif isinstance(node, SequenceNode):
            return {function_name: loader.construct_sequence(node)}
    except Exception:
        pass
    return None


def process_yaml_include(
    loader: SafeConstructor, node: Union[ScalarNode, MappingNode, SequenceNode]
):
    """
    Args:
        loader (SafeConstructor): _description_
        node (Union[ScalarNode, MappingNode, SequenceNode]): _description_
    """
    pass


def construct_mapping(
    loader: SafeConstructor, node: MappingNode, deep=False
) -> Mapping:
    """
    Create a mapping object from a YAML file.  This is a convenience function for constructing a mapping object

    :param loader:
    :param node:
    :param deep:
    :return:
    """

    # Allow YAML merge operator (<<)
    loader.flatten_mapping(node)

    # Fail on duplicate keys
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        value = loader.construct_object(value_node, deep=deep)
        if key in mapping:
            raise MappingConstructorError(f"Duplicate key '{key}'", key_node.start_mark)
        mapping[key] = value

    return loader.construct_mapping(node, deep)


class MappingConstructorError(yaml.constructor.ConstructorError):
    """
    Create a type mapping for the constructor error
    """

    pass


def represent_ordereddict(dumper: BaseRepresenter, data: OrderedDict) -> MappingNode:
    """
    Create a YAML representation of an OrderedDict
    :param dumper:
    :param data:
    :return:
    """
    value = [
        (dumper.represent_data(item_key), dumper.represent_data(item_value))
        for item_key, item_value in data.items()
    ]
    return MappingNode("tag:yaml.org,2002:map", value)


def represent_string(dumper: BaseRepresenter, data: Any) -> ScalarNode:
    """
    Make string representations of numbers
    :param dumper:
    :param data:
    :return:
    """
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", data, style="'" if data.isnumeric() else None
    )


def patch_the_monkeys():
    """
    Why we monkeypatch?  I don't know.  Seems like a waste of space.

    :return:
    """
    custom_tags = [
        "!Base64",
        "!Cidr",
        "!FindInMap",
        "!GetAtt",
        "!GetAZs",
        "!ImportValue",
        "!Join",
        "!Select",
        "!Split",
        "!Sub",
        "!Ref",
        "!And",
        "!Equals",
        "!If",
        "!Not",
        "!Or",
    ]

    for tag in custom_tags:
        yaml.add_constructor(tag, construct_aws_fn, Loader=yaml.SafeLoader)

    yaml.add_constructor("!Include", process_yaml_include, Loader=yaml.SafeLoader)
    yaml.add_constructor(
        BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping, Loader=yaml.SafeLoader
    )

    yaml.add_representer(str, represent_string, Dumper=yaml.SafeDumper)
    yaml.add_representer(OrderedDict, represent_ordereddict, Dumper=yaml.SafeDumper)
