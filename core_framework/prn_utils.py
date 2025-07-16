"""Utilities to validate or generate PRN Identifiers"""

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
        prn = obj.get(PRN, "")
    elif isinstance(obj, str):
        return obj
    elif hasattr(obj, PRN):
        return obj.prn
    return prn


def extract_portfolio(obj: Any) -> str | None:
    """
    Extract the portfolio from the provided Object which can be a string or dictionary

    Args:
        obj (Any): The Identity or PRN information

    Returns:
        str | None: The portfolio name or None if not found
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[1] if len(prn_sections) > 1 else None


def extract_app(obj: Any) -> str | None:
    """
    Extract the app from the provided Object which can be a string or dictionary

    Args:
        obj (Any): The Identity or PRN information

    Returns:
        str | None: The app name or None if not found
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[2] if len(prn_sections) > 2 else None


def extract_branch(obj: Any) -> str | None:
    """
    Extract the branch from the provided Object which can be a string or dictionary

    Args:
        obj (Any): The Identity or PRN information

    Returns:
        str | None: The branch name or None if not found
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[3] if len(prn_sections) > 3 else None


def extract_build(obj: Any) -> str | None:
    """
    Extract the build from the provided Object which can be a string or dictionary

    Args:
        obj (Any): The Identity or PRN information

    Returns:
        str | None: The build name or None if not found
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[4] if len(prn_sections) > 4 else None


def extract_component(obj: Any) -> str | None:
    """
    Extract the component from the provided Object which can be a string or dictionary

    Args:
        obj (Any): The Identity or PRN information

    Returns:
        str | None: The component name or None if not found
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[5] if len(prn_sections) > 5 else None


def extract_portfolio_prn(obj: Any) -> str:
    """
    Uses a regular expression to extract the portfolio prn from the provided object
    after calling the extract_prn function to get the prn value.

    Args:
        obj (Any): The PRN information

    Returns:
        str: The portfolio prn in the formatn "prn:portfolio" or ""
    """

    matches = re.match(PORTFOLIO_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    portfolio_prn = V_EMPTY.join(matches.groups())
    return portfolio_prn


def extract_app_prn(obj: Any) -> str:
    """
    Uses a regular expression to extract the app prn from the provided object
    after calling the extract_prn function to get the prn value.

    Args:
        obj (Any): The PRN information

    Returns:
        str: The app prn in the formatn "prn:portfolio:app" or ""
    """
    matches = re.match(APP_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    app_prn = V_EMPTY.join(matches.groups())
    return app_prn


def extract_branch_prn(obj: Any) -> str:
    """
    Uses a regular expression to extract the branch prn from the provided object
    after calling the extract_prn function to get the prn value.

    Args:
        obj (Any): The PRN information

    Returns:
        str: The branch prn in the formatn "prn:portfolio:app:branch" or ""
    """
    matches = re.match(BRANCH_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    branch_prn = V_EMPTY.join(matches.groups())
    return branch_prn


def extract_build_prn(obj: Any) -> str:
    """
    Uses a regular expression to extract the build prn from the provided object
    after calling the extract_prn function to get the prn value.

    Args:
        obj (Any): The PRN information

    Returns:
        str: The build prn in the formatn "prn:portfolio:app:branch:build" or ""
    """
    matches = re.match(BUILD_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    build_prn = V_EMPTY.join(matches.groups())
    return build_prn


def extract_component_prn(obj: Any) -> str:
    """
    Uses a regular expression to extract the component prn from the provided object
    after calling the extract_prn function to get the prn value.

    Args:
        obj (Any): The PRN information

    Returns:
        str: The component prn in the formatn "prn:portfolio:app:branch:build:component" or ""
    """
    matches = re.match(COMPONENT_PRN_REGEX, extract_prn(obj))
    if matches is None:
        return V_EMPTY
    component_prn = V_EMPTY.join(matches.groups())
    return component_prn


def generate_prn(scope: str, request: dict) -> str | None:
    """
    Generate a prn from the item_type which is "portfolio", "app", "branch", "build", or "component"
    and the request informatin such as:

    request should contain PRN's at the top level including one or more of the following:

    .. code-block:: json

            {
                "prn": "prn:portfolio:app:branch:build",
                "portfolio_prn": "prn:portfolio",
                "app_prn": "prn:portfolio:app",
                "branch_prn": "prn:portfolio:app:branch",
                "build_prn": "prn:portfolip:app:branch:build",
                "component_prn": "prn:portfolio:app:branch:build:component",
            }

    The primary attribute in requests object is "prn" and if not present, the other keys
    will be insspected based on the scope.

    Args:
        scope (str): The type/scope of item: "portfolio", "app", "branch", "build", or "component"
        request (dict): The input dictionary

    Returns:
        str | None: The generated PRN or None if the item_type is invalid or the prn cannot be determined.
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
    """
    Validate the PRN based on the scope of the item.  The scopes are "portfolio", "app", "branch", "build", or "component"

    Args:
        scope (str): The type/scope of item: "portfolio", "app", "branch", "build", or "component"
        prn (Any): The Pipeline Reference Number (PRN) to validate.

    Returns:
        bool: True if the PRN is valid for the scope.

    """

    if scope == SCOPE_PORTFOLIO:
        return validate_portfolio_prn(prn)
    elif scope == SCOPE_APP:
        return validate_app_prn(prn)
    elif scope == SCOPE_BRANCH:
        return validate_branch_prn(prn)
    elif scope == SCOPE_BUILD:
        return validate_build_prn(prn)
    elif scope == SCOPE_COMPONENT:
        return validate_component_prn(prn)
    else:
        return False


