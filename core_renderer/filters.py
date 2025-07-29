from typing import Any

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
    """
    Create a list of AWS tags from the render context and scope.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param scope: The scope of the tags (e.g., SCOPE_BUILD, SCOPE_ENVIRONMENT, etc.).
    :param component_name: The name of the component to include in the tags.
    :return: A list of dictionaries representing the tags.
    :raises jinja2.exceptions.UndefinedError: If the context does not contain the required facts.
    """
    tags_hash = filter_tags(render_context, scope, component_name)

    items: list[dict] = [
        {"Key": key, "Value": value} for key, value in tags_hash.items()
    ]

    return items


@pass_context
def filter_docker_image(render_context: Context, object: Any) -> str | None:
    """
    Generate a Docker image name based on the provided object and render context.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param object: The object containing the Docker image name.
    :return: The full Docker image name or None if the context is not available.
    :raises jinja2.exceptions.UndefinedError: If the required keys are not present in the object.
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
    """
    Enforce encryption for EBS volumes in the provided EBS specification.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param ebs_spec: A list of dictionaries representing the EBS specifications.
    :return: The modified EBS specification with encryption enforced.
    :raises jinja2.exceptions.UndefinedError: If the EBS specification is not a list.
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
    """
    Wrap the object in a list if it isn't already a list.

    :param object: The object to ensure is a list.
    :return: The object list or an empty list if the object is None or Undefined.
    :raises jinja2.exceptions.UndefinedError: If the object is Undefined.
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
    """
    Extract a value from an object using JMESPath.

    :param object: The object to extract the value from.
    :param path: The JMESPath expression to extract the value.
    :param default: The default value to return if the path does not exist.
    :return: The extracted value or the default value.
    :raises jinja2.exceptions.UndefinedError: If the path does not exist and default is "_error_".
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
    """
    Create IAM security rules based on the provided resource and render context.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param resource: The resource dictionary containing security rules.
    :return: A list of security rules.
    :raises jinja2.exceptions.FilterArgumentError: If the security source is not a label of a component in the app.
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
    """
    Convert an image alias to its corresponding image ID.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param image_alias: The alias of the image to look up.
    :return: The image ID corresponding to the alias or None if not found.
    :raises jinja2.exceptions.UndefinedError: If the image alias is not found in the facts.
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
    """
    Get the image ID from the render context based on the provided object.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param o: The object containing the image ID lookup.
    :return: The image ID corresponding to the alias or None if not found.
    :raises jinja2.exceptions.UndefinedError: If the image alias is not specified or not found in the facts.
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
    """
    Get the image name from the render context based on the provided object.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param o: The object containing the image ID lookup.
    :return: The image name corresponding to the alias.
    :raises jinja2.exceptions.UndefinedError: If the image alias is not specified or not found in the facts.
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
    """
    Generate a list of security rules based on the provided resource and render context.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param resource: The resource dictionary containing security rules.
    :param rule_type: The type of rule to generate (default is 'ip').
    :param source_types: A list of source types to filter the security rules (default is ['cidr', 'component', 'prefix']).
    :param source_only: If True, only include the source without Allow information (default is False).
    :return: A list of security rules.
    :raises jinja2.exceptions.UndefinedError: If the security source is not a security alias or a component.
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
    """
    Look up a value in the render context using the specified path.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param path: The path to look up in the render context.
    :param default: The default value to return if the path does not exist.
    :return: The value found at the specified path or the default value.
    :raises jinja2.exceptions.UndefinedError: If the path does not exist and default is "_error_".
    """

    value = jmespath.search(path, render_context.parent)

    if value is None:
        if default == "_error_":
            raise jinja2.exceptions.UndefinedError(
                "Filter_lookup: Error during value lookup - no attribute '{}'".format(
                    path
                )
            )
        return default

    return value


def filter_min_int(*values) -> Any | None:
    """
    Useful for stuff like MinSuccessfulInstancesPercent, where you want to establish a "floor" value.

    :param values: A variable number of integer values.
    :return: The minimum integer value from the provided values, or None if no values are provided.
    :raises jinja2.exceptions.FilterArgumentError: If no values are provided.

    """
    # The values are passed are a tuple, so we need to check if the first element is a list.
    # We need to get the list from the tuple.
    if not values or len(values) == 0:
        return None

    return min(list(values))


@pass_context
def filter_output_name(render_context: Context, o: dict) -> str | None:
    """
    Get the output name based on the deployment details and output configuration.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param o: The object containing the output configuration.
    :return: The output name based on the deployment details and output configuration.
    :raises jinja2.exceptions.UndefinedError: If the Fn::Pipeline::GetOutput is not specified or if the lifecycle scope is not supported.
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
    """
    Parse a port specification string into a dictionary with Protocol, FromPort, and ToPort.

    :param port_spec: The port specification string to parse.
    :return: A dictionary with keys 'Protocol', 'FromPort', and 'ToPort'.
    :raises jinja2.exceptions.UndefinedError: If the port specification is invalid.
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
    """
    Generate a policy statement based on the provided statement and render context.
    :param render_context: The Jinja2 context containing the facts and other variables.
    :param statement: The policy statement to process.
    :return: A dictionary representing the policy statement with resources.
    :raises jinja2.exceptions.UndefinedError: If the statement does not contain 'Action' or 'Effect'.
    :raises jinja2.exceptions.FilterArgumentError: If the statement does not contain 'Action' and 'Effect'.
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
    """
    Process the CloudFormation Init configuration to ensure all sources and files are prefixed with the S3 artefact URL.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param cfn_init: The CloudFormation Init configuration to process.
    :return: The processed CloudFormation Init configuration or None if the context is not available.
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
    """A non-optimal implementation of a regex filter

    :param s: The string to perform the replacement on.
    :param find: The regex pattern to find in the string.
    :param replace: The string to replace the found pattern with.
    :return: The modified string after performing the replacement.
    """
    return re.sub(find, replace, s)


def filter_format_date(value: Any, f: str = "%d-%b-%y") -> str:
    """
    Format a date object or a string representation of "now" into a specified format.

    :param value: The value to format, can be a date object or the string "now".
    :param f: The format string to use for formatting the date.
    :return: The formatted date string.
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
    """
    Remove trailing characters from a string.

    :param value: The string to process.
    :param chars: The characters to remove from the end of the string.
    :return: The string with trailing characters removed.
    """
    return value.rstrip(chars)


