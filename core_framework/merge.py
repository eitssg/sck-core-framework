"""Dictionary merging utilities for the Core Automation framework.

Provides utilities for deep merging dictionaries with fine-grained control over
merge behavior, including list handling and conditional key merging. Supports
both in-place and immutable merge operations for flexible data manipulation.

Key Features:
    - **Deep merging** with recursive nested dictionary support
    - **List handling** with configurable append or replace behavior
    - **Conditional merging** with custom predicate functions
    - **In-place operations** for memory-efficient mutations
    - **Immutable operations** for functional programming patterns
    - **Nested path setting** for dynamic dictionary construction

Common Use Cases:
    - Configuration file merging and overrides
    - Template parameter combination
    - Deployment specification composition
    - Environment-specific setting overlays
"""

from typing import Any
from collections.abc import Callable
import copy


def deep_copy(obj: Any) -> Any:
    """Create a deep copy of an object.

    Convenience wrapper around copy.deepcopy for consistent object duplication
    throughout the framework.

    Args:
        obj: The object to be copied.

    Returns:
        A new object that is a deep copy of the input object.

    Examples:
        >>> original = {"a": {"b": [1, 2, 3]}}
        >>> copied = deep_copy(original)
        >>> copied["a"]["b"].append(4)
        >>> print(original["a"]["b"])
        [1, 2, 3]  # Original unchanged
        >>> print(copied["a"]["b"])
        [1, 2, 3, 4]  # Copy modified
    """
    return copy.deepcopy(obj)


def __default_should_merge(key: str) -> bool:
    """Default predicate function that always returns True.

    Used by merge functions to indicate that all keys should be merged by default.
    This function serves as the default behavior when no custom merge predicate
    is provided.

    Args:
        key: The key to inspect (unused in this default implementation).

    Returns:
        Always returns True to allow merging of all keys.
    """
    return True


def deep_merge_in_place(
    *dicts: dict[str, Any],
    merge_lists: bool = False,
    should_merge: Callable[[str], bool] = __default_should_merge,
) -> dict[str, Any]:
    """Merge multiple dictionaries into the first dictionary in-place.

    Performs deep merging by recursively combining nested dictionaries and
    optionally handling list concatenation. The first dictionary is modified
    and returned as the result.

    Args:
        *dicts: Variable number of dictionaries to merge. The first dictionary
               is modified to contain the merged result.
        merge_lists: If True, lists from subsequent dictionaries are appended
                    to lists in the base dictionary. If False, lists are replaced.
        should_merge: Predicate function that takes a key and returns True if
                     the value should be overwritten, False to keep original value.

    Returns:
        The first dictionary, now containing the merged values from all inputs.

    Examples:
        >>> base = {"a": 1, "b": {"c": 2}}
        >>> overlay = {"b": {"d": 3}, "e": 4}
        >>> result = deep_merge_in_place(base, overlay)
        >>> print(result)
        {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        >>> print(base is result)
        True  # base was modified in-place

        >>> # List merging behavior
        >>> base = {"items": [1, 2]}
        >>> overlay = {"items": [3, 4]}
        >>> deep_merge_in_place(base, overlay, merge_lists=True)
        >>> print(base["items"])
        [1, 2, 3, 4]  # Lists concatenated

        >>> # Conditional merging
        >>> def skip_protected(key: str) -> bool:
        ...     return not key.startswith("_")
        >>> base = {"public": 1, "_private": 2}
        >>> overlay = {"public": 10, "_private": 20}
        >>> deep_merge_in_place(base, overlay, should_merge=skip_protected)
        >>> print(base)
        {"public": 10, "_private": 2}  # Private key preserved
    """
    merged_dict = dicts[0]
    for d in dicts[1:]:
        __deep_merge(
            merged_dict,
            deep_copy(d),
            merge_lists=merge_lists,
            should_merge=should_merge,
        )
    return merged_dict


