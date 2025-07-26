"""Provides utilities for deep merging dictionaries with fine-grained control."""

from typing import Any
from collections.abc import Callable
import copy


def deep_copy(obj: Any) -> Any:
    """Creates a deep copy of an object.

    This is a convenience wrapper around ``copy.deepcopy``.

    :param obj: The object to be copied.
    :type obj: Any
    :return: A new object that is a deep copy of the input object.
    :rtype: Any
    """
    return copy.deepcopy(obj)


def __default_should_merge(key: str) -> bool:
    """Default predicate function that always returns True.

    Used by merge functions to indicate that all keys should be merged by default.

    :param key: The key to inspect (unused in this default implementation).
    :type key: str
    :return: Always returns True.
    :rtype: bool
    """
    return True


def deep_merge_in_place(
    *dicts: dict[str, Any],
    merge_lists: bool = False,
    should_merge: Callable[[str], bool] = __default_should_merge,
) -> dict[str, Any]:
    """Merges multiple dictionaries into the first dictionary in-place, mutating it.

    :param dicts: The dictionaries to merge. The first dictionary is modified.
    :type dicts: dict[str, Any]
    :param merge_lists: If True, lists from subsequent dictionaries are
        appended to the list in the base dictionary. Defaults to False.
    :type merge_lists: bool, optional
    :param should_merge: A function that takes a key and returns True if a value
        for that key should be overwritten, or False to keep the original value.
        Defaults to merging all keys.
    :type should_merge: Callable[[str], bool], optional
    :return: The first dictionary, now containing the merged values.
    :rtype: dict[str, Any]
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
    """Merges multiple dictionaries into a new dictionary, without mutating the originals.

    :param dicts: The dictionaries to merge.
    :type dicts: dict[str, Any]
    :param merge_lists: If True, lists from subsequent dictionaries are
        appended to the list in the base dictionary. Defaults to False.
    :type merge_lists: bool, optional
    :param should_merge: A function that takes a key and returns True if a value
        for that key should be overwritten, or False to keep the original value.
        Defaults to merging all keys.
    :type should_merge: Callable[[str], bool], optional
    :return: A new dictionary containing the merged values.
    :rtype: dict[str, Any]
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
    """Recursively merges dict2 into dict1 in-place.

    :param dict1: The base dictionary to merge into (mutated).
    :type dict1: dict[str, Any]
    :param dict2: The dictionary to merge from.
    :type dict2: dict[str, Any]
    :param merge_lists: If True, appends lists instead of overwriting.
    :type merge_lists: bool
    :param should_merge: Predicate to control overwriting values.
    :type should_merge: Callable[[str], bool]
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
    """Sets a value in a nested dictionary using a list of keys.

    Creates nested dictionaries if they do not exist.

    :param dic: The dictionary to modify.
    :type dic: dict
    :param keys: A list of keys representing the path to the value.
    :type keys: list[str]
    :param value: The value to set at the specified path.
    :type value: Any
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value
