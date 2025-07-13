"""
Module containing the yamlmerge function Constructure to enhancel YAML file processing.

Not only monkeypatch, but also !Include processing constructors to combine YAML files.
"""

import warnings
from typing import Any

import ruamel.yaml
from ruamel.yaml.nodes import MappingNode, SequenceNode, ScalarNode
from ruamel.yaml.constructor import (
    ConstructorError,
    DuplicateKeyFutureWarning,
    DuplicateKeyError,
    SafeConstructor,
)
from pathlib import Path

ERR_INTRO = "while constructing a mapping"
TAG_MERGE = "tag:yaml.org,2002:merge"
TAG_VALUE = "tag:yaml.org,2002:value"
TAG_STRING = "tag:yaml.org,2002:str"


class MyConstructor(SafeConstructor):

    def flatten_mapping(self, node: Any) -> Any:  # noqa: C901
        """
        This implements the merge key feature http://yaml.org/type/merge.html
        by inserting keys from the merge dict/list of dicts if not yet
        available in this node

        Args:
            node: The node to flatten

        Returns:
            Any: The flattened node
        """
        merge: list[Any] = []
        index = 0
        while index < len(node.value):

            key_node, value_node = node.value[index]

            if key_node.tag == TAG_MERGE:
                if merge:  # double << key
                    if self.allow_duplicate_keys:
                        del node.value[index]
                        index += 1
                        continue

                    args = self.generate_args(node, key_node)

                    if self.allow_duplicate_keys is None:
                        warnings.warn(DuplicateKeyFutureWarning(*args))
                    else:
                        raise DuplicateKeyError(*args)

                del node.value[index]

                if isinstance(value_node, ScalarNode) and value_node.tag == "!load":
                    self.scaler_node(merge, value_node)
                elif isinstance(value_node, MappingNode):
                    self.mapping_node(merge, value_node)
                elif isinstance(value_node, SequenceNode):
                    self.sequence_node(merge, node, value_node)
                else:
                    self.generate_constructor_error(node, value_node)
            elif key_node.tag == TAG_VALUE:
                key_node.tag = TAG_STRING
                index += 1
            else:
                index += 1
        if bool(merge):
            node.merge = (
                merge  # separate merge keys to be able to update without duplicate
            )
            node.value = merge + node.value

    def generate_constructor_error(self, node, value_node):
        raise ConstructorError(
            ERR_INTRO,
            node.start_mark,
            f"expected a mapping or list of mappings for merging, but found {value_node.id}",
            value_node.start_mark,
        )

    def sequence_node(self, merge, node, value_node):

        submerge = []

        for subnode in value_node.value:

            if not isinstance(subnode, MappingNode):
                raise ConstructorError(
                    ERR_INTRO,
                    node.start_mark,
                    f"expected a mapping for merging, but found {subnode.id}",
                    subnode.start_mark,
                )
            self.flatten_mapping(subnode)
            submerge.append(subnode.value)

        submerge.reverse()

        for value in submerge:
            merge.extend(value)

    def mapping_node(self, merge, value_node):
        self.flatten_mapping(value_node)
        print("vn0", type(value_node.value), value_node.value)
        merge.extend(value_node.value)

    def scaler_node(self, merge, value_node):

        file_path = None

        try:
            if self.loader.reader.stream is not None:
                file_path = (
                    Path(self.loader.reader.stream.name).parent / value_node.value
                )
        except AttributeError:
            pass

        if file_path is None:
            file_path = Path(value_node.value)

        # there is a bug in ruamel.yaml<=0.17.20 that prevents
        # the use of a Path as argument to compose()
        with file_path.open("rb") as fp:
            merge.extend(ruamel.yaml.YAML().compose(fp).value)

    @staticmethod
    def generate_args(node, key_node) -> list:
        return [
            "while constructing a mapping",
            node.start_mark,
            f'found duplicate key "{key_node.value}"',
            key_node.start_mark,
            "\nTo suppress this check see:\n"
            "http://yaml.readthedocs.io/en/latest/api.html#duplicate-keys\n",
            "\nDuplicate keys will become an error in future releases, and are errors\n"
            "by default when using the new API.\n",
        ]


def from_yaml(stream: Any) -> Any:
    yaml = ruamel.yaml.YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    yaml.Constructor = MyConstructor
    return yaml.load(stream)