def deep_merge(
    *dicts: dict[str, Any],
    merge_lists: bool = False,
    should_merge: Callable[[str], bool] = __default_should_merge,
) -> dict[str, Any]:
    """Merge multiple dictionaries into a new dictionary without mutation.

    Creates a new dictionary containing the merged values from all input
    dictionaries. Original dictionaries remain unchanged, making this suitable
    for functional programming patterns.

    Args:
        *dicts: Variable number of dictionaries to merge. All remain unchanged.
        merge_lists: If True, lists from subsequent dictionaries are appended
                    to lists in the base dictionary. If False, lists are replaced.
        should_merge: Predicate function that takes a key and returns True if
                     the value should be overwritten, False to keep original value.

    Returns:
        A new dictionary containing the merged values from all inputs.

    Examples:
        >>> config_base = {"timeout": 30, "retries": 3}
        >>> config_env = {"timeout": 60, "debug": True}
        >>> merged = deep_merge(config_base, config_env)
        >>> print(merged)
        {"timeout": 60, "retries": 3, "debug": True}
        >>> print(config_base)
        {"timeout": 30, "retries": 3}  # Original unchanged

        >>> # Empty input handling
        >>> result = deep_merge()
        >>> print(result)
        {}

        >>> # Multiple dictionary merging
        >>> base = {"a": 1}
        >>> env1 = {"b": 2}
        >>> env2 = {"c": 3}
        >>> result = deep_merge(base, env1, env2)
        >>> print(result)
        {"a": 1, "b": 2, "c": 3}
    """
    if not dicts:
        return {}
    first_dict = deep_copy(dicts[0])
    return deep_merge_in_place(first_dict, *dicts[1:], merge_lists=merge_lists, should_merge=should_merge)


def __deep_merge(
    dict1: dict[str, Any],
    dict2: dict[str, Any],
    merge_lists: bool = False,
    should_merge: Callable[[str], bool] = __default_should_merge,
) -> None:
    """Recursively merge dict2 into dict1 in-place.

    Internal implementation function that performs the actual recursive merging
    logic. Handles nested dictionaries, list concatenation, and conditional
    key merging based on the provided predicate function.

    Args:
        dict1: The base dictionary to merge into (modified in-place).
        dict2: The dictionary to merge from (read-only).
        merge_lists: If True, appends lists instead of overwriting them.
        should_merge: Predicate function to control value overwriting behavior.

    Side Effects:
        Modifies dict1 in-place with merged values from dict2.

    Merge Logic:
        - **Nested dicts**: Recursively merged
        - **Lists**: Concatenated if merge_lists=True, otherwise replaced
        - **Equal values**: No change (optimization)
        - **Different values**: Replaced if should_merge(key) returns True
        - **New keys**: Always added to the target dictionary
    """
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                __deep_merge(
                    dict1[key],
                    dict2[key],
                    merge_lists=merge_lists,
                    should_merge=should_merge,
                )
            elif merge_lists and isinstance(dict1[key], list) and isinstance(dict2[key], list):
                dict1[key].extend(dict2[key])

            elif dict1[key] == dict2[key]:
                pass  # Do nothing if values are the same

            elif should_merge(key):
                dict1[key] = dict2[key]
        else:
            dict1[key] = dict2[key]


def set_nested(dic: dict, keys: list[str], value: Any) -> None:
    """Set a value in a nested dictionary using a path of keys.

    Creates intermediate nested dictionaries as needed to establish the full
    path to the target location. Useful for dynamically constructing complex
    nested dictionary structures.

    Args:
        dic: The dictionary to modify in-place.
        keys: List of keys representing the path to the value location.
              Must contain at least one key.
        value: The value to set at the specified nested path.

    Raises:
        IndexError: If keys list is empty.
        TypeError: If intermediate path elements cannot be treated as dictionaries.

    Examples:
        >>> config = {}
        >>> set_nested(config, ["database", "connection", "host"], "localhost")
        >>> print(config)
        {"database": {"connection": {"host": "localhost"}}}

        >>> # Extending existing structure
        >>> set_nested(config, ["database", "connection", "port"], 5432)
        >>> set_nested(config, ["database", "pool_size"], 10)
        >>> print(config)
        {
            "database": {
                "connection": {"host": "localhost", "port": 5432},
                "pool_size": 10
            }
        }

        >>> # Single-level setting
        >>> data = {}
        >>> set_nested(data, ["name"], "test")
        >>> print(data)
        {"name": "test"}

    Usage Patterns:
        Common for dynamic configuration building:
        >>> settings = {}
        >>> for env_var, path_value in environment_mappings.items():
        ...     path, default = path_value
        ...     set_nested(settings, path.split('.'), os.getenv(env_var, default))
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value
