"""Jinja2 Template Filters for Core Automation Framework Rendering.

This module provides a comprehensive collection of custom Jinja2 filters specifically
designed for the Core Automation framework. These filters enable powerful template
rendering capabilities for AWS infrastructure as code, configuration management,
and deployment automation.

Key Features:
    - **AWS Integration**: Filters for AWS resource names, tags, and ARNs
    - **Network Operations**: CIDR splitting, subnet management, and port specifications
    - **Security Rules**: IAM policies, security groups, and access control
    - **Image Management**: Docker image names and AMI ID resolution
    - **Data Transformation**: JSON/YAML conversion, string manipulation, and formatting
    - **Context-Aware**: Automatic extraction of deployment context and metadata

Filter Categories:
    **AWS Resource Filters:**
    - aws_tags: Generate AWS tag lists from context and scope
    - docker_image: Construct ECR image names with registry URIs
    - image_id: Resolve AMI IDs from image aliases
    - output_name: Generate CloudFormation output reference names

    **Security and Network Filters:**
    - ip_rules: Generate security group rules from resource specifications
    - iam_rules: Create IAM policy statements with resource ARNs
    - parse_port_spec: Parse port specifications for security groups
    - split_cidr: Split CIDR blocks into subnets

    **Data Processing Filters:**
    - lookup: Navigate nested data structures with dot notation
    - extract: Extract values using JMESPath expressions
    - ensure_list: Normalize values to list format
    - to_json/to_yaml: Convert data between formats

    **String and Utility Filters:**
    - shorten_unique: Truncate strings with unique suffixes
    - regex_replace: Pattern-based string replacement
    - format_date: Date formatting with flexible input
    - min_int: Find minimum values from multiple inputs

Integration:
    All filters are designed to work seamlessly with the Core Automation framework's
    context system, automatically extracting deployment metadata like portfolio,
    application, branch, build, and environment information for consistent resource
    naming and tagging across AWS deployments.

Thread Safety:
    All filters are stateless and thread-safe, suitable for concurrent template
    rendering in multi-threaded environments and serverless functions.
"""

from typing import Any

import os
import copy
import jinja2
import jmespath
import re
import random
import string
import netaddr

from datetime import date

from jinja2 import pass_context
from jinja2.environment import Context, Environment

import core_framework as util

from core_framework.constants import (
    CTX_ACCOUNT_ALIASES,
    CTX_APP,
    CTX_APP_FILES_PREFIX,
    CTX_BRANCH_FILES_PREFIX,
    CTX_BUILD_FILES_PREFIX,
    CTX_COMPONENT_NAME,
    CTX_CONTEXT,
    CTX_FILES_BUCKET_URL,
    CTX_PORTFOLIO_FILES_PREFIX,
    CTX_SHARED_FILES_PREFIX,
    CTX_SNAPSHOT_ALIASES,
    DD_APP,
    DD_BRANCH,
    DD_BRANCH_SHORT_NAME,
    DD_BUILD,
    DD_ECR,
    DD_ENVIRONMENT,
    DD_PORTFOLIO,
    DD_SCOPE,
    DD_TAGS,
    ECR_REGISTRY_URI,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_ENVIRONMENT,
    SCOPE_PORTFOLIO,
    SCOPE_SHARED,
    ST_CIDR,
    ST_COMPONENT,
    ST_IP_ADDRESS,
    ST_PREFIX,
    ST_SECURITY_GROUP,
    TAG_APP,
    TAG_BRANCH,
    TAG_BUILD,
    TAG_COMPONENT,
    TAG_ENVIRONMENT,
    TAG_NAME,
    TAG_PORTFOLIO,
)


@pass_context
def filter_aws_tags(
    render_context: Context, scope: str, component_name: str | None = None
) -> list[dict]:
    """Create a list of AWS tags from the render context and scope.

    Generates standardized AWS resource tags based on the deployment context
    and specified scope. Tags include portfolio, application, branch, build,
    environment, and component information following Core Automation naming
    conventions.

    Args:
        render_context: The Jinja2 context containing deployment facts and variables.
        scope: The lifecycle scope determining tag composition (SCOPE_BUILD,
               SCOPE_ENVIRONMENT, SCOPE_PORTFOLIO, etc.).
        component_name: Optional component name to include in tags. If None,
                       extracted from context.

    Returns:
        List of dictionaries with 'Key' and 'Value' fields suitable for AWS
        resource tagging APIs.

    Raises:
        jinja2.exceptions.UndefinedError: If context lacks required deployment facts.
    """
    tags_hash = filter_tags(render_context, scope, component_name)

    items: list[dict] = [
        {"Key": key, "Value": value} for key, value in tags_hash.items()
    ]

    return items


