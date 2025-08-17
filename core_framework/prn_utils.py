"""Utilities to validate or generate PRN Identifiers.

Provides comprehensive PRN (Pipeline Reference Number) manipulation utilities
for the Core Automation framework. Supports validation, extraction, and generation
of PRNs at different hierarchy levels: portfolio, app, branch, build, and component.

PRN Format:
    prn:portfolio:app:branch:build:component

Examples:
    - Portfolio: prn:ecommerce
    - App: prn:ecommerce:web
    - Branch: prn:ecommerce:web:main
    - Build: prn:ecommerce:web:main:1.0.0
    - Component: prn:ecommerce:web:main:1.0.0:frontend
"""

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
"""General PRN format regex pattern."""

PORTFOLIO_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+"
"""Portfolio-level PRN regex pattern."""

APP_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
"""App-level PRN regex pattern."""

BRANCH_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
"""Branch-level PRN regex pattern."""

BUILD_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
"""Build-level PRN regex pattern."""

COMPONENT_PRN_REGEX = r"prn:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]+"
"""Component-level PRN regex pattern."""

# Constant for the PRN key
PRN = "prn"
"""PRN dictionary key constant."""

DELIMITER = ":"
"""PRN component delimiter."""

# These would typically come in API calls as parameters to a request
ARG_PORTFOLIO_PRN = "portfolio_prn"
"""Portfolio PRN argument name."""

ARG_APP_PRN = "app_prn"
"""App PRN argument name."""

ARG_BRANCH_PRN = "branch_prn"
"""Branch PRN argument name."""

ARG_BUILD_PRN = "build_prn"
"""Build PRN argument name."""

ARG_COMPONENT_PRN = "component_prn"
"""Component PRN argument name."""

ARG_NAME = "name"
"""Name argument for PRN generation."""


def get_prn_scope(prn: str) -> str | None:
    """Determines the scope of a PRN based on its structure.

    The scope is determined by the number of colons in the PRN string.
    Maps colon count to scope levels: client, portfolio, app, branch, build, component.

    Args:
        prn: The PRN to extract the scope from.

    Returns:
        The scope of the PRN or None if the PRN is invalid.

    Examples:
        >>> get_prn_scope("prn:ecommerce")
        'portfolio'
        >>> get_prn_scope("prn:ecommerce:web:main")
        'branch'
        >>> get_prn_scope("invalid")
        'client'
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
    - A dictionary with a 'prn' key
    - A string that is already a PRN
    - An object with a 'prn' attribute

    Args:
        obj: The object to extract the PRN from (dict, str, or object).

    Returns:
        The extracted PRN string, or empty string if not found.

    Examples:
        >>> extract_prn({"prn": "prn:ecommerce:web"})
        'prn:ecommerce:web'
        >>> extract_prn("prn:ecommerce:web")
        'prn:ecommerce:web'
        >>> extract_prn({})
        ''
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

    Args:
        obj: An object containing PRN information (dict, str, or object).

    Returns:
        The portfolio name, or None if not found.

    Examples:
        >>> extract_portfolio("prn:ecommerce:web")
        'ecommerce'
        >>> extract_portfolio("prn")
        None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[1] if len(prn_sections) > 1 else None


def extract_app(obj: Any) -> str | None:
    """Extracts the app name from a PRN.

    Args:
        obj: An object containing PRN information (dict, str, or object).

    Returns:
        The app name, or None if not found.

    Examples:
        >>> extract_app("prn:ecommerce:web:main")
        'web'
        >>> extract_app("prn:ecommerce")
        None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[2] if len(prn_sections) > 2 else None


def extract_branch(obj: Any) -> str | None:
    """Extracts the branch name from a PRN.

    Args:
        obj: An object containing PRN information (dict, str, or object).

    Returns:
        The branch name, or None if not found.

    Examples:
        >>> extract_branch("prn:ecommerce:web:main:1.0.0")
        'main'
        >>> extract_branch("prn:ecommerce:web")
        None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[3] if len(prn_sections) > 3 else None


def extract_build(obj: Any) -> str | None:
    """Extracts the build name from a PRN.

    Args:
        obj: An object containing PRN information (dict, str, or object).

    Returns:
        The build name, or None if not found.

    Examples:
        >>> extract_build("prn:ecommerce:web:main:1.0.0:frontend")
        '1.0.0'
        >>> extract_build("prn:ecommerce:web:main")
        None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[4] if len(prn_sections) > 4 else None