def filter_shorten_unique(
    value: str, limit: int, unique_length: int = 0, charset: str | None = None
):
    """
    Shorten a string to a specified limit and append a unique string of a given length.

    :param value: The string to shorten.
    :param limit: The maximum length of the resulting string.
    :param unique_length: The length of the unique string to append (default is 0, meaning no unique string).
    :param charset: The characters to use for generating the unique string (default is alphanumeric characters).
    :return: The shortened string with a unique suffix.
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
    """
    Retrieve the snapshot identifier from the render context based on the provided snapshot specification and component type.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param snapshot_spec: The snapshot specification containing the Fn::Pipeline::SnapshotId lookup.
    :param component_type: The type of component for which to retrieve the snapshot identifier.
    :return: A dictionary with the snapshot identifier and owner account, or None if not found.
    :raises jinja2.exceptions.UndefinedError: If the snapshot specification is not a dictionary or if the context does not contain valid snapshot aliases.
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
    """
    Retrieve the snapshot name from the render context based on the provided snapshot specification and component type.

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param snapshot_spec: The snapshot specification containing the Fn::Pipeline::SnapshotId lookup.
    :param component_type: The type of component for which to retrieve the snapshot name.
    :return: The snapshot name or None if not found.
    :raises jinja2.exceptions.UndefinedError: If the snapshot specification does not contain Fn::Pipeline::SnapshotId or if the context does not contain valid snapshot aliases.
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
    """
    Split a CIDR into subnets based on allowed prefix lengths.

    :param cidr: The CIDR notation to split.
    :param allowed_prefix_lengths: A list of allowed prefix lengths to split the CIDR into.
    :return: A list of subnets in CIDR notation.
    :raises jinja2.exceptions.FilterArgumentError: If the CIDR is invalid or if the prefix length is larger than any allowed prefix length.
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
    """
    Retrieve the network zone from the subnet ID object.

    :param data: The object containing the Fn::Pipeline::SubnetId lookup.
    :param default: The default value to return if the network zone is not specified (default is 'private').
    :return: The network zone or the default value if not specified.
    :raises jinja2.exceptions.FilterArgumentError: If the Fn::Pipeline::SubnetId lookup is not specified.
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
    """
    Retrieve the Availability Zone index from the subnet ID object.

    :param data: The object containing the Fn::Pipeline::SubnetId lookup.
    :param default: The default value to return if the AzIndex is not specified (default is 0).
    :return: The AzIndex or the default value if not specified.
    :raises jinja2.exceptions.FilterArgumentError: If the Fn::Pipeline::SubnetId lookup is not specified or if AzIndex is not present.
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
    """
    Create the standard tags from the context and component name.
    This is a Jija2 filter and the render_context is the variables passed to jinja2

    :param render_context: The Jinja2 context containing the facts and other variables.
    :param scope: The scope of the tags (e.g., SCOPE_BUILD, SCOPE_ENVIRONMENT, etc.).
    :param component_name: The name of the component to include in the tags.
    :return: A dictionary of tags.
    :raises jinja2.exceptions.UndefinedError: If the context does not contain the required facts.
    :raises jinja2.exceptions.FilterArgumentError: If the scope is not recognized.
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
    """
    Convert data to JSON format.

    :param data: The data to convert to JSON.
    :return: The JSON representation of the data.
    :raises jinja2.exceptions.UndefinedError: If the data cannot be converted to JSON.
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
    """
    Convert data to YAML format.

    :param data: The data to convert to YAML.
    :return: The YAML representation of the data.
    :raises jinja2.exceptions.UndefinedError: If the data cannot be converted to YAML.
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


def __file_url(facts: dict, pipeline_file_spec: dict) -> Any:
    """
    Generate a file URL based on the provided pipeline file specification and context facts.

    :param facts: The context facts containing the files bucket URL and prefixes.
    :param pipeline_file_spec: The pipeline file specification containing the Fn::Pipeline::FileUrl
    :return: The generated file URL or the original pipeline file specification if not a Fn::Pipeline::FileUrl.
    :raises jinja2.exceptions.UndefinedError: If the scope in Fn::Pipeline::FileUrl is unknown.
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
    """
    Format an ARN based on the provided parameters.

    :param service: The AWS service (e.g., 'sns', 'sqs', 'dynamodb', etc.).
    :param region: The AWS region (e.g., 'us-west-2').
    :param account_id: The AWS account ID.
    :param resource: The resource name or ID.
    :param resource_type: The resource type (optional, e.g., 'table' for DynamoDB).
    :return: The formatted ARN.
    """
    if resource_type:
        return f"arn:aws:{service}:{region}:{account_id}:{resource_type}/{resource}"
    else:
        return f"arn:aws:{service}:{region}:{account_id}:{resource}"


def __create_resource_arn(
    group: str, region: str, account_id: str, base_resource_name_hyphenated: str
) -> str:
    """
    Create a standard ARN for the specified AWS service group, region, account ID, and base resource name.

    :param group: The AWS service group (e.g., 'sns', 'sqs', 'dynamodb', etc.).
    :param region: The AWS region (e.g., 'us-west-2').
    :param account_id: The AWS account ID.
    :param base_resource_name_hyphenated: The base resource name in hyphenated format.
    :return: The formatted ARN for the specified service group.
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


def load_filters(environment: Environment):
    """
    Load custom filters into the Jinja2 environment.

    :param environment: The Jinja2 environment to load the filters into.
    :raises jinja2.exceptions.UndefinedError: If the environment is not a Jinja2 Environment instance.
    """
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

    # Globals
    environment.globals["raise"] = raise_exception


def raise_exception(message):
    raise Exception(message)  # NOSONAR: python:S112