@pass_context
def filter_docker_image(render_context: Context, object: Any) -> str | None:
    """Generate a Docker image name based on the provided object and render context.

    Constructs fully qualified ECR image names using deployment context and
    Docker image specifications. Combines ECR registry URI with standardized
    repository naming based on portfolio, application, branch, build, and
    component information.

    Args:
        render_context: The Jinja2 context containing deployment facts and ECR
                       registry information.
        object: Dictionary containing 'Fn::Pipeline::DockerImage' specification
               with 'Name' field for the image tag.

    Returns:
        Fully qualified ECR image name in format:
        '{registry_uri}/private/{portfolio}-{app}-{branch}-{build}-{component}:{tag}'
        Returns None if context is unavailable.

    Raises:
        jinja2.exceptions.UndefinedError: If object lacks required
                                        'Fn::Pipeline::DockerImage' specification.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if facts is None:
        return None

    if "Fn::Pipeline::DockerImage" not in object:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::DockerImage lookup"
        )

    portfolio = facts.get(DD_PORTFOLIO, "")
    app = facts.get(DD_APP, "")
    branch = facts.get(DD_BRANCH_SHORT_NAME, "")
    build = facts.get(DD_BUILD, "")
    component = render_context.get(CTX_COMPONENT_NAME, "unspecified")

    ecr_repository_name = "-".join(
        [
            f"private/{portfolio}",
            app,
            branch,
            build,
            component,
        ]
    )

    image_name = object["Fn::Pipeline::DockerImage"]["Name"]

    ecr: dict = facts.get(DD_ECR, {})
    registry_uri = ecr.get(ECR_REGISTRY_URI, "unspecified")

    return "{}/{}:{}".format(registry_uri, ecr_repository_name, image_name)


def filter_ebs_encrypt(ebs_spec: list[dict] | None) -> list:
    """Enforce encryption for EBS volumes in the provided EBS specification.

    Processes EBS block device mapping specifications to ensure all EBS volumes
    have encryption enabled. Creates a deep copy to avoid modifying the original
    specification and sets 'Encrypted': 'true' for all EBS volumes.

    Args:
        ebs_spec: List of block device mapping dictionaries containing EBS
                 volume specifications. Can be None.

    Returns:
        Modified copy of the EBS specification with encryption enforced on
        all EBS volumes. Returns empty list if input is None.

    Note:
        KmsKeyId is not supported for BlockDeviceMappings in CloudFormation,
        so only the Encrypted flag is set to true.
    """
    # Work on a copy to avoid side effects
    spec_copy = copy.deepcopy(ebs_spec)
    for bdm in spec_copy:

        if "Ebs" in bdm:
            # Enforce encryption for ebs volumes.
            bdm["Ebs"]["Encrypted"] = "true"

            # It seems KmsKeyId is not supported for BlockDeviceMappings (which is our use case). So encrypted = true will have to do.
            # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ec2-blockdev-template.html
            # bdm['Ebs']['KmsKeyId'] = ${KmsKeyArn}

    return spec_copy


def filter_ensure_list(object: Any) -> list[Any]:
    """Wrap the object in a list if it isn't already a list.

    Normalizes input values to list format for consistent processing in templates.
    Handles None, undefined values, single objects, and existing lists gracefully.

    Args:
        object: Any value to normalize to list format.

    Returns:
        - If object is already a list: returns the original list
        - If object is None or Undefined: returns empty list
        - Otherwise: returns list containing the single object

    Note:
        This filter is commonly used to handle optional list parameters that
        may be provided as single values or arrays.
    """
    if isinstance(object, list):
        # Already a list, simply return it
        return object
    elif object is None or isinstance(object, jinja2.Undefined):
        # None or Undefined, return empty list
        return []
    else:
        # Place the object into a list
        return [object]


def filter_extract(object: Any, path: str, default: str = "_error_") -> str:
    """Extract a value from an object using JMESPath.

    Performs safe value extraction from complex nested data structures using
    JMESPath query expressions. Provides flexible error handling with
    configurable default values.

    Args:
        object: The source object to query. Can be dict, list, or any
               JSON-serializable structure.
        path: JMESPath expression defining the extraction path
             (e.g., 'items[0].name', 'config.database.host').
        default: Value to return if path doesn't exist. Special value
                '_error_' causes an exception to be raised.

    Returns:
        The extracted value from the specified path, or the default value
        if the path doesn't exist.

    Raises:
        jinja2.exceptions.UndefinedError: If path doesn't exist and default
                                        is '_error_'.
    """
    value = (
        None
        if object is None or isinstance(object, jinja2.Undefined)
        else jmespath.search(path, object)
    )

    if value is None:
        if default == "_error_":
            raise jinja2.exceptions.UndefinedError(
                "Filter_extract: Error during value extraction - no attribute '{}'".format(
                    path
                )
            )
        value = default

    return value


@pass_context
def filter_iam_rules(render_context: Context, resource: dict) -> list:
    """Create IAM security rules based on the provided resource and render context.

    Generates IAM security rules for cross-component access within an application.
    Processes Pipeline::Security specifications to create component-based security
    rules with proper role names and security group references.

    Args:
        render_context: The Jinja2 context containing deployment facts and
                       application component definitions.
        resource: Resource dictionary containing 'Pipeline::Security' section
                 with source and allow specifications.

    Returns:
        List of security rule dictionaries containing:
        - Type: 'component'
        - Value: IAM role name for the source component
        - Description: Human-readable description
        - Allow: List of allowed actions/permissions
        - SourceType: Component type from application definition
        - SecurityGroupId: Security group reference for the component

    Raises:
        jinja2.exceptions.FilterArgumentError: If security source is not a valid
                                             component label in the application.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    app: dict | None = render_context.get(CTX_APP, None)

    if facts is None or app is None:
        return []

    portfolio = facts.get(DD_PORTFOLIO, "")
    app_name = facts.get(DD_APP, "")
    branch_short_name = facts.get(DD_BRANCH_SHORT_NAME, "")

    security_rules: list[dict] = []
    for security_rule in resource.get("Pipeline::Security", {}):

        if not isinstance(security_rule, dict):
            continue

        security_rule_sources = filter_ensure_list(security_rule.get("Source", []))

        for source in security_rule_sources:

            if not isinstance(source, str):
                raise jinja2.exceptions.FilterArgumentError(
                    f"Filter_iam_rules: Invalid security source '{source}' - must be a string/key for the source name"
                )

            # Checks to see if the "Source" is in the "app"
            if source not in app:
                # If the Source component is not nin the app, then raise exception
                raise jinja2.exceptions.FilterArgumentError(
                    f"Filter_iam_rules: Invalid security source '{source}' - must be a label of a component in the app"
                )

            app_source = app[source]

            if not isinstance(app_source, dict):
                raise jinja2.exceptions.FilterArgumentError(
                    f"Filter_iam_rules: Invalid app source '{source}' - must be a dictionary"
                )

            # Source is component
            security_rules.append(
                {
                    "Type": "component",
                    "Value": "-".join(
                        [
                            portfolio,
                            app_name,
                            branch_short_name,
                            source,
                            "security:RoleName",
                        ]
                    ),
                    "Description": f"Component {source}",
                    "Allow": filter_ensure_list(security_rule.get("Allow", [])),
                    "SourceType": app_source.get("Type", ""),
                    "SecurityGroupId": "-".join(
                        [
                            portfolio,
                            app_name,
                            branch_short_name,
                            source,
                            "security:SecurityGroupId",
                        ]
                    ),
                }
            )

    return security_rules


@pass_context
def filter_image_alias_to_id(render_context: Context, image_alias: str) -> str | None:
    """Convert an image alias to its corresponding image ID.

    Resolves human-readable image aliases to actual AMI IDs using the
    ImageAliases mapping from the deployment context. Enables template
    authors to use meaningful names instead of region-specific AMI IDs.

    Args:
        render_context: The Jinja2 context containing deployment facts with
                       ImageAliases mapping.
        image_alias: Human-readable alias for the AMI (e.g., 'ubuntu-20.04',
                    'amazon-linux-2').

    Returns:
        The actual AMI ID corresponding to the alias, or None if context
        is unavailable.

    Raises:
        jinja2.exceptions.UndefinedError: If the image alias is not found in
                                        the ImageAliases mapping.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if facts is None:
        return None

    image_aliases: dict = facts.get("ImageAliases", {})

    if image_alias not in image_aliases:
        raise jinja2.exceptions.UndefinedError(f"Unknown image '{image_alias}'")

    return image_aliases.get(image_alias)


@pass_context
def filter_image_id(render_context: Context, o: dict) -> str | None:
    """Get the image ID from the render context based on the provided object.

    Extracts and resolves AMI IDs from Fn::Pipeline::ImageId specifications.
    Combines image name extraction with alias-to-ID resolution for complete
    AMI reference handling in templates.

    Args:
        render_context: The Jinja2 context containing deployment facts with
                       ImageAliases mapping.
        o: Dictionary containing 'Fn::Pipeline::ImageId' specification with
           'Name' field for the image alias.

    Returns:
        The actual AMI ID corresponding to the alias, or None if context
        is unavailable.

    Raises:
        jinja2.exceptions.UndefinedError: If image alias is not specified or
                                        not found in the ImageAliases mapping.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if not facts:
        return None

    image_alias: str = filter_image_name(o)

    image_aliases: dict = facts.get("ImageAliases", {})
    if image_alias not in image_aliases:
        raise jinja2.exceptions.UndefinedError(f"Unknown image '{image_alias}'")

    return image_aliases.get(image_alias)


