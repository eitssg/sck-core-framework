from typing import Any

import copy
import jinja2
import jmespath
import re
import yaml
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

    tags_hash = filter_tags(render_context, scope, component_name)

    items: list[dict] = []

    for key, value in tags_hash.items():
        items.append({"Key": key, "Value": value})

    return items


@pass_context
def filter_docker_image(render_context: Context, object: Any) -> str | None:

    facts = render_context.get(CTX_CONTEXT)

    if facts is None:
        return None

    if "Fn::Pipeline::DockerImage" not in object:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::DockerImage lookup"
        )

    ecr_repository_name = "private/{}-{}-{}-{}-{}".format(
        facts[DD_PORTFOLIO],
        facts[DD_APP],
        facts[DD_BRANCH_SHORT_NAME],
        facts[DD_BUILD],
        render_context[CTX_COMPONENT_NAME],
    )

    image_name = object["Fn::Pipeline::DockerImage"]["Name"]

    return "{}/{}:{}".format(
        facts[DD_ECR][ECR_REGISTRY_URI], ecr_repository_name, image_name
    )


def filter_ensure_list(object: Any) -> list[Any]:
    """
    Wrap the object in a list if it isn't already a list.

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

    if object is None or isinstance(object, jinja2.Undefined):
        value = None
    else:
        value = jmespath.search(path, object)

    if value is None:
        if default == "_error_":
            raise jinja2.exceptions.UndefinedError(
                "Filter_extract: Error during value extraction - no attribute '{}'".format(
                    path
                )
            )
        else:
            value = default

    return value


def filter_min_int(*values) -> Any:
    """
    Useful for stuff like MinSuccessfulInstancesPercent, where you want to establish a "floor" value.
    """
    if len(values) == 0:
        return None
    return min(values)


@pass_context
def filter_iam_rules(render_context: Context, resource: dict) -> list:

    facts = render_context.get(CTX_CONTEXT)  # Conteext is a DeploymentDetails object

    if facts is None:
        return []

    app = render_context[CTX_APP]

    security_rules = []
    for security_rule in resource.get("Pipeline::Security", []):

        for security_source in filter_ensure_list(security_rule["Source"]):

            if security_source in app:

                # Source is component
                security_rules.append(
                    {
                        "Type": "component",
                        "Value": "-".join(
                            [
                                facts[DD_PORTFOLIO],
                                facts[DD_APP],
                                facts[DD_BRANCH_SHORT_NAME],
                                security_source,
                                "security:RoleName",
                            ]
                        ),
                        "Description": "Component {}".format(security_source),
                        "Allow": filter_ensure_list(security_rule.get("Allow")),
                        "SourceType": app[security_source]["Type"],
                        "SecurityGroupId": "-".join(
                            [
                                facts[DD_PORTFOLIO],
                                facts[DD_APP],
                                facts[DD_BRANCH_SHORT_NAME],
                                security_source,
                                "security:SecurityGroupId",
                            ]
                        ),
                    }
                )
            else:
                # Unknown source
                raise jinja2.exceptions.UndefinedError(
                    "Filter_iam_rules: Invalid security source '{}' - must be a component".format(
                        security_source
                    )
                )

    return security_rules


@pass_context
def filter_policy_statements(render_context: Context, statement: dict) -> dict:

    facts = render_context.get(CTX_CONTEXT)  # Context is a DeploymentDetails object]

    if facts is None:
        return {}

    base_resource_name_hyphenated = "-".join(
        [facts[DD_PORTFOLIO], facts[DD_APP], facts[DD_BRANCH_SHORT_NAME]]
    )

    resources = []
    added: set[str] = set()

    # AWS Poliction Statement
    for action in statement["Action"]:
        group = action.split(":")[0]
        if group not in added:
            arn = create_resource_arn(
                group,
                facts["AwsRegion"],
                facts["AwsAccountId"],
                base_resource_name_hyphenated,
            )
            if arn is not None:
                resources.append(arn)
            else:
                raise jinja2.exceptions.UndefinedError(
                    f"Filter_policy_statements: Currently free form policy for group {group} not supported"
                )

    return {
        "Action": statement["Action"],
        "Effect": statement["Effect"],
        "Resource": resources,
    }


def format_arn(
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


def create_resource_arn(
    group: str, region: str, account_id: str, base_resource_name_hyphenated: str
) -> str:

    std_arns = {
        "sns": "arn:aws:sns:{}:{}:{}-*",
        "sqs": "arn:aws:sqs:{}:{}:{}-*",
        "secretsmanager": "arn:aws:sns:{}:{}:{}-*",
        "ssm": "arn:aws:sns:{}:{}:{}-*",
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

    return format_arn(group, region, account_id, base_resource_name_hyphenated)


@pass_context
def filter_ebs_encrypt(render_context: Context, ebs_spec: list[dict]) -> list:

    for bdm in ebs_spec:

        if "Ebs" in bdm:
            bdm["Ebs"]["Encrypted"] = "true"  # Enforce encryption for ebs volumes.
            # TODO. it seems KmsKey is not supported for BlockDeviceMappings
            # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ec2-blockdev-template.html
            # bdm['Ebs']['KmsKeyId'] = ${KmsKeyArn}

    return ebs_spec


@pass_context
def filter_image_alias_to_id(render_context: Context, image_alias: str) -> str | None:

    facts = render_context.get(CTX_CONTEXT)

    if facts is None:
        return None

    if image_alias not in facts["ImageAliases"]:
        raise jinja2.exceptions.UndefinedError("Unknown image '{}'".format(image_alias))

    return facts["ImageAliases"][image_alias]


@pass_context
def filter_image_id(render_context: Context, o: dict) -> str | None:

    facts = render_context.get(CTX_CONTEXT)

    if not facts:
        return None

    if "Fn::Pipeline::ImageId" not in o:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::ImageId lookup"
        )

    image_alias = o["Fn::Pipeline::ImageId"]["Name"]

    if image_alias not in facts["ImageAliases"]:
        raise jinja2.exceptions.UndefinedError("Unknown image '{}'".format(image_alias))

    return facts["ImageAliases"][image_alias]


@pass_context
def filter_image_name(render_context: Context, o: dict):

    if "Fn::Pipeline::ImageId" not in o:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::ImageId lookup"
        )

    image_name = o["Fn::Pipeline::ImageId"]["Name"]

    return image_name


@pass_context
def filter_ip_rules(  # noqa C901
    render_context: Context,
    resource: dict,
    rule_type: str = ST_IP_ADDRESS,
    source_types: list[str] = [ST_CIDR, ST_COMPONENT, ST_PREFIX],
    source_only: bool = False,
) -> list[dict]:

    facts = render_context[CTX_CONTEXT]  # Context is a DeploymentDetails object

    app = render_context[CTX_APP]

    security_rules: list[dict] = []

    if facts is None or app is None:
        return security_rules

    for security_rule in resource.get("Pipeline::Security", []):

        for security_source in filter_ensure_list(security_rule["Source"]):

            if not isinstance(security_source, str):
                continue

            sources: list[dict] = []

            if security_source in facts["SecurityAliases"]:
                # Source is an alias in facts
                sources = [
                    o
                    for o in facts["SecurityAliases"][security_source]
                    if isinstance(o, dict)
                ]
            elif security_source in app:
                # Source is component
                sources = [
                    {
                        "Type": ST_COMPONENT,
                        "Value": "-".join(
                            [
                                facts[DD_PORTFOLIO],
                                facts[DD_APP],
                                facts[DD_BRANCH_SHORT_NAME],
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
            sources = [source for source in sources if source["Type"] in source_types]

            for source in sources:
                if source_only or source["Type"] == ST_SECURITY_GROUP:
                    # Add the source as-is (without Allow information)
                    security_rules.append(source)
                else:
                    # Combine the source with Allow information, for each Allow rule
                    for allow in filter_ensure_list(security_rule["Allow"]):
                        if not isinstance(allow, str):
                            continue
                        security_rules.append(
                            {**source, **filter_parse_port_spec(allow)}
                        )

    return security_rules


@pass_context
def filter_lookup(render_context: Context, path: str, default: str = "_error_") -> str:

    if path in render_context:
        value = render_context[path]
    elif default != "_error_":
        value = default
    else:
        raise jinja2.exceptions.UndefinedError(
            "Filter_lookup: Lookup failed for '{}'".format(path)
        )

    return value


@pass_context
def filter_output_name(render_context: Context, o: dict) -> str | None:
    """
    Originally written purely for lambda.
    Renamed to be more generic.
    """
    facts = render_context.get(
        CTX_CONTEXT
    )  # This context is a DeploymentDetails object

    if facts is None:
        return None

    output_config: dict | None = o.get("Fn::Pipeline::GetOutput", None)

    if not output_config:
        raise jinja2.exceptions.UndefinedError(
            "Filter_output_name: Must specify Fn::Pipeline::GetOutput (Scope, Component, ExportName)."
        )

    lifecycle_scope = output_config.get(DD_SCOPE, SCOPE_BUILD)
    component_name = output_config["Component"]
    output_name = output_config["OutputName"]

    if lifecycle_scope == SCOPE_BUILD:
        return "-".join(
            [
                facts[DD_PORTFOLIO],
                facts[DD_APP],
                facts[DD_BRANCH],
                facts[DD_BUILD],
                component_name,
                "pointers:{}".format(output_name),
            ]
        )
    else:
        raise NotImplementedError(
            "Filter_output_name: Only build scope supported at this time. Add 'release' scope later."
        )


def filter_parse_port_spec(port_spec: str) -> dict:

    # Used for AWS::EC2::SecurityGroupIngress configuration. See ip_rules method.

    PORT_SPEC_REGEX = r"^((?:TCP)|(?:UDP)|(?:ICMP)|(?:ALL)):((?:[0-9]+)|(?:\*))(?:-((?:[0-9]+)|(?:\*)))?$"
    match = re.match(PORT_SPEC_REGEX, port_spec)
    if match is None:
        raise jinja2.exceptions.UndefinedError(
            "Filter_parse_port_spec: Invalid port specification '{}'. Must be <protocol>:<from_port>[-<to_port>]".format(
                port_spec
            )
        )

    # Extract regex captures
    matches = match.groups()
    protocol = matches[0]
    from_port = matches[1]
    to_port = matches[2]

    if protocol == "ALL":
        protocol = "-1"
    elif protocol == "ICMP":
        to_port = "-1"

    if from_port == "*":
        from_port = 0

    if to_port is None or to_port == "":
        to_port = from_port
    elif to_port == "*":
        to_port = 65535

    return {"Protocol": protocol, "FromPort": from_port, "ToPort": to_port}


@pass_context
def filter_process_cfn_init(render_context: Context, cfn_init: dict) -> dict | None:

    facts = render_context[CTX_CONTEXT]  # Context is a DeploymentDetails object

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


def filter_rstrip(value: str, chars: str) -> str:
    return value.rstrip(chars)


def filter_shorten_unique(
    value: str, limit: int, unique_length: int = 0, charset: str | None = None
):

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

    facts: dict | None = render_context.get(CTX_CONTEXT)

    if not facts:
        return None

    snapshot_id: dict | None = snapshot_spec.get("Fn::Pipeline::SnapshotId", None)

    if not snapshot_id:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::SnapshotId lookup"
        )

    snapshot_alias_name = snapshot_id.get("Name", "unsepcified")

    context_snapshot_aliases = facts.get(CTX_SNAPSHOT_ALIASES, None)
    if not context_snapshot_aliases:
        raise jinja2.exceptions.UndefinedError("No snapshot aliases defined in context")

    snapshot_alias_type = context_snapshot_aliases.get(component_type, None)
    if not snapshot_alias_type:
        raise jinja2.exceptions.UndefinedError(
            "Unknown component_type '{}'".format(component_type)
        )

    snap_alias = snapshot_alias_type[snapshot_alias_name]
    if not snap_alias:
        raise jinja2.exceptions.UndefinedError(
            "Unknown snapshot_alias '{}'".format(snapshot_alias_name)
        )

    params = {"SnapshotIdentifier": snap_alias["SnapshotIdentifier"]}

    if "AccountAlias" in snap_alias:
        params["OwnerAccount"] = facts[CTX_ACCOUNT_ALIASES][snap_alias["AccountAlias"]]

    return params


@pass_context
def filter_snapshot_name(
    render_context: Context, snapshot_spec: dict, component_type: str
) -> str | None:

    context = render_context.get(CTX_CONTEXT)

    if not context:
        return None

    snapshot_id = snapshot_spec.get("Fn::Pipeline::SnapshotId", None)

    if not snapshot_id:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::SnapshotId lookup"
        )

    snapshot_alias_name = snapshot_id.get("Name", "unspecified")

    context_snapshot_aliases = context.get(CTX_SNAPSHOT_ALIASES, None)
    if not context_snapshot_aliases:
        raise jinja2.exceptions.UndefinedError("No snapshot aliases defined in context")

    snapshot_alias_type = context_snapshot_aliases.get(component_type, None)
    if not snapshot_alias_type:
        raise jinja2.exceptions.UndefinedError(
            "Unknown component_type '{}'".format(component_type)
        )

    snap_alias = snapshot_alias_type[snapshot_alias_name]
    if not snap_alias:
        raise jinja2.UndefinedError(
            "Unknown snapshot_alias '{}'".format(snapshot_alias_name)
        )

    return snap_alias["SnapshotIdentifier"]


def filter_split_cidr(
    cidr: str, allowed_prefix_lengths: list[int] = [8, 16, 24, 32]
) -> list[str]:

    # Load the CIDR using netaddr

    try:
        ip = netaddr.IPNetwork(cidr)
    except Exception as e:
        raise jinja2.exceptions.UndefinedError("Invalid CIDR '{}' - {}".format(cidr, e))

    # Do not split if CIDR already has an allowed prefix length
    if ip.prefixlen in allowed_prefix_lengths:
        return [str(ip)]

    # Find the smallest allowed prefix length
    try:
        size = next(s for s in allowed_prefix_lengths if s >= ip.prefixlen)
    except Exception as e:
        raise jinja2.exceptions.UndefinedError(
            "Failed to split CIDR '{}', prefix {} is larger than any allowed prefix length {} - {}".format(
                cidr, ip.prefixlen, allowed_prefix_lengths, e
            )
        )

    # Split the CIDR
    try:
        split_cidrs = list(ip.subnet(size))
    except Exception as e:
        raise jinja2.exceptions.UndefinedError(
            "Failed to split CIDR '{}' into prefix lengths of {} - {}".format(
                cidr, size, e
            )
        )

    return [str(x) for x in split_cidrs]


def filter_subnet_network_zone(object: Any, default: str = "private") -> str:

    if object is None or isinstance(object, jinja2.Undefined):
        return default

    if "Fn::Pipeline::SubnetId" not in object:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::SubnetId lookup"
        )

    if "NetworkZone" not in object["Fn::Pipeline::SubnetId"]:
        return default

    return object["Fn::Pipeline::SubnetId"]["NetworkZone"]


def filter_subnet_az_index(object: Any, default: int = 0) -> int:

    if object is None or isinstance(object, jinja2.Undefined):
        return default

    if "Fn::Pipeline::SubnetId" not in object:
        raise jinja2.exceptions.UndefinedError(
            "Must specify Fn::Pipeline::SubnetId lookup"
        )

    if "AzIndex" not in object["Fn::Pipeline::SubnetId"]:
        return default

    return object["Fn::Pipeline::SubnetId"]["AzIndex"]


@pass_context
def filter_tags(
    render_context: Context, scope: str | None = None, component_name: str | None = None
) -> dict:
    """Create the standard tags from the context and component name.
    This is a Jija2 filter and the render_context is the variables passed to jinja2

    Args:
        render_context (Context): The context passed to the jinja2 filter
        scope (str, optional): The scope of the tags. Defaults to SCOPE_BUILD.
        component_name (str, optional): The component name. Defaults to None.

    """

    facts: dict | None = render_context.get(CTX_CONTEXT)

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

    tags = {TAG_PORTFOLIO: portfolio, TAG_APP: app, **facts.get(DD_TAGS, {})}

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
                TAG_NAME: f"{portfolio}-{component_name}",
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
            }
        )
    elif scope == SCOPE_APP:
        tags.update(
            {
                TAG_NAME: f"{portfolio}-{app}-{component_name}",
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
            }
        )
    elif scope == SCOPE_BRANCH:
        tags.update(
            {
                TAG_BRANCH: branch,
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
                TAG_NAME: f"{portfolio}-{app}-{branch}-{component_name}",
            }
        )

    elif scope == SCOPE_BUILD:
        tags.update(
            {
                TAG_BRANCH: branch,
                TAG_BUILD: build,
                TAG_ENVIRONMENT: environment,
                TAG_COMPONENT: component_name,
                TAG_NAME: f"{portfolio}-{app}-{branch_short_name}-{build}-{component_name}",
            }
        )

    return tags


def filter_to_json(data: Any) -> Any:

    if isinstance(data, jinja2.Undefined):
        return data

    return util.to_json(data)


def filter_to_yaml(data: Any) -> Any:

    if isinstance(data, jinja2.Undefined):
        return data

    dumped = yaml.safe_dump(data, default_flow_style=False)

    dumped = re.sub(r"\n...\n$", "\n", dumped)

    return dumped.rstrip("\n")


def __file_url(facts: dict, pipeline_file_spec: dict) -> Any:

    pipeline_file_url = pipeline_file_spec.get("Fn::Pipeline::FileUrl", None)

    if pipeline_file_url:

        name = pipeline_file_url.get("Path", "unspecified")
        scope = pipeline_file_url.get("Scope", SCOPE_BUILD)
        bucket_url = facts.get(CTX_FILES_BUCKET_URL, "")

        if scope == SCOPE_SHARED:
            url = "{}/{}/{}".format(bucket_url, facts[CTX_SHARED_FILES_PREFIX], name)
        elif scope == SCOPE_PORTFOLIO:
            url = "{}/{}/{}".format(bucket_url, facts[CTX_PORTFOLIO_FILES_PREFIX], name)
        elif scope == SCOPE_APP:
            url = "{}/{}/{}".format(bucket_url, facts[CTX_APP_FILES_PREFIX], name)
        elif scope == SCOPE_BRANCH:
            url = "{}/{}/{}".format(bucket_url, facts[CTX_BRANCH_FILES_PREFIX], name)
        elif scope == SCOPE_BUILD:
            url = "{}/{}/{}".format(bucket_url, facts[CTX_BUILD_FILES_PREFIX], name)
        else:
            raise jinja2.exceptions.UndefinedError(
                "Unknown value '{}' for Fn::Pipeline::FileUrl Scope".format(scope)
            )
        return url

    # if not a Fn::Pipeline::FileUrl, return the original object unchanged
    return pipeline_file_spec


def filter_regex_replace(s, find, replace) -> str:
    """A non-optimal implementation of a regex filter"""
    return re.sub(find, replace, s)


def filter_format_date(f: str = "%d-%b-%y") -> str:
    return date.today().strftime(f)


def load_filters(environment: Environment):

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
