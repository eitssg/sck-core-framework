from typing import Any

from collections.abc import Callable

import copy


def deep_copy(obj: Any) -> Any:
    return copy.deepcopy(obj)


def __default_should_merge(key: str) -> bool:
    """
    This is the default function that always return 'True' to merge all keys.

    Args:
        key (str): The key to inspect

    Returns:
        bool: Return True or False if the key should be merged or not.
    """
    return True


def deep_merge_in_place(
    *dicts: dict[str, Any],
    merge_lists: bool = False,
    should_merge: Callable[[str], bool] = __default_should_merge
) -> dict[str, Any]:
    """
    Merge multiple dictionaries into the first dictionary in place.  Mutates the first dictionary.

    Args:
        *dicts (dict[str, Any]): the dictionaries to merge
        merge_lists (bool, optional): True to merge lists. Defaults to False.
        should_merge (Callable[[str], bool], optional): supply a function to check if a particular.
            key should be marged or not.  Defaults to merge all keys.

    Returns:
        dict[str, Any]: the first dictionary
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
    should_merge: Callable[[str], bool] = __default_should_merge
) -> dict[str, Any]:
    """
    Merges multiple dictionaries into a new dictionary.  Does not mutate the original dictionaries.

    Args:
        *dicts (dict[str, Any]): the dictionaries to merge
        merge_lists (bool, optional): _description_. Defaults to False.
        should_merge (Callable[[str], bool], optional): _description_. Defaults to __default_should_merge.

    Returns:
        dict[str, Any]: A new merged dictionary
    """
    first_dict = deep_copy(dicts[0])
    return deep_merge_in_place(
        first_dict, *dicts[1:], merge_lists=merge_lists, should_merge=should_merge
    )


def __deep_merge(
    dict1: dict[str, Any],
    dict2: dict[str, Any],
    merge_lists: bool = False,
    should_merge: Callable[[str], bool] = __default_should_merge,
) -> None:
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                __deep_merge(
                    dict1[key],
                    dict2[key],
                    merge_lists=merge_lists,
                    should_merge=should_merge,
                )
            elif (
                merge_lists
                and isinstance(dict1[key], list)
                and isinstance(dict2[key], list)
            ):
                dict1[key] = dict1[key] + dict2[key]

            elif dict1[key] == dict2[key]:
                pass

            elif should_merge(key):
                dict1[key] = dict2[key]
        else:
            dict1[key] = dict2[key]


def set_nested(dic: dict, keys: list, value: Any) -> None:
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value