def filter_image_name(o: dict) -> str:
    """Get the image name from the render context based on the provided object.

    Extracts the image alias name from Fn::Pipeline::ImageId lookup specifications.
    Used as a helper function for image ID resolution workflows.

    Args:
        o: Dictionary containing 'Fn::Pipeline::ImageId' specification with
           'Name' field for the image alias.

    Returns:
        The image alias name from the specification.

    Raises:
        jinja2.exceptions.UndefinedError: If 'Fn::Pipeline::ImageId' lookup
                                        specification is missing or invalid.
    """

    lookup_values: dict | None = o.get("Fn::Pipeline::ImageId", None)

    if not lookup_values or not isinstance(lookup_values, dict):
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::ImageId lookup dictionary"
        )

    return lookup_values.get("Name", "")


@pass_context
def filter_ip_rules(  # noqa C901
    render_context: Context,
    resource: dict,
    rule_type: str = ST_IP_ADDRESS,
    source_types: list[str] = [ST_CIDR, ST_COMPONENT, ST_PREFIX],
    source_only: bool = False,
) -> list[dict]:
    """Generate a list of security rules based on the provided resource and render context.

    Creates comprehensive security group rules from Pipeline::Security specifications.
    Supports multiple source types including CIDR blocks, component references,
    IP prefixes, and security group IDs with flexible filtering and formatting.

    Args:
        render_context: The Jinja2 context containing deployment facts,
                       security aliases, and application component definitions.
        resource: Resource dictionary containing 'Pipeline::Security' section
                 with source and allow specifications.
        rule_type: Type of security rule to generate. Currently supports
                  'ip' for IP-based rules.
        source_types: List of source types to include in output. Filters rules
                     to specified types: 'cidr', 'component', 'prefix', 'sg'.
        source_only: If True, returns only source information without combining
                    with Allow specifications. Useful for security group references.

    Returns:
        List of security rule dictionaries. Format varies based on source_only:
        - source_only=False: Combined source and port/protocol specifications
        - source_only=True: Source information only

    Raises:
        jinja2.exceptions.UndefinedError: If security source is not a valid
                                        security alias or application component.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    app: dict | None = render_context.get(CTX_APP, None)

    if facts is None or app is None:
        return []

    security_aliases: dict = facts.get("SecurityAliases", {})
    portfolio = facts.get(DD_PORTFOLIO, "")
    branch_short_name = facts.get(DD_BRANCH_SHORT_NAME, "")
    app_name = facts.get(DD_APP, "")

    security_rules: list[dict] = []

    for security_rule in resource.get("Pipeline::Security", []):

        for security_source in filter_ensure_list(security_rule["Source"]):

            if not isinstance(security_source, str):
                continue

            sources: list[dict] = []

            if security_source in security_aliases:
                # Source is an alias in facts
                sources = [
                    o
                    for o in security_aliases.get(security_source, None)
                    if isinstance(o, dict)
                ]
            elif security_source in app:
                # Source is component
                sources = [
                    {
                        "Type": ST_COMPONENT,
                        "Value": "-".join(
                            [
                                portfolio,
                                app_name,
                                branch_short_name,
                                security_source,
                                "security:SecurityGroupId",
                            ]
                        ),
                        "Description": "Component {}".format(security_source),
                    }
                ]
            else:
                # Unknown source
                raise jinja2.exceptions.UndefinedError(
                    "Filter_ip_rules: Invalid security source '{}' - must be a security alias or a component".format(
                        security_source
                    )
                )

            # Convert old format SecurityAliases to new format
            sources = list(
                map(
                    lambda source: (
                        source
                        if isinstance(source, dict)
                        else {
                            "Type": ST_CIDR,
                            "Value": source,
                            "Description": security_source,
                        }
                    ),
                    sources,
                )
            )

            # Filter security rule source_types
            sources = [
                source for source in sources if source.get("Type", "") in source_types
            ]

            for source in sources:
                if source_only or source.get("Type", "") == ST_SECURITY_GROUP:
                    # Add the source as-is (without Allow information)
                    security_rules.append(source)
                else:
                    # Combine the source with Allow information, for each Allow rule
                    for allow in filter_ensure_list(security_rule.get("Allow", [])):
                        if not isinstance(allow, str):
                            continue
                        security_rules.append(
                            {**source, **filter_parse_port_spec(allow)}
                        )

    return security_rules


@pass_context
def filter_lookup(render_context: Context, path: str, default: str = "_error_") -> str:
    """Look up a value in the render context using the specified path.

    Navigates nested data structures using dot notation with support for
    array indexing and property names containing special characters. Provides
    flexible path traversal for complex template variable access.

    Args:
        render_context: The Jinja2 context containing template variables and data.
        path: Dot-separated path to navigate (e.g., 'config.database.host',
             'items[0].name', 'data.key/with/slashes').
        default: Value to return if path doesn't exist. Special value '_error_'
                causes an exception to be raised.

    Returns:
        The value found at the specified path, or the default value if
        path doesn't exist.

    Raises:
        jinja2.exceptions.UndefinedError: If path doesn't exist and default
                                        is '_error_'.
    """
    context_data = render_context.parent

    value = _navigate_path(context_data, path)

    if value is None:
        if default == "_error_":
            raise jinja2.exceptions.UndefinedError(
                "Filter_lookup: Error during value lookup - no attribute '{}'".format(
                    path
                )
            )
        return default

    return value


def _navigate_path(data: Any, path: str) -> Any:
    """Recursively navigate through nested data using dot-separated path.

    Internal helper function that handles the complex logic of path navigation
    through nested dictionaries and lists. Supports array indexing with bracket
    notation and property names containing forward slashes.

    Args:
        data: The current data object to navigate through (dict, list, or other).
        path: The remaining path to navigate using dot-separated segments.
             Supports array indexing with [n] syntax.

    Returns:
        The value at the specified path, or None if path is invalid or not found.

    Features:
        - Array indexing: 'items[0]' accesses first element of items array
        - Property names with slashes: 'config.key/with/slashes.value'
        - Recursive navigation through nested structures
    """
    if not path:
        return data

    if not isinstance(data, (dict, list)):
        return None

    # Split on the first dot to get the current segment and remaining path
    if "." in path:
        current_segment, remaining_path = path.split(".", 1)
    else:
        current_segment = path
        remaining_path = ""

    # Handle array indexing: items[1] -> key="items", index=1
    if "[" in current_segment and current_segment.endswith("]"):
        # Extract the key and index
        key_part, index_part = current_segment.split("[", 1)
        index_str = index_part.rstrip("]")

        try:
            index = int(index_str)
        except ValueError:
            return None  # Invalid index

        # Navigate to the array first
        if isinstance(data, dict):
            if key_part not in data:
                return None
            array_data = data[key_part]
        else:
            return None  # Can't use key on non-dict

        # Check if it's actually a list and index is valid
        if not isinstance(array_data, list) or index >= len(array_data) or index < 0:
            return None

        # Get the item at the index
        current_value = array_data[index]

    else:
        # Regular property access (handles keys with forward slashes)
        if isinstance(data, dict):
            if current_segment not in data:
                return None
            current_value = data[current_segment]
        elif isinstance(data, list):
            # If we're trying to access a property on a list, that's invalid
            return None
        else:
            return None

    # If no remaining path, return the current value
    if not remaining_path:
        return current_value

    # Recursively navigate the remaining path
    return _navigate_path(current_value, remaining_path)


def filter_min_int(*values) -> Any | None:
    """Find the minimum integer value from the provided arguments.

    Utility filter for establishing floor values in configurations like
    MinSuccessfulInstancesPercent for Auto Scaling Groups or similar
    deployment parameters requiring minimum thresholds.

    Args:
        *values: Variable number of numeric values to compare.

    Returns:
        The minimum value from all provided arguments, or None if no
        values are provided.
    """
    # The values are passed are a tuple, so we need to check if the first element is a list.
    # We need to get the list from the tuple.
    if not values or len(values) == 0:
        return None

    return min(list(values))


@pass_context
def filter_output_name(render_context: Context, o: dict) -> str | None:
    """Get the output name based on the deployment details and output configuration.

    Generates standardized CloudFormation output reference names based on
    lifecycle scope and component information. Creates consistent naming
    for cross-stack references and parameter passing.

    Args:
        render_context: The Jinja2 context containing deployment facts.
        o: Dictionary containing 'Fn::Pipeline::GetOutput' specification with
           Scope, Component, and OutputName fields.

    Returns:
        Formatted output reference name following the pattern:
        '{portfolio}-{app}-{branch}-{build}-{component}-pointers:{output_name}'
        Returns None if context is unavailable.

    Raises:
        jinja2.exceptions.UndefinedError: If 'Fn::Pipeline::GetOutput' specification
                                        is missing.
        NotImplementedError: If lifecycle scope other than 'build' is specified.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if facts is None:
        return None

    output_config: dict | None = o.get("Fn::Pipeline::GetOutput", None)

    if not output_config:
        raise jinja2.exceptions.UndefinedError(
            "Filter_output_name: Must specify Fn::Pipeline::GetOutput (Scope, Component, ExportName)."
        )

    lifecycle_scope = output_config.get(DD_SCOPE, SCOPE_BUILD)
    component_name = output_config.get("Component", "")
    output_name = output_config.get("OutputName", "")
    portfolio = facts.get(DD_PORTFOLIO, "")
    app = facts.get(DD_APP, "")
    branch = facts.get(DD_BRANCH_SHORT_NAME, "")
    build = facts.get(DD_BUILD, "")

    if lifecycle_scope == SCOPE_BUILD:
        result = "-".join(
            [portfolio, app, branch, build, component_name, f"pointers:{output_name}"]
        )
        return result

    raise NotImplementedError(
        "Filter_output_name: Only build scope supported at this time. Add 'release' scope later."
    )