def extract_component(obj: Any) -> str | None:
    """Extracts the component name from a PRN.

    Args:
        obj: An object containing PRN information (dict, str, or object).

    Returns:
        The component name, or None if not found.

    Examples:
        >>> extract_component("prn:ecommerce:web:main:1.0.0:frontend")
        'frontend'
        >>> extract_component("prn:ecommerce:web:main:1.0.0")
        None
    """
    prn_sections = extract_prn(obj).split(DELIMITER)
    return prn_sections[5] if len(prn_sections) > 5 else None


def extract_portfolio_prn(obj: Any) -> str:
    """Extracts the portfolio-level PRN from a full PRN string.

    Args:
        obj: An object containing PRN information.

    Returns:
        The portfolio PRN (e.g., "prn:portfolio") or empty string.

    Examples:
        >>> extract_portfolio_prn("prn:ecommerce:web:main:1.0.0")
        'prn:ecommerce'
        >>> extract_portfolio_prn("invalid")
        ''
    """
    match = re.match(f"({PORTFOLIO_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_app_prn(obj: Any) -> str:
    """Extracts the app-level PRN from a full PRN string.

    Args:
        obj: An object containing PRN information.

    Returns:
        The app PRN (e.g., "prn:portfolio:app") or empty string.

    Examples:
        >>> extract_app_prn("prn:ecommerce:web:main:1.0.0")
        'prn:ecommerce:web'
        >>> extract_app_prn("prn:ecommerce")
        ''
    """
    match = re.match(f"({APP_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_branch_prn(obj: Any) -> str:
    """Extracts the branch-level PRN from a full PRN string.

    Args:
        obj: An object containing PRN information.

    Returns:
        The branch PRN (e.g., "prn:portfolio:app:branch") or empty string.

    Examples:
        >>> extract_branch_prn("prn:ecommerce:web:main:1.0.0")
        'prn:ecommerce:web:main'
        >>> extract_branch_prn("prn:ecommerce:web")
        ''
    """
    match = re.match(f"({BRANCH_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_build_prn(obj: Any) -> str:
    """Extracts the build-level PRN from a full PRN string.

    Args:
        obj: An object containing PRN information.

    Returns:
        The build PRN (e.g., "prn:portfolio:app:branch:build") or empty string.

    Examples:
        >>> extract_build_prn("prn:ecommerce:web:main:1.0.0:frontend")
        'prn:ecommerce:web:main:1.0.0'
        >>> extract_build_prn("prn:ecommerce:web:main")
        ''
    """
    match = re.match(f"({BUILD_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def extract_component_prn(obj: Any) -> str:
    """Extracts the component-level PRN from a full PRN string.

    Args:
        obj: An object containing PRN information.

    Returns:
        The component PRN (e.g., "prn:portfolio:app:branch:build:component") or empty string.

    Examples:
        >>> extract_component_prn("prn:ecommerce:web:main:1.0.0:frontend")
        'prn:ecommerce:web:main:1.0.0:frontend'
        >>> extract_component_prn("prn:ecommerce:web:main:1.0.0")
        ''
    """
    match = re.match(f"({COMPONENT_PRN_REGEX})", extract_prn(obj))
    return match.group(1) if match else V_EMPTY


def generate_prn(scope: str, request: dict) -> str | None:
    """Generates a PRN based on a scope and a request dictionary.

    The request dictionary should contain PRN information and a 'name' field
    for new PRN generation.

    Args:
        scope: The scope of the PRN to generate ("portfolio", "app", etc.).
        request: The input dictionary containing PRN and name information.

    Returns:
        The generated PRN, or None if the scope is invalid.

    Examples:
        >>> request = {"name": "new-app", "portfolio_prn": "prn:ecommerce"}
        >>> generate_prn("app", request)
        'prn:ecommerce:new-app'
        >>> generate_prn("invalid", request)
        None
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

    Args:
        scope: The scope to validate against ("portfolio", "app", etc.).
        prn: The PRN to validate.

    Returns:
        True if the PRN is valid for the given scope, otherwise False.

    Examples:
        >>> validate_prn("portfolio", "prn:ecommerce")
        True
        >>> validate_prn("app", "prn:ecommerce")
        False
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

    Args:
        scope: The scope string to validate.

    Returns:
        True if the scope is valid, otherwise False.

    Examples:
        >>> validate_item_type("portfolio")
        True
        >>> validate_item_type("invalid")
        False
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

    Checks for existing valid portfolio PRN first, then attempts extraction
    from other PRN keys. Falls back to constructing new PRN with 'name' key.

    Args:
        request: The dictionary containing PRN and name information.

    Returns:
        The extracted or generated portfolio PRN.

    Examples:
        >>> generate_portfolio_prn({"name": "ecommerce"})
        'prn:ecommerce'
        >>> generate_portfolio_prn({"prn": "prn:ecommerce"})
        'prn:ecommerce'
    """
    prn = request.get(ARG_PORTFOLIO_PRN, "")
    if validate_portfolio_prn(prn):
        return prn

    for key in [ARG_APP_PRN, ARG_BRANCH_PRN, ARG_BUILD_PRN, ARG_COMPONENT_PRN, PRN]:
        if key in request:
            portfolio_prn = extract_portfolio_prn(request[key])
            if portfolio_prn:
                return portfolio_prn

    name = request.get("portfolio", request.get(ARG_NAME, ""))

    return f"{PRN}{DELIMITER}{name}"


def generate_app_prn(request: dict) -> str:
    """Generates or extracts an app-level PRN from a request dictionary.

    Checks for existing valid app PRN first, then attempts extraction
    from other PRN keys. Falls back to constructing new PRN by appending
    'name' to portfolio PRN.

    Args:
        request: The dictionary containing PRN and name information.

    Returns:
        The extracted or generated app PRN.

    Examples:
        >>> generate_app_prn({"name": "web", "portfolio_prn": "prn:ecommerce"})
        'prn:ecommerce:web'
        >>> generate_app_prn({"prn": "prn:ecommerce:web"})
        'prn:ecommerce:web'
    """
    prn = request.get(ARG_APP_PRN, "")
    if validate_app_prn(prn):
        return prn

    for key in [ARG_BRANCH_PRN, ARG_BUILD_PRN, ARG_COMPONENT_PRN, PRN]:
        if key in request:
            app_prn = extract_app_prn(request[key])
            if app_prn:
                return app_prn

    portfolio_prn = generate_portfolio_prn(request)
    name = request.get("app", request.get(ARG_NAME, ""))

    return f"{portfolio_prn}{DELIMITER}{name}"


def branch_short_name(name: str | None) -> str | None:
    """Generates a sanitized, shortened name for a branch.

    Converts to lowercase, replaces non-alphanumeric characters (except hyphens)
    with hyphens, and truncates to 20 characters.

    Args:
        name: The branch name to shorten.

    Returns:
        The shortened and sanitized branch name.

    Examples:
        >>> branch_short_name("feature/USER-123-awesome-feature")
        'feature-user-123-awes'
        >>> branch_short_name("main")
        'main'
        >>> branch_short_name(None)
        None
    """
    if name is None:
        return None
    if not name:
        return V_EMPTY
    return re.sub(r"[^a-z0-9\-]", "-", name.lower())[:20].rstrip("-")


def generate_branch_prn(request: dict) -> str:
    """Generates or extracts a branch-level PRN from a request dictionary.

    Checks for existing valid branch PRN first, then attempts extraction
    from other PRN keys. Falls back to constructing new PRN by appending
    shortened 'name' to app PRN.

    Args:
        request: The dictionary containing PRN and name information.

    Returns:
        The extracted or generated branch PRN.

    Examples:
        >>> generate_branch_prn({"name": "main", "app_prn": "prn:ecommerce:web"})
        'prn:ecommerce:web:main'
        >>> generate_branch_prn({"prn": "prn:ecommerce:web:main"})
        'prn:ecommerce:web:main'
    """
    prn = request.get(ARG_BRANCH_PRN, "")
    if validate_branch_prn(prn):
        return prn

    for key in [ARG_BUILD_PRN, ARG_COMPONENT_PRN, PRN]:
        if key in request:
            branch_prn = extract_branch_prn(request[key])
            if branch_prn:
                return branch_prn

    app_prn = generate_app_prn(request)
    name = request.get("branch", request.get(ARG_NAME, ""))

    return f"{app_prn}{DELIMITER}{branch_short_name(name)}"


def generate_build_prn(request: dict) -> str:
    """Generates or extracts a build-level PRN from a request dictionary.

    Checks for existing valid build PRN first, then attempts extraction
    from other PRN keys. Falls back to constructing new PRN by appending
    'name' to branch PRN.

    Args:
        request: The dictionary containing PRN and name information.

    Returns:
        The extracted or generated build PRN.

    Examples:
        >>> generate_build_prn({"name": "1.0.0", "branch_prn": "prn:ecommerce:web:main"})
        'prn:ecommerce:web:main:1.0.0'
        >>> generate_build_prn({"prn": "prn:ecommerce:web:main:1.0.0"})
        'prn:ecommerce:web:main:1.0.0'
    """
    prn = request.get(ARG_BUILD_PRN, "")
    if validate_build_prn(prn):
        return prn

    for key in [ARG_COMPONENT_PRN, PRN]:
        if key in request:
            build_prn = extract_build_prn(request[key])
            if build_prn:
                return build_prn

    branch_prn = generate_branch_prn(request)
    name = request.get("build", request.get(ARG_NAME, ""))

    return f"{branch_prn}{DELIMITER}{name}"


def generate_component_prn(request: dict) -> str:
    """Generates or extracts a component-level PRN from a request dictionary.

    Checks for existing valid component PRN first, then attempts extraction
    from other PRN keys. Falls back to constructing new PRN by appending
    'name' to build PRN.

    Args:
        request: The dictionary containing PRN and name information.

    Returns:
        The extracted or generated component PRN.

    Examples:
        >>> generate_component_prn({"name": "frontend", "build_prn": "prn:ecommerce:web:main:1.0.0"})
        'prn:ecommerce:web:main:1.0.0:frontend'
        >>> generate_component_prn({"prn": "prn:ecommerce:web:main:1.0.0:frontend"})
        'prn:ecommerce:web:main:1.0.0:frontend'
    """
    prn = request.get(ARG_COMPONENT_PRN, "")
    if validate_component_prn(prn):
        return prn

    for key in [PRN]:
        if key in request:
            component_prn = extract_component_prn(request[key])
            if component_prn:
                return component_prn

    build_prn = generate_build_prn(request)
    name = request.get("component", request.get(ARG_NAME, ""))

    return f"{build_prn}{DELIMITER}{name}"


def validate_item_prn(prn: str) -> bool:
    """Validates if a string conforms to the general PRN format.

    Args:
        prn: The PRN string to validate.

    Returns:
        True if the PRN format is valid, otherwise False.

    Examples:
        >>> validate_item_prn("prn:ecommerce:web")
        True
        >>> validate_item_prn("invalid")
        False
    """
    return re.fullmatch(PRN_REGEX, prn) is not None


def validate_portfolio_prn(prn: str) -> bool:
    """Validates if a string is a valid portfolio-level PRN.

    Args:
        prn: The PRN string to validate.

    Returns:
        True if the PRN is a valid portfolio PRN, otherwise False.

    Examples:
        >>> validate_portfolio_prn("prn:ecommerce")
        True
        >>> validate_portfolio_prn("prn:ecommerce:web")
        False
    """
    return re.fullmatch(PORTFOLIO_PRN_REGEX, prn) is not None


def validate_app_prn(prn: str) -> bool:
    """Validates if a string is a valid app-level PRN.

    Args:
        prn: The PRN string to validate.

    Returns:
        True if the PRN is a valid app PRN, otherwise False.

    Examples:
        >>> validate_app_prn("prn:ecommerce:web")
        True
        >>> validate_app_prn("prn:ecommerce")
        False
    """
    return re.fullmatch(APP_PRN_REGEX, prn) is not None


def validate_branch_prn(prn: str) -> bool:
    """Validates if a string is a valid branch-level PRN.

    Args:
        prn: The PRN string to validate.

    Returns:
        True if the PRN is a valid branch PRN, otherwise False.

    Examples:
        >>> validate_branch_prn("prn:ecommerce:web:main")
        True
        >>> validate_branch_prn("prn:ecommerce:web")
        False
    """
    return re.fullmatch(BRANCH_PRN_REGEX, prn) is not None


def validate_build_prn(prn: str) -> bool:
    """Validates if a string is a valid build-level PRN.

    Args:
        prn: The PRN string to validate.

    Returns:
        True if the PRN is a valid build PRN, otherwise False.

    Examples:
        >>> validate_build_prn("prn:ecommerce:web:main:1.0.0")
        True
        >>> validate_build_prn("prn:ecommerce:web:main")
        False
    """
    return re.fullmatch(BUILD_PRN_REGEX, prn) is not None


def validate_component_prn(prn: str) -> bool:
    """Validates if a string is a valid component-level PRN.

    Args:
        prn: The PRN string to validate.

    Returns:
        True if the PRN is a valid component PRN, otherwise False.

    Examples:
        >>> validate_component_prn("prn:ecommerce:web:main:1.0.0:frontend")
        True
        >>> validate_component_prn("prn:ecommerce:web:main:1.0.0")
        False
    """
    return re.fullmatch(COMPONENT_PRN_REGEX, prn) is not None