def validate_item_type(scope: str) -> bool:
    """
    Validate the scope to ensure it is one of the valid values: "portfolio", "app", "branch", "build", or "component"

    Args:
        scope (str): A string to inspect

    Returns:
        bool: True if the scope is one of the valid values
    """
    return scope in [
        SCOPE_PORTFOLIO,
        SCOPE_APP,
        SCOPE_BRANCH,
        SCOPE_BUILD,
        SCOPE_COMPONENT,
    ]


def generate_portfolio_prn(request: dict) -> str:
    """
    Inspects the rqeust dictionary and looks for a prn that can be considered a "portfolio" prn.

    It will inspect "prn" first, and if that is not a portfolio prn, it will generate a portfolio
    prn from one of the following keys: "portfolio_prn", "app_prn", "branch_prn", or "build_prn"

    If none of the supplied prn's are valid, a PRN will be constructed using the "name" attribute
    of the request object. "prn:<name>"

    Args:
        request (dict): The object containing PRN's

    Returns:
        str: The extracted or generated portfolio prn
    """
    if PRN in request and validate_portfolio_prn(request[PRN]):
        return request[PRN]
    elif ARG_PORTFOLIO_PRN in request:
        return extract_portfolio_prn(request.get(ARG_PORTFOLIO_PRN))
    elif ARG_APP_PRN in request:
        return extract_portfolio_prn(request.get(ARG_APP_PRN))
    elif ARG_BRANCH_PRN in request:
        return extract_portfolio_prn(request.get(ARG_BRANCH_PRN))
    elif ARG_BUILD_PRN in request:
        return extract_portfolio_prn(request.get(ARG_BUILD_PRN))
    else:
        return "{}:{}".format(PRN, request.get(ARG_NAME))


def generate_app_prn(request: dict) -> str:
    """
    Inspects the rqeust dictionary and looks for a prn that can be considered a "app" prn.

    It will inspect "prn" first, and if that is not a app prn, it will generate a app
    prn from one of the following keys: "portfolio_prn", "app_prn", "branch_prn", or "build_prn"

    If none of the supplied prn's are valid, a PRN will be constructed using the "name" attribute
    of the request object. "prn:portfolio:<name>"

    Args:
        request (dict): The object containing PRN's

    Returns:
        str: The extracted or generated app prn
    """
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


def branch_short_name(name: str | None) -> str | None:
    """
    Geneerate a short name for a branch based on the name attribute.  The name will be lower case
    and should contain only letters, numbers, and hyphens.  The name will be truncated to 20 characters.

    Args:
        name (str): The name to shorten.  Usually the name of the branch

    Returns:
        str: The shortened name.
    """
    if name is None:
        return None
    if not name:
        return V_EMPTY
    return re.sub(r"[^a-z0-9\\-]", "-", name.lower())[0:20].rstrip("-")