def filter_parse_port_spec(port_spec: str) -> dict:
    """Parse a port specification string into a dictionary with Protocol, FromPort, and ToPort.

    Converts human-readable port specifications into AWS security group rule format.
    Supports TCP, UDP, ICMP, and ALL protocols with flexible port range syntax
    and wildcard handling for comprehensive security rule definitions.

    Args:
        port_spec: Port specification string in format:
                  - 'TCP:80' (single port)
                  - 'TCP:80-443' (port range)
                  - 'UDP:*' (all UDP ports)
                  - 'ICMP:8' (ICMP echo request)
                  - 'ALL:*' (all protocols and ports)

    Returns:
        Dictionary with keys:
        - 'Protocol': Protocol name or '-1' for ALL
        - 'FromPort': Starting port number or ICMP type
        - 'ToPort': Ending port number or ICMP type

    Raises:
        jinja2.exceptions.FilterArgumentError: If port specification format is invalid
                                             or values are out of valid ranges.
    """
    PORT_SPEC_REGEX = r"^((?:TCP)|(?:UDP)|(?:ICMP)|(?:ALL)):((?:[0-9]+)|(?:\*))(?:-((?:[0-9]+)|(?:\*)))?$"
    match = re.match(PORT_SPEC_REGEX, port_spec)

    if match is None:
        if any(port_spec.startswith(k) for k in ["TCP", "UDP", "ICMP", "ALL"]):
            protocol = port_spec.split(":")[0]
            from_port = "*"
            to_port = "*"
        else:
            raise jinja2.exceptions.FilterArgumentError(
                "Filter_parse_port_spec: Invalid port specification '{}'. Must be <protocol>:<from_port>[-<to_port>]".format(
                    port_spec
                )
            )
    else:
        # Extract regex captures
        matches = match.groups()
        # Protocol can be TCP, UDP, ICMP, or ALL and regex ensures it is one of these
        protocol: str = matches[0]
        # From port can be a number or '*' (wildcard). Regex ensures it is a number or '*'
        from_port: str = matches[1]
        # To port can be a number or '*' (wildcard). Regex ensures it is a number, '', or '*'
        to_port: str = matches[2]

    if not to_port:
        to_port = from_port

    if protocol == "ALL":
        protocol = "-1"

    if protocol == "ICMP":
        # Common ICMP Types for AWS Security Groups:
        #
        # 0 - Echo Reply
        # 8 - Echo Request
        # 11 - Time Exceeded
        # 3 - Destination Unreachable
        # 4 - Source Quench (deprecated)
        # 5 - Redirect Message (deprecated)
        # 13 - Timestamp Request
        # 14 - Timestamp Reply
        # 15 - Information Request (deprecated)
        # 16 - Information Reply (deprecated)
        # -1 - All ICMP types
        #
        # For ICMP, the "port" is the ICMP Type. A value of -1 means all types.
        # If a single type is given (e.g., ICMP:8), From and To ports are the same.
        # If '*' is given, it means all types, so both ports must be -1.
        if from_port == "*":
            from_port = "-1"
            to_port = "-1"

        if int(from_port) not in [0, 3, 4, 5, 8, 11, 13, 14, 15, 16, -1]:
            raise jinja2.exceptions.UndefinedError(
                "Filter_parse_port_spec: Invalid ICMP type '{}'. Must be one of 0, 3, 4, 5, 8, 11, 13, 14, 15, 16 or -1 for all types.".format(
                    from_port
                )
            )
    else:
        if from_port == "*":
            from_port = "0"
        if to_port == "*":
            to_port = "65535"

    if protocol != "ICMP" and (int(from_port) < 0 or int(to_port) < 0):
        raise jinja2.exceptions.UndefinedError(
            "Filter_parse_port_spec: Port numbers must be non-negative integers."
        )

    if int(from_port) > int(to_port):
        raise jinja2.exceptions.UndefinedError(
            "Filter_parse_port_spec: FromPort cannot be greater than ToPort."
        )

    if int(from_port) > 65535 or int(to_port) > 65535:
        raise jinja2.exceptions.UndefinedError(
            "Filter_parse_port_spec: FromPort and ToPort cannot greater than 65535."
        )

    return {"Protocol": protocol, "FromPort": from_port, "ToPort": to_port}


