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

PRN_REGEX = r"(prn)(:[a-zA-Z0-9\-]+)*"
PORTFOLIO_PRN_REGEX = r"(prn)(:[a-zA-Z0-9\-]+)"
APP_PRN_REGEX = r"(prn)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)"
BRANCH_PRN_REGEX = r"(prn)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)"
BUILD_PRN_REGEX = (
    r"(prn)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)"
)
COMPONENT_PRN_REGEX = r"(prn)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)(:[a-zA-Z0-9\-]+)"

# Constant for the PRN key
PRN = "prn"
DELIMITER = ":"

# These would typically come in API calles as paramters to a request
ARG_PORTFOLIO_PRN = "portfolio_prn"
ARG_APP_PRN = "app_prn"
ARG_BRANCH_PRN = "branch_prn"
ARG_BUILD_PRN = "build_prn"
ARG_COMPONENT_PRN = "component_prn"
ARG_NAME = "name"


def get_prn_scope(prn: str) -> str | None:
    """
    Returns the scope of the PRN.  The copses are "client", "portfolio", "app", "branch", "build", "component".

    If there are no colons, then the scope is "client"

    Args:
        prn (str): The PRN to extract the scope from

    Returns:
        str | None: The scope of the PRN or None if the PRN is invalid

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
    """
    A little helper that will extract a prn based on various input:

    obj: dict = { "prn": 'prn:portfolio:app:branch:build:component' }
    and return the obj['prn'] value

    obj: str = 'prn:portfolio:app:branch:build:component'
    and return the obj value

    obj: class = Class namespace
    and return the obj.prn vaue

    Args:
        obj (Any): dict, string, or class namespace

    Returns:
        str: the prn value
    """
    if isinstance(obj, dict):
        prn = obj[PRN]
    elif isinstance(obj, str):
        return obj
    elif hasattr(obj, PRN):
        return obj.prn
    return prn


def extract_portfolio(obj: Any) -> str | None:
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[1] if len(prn_sections) > 1 else None


def extract_app(obj: Any) -> str | None:
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[2] if len(prn_sections) > 2 else None


def extract_branch(obj: Any) -> str | None:
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[3] if len(prn_sections) > 3 else None


def extract_build(obj: Any) -> str | None:
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[4] if len(prn_sections) > 4 else None


def extract_component(obj: Any) -> str | None:
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[5] if len(prn_sections) > 5 else None


def extract_portfolio_prn(obj: Any) -> str:
    matches = re.match(PORTFOLIO_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    portfolio_prn = V_EMPTY.join(matches.groups())
    return portfolio_prn


def extract_app_prn(obj: Any) -> str:
    matches = re.match(APP_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    app_prn = V_EMPTY.join(matches.groups())
    return app_prn


def extract_branch_prn(obj: Any) -> str:
    matches = re.match(BRANCH_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    branch_prn = V_EMPTY.join(matches.groups())
    return branch_prn


def extract_build_prn(obj: Any) -> str:
    matches = re.match(BUILD_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    build_prn = V_EMPTY.join(matches.groups())
    return build_prn


def extract_component_prn(obj: Any):
    matches = re.match(COMPONENT_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    component_prn = V_EMPTY.join(matches.groups())
    return component_prn


def generate_prn(item_type: str, request: dict) -> str | None:
    if item_type == SCOPE_PORTFOLIO:
        return generate_portfolio_prn(request)
    elif item_type == SCOPE_APP:
        return generate_app_prn(request)
    elif item_type == SCOPE_BRANCH:
        return generate_branch_prn(request)
    elif item_type == SCOPE_BUILD:
        return generate_build_prn(request)
    elif item_type == SCOPE_COMPONENT:
        return generate_component_prn(request)
    else:
        return None


def validate_prn(item_type: str, prn: Any) -> bool:
    if item_type == SCOPE_PORTFOLIO:
        return validate_portfolio_prn(prn)
    elif item_type == SCOPE_APP:
        return validate_app_prn(prn)
    elif item_type == SCOPE_BRANCH:
        return validate_branch_prn(prn)
    elif item_type == SCOPE_BUILD:
        return validate_build_prn(prn)
    elif item_type == SCOPE_COMPONENT:
        return validate_component_prn(prn)
    else:
        return False


def validate_item_type(item_type: str) -> bool:
    return item_type in [
        SCOPE_PORTFOLIO,
        SCOPE_APP,
        SCOPE_BRANCH,
        SCOPE_BUILD,
        SCOPE_COMPONENT,
    ]


def generate_portfolio_prn(request: dict) -> str:
    if PRN in request and validate_portfolio_prn(request[PRN]):
        return request[PRN]
    elif ARG_PORTFOLIO_PRN in request:
        return extract_portfolio_prn(request[ARG_PORTFOLIO_PRN])
    elif ARG_APP_PRN in request:
        return extract_portfolio_prn(request[ARG_APP_PRN])
    elif ARG_BRANCH_PRN in request:
        return extract_portfolio_prn(request[ARG_BRANCH_PRN])
    elif ARG_BUILD_PRN in request:
        return extract_portfolio_prn(request[ARG_BUILD_PRN])
    else:
        return "{}:{}".format(PRN, request[ARG_NAME])


def generate_app_prn(request: dict) -> str:
    if PRN in request and validate_app_prn(request[PRN]):
        return request[PRN]
    elif ARG_APP_PRN in request:
        return extract_app_prn(request[ARG_APP_PRN])
    elif ARG_BRANCH_PRN in request:
        return extract_app_prn(request[ARG_BRANCH_PRN])
    elif ARG_BUILD_PRN in request:
        return extract_app_prn(request[ARG_BUILD_PRN])
    else:
        return "{}:{}".format(request[ARG_PORTFOLIO_PRN], request[ARG_NAME])


def branch_short_name(name: str) -> str:
    return re.sub(r"[^a-z0-9\\-]", "-", name.lower())[0:20].rstrip("-")


def generate_branch_prn(request: dict) -> str:
    if PRN in request and validate_branch_prn(request[PRN]):
        return request[PRN]
    elif ARG_BRANCH_PRN in request:
        return extract_branch_prn(request[ARG_BRANCH_PRN])
    elif ARG_BUILD_PRN in request:
        return extract_branch_prn(request[ARG_BUILD_PRN])
    else:
        short_name = branch_short_name(request[ARG_NAME])
        return "{}:{}".format(request[ARG_APP_PRN], short_name)


def generate_build_prn(request: dict) -> str:
    if PRN in request and validate_build_prn(request[PRN]):
        return request[PRN]
    elif ARG_BUILD_PRN in request:
        return extract_build_prn(request[ARG_BUILD_PRN])
    else:
        return "{}:{}".format(request[ARG_BRANCH_PRN], request[ARG_NAME])


def generate_component_prn(request: dict) -> str:
    if PRN in request and validate_component_prn(request[PRN]):
        return request[PRN]
    elif ARG_COMPONENT_PRN in request:
        return extract_component_prn(request[ARG_COMPONENT_PRN])
    else:
        return "{}:{}".format(request[ARG_BUILD_PRN], request[ARG_NAME])


def validate_item_prn(prn: str) -> bool:
    return re.fullmatch(PRN_REGEX, prn) is not None


def validate_portfolio_prn(prn: str) -> bool:
    return re.fullmatch(PORTFOLIO_PRN_REGEX, prn) is not None


def validate_app_prn(prn: str) -> bool:
    return re.fullmatch(APP_PRN_REGEX, prn) is not None


def validate_branch_prn(prn: str) -> bool:
    return re.fullmatch(BRANCH_PRN_REGEX, prn) is not None


def validate_build_prn(prn: str) -> bool:
    return re.fullmatch(BUILD_PRN_REGEX, prn) is not None


def validate_component_prn(prn: str) -> bool:
    return re.fullmatch(COMPONENT_PRN_REGEX, prn) is not None