def generate_branch_prn(request: dict) -> str:
    """
    Inspects the rqeust dictionary and looks for a prn that can be considered a "branch" prn.

    It will inspect "prn" first, and if that is not a branch prn, it will generate a branch
    prn from one of the following keys: "portfolio_prn", "app_prn", "branch_prn", or "build_prn"

    If none of the supplied prn's are valid, a PRN will be constructed using the "name" attribute
    of the request object. "prn:portfolio:app:<name>"

    Args:
        request (dict): The object containing PRN's

    Returns:
        str: The extracted or generated branch prn
    """
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
    """
    Inspects the rqeust dictionary and looks for a prn that can be considered a "build" prn.

    It will inspect "prn" first, and if that is not a build prn, it will generate a build
    prn from one of the following keys: "portfolio_prn", "app_prn", "branch_prn", or "build_prn"

    If none of the supplied prn's are valid, a PRN will be constructed using the "name" attribute
    of the request object. "prn:portfolio:app:branch:<name>"

    Args:
        request (dict): The object containing PRN's

    Returns:
        str: The extracted or generated build prn
    """
    if PRN in request and validate_build_prn(request[PRN]):
        return request[PRN]
    elif ARG_BUILD_PRN in request:
        return extract_build_prn(request[ARG_BUILD_PRN])
    else:
        return "{}:{}".format(request[ARG_BRANCH_PRN], request[ARG_NAME])


def generate_component_prn(request: dict) -> str:
    """
    Inspects the rqeust dictionary and looks for a prn that can be considered a "componnent" prn.

    It will inspect "prn" first, and if that is not a component prn, it will generate a component
    prn from one of the following keys: "portfolio_prn", "app_prn", "branch_prn", or "build_prn"

    If none of the supplied prn's are valid, a PRN will be constructed using the "name" attribute
    of the request object. "prn:portfolio:app:branch:build:<name>"

    Args:
        request (dict): The object containing PRN's

    Returns:
        str: The extracted or generated component prn
    """
    if PRN in request and validate_component_prn(request[PRN]):
        return request[PRN]
    elif ARG_COMPONENT_PRN in request:
        return extract_component_prn(request[ARG_COMPONENT_PRN])
    else:
        return "{}:{}".format(request[ARG_BUILD_PRN], request[ARG_NAME])


def validate_item_prn(prn: str) -> bool:
    """
    Uses the regular express PRN_REGEX to determine if the PRN is valid.

    Args:
        prn (str): A Pipeline Reference Number

    Returns:
        bool: Ture if the PRN is valid
    """
    return re.fullmatch(PRN_REGEX, prn) is not None


def validate_portfolio_prn(prn: str) -> bool:
    """
    Uses the regular express PORTFOLIO_PRN_REGEX to determine if the PRN is valid

    Args:
        prn (str): A Pipeline Reference Number

    Returns:
        bool: True if the PRN is valid
    """
    return re.fullmatch(PORTFOLIO_PRN_REGEX, prn) is not None


def validate_app_prn(prn: str) -> bool:
    """
    Uses the regular express APP_PRN_REGEX to determine if the PRN is valid

    Args:
        prn (str): A Pipeline Reference Number

    Returns:
        bool: True if the PRN is valid
    """
    return re.fullmatch(APP_PRN_REGEX, prn) is not None


def validate_branch_prn(prn: str) -> bool:
    """
    Uses the regular express BRANCH_PRN_REGEX to determine if the PRN is valid

    Args:
        prn (str): A Pipeline Reference Number

    Returns:
        bool: True if the PRN is valid
    """
    return re.fullmatch(BRANCH_PRN_REGEX, prn) is not None


def validate_build_prn(prn: str) -> bool:
    """
    Uses the regular express BUILD_PRN_REGEX to determine if the PRN is valid

    Args:
        prn (str): A Pipeline Reference Number

    Returns:
        bool: True if the PRN is valid
    """
    return re.fullmatch(BUILD_PRN_REGEX, prn) is not None


def validate_component_prn(prn: str) -> bool:
    """
    Uses the regular express COMPONENT_PRN_REGEX to determine if the PRN is valid

    Args:
        prn (str): A Pipeline Reference Number

    Returns:
        bool: True if the PRN is valid
    """
    return re.fullmatch(COMPONENT_PRN_REGEX, prn) is not None