@pass_context
def filter_policy_statements(render_context: Context, statement: dict) -> dict:
    """Generate a policy statement based on the provided statement and render context.

    Creates IAM policy statements with automatically generated resource ARNs based on
    deployment context and AWS service actions. Generates resource ARNs for different
    AWS services following standard naming conventions.

    Args:
        render_context: The Jinja2 context containing deployment facts and AWS
                       account information.
        statement: Policy statement dictionary containing 'Action' and 'Effect' fields.

    Returns:
        Dictionary representing the policy statement with:
        - Action: List of AWS actions from input statement
        - Effect: Allow or Deny from input statement
        - Resource: List of generated resource ARNs based on actions

    Raises:
        jinja2.exceptions.FilterArgumentError: If statement lacks required
                                             'Action' and 'Effect' fields.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if facts is None:
        return {}

    aws_region = facts.get("AwsRegion", util.get_aws_region())
    aws_account_id = facts.get("AwsAccountId", "")

    portfolio = facts.get(DD_PORTFOLIO, "")
    app = facts.get(DD_APP, "")
    branch_short_name = facts.get(DD_BRANCH_SHORT_NAME, "")

    base_resource_name_hyphenated = "-".join([portfolio, app, branch_short_name])

    resources = []
    added: set[str] = set()

    action_statements = statement.get("Action", [])

    # AWS Poliction Statement
    for action in action_statements:
        group = action.split(":")[0]
        if group not in added:
            arn = __create_resource_arn(
                group,
                aws_region,
                aws_account_id,
                base_resource_name_hyphenated,
            )
            resources.append(arn)
            added.add(group)

    if "Action" not in statement or "Effect" not in statement:
        raise jinja2.exceptions.FilterArgumentError(
            "Filter_policy_statements: Must specify 'Action' and 'Effect' in the statement parameter"
        )

    return {
        "Action": statement.get("Action"),
        "Effect": statement.get("Effect"),
        "Resource": resources,
    }


@pass_context
def filter_process_cfn_init(render_context: Context, cfn_init: dict) -> dict | None:
    """Process the CloudFormation Init configuration to ensure all sources and files are prefixed with the S3 artifact URL.

    Processes CloudFormation Init configurations to automatically prefix file and
    source URLs with the appropriate S3 artifact bucket URL from the deployment
    context. Enables portable configurations across different environments.

    Args:
        render_context: The Jinja2 context containing deployment facts with
                       S3 bucket URLs and file prefixes.
        cfn_init: CloudFormation Init configuration dictionary with sources
                 and files sections to process.

    Returns:
        Processed CloudFormation Init configuration with S3 URLs prefixed,
        or None if context is unavailable.

    Note:
        Only the sources and files sections are processed. Other sections
        of the CloudFormation Init configuration are not modified.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if facts is None:
        return None

    cfn_init = copy.deepcopy(cfn_init)

    for key, config_block in cfn_init.items():
        if key == "configSets":
            continue

        # Prefix sources with S3 artefact url
        sources = config_block.get("sources", {})
        for key, source_spec in sources.items():
            sources[key] = __file_url(facts, source_spec)

        # Prefix files with S3 artefact url
        files = config_block.get("files", {})
        for key, file_spec in files.items():
            if "source" not in file_spec:
                continue
            file_spec["source"] = __file_url(facts, file_spec["source"])

    return cfn_init


def filter_regex_replace(s, find, replace) -> str:
    """Perform regex-based string replacement operations.

    Provides regex pattern matching and replacement functionality for template
    string manipulation. Uses Python's re.sub for pattern matching.

    Args:
        s: The source string to perform replacement on.
        find: Regular expression pattern to search for.
        replace: Replacement string or pattern with capture group references.

    Returns:
        Modified string with all pattern matches replaced.
    """
    return re.sub(find, replace, s)


def filter_format_date(value: Any, f: str = "%d-%b-%y") -> str:
    """Format a date object or string representation into a specified format.

    Provides flexible date formatting with support for date objects, ISO date
    strings, and the special "now" keyword for current date formatting.

    Args:
        value: Value to format. Can be:
              - date object: Used directly for formatting
              - "now" string: Uses current date
              - ISO date string: Parsed then formatted
        f: Python strftime format string for date formatting.

    Returns:
        Formatted date string according to the specified format.

    Raises:
        jinja2.exceptions.FilterArgumentError: If date string is invalid format.
    """

    date_to_format = value
    if isinstance(value, str):
        if value.lower() == "now":
            date_to_format = date.today()
        else:
            # Attempt to parse the string as a date
            try:
                date_to_format = date.fromisoformat(value)
            except ValueError:
                raise jinja2.exceptions.FilterArgumentError(
                    f"Invalid date string '{value}'. Expected 'now' or a valid ISO date."
                )
    else:
        # Fallback to today() if the provided value is not a valid date object
        if not hasattr(date_to_format, "strftime"):
            date_to_format = date.today()

    return date_to_format.strftime(f)


def filter_rstrip(value: str, chars: str) -> str:
    """Remove trailing characters from a string.

    Provides string trimming functionality to remove specified characters
    from the end of strings. Useful for cleaning file paths and URLs.

    Args:
        value: The source string to process.
        chars: Characters to remove from the string's end.

    Returns:
        String with specified trailing characters removed.
    """
    return value.rstrip(chars)


def filter_shorten_unique(
    value: str, limit: int, unique_length: int = 0, charset: str | None = None
):
    """Shorten a string to a specified limit and append a unique string of a given length.

    Truncates strings while maintaining uniqueness through deterministic suffix
    generation. Useful for AWS resource names with length limitations while
    ensuring collision avoidance.

    Args:
        value: The source string to shorten.
        limit: Maximum length of the resulting string.
        unique_length: Length of unique suffix to append. 0 means no suffix.
        charset: Character set for unique string generation. Defaults to
                alphanumeric uppercase characters.

    Returns:
        Shortened string with deterministic unique suffix if needed.
        Returns original string if it's already within the limit.
    """
    if len(value) <= limit:
        return value

    if charset is None:
        charset = string.ascii_uppercase + string.digits

    shortened_string = value[0 : (limit - unique_length)]

    random.seed(value)
    unique_string = "".join(random.choice(charset) for _ in range(unique_length))

    return shortened_string + unique_string


