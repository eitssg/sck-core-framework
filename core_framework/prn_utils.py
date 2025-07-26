"""Utilities to validate or generate PRN Identifiers."""

from typing import Any
import re
from .constants import (
    SCOPE_CLIENT,
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
    V_EMPTY,
)

PRN_REGEX = r"prn(:[a-zA-Z0-9\-]+)*"
PORTFOLIO_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+"
APP_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
BRANCH_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
BUILD_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
COMPONENT_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"

# Constant for the PRN key
PRN = "prn"
DELIMITER = ":"

# These would typically come in API calls as parameters to a request
ARG_PORTFOLIO_PRN = "portfolio_prn"
ARG_APP_PRN = "app_prn"
ARG_BRANCH_PRN = "branch_prn"
ARG_BUILD_PRN = "build_prn"
ARG_COMPONENT_PRN = "component_prn"
ARG_NAME = "name"


def get_prn_scope(prn: str) -> str | None:
    """Determines the scope of a PRN based on its structure.

    The scope is determined by the number of colons in the PRN string.
    The scopes are "client", "portfolio", "app", "branch", "build", and "component".

    :param prn: The PRN to extract the scope from.
    :type prn: str
    :return: The scope of the PRN or None if the PRN is invalid.
    :rtype: str or None
    """
    # Define the mapping of colon counts to scopes
    scope_mapping = {
        0: SCOPE_CLIENT,
        1: SCOPE_PORTFOLIO,
        2: SCOPE_APP,
        3: SCOPE_BRANCH,
        4: SCOPE_BUILD,
        5: SCOPE_COMPONENT,
    }

    # Count the number of colons in the prn
    c = prn.count(":")

    # Return the corresponding scope or None if the count is greater than 5
    return scope_mapping.get(c, None)


def extract_prn(obj: Any) -> str:
    """Extracts a PRN string from various object types.

    This helper function can extract a PRN from:
    - A dictionary with a 'prn' key.
    - A string that is already a PRN.
    - An object with a 'prn' attribute.

    :param obj: The object to extract the PRN from (dict, str, or object).
    :type obj: Any
    :return: The extracted PRN string, or an empty string if not found.
    :rtype: str
    """
    if isinstance(obj, dict):
        return obj.get(PRN, "")
    elif isinstance(obj, str):
        return obj
    elif hasattr(obj, PRN):
        return getattr(obj, PRN, "")
    return ""


def extract_portfolio(obj: Any) -> str | None:
    """Extracts the portfolio name from a PRN.

    :param obj: An object containing PRN information (dict, str, or object).
    :type obj: Any
    :return: The portfolio name, or None if not found.
    :rtype: str or None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[1] if len(prn_sections) > 1 else None


def extract_app(obj: Any) -> str | None:
    """Extracts the app name from a PRN.

    :param obj: An object containing PRN information (dict, str, or object).
    :type obj: Any
    :return: The app name, or None if not found.
    :rtype: str or None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[2] if len(prn_sections) > 2 else None


def extract_branch(obj: Any) -> str | None:
    """Extracts the branch name from a PRN.

    :param obj: An object containing PRN information (dict, str, or object).
    :type obj: Any
    :return: The branch name, or None if not found.
    :rtype: str or None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[3] if len(prn_sections) > 3 else None


def extract_build(obj: Any) -> str | None:
    """Extracts the build name from a PRN.

    :param obj: An object containing PRN information (dict, str, or object).
    :type obj: Any
    :return: The build name, or None if not found.
    :rtype: str or None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[4] if len(prn_sections) > 4 else None