@pass_context
def filter_snapshot_id(
    render_context: Context, snapshot_spec: dict, component_type: str
) -> dict | None:
    """Retrieve the snapshot identifier from the render context based on the provided snapshot specification and component type.

    Resolves EBS snapshot specifications to actual snapshot IDs and owner account
    information using deployment context aliases. Enables cross-account snapshot
    sharing and component-specific snapshot management.

    Args:
        render_context: The Jinja2 context containing deployment facts with
                       snapshot aliases and account mappings.
        snapshot_spec: Dictionary containing 'Fn::Pipeline::SnapshotId' specification
                      with 'Name' field for snapshot alias lookup.
        component_type: Component type for snapshot categorization (e.g., 'database',
                       'application').

    Returns:
        Dictionary with snapshot parameters:
        - SnapshotIdentifier: The actual EBS snapshot ID
        - OwnerAccount: Account ID if cross-account sharing (optional)
        Returns None if snapshot not found or context unavailable.

    Raises:
        jinja2.exceptions.UndefinedError: If snapshot specification is invalid or
                                        context lacks valid snapshot aliases.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if not facts:
        return None

    snapshot_id: dict | None = snapshot_spec.get("Fn::Pipeline::SnapshotId", {})
    if not isinstance(snapshot_id, dict):
        raise jinja2.exceptions.UndefinedError(
            'Must specify {"Fn::Pipeline::SnapshotId": {}} dictionary for lookup'
        )

    snapshot_alias_name = snapshot_id.get("Name", "unsepcified")

    context_snapshot_aliases = facts.get(CTX_SNAPSHOT_ALIASES, {})
    if not isinstance(context_snapshot_aliases, dict):
        raise jinja2.exceptions.UndefinedError(
            "Invalid snapshot aliases defined in context"
        )

    account_aliases = facts.get(CTX_ACCOUNT_ALIASES, {})
    if not isinstance(account_aliases, dict):
        account_aliases = {}

    snapshot_type_aliases = context_snapshot_aliases.get(component_type, None)
    if not isinstance(snapshot_type_aliases, dict):
        return None

    snapshot_type_alias_details = snapshot_type_aliases.get(snapshot_alias_name, None)

    if not snapshot_type_alias_details:
        return None

    snapshot_identifier = snapshot_type_alias_details.get("SnapshotIdentifier", None)
    if not snapshot_identifier:
        return None
    params = {"SnapshotIdentifier": snapshot_identifier}

    snapshot_account_alias = snapshot_type_alias_details.get("AccountAlias", None)
    if snapshot_account_alias:
        owner_account_number = account_aliases.get(snapshot_account_alias, None)
        if owner_account_number:
            params["OwnerAccount"] = owner_account_number

    return params


@pass_context
def filter_snapshot_name(
    render_context: Context, snapshot_spec: dict, component_type: str
) -> str | None:
    """Retrieve the snapshot name from the render context based on the provided snapshot specification and component type.

    Extracts snapshot identifiers from deployment context using snapshot aliases
    and component type filtering. Provides simple name resolution for snapshot
    references in templates.

    Args:
        render_context: The Jinja2 context containing deployment facts with
                       snapshot aliases and component mappings.
        snapshot_spec: Dictionary containing 'Fn::Pipeline::SnapshotId' specification
                      with 'Name' field for snapshot alias lookup.
        component_type: Component type for snapshot categorization filtering.

    Returns:
        The snapshot identifier string, or None if not found or context unavailable.

    Raises:
        jinja2.exceptions.FilterArgumentError: If snapshot specification lacks
                                             required Fn::Pipeline::SnapshotId or Name fields.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if not facts:
        return None

    snapshot_id: dict | None = snapshot_spec.get("Fn::Pipeline::SnapshotId")
    if not isinstance(snapshot_id, dict):
        raise jinja2.exceptions.FilterArgumentError(
            "Must specify Fn::Pipeline::SnapshotId lookup in the snapshot_spec parameter"
        )

    snapshot_alias_name = snapshot_id.get("Name")
    if not snapshot_alias_name:
        raise jinja2.exceptions.FilterArgumentError(
            "Fn::Pipeline::SnapshotId[Name]: Must specify 'Name' attribute in Fn::Pipeline::SnapshotId lookup snapshot_spec parameter"
        )

    # Safely look up the nested snapshot details
    snapshot_aliases = facts.get(CTX_SNAPSHOT_ALIASES, None)
    if not snapshot_aliases or not isinstance(snapshot_aliases, dict):
        return None

    snapshot_type_aliases = snapshot_aliases.get(component_type, None)
    if not snapshot_type_aliases or not isinstance(snapshot_type_aliases, dict):
        return None

    snapshot_details = snapshot_type_aliases.get(snapshot_alias_name, None)
    if not snapshot_details or not isinstance(snapshot_details, dict):
        return None

    return snapshot_details.get("SnapshotIdentifier")


def filter_split_cidr(
    cidr: str, allowed_prefix_lengths: list[int] = [8, 16, 24, 32]
) -> list[str]:
    """Split a CIDR into subnets based on allowed prefix lengths.

    Divides CIDR blocks into smaller subnets using specified prefix lengths.
    Useful for VPC subnet planning and network segmentation in AWS deployments.

    Args:
        cidr: CIDR notation string to split (e.g., '10.0.0.0/16').
        allowed_prefix_lengths: List of valid prefix lengths for subnet creation.
                               Defaults to common subnet sizes [8, 16, 24, 32].

    Returns:
        List of subnet CIDR strings. Returns original CIDR if it already
        matches an allowed prefix length.

    Raises:
        jinja2.exceptions.FilterArgumentError: If CIDR is invalid or prefix
                                             length exceeds allowed values.
    """

    try:
        ip = netaddr.IPNetwork(cidr)
    except Exception as e:
        raise jinja2.exceptions.FilterArgumentError(
            "Invalid CIDR '{}' - {}".format(cidr, str(e))
        )

    # Do not split if CIDR already has an allowed prefix length
    if ip.prefixlen in allowed_prefix_lengths:
        return [str(ip)]

    # Find the smallest allowed prefix length
    try:
        size = next(s for s in allowed_prefix_lengths if s >= ip.prefixlen)
    except Exception:
        raise jinja2.exceptions.FilterArgumentError(
            "Failed to split CIDR '{}', prefix {} is larger than any allowed prefix length {}".format(
                cidr, ip.prefixlen, allowed_prefix_lengths
            )
        )

    return [str(x) for x in ip.subnet(size)]


def filter_subnet_network_zone(data: Any, default: str = "private") -> str:
    """Retrieve the network zone from the subnet ID object.

    Extracts network zone information from subnet ID specifications for
    AWS VPC subnet placement. Supports public, private, and custom zone types.

    Args:
        data: Dictionary containing 'Fn::Pipeline::SubnetId' specification
             with optional 'NetworkZone' field.
        default: Default network zone to return if not specified.

    Returns:
        Network zone string ('public', 'private', etc.) or default value.

    Raises:
        jinja2.exceptions.FilterArgumentError: If Fn::Pipeline::SubnetId
                                             specification is invalid.
    """
    # Used for AWS::EC2::SubnetId configuration. See subnet_id method.
    if data is None or isinstance(data, jinja2.Undefined):
        return default

    if not isinstance(data, dict):
        raise jinja2.exceptions.FilterArgumentError(
            "Filter_subnet_network_zone: Object must be a dictionary"
        )

    subnets = data.get("Fn::Pipeline::SubnetId", {})
    if not isinstance(subnets, dict):
        raise jinja2.exceptions.FilterArgumentError(
            "Filter_subnet_network_zone: Fn::Pipeline::SubnetId must be a dictionary"
        )
    return subnets.get("NetworkZone", default)


def filter_subnet_az_index(data: Any, default: int = 0) -> int:
    """Retrieve the Availability Zone index from the subnet ID object.

    Extracts availability zone index from subnet ID specifications for
    AWS VPC subnet placement across multiple AZs. Enables predictable
    AZ distribution for high availability deployments.

    Args:
        data: Dictionary containing 'Fn::Pipeline::SubnetId' specification
             with optional 'AzIndex' field.
        default: Default AZ index to return if not specified.

    Returns:
        Availability zone index integer (0, 1, 2, etc.) or default value.

    Raises:
        jinja2.exceptions.FilterArgumentError: If Fn::Pipeline::SubnetId
                                             specification is invalid.
    """
    if data is None or isinstance(data, jinja2.Undefined) or not isinstance(data, dict):
        return default

    if not isinstance(data, dict):
        raise jinja2.exceptions.FilterArgumentError(
            "Filter_subnet_az_index: Object must be a dictionary"
        )

    subnets = data.get("Fn::Pipeline::SubnetId", {})
    if not isinstance(subnets, dict):
        raise jinja2.exceptions.FilterArgumentError(
            "Filter_subnet_az_index: Fn::Pipeline::SubnetId must be a dictionary"
        )

    return subnets.get("AzIndex", default)


@pass_context
def filter_tags(
    render_context: Context, scope: str | None = None, component_name: str | None = None
) -> dict:
    """Create the standard tags from the context and component name.

    Generates comprehensive AWS resource tags based on deployment context and
    lifecycle scope. Tags follow Core Automation naming conventions and include
    portfolio, application, branch, build, environment, and component information.

    Args:
        render_context: The Jinja2 context containing deployment facts and variables.
        scope: Lifecycle scope determining tag composition:
              - SCOPE_ENVIRONMENT: Environment-level resources
              - SCOPE_PORTFOLIO: Portfolio-level resources
              - SCOPE_APP: Application-level resources
              - SCOPE_BRANCH: Branch-level resources
              - SCOPE_BUILD: Build-level resources (default)
        component_name: Component name to include in tags. If None,
                       extracted from context.

    Returns:
        Dictionary of tag key-value pairs including:
        - Portfolio: Always included
        - Name: Generated based on scope
        - Additional scope-specific tags (App, Branch, Build, Environment, Component)
        - Custom tags from deployment facts

    Notes:
        The Name tag format varies by scope to ensure unique resource naming
        across different lifecycle stages and deployment contexts.
    """
    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    if not facts:
        return {}

    if component_name is None:
        component_name = render_context.get(CTX_COMPONENT_NAME, "")

    portfolio = facts.get(DD_PORTFOLIO, "")
    app = facts.get(DD_APP, "")
    branch = facts.get(DD_BRANCH, "")
    branch_short_name = facts.get(DD_BRANCH_SHORT_NAME, "")
    build = facts.get(DD_BUILD, "")
    environment = facts.get(DD_ENVIRONMENT, "")

    # Portfolio is mandatory, and always included in the tags
    tags = {TAG_PORTFOLIO: portfolio, **facts.get(DD_TAGS, {})}

    if not scope:
        scope = facts.get(DD_SCOPE, SCOPE_BUILD)

    if scope == SCOPE_ENVIRONMENT:
        tags.update(
            {
                TAG_NAME: f"{portfolio}-{app}-{environment}-{component_name}",
                TAG_ENVIRONMENT: environment,
            }
        )
    elif scope == SCOPE_PORTFOLIO:
        tags.update(
            {
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
                TAG_NAME: f"{portfolio}-{component_name}",
            }
        )
    elif scope == SCOPE_APP:
        tags.update(
            {
                TAG_APP: app,
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
                TAG_NAME: f"{portfolio}-{app}-{component_name}",
            }
        )
    elif scope == SCOPE_BRANCH:
        tags.update(
            {
                TAG_APP: app,
                TAG_BRANCH: branch,
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
                TAG_NAME: f"{portfolio}-{app}-{branch}-{component_name}",
            }
        )

    elif scope == SCOPE_BUILD:
        tags.update(
            {
                TAG_APP: app,
                TAG_BRANCH: branch,
                TAG_BUILD: build,
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
                TAG_NAME: f"{portfolio}-{app}-{branch_short_name}-{build}-{component_name}",
            }
        )

    return tags


def filter_to_json(data: Any) -> Any:
    """Convert data to JSON format.

    Serializes Python data structures to JSON string format for template
    output and configuration file generation. Handles undefined values gracefully.

    Args:
        data: Python data structure to convert to JSON format.

    Returns:
        JSON string representation of the data, or the original value
        if it's undefined.

    Raises:
        jinja2.exceptions.UndefinedError: If data cannot be serialized to JSON.
    """
    if isinstance(data, jinja2.Undefined):
        return data

    try:
        return util.to_json(data)
    except Exception as e:
        raise jinja2.exceptions.UndefinedError(
            "Error converting data to JSON: {}".format(str(e))
        ) from e


def filter_to_yaml(data: Any) -> Any:
    """Convert data to YAML format.

    Serializes Python data structures to YAML string format for configuration
    files and human-readable output. Uses block style for readability.

    Args:
        data: Python data structure to convert to YAML format.

    Returns:
        YAML string representation of the data in block style format,
        or empty string if data is empty, or original value if undefined.

    Raises:
        jinja2.exceptions.UndefinedError: If data cannot be serialized to YAML.
    """
    if isinstance(data, jinja2.Undefined):
        return data

    if not data:
        return ""

    try:
        # Use yaml.safe_dump to convert the data to YAML format
        # default_flow_style=False ensures that the output is in block style
        # which is more readable for configuration files
        # dumped = yaml.safe_dump(data, default_flow_style=False)
        # dumped = re.sub(r"\n...\n$", "\n", dumped)
        dumped = util.to_yaml(data)
        return dumped.rstrip("\n")
    except Exception as e:
        raise jinja2.exceptions.UndefinedError(
            "Error converting data to YAML: {}".format(str(e))
        ) from e


@pass_context
def filter_read_file(render_context: Context, file_path: str) -> str:
    """Read the contents of a file and return as string."""

    facts: dict | None = render_context.get(CTX_CONTEXT, None)

    # Handle relative paths from the template directory
    if hasattr(filter_read_file, "_template_path") and filter_read_file._template_path:
        full_path = os.path.join(filter_read_file._template_path, file_path)
    else:
        full_path = __file_url(facts, {"Fn::Pipeline::FileUrl": {"Path": file_path}})

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading template file {file_path}: {str(e)}")

    raise jinja2.exceptions.UndefinedError(
        "Error reading file '{}': {}".format(file_path, str(e))
    ) from e