def extract_component(obj: Any) -> str | None:
    """Extracts the component name from a PRN.

    :param obj: An object containing PRN information (dict, str, or object).
    :type obj: Any
    :return: The component name, or None if not found.
    :rtype: str or None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[5] if len(prn_sections) > 5 else None


def extract_portfolio_prn(obj: Any) -> str:
    """Extracts the portfolio-level PRN from a full PRN string.

    :param obj: An object containing PRN information.
    :type obj: Any
    :return: The portfolio PRN (e.g., "prn:portfolio") or an empty string.
    :rtype: str
    """
    match = re.match(f"({PORTFOLIO_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_app_prn(obj: Any) -> str:
    """Extracts the app-level PRN from a full PRN string.

    :param obj: An object containing PRN information.
    :type obj: Any
    :return: The app PRN (e.g., "prn:portfolio:app") or an empty string.
    :rtype: str
    """
    match = re.match(f"({APP_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_branch_prn(obj: Any) -> str:
    """Extracts the branch-level PRN from a full PRN string.

    :param obj: An object containing PRN information.
    :type obj: Any
    :return: The branch PRN (e.g., "prn:portfolio:app:branch") or an empty string.
    :rtype: str
    """
    match = re.match(f"({BRANCH_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_build_prn(obj: Any) -> str:
    """Extracts the build-level PRN from a full PRN string.

    :param obj: An object containing PRN information.
    :type obj: Any
    :return: The build PRN (e.g., "prn:portfolio:app:branch:build") or an empty string.
    :rtype: str
    """
    match = re.match(f"({BUILD_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_component_prn(obj: Any) -> str:
    """Extracts the component-level PRN from a full PRN string.

    :param obj: An object containing PRN information.
    :type obj: Any
    :return: The component PRN (e.g., "prn:portfolio:app:branch:build:component") or an empty string.
    :rtype: str
    """
    match = re.match(f"({COMPONENT_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def generate_prn(scope: str, request: dict) -> str | None:
    """Generates a PRN based on a scope and a request dictionary.

    The request dictionary should contain PRN information. For example:

    .. code-block:: json

        {
            "prn": "prn:portfolio:app:branch:build",
            "portfolio_prn": "prn:portfolio",
            "app_prn": "prn:portfolio:app",
            "branch_prn": "prn:portfolio:app:branch",
            "name": "new-item-name"
        }

    :param scope: The scope of the PRN to generate ("portfolio", "app", etc.).
    :type scope: str
    :param request: The input dictionary containing PRN and name information.
    :type request: dict
    :return: The generated PRN, or None if the scope is invalid.
    :rtype: str or None
    """
    if scope == SCOPE_PORTFOLIO:
        return generate_portfolio_prn(request)
    elif scope == SCOPE_APP:
        return generate_app_prn(request)
    elif scope == SCOPE_BRANCH:
        return generate_branch_prn(request)
    elif scope == SCOPE_BUILD:
        return generate_build_prn(request)
    elif scope == SCOPE_COMPONENT:
        return generate_component_prn(request)
    else:
        return None


def validate_prn(scope: str, prn: Any) -> bool:
    """Validates a PRN against a specific scope.

    :param scope: The scope to validate against ("portfolio", "app", etc.).
    :type scope: str
    :param prn: The PRN to validate.
    :type prn: Any
    :return: True if the PRN is valid for the given scope, otherwise False.
    :rtype: bool
    """
    prn_str = extract_prn(prn)
    if scope == SCOPE_PORTFOLIO:
        return validate_portfolio_prn(prn_str)
    elif scope == SCOPE_APP:
        return validate_app_prn(prn_str)
    elif scope == SCOPE_BRANCH:
        return validate_branch_prn(prn_str)
    elif scope == SCOPE_BUILD:
        return validate_build_prn(prn_str)
    elif scope == SCOPE_COMPONENT:
        return validate_component_prn(prn_str)
    else:
        return False


def validate_item_type(scope: str) -> bool:
    """Validates if a scope string is a recognized PRN scope.

    :param scope: The scope string to validate.
    :type scope: str
    :return: True if the scope is valid, otherwise False.
    :rtype: bool
    """
    return scope in [
        SCOPE_PORTFOLIO,
        SCOPE_APP,
        SCOPE_BRANCH,
        SCOPE_BUILD,
        SCOPE_COMPONENT,
    ]


def generate_portfolio_prn(request: dict) -> str:
    """Generates or extracts a portfolio-level PRN from a request dictionary.

    It checks for a valid portfolio PRN in the 'prn' key first. If not found,
    it attempts to extract it from other PRN keys. If all else fails, it
    constructs a new PRN using the 'name' key (e.g., "prn:<name>").

    :param request: The dictionary containing PRN and name information.
    :type request: dict
    :return: The extracted or generated portfolio PRN.
    :rtype: str
    """
    prn = request.get(PRN, "")
    if validate_portfolio_prn(prn):
        return prn

    for key in [ARG_PORTFOLIO_PRN, ARG_APP_PRN, ARG_BRANCH_PRN, ARG_BUILD_PRN]:
        if key in request:
            portfolio_prn = extract_portfolio_prn(request[key])
            if portfolio_prn:
                return portfolio_prn

    return f"{PRN}{DELIMITER}{request.get(ARG_NAME, '')}"


def generate_app_prn(request: dict) -> str:
    """Generates or extracts an app-level PRN from a request dictionary.

    It checks for a valid app PRN in the 'prn' key first. If not found,
    it attempts to extract it from other PRN keys. If all else fails, it
    constructs a new PRN by appending the 'name' key to the portfolio PRN.

    :param request: The dictionary containing PRN and name information.
    :type request: dict
    :return: The extracted or generated app PRN.
    :rtype: str
    """
    prn = request.get(PRN, "")
    if validate_app_prn(prn):
        return prn

    for key in [ARG_APP_PRN, ARG_BRANCH_PRN, ARG_BUILD_PRN]:
        if key in request:
            app_prn = extract_app_prn(request[key])
            if app_prn:
                return app_prn

    portfolio_prn = generate_portfolio_prn(request)
    return f"{portfolio_prn}{DELIMITER}{request.get(ARG_NAME, '')}"


def branch_short_name(name: str | None) -> str | None:
    """Generates a sanitized, shortened name for a branch.

    The name is converted to lower case, non-alphanumeric characters (except
    hyphens) are replaced with hyphens, and it is truncated to 20 characters.

    :param name: The branch name to shorten.
    :type name: str or None
    :return: The shortened and sanitized branch name.
    :rtype: str or None
    """
    if name is None:
        return None
    if not name:
        return V_EMPTY
    return re.sub(r"[^a-z0-9\-]", "-", name.lower())[:20].rstrip("-")


def generate_branch_prn(request: dict) -> str:
    """Generates or extracts a branch-level PRN from a request dictionary.

    It checks for a valid branch PRN in the 'prn' key first. If not found,
    it attempts to extract it from other PRN keys. If all else fails, it

    constructs a new PRN by appending a shortened 'name' to the app PRN.

    :param request: The dictionary containing PRN and name information.
    :type request: dict
    :return: The extracted or generated branch PRN.
    :rtype: str
    """
    prn = request.get(PRN, "")
    if validate_branch_prn(prn):
        return prn

    for key in [ARG_BRANCH_PRN, ARG_BUILD_PRN]:
        if key in request:
            branch_prn = extract_branch_prn(request[key])
            if branch_prn:
                return branch_prn

    app_prn = generate_app_prn(request)
    short_name = branch_short_name(request.get(ARG_NAME, ""))
    return f"{app_prn}{DELIMITER}{short_name}"


def generate_build_prn(request: dict) -> str:
    """Generates or extracts a build-level PRN from a request dictionary.

    It checks for a valid build PRN in the 'prn' key first. If not found,
    it attempts to extract it from other PRN keys. If all else fails, it
    constructs a new PRN by appending the 'name' key to the branch PRN.

    :param request: The dictionary containing PRN and name information.
    :type request: dict
    :return: The extracted or generated build PRN.
    :rtype: str
    """
    prn = request.get(PRN, "")
    if validate_build_prn(prn):
        return prn

    if ARG_BUILD_PRN in request:
        build_prn = extract_build_prn(request[ARG_BUILD_PRN])
        if build_prn:
            return build_prn

    branch_prn = generate_branch_prn(request)
    return f"{branch_prn}{DELIMITER}{request.get(ARG_NAME, '')}"


def generate_component_prn(request: dict) -> str:
    """Generates or extracts a component-level PRN from a request dictionary.

    It checks for a valid component PRN in the 'prn' key first. If not found,
    it attempts to extract it from other PRN keys. If all else fails, it
    constructs a new PRN by appending the 'name' key to the build PRN.

    :param request: The dictionary containing PRN and name information.
    :type request: dict
    :return: The extracted or generated component PRN.
    :rtype: str
    """
    prn = request.get(PRN, "")
    if validate_component_prn(prn):
        return prn

    if ARG_COMPONENT_PRN in request:
        component_prn = extract_component_prn(request[ARG_COMPONENT_PRN])
        if component_prn:
            return component_prn

    build_prn = generate_build_prn(request)
    return f"{build_prn}{DELIMITER}{request.get(ARG_NAME, '')}"


def validate_item_prn(prn: str) -> bool:
    """Validates if a string conforms to the general PRN format.

    :param prn: The PRN string to validate.
    :type prn: str
    :return: True if the PRN format is valid, otherwise False.
    :rtype: bool
    """
    return re.fullmatch(PRN_REGEX, prn) is not None


def validate_portfolio_prn(prn: str) -> bool:
    """Validates if a string is a valid portfolio-level PRN.

    :param prn: The PRN string to validate.
    :type prn: str
    :return: True if the PRN is a valid portfolio PRN, otherwise False.
    :rtype: bool
    """
    return re.fullmatch(PORTFOLIO_PRN_REGEX, prn) is not None


def validate_app_prn(prn: str) -> bool:
    """Validates if a string is a valid app-level PRN.

    :param prn: The PRN string to validate.
    :type prn: str
    :return: True if the PRN is a valid app PRN, otherwise False.
    :rtype: bool
    """
    return re.fullmatch(APP_PRN_REGEX, prn) is not None


def validate_branch_prn(prn: str) -> bool:
    """Validates if a string is a valid branch-level PRN.

    :param prn: The PRN string to validate.
    :type prn: str
    :return: True if the PRN is a valid branch PRN, otherwise False.
    :rtype: bool
    """
    return re.fullmatch(BRANCH_PRN_REGEX, prn) is not None


def validate_build_prn(prn: str) -> bool:
    """Validates if a string is a valid build-level PRN.

    :param prn: The PRN string to validate.
    :type prn: str
    :return: True if the PRN is a valid build PRN, otherwise False.
    :rtype: bool
    """
    return re.fullmatch(BUILD_PRN_REGEX, prn) is not None


def validate_component_prn(prn: str) -> bool:
    """Validates if a string is a valid component-level PRN.

    :param prn: The PRN string to validate.
    :type prn: str
    :return: True if the PRN is a valid component PRN, otherwise False.
    :rtype: bool
    """
    return re.fullmatch(COMPONENT_PRN_REGEX, prn) is not None