def __file_url(facts: dict, pipeline_file_spec: dict) -> Any:
    """Generate a file URL based on the provided pipeline file specification and context facts.

    Internal helper function that constructs S3 file URLs from Pipeline::FileUrl
    specifications and deployment context. Supports different scopes with
    appropriate prefix handling.

    Args:
        facts: Deployment context facts containing S3 bucket URLs and file prefixes.
        pipeline_file_spec: Pipeline file specification dictionary that may contain
                           'Fn::Pipeline::FileUrl' with Path and Scope fields.

    Returns:
        Generated S3 file URL for Pipeline::FileUrl specifications, or the
        original specification if not a file URL lookup.

    Raises:
        jinja2.exceptions.UndefinedError: If FileUrl scope is not recognized.
    """
    pipeline_file_url: dict | None = pipeline_file_spec.get(
        "Fn::Pipeline::FileUrl", None
    )

    if pipeline_file_url:

        name = pipeline_file_url.get("Path", "unspecified")
        scope = pipeline_file_url.get("Scope", SCOPE_BUILD)
        bucket_url = facts.get(CTX_FILES_BUCKET_URL, "")

        if scope == SCOPE_SHARED:
            url = "{}/{}/{}".format(
                bucket_url, facts.get(CTX_SHARED_FILES_PREFIX, ""), name
            )
        elif scope == SCOPE_PORTFOLIO:
            url = "{}/{}/{}".format(
                bucket_url, facts.get(CTX_PORTFOLIO_FILES_PREFIX, ""), name
            )
        elif scope == SCOPE_APP:
            url = "{}/{}/{}".format(
                bucket_url, facts.get(CTX_APP_FILES_PREFIX, ""), name
            )
        elif scope == SCOPE_BRANCH:
            url = "{}/{}/{}".format(
                bucket_url, facts.get(CTX_BRANCH_FILES_PREFIX, ""), name
            )
        elif scope == SCOPE_BUILD:
            url = "{}/{}/{}".format(
                bucket_url, facts.get(CTX_BUILD_FILES_PREFIX, ""), name
            )
        else:
            raise jinja2.exceptions.UndefinedError(
                "Unknown value '{}' for Fn::Pipeline::FileUrl Scope".format(scope)
            )
        return url

    # if not a Fn::Pipeline::FileUrl, return the original object unchanged
    return pipeline_file_spec


def __format_arn(
    service: str,
    region: str,
    account_id: str,
    resource: str,
    resource_type: str | None = None,
) -> str:
    """Format an ARN based on the provided parameters.

    Internal helper function that constructs AWS ARNs using the standard
    ARN format with optional resource type specification.

    Args:
        service: AWS service name (e.g., 'sns', 'sqs', 'dynamodb').
        region: AWS region identifier (e.g., 'us-west-2').
        account_id: AWS account ID (12-digit string).
        resource: Resource name or identifier.
        resource_type: Optional resource type (e.g., 'table' for DynamoDB).

    Returns:
        Formatted ARN string following AWS ARN conventions:
        arn:aws:service:region:account:resource or
        arn:aws:service:region:account:resource_type/resource
    """
    if resource_type:
        return f"arn:aws:{service}:{region}:{account_id}:{resource_type}/{resource}"
    else:
        return f"arn:aws:{service}:{region}:{account_id}:{resource}"


def __create_resource_arn(
    group: str, region: str, account_id: str, base_resource_name_hyphenated: str
) -> str:
    """Create a standard ARN for the specified AWS service group, region, account ID, and base resource name.

    Internal helper function that generates standard ARNs for common AWS services
    using predefined patterns and the deployment base resource name.

    Args:
        group: AWS service group identifier (e.g., 'sns', 'sqs', 'dynamodb').
        region: AWS region identifier.
        account_id: AWS account ID.
        base_resource_name_hyphenated: Base resource name with hyphens for consistent naming.

    Returns:
        Formatted ARN string with wildcard patterns for the specified service,
        following standard Core Automation resource naming conventions.
    """
    std_arns = {
        "sns": "arn:aws:sns:{}:{}:{}-*",
        "sqs": "arn:aws:sqs:{}:{}:{}-*",
        "secretsmanager": "arn:aws:secretsmanager:{}:{}:secret:{}-*",
        "ssm": "arn:aws:ssm:{}:{}:parameter/{}-*",
        "dynamodb": "arn:aws:dynamodb:{}:{}:table/{}-*",
        "ses": "arn:aws:ses:{}:{}:identity/{}-*",
    }

    test_arn = std_arns.get(group, None)

    if test_arn is not None:
        return test_arn.format(region, account_id, base_resource_name_hyphenated)

    another_arns = {"s3": "arn:aws:s3:::{}-*"}
    test_arn = another_arns.get(group, None)

    if test_arn is not None:
        return test_arn.format(base_resource_name_hyphenated)

    return __format_arn(group, region, account_id, base_resource_name_hyphenated)


def load_filters(environment: Environment) -> None:
    """Load custom filters into the Jinja2 environment.

    Registers all Core Automation filters and globals with the provided
    Jinja2 environment for template rendering functionality.

    Args:
        environment: Jinja2 Environment instance to register filters with.

    Note:
        This function must be called to make all custom filters available
        in Jinja2 templates for Core Automation rendering.
    """

    if hasattr(environment.loader, "searchpath") and environment.loader.searchpath:
        filter_read_file._template_path = environment.loader.searchpath[0]

    # Filters
    environment.filters["aws_tags"] = filter_aws_tags
    environment.filters["docker_image"] = filter_docker_image
    environment.filters["ebs_encrypt"] = filter_ebs_encrypt
    environment.filters["ensure_list"] = filter_ensure_list
    environment.filters["extract"] = filter_extract
    environment.filters["format_date"] = filter_format_date
    environment.filters["iam_rules"] = filter_iam_rules
    environment.filters["image_alias_to_id"] = filter_image_alias_to_id
    environment.filters["image_id"] = filter_image_id
    environment.filters["image_name"] = filter_image_name
    environment.filters["ip_rules"] = filter_ip_rules
    environment.filters["lookup"] = filter_lookup
    environment.filters["min_int"] = filter_min_int
    environment.filters["output_name"] = filter_output_name
    environment.filters["parse_port_spec"] = filter_parse_port_spec
    environment.filters["process_cfn_init"] = filter_process_cfn_init
    environment.filters["regex_replace"] = filter_regex_replace
    environment.filters["rstrip"] = filter_rstrip
    environment.filters["shorten_unique"] = filter_shorten_unique
    environment.filters["snapshot_id"] = filter_snapshot_id
    environment.filters["snapshot_name"] = filter_snapshot_name
    environment.filters["split_cidr"] = filter_split_cidr
    environment.filters["subnet_az_index"] = filter_subnet_az_index
    environment.filters["subnet_network_zone"] = filter_subnet_network_zone
    environment.filters["tags"] = filter_tags
    environment.filters["to_json"] = filter_to_json
    environment.filters["to_yaml"] = filter_to_yaml
    environment.filters["policy_statements"] = filter_policy_statements
    environment.filters["read_file"] = filter_read_file

    # Globals
    environment.globals["raise"] = raise_exception


def raise_exception(message):
    """Raise an exception with the specified message.

    Global function available in Jinja2 templates for error handling
    and validation purposes.

    Args:
        message: Error message to include in the raised exception.
    """
    raise Exception(message)  # NOSONAR:
