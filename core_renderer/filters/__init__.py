"""
This is a filters library for the Jinja2 template platform

"""

from jinja2.environment import Environment

from .filters import (
    filter_aws_tags,
    filter_docker_image,
    filter_ensure_list,
    filter_extract,
    filter_min_int,
    filter_iam_rules,
    filter_policy_statements,
    filter_ebs_encrypt,
    filter_image_alias_to_id,
    filter_image_id,
    filter_image_name,
    filter_ip_rules,
    filter_lookup,
    filter_output_name,
    filter_parse_port_spec,
    filter_process_cfn_init,
    filter_rstrip,
    filter_shorten_unique,
    filter_snapshot_id,
    filter_snapshot_name,
    filter_split_cidr,
    filter_subnet_network_zone,
    filter_subnet_az_index,
    filter_tags,
    filter_to_json,
    filter_to_yaml,
    filter_regex_replace,
    filter_format_date,
)

__all__ = [
    "filter_aws_tags",
    "filter_docker_image",
    "filter_ensure_list",
    "filter_extract",
    "filter_min_int",
    "filter_iam_rules",
    "filter_policy_statements",
    "filter_ebs_encrypt",
    "filter_image_alias_to_id",
    "filter_image_id",
    "filter_image_name",
    "filter_ip_rules",
    "filter_lookup",
    "filter_output_name",
    "filter_parse_port_spec",
    "filter_process_cfn_init",
    "filter_rstrip",
    "filter_shorten_unique",
    "filter_snapshot_id",
    "filter_snapshot_name",
    "filter_split_cidr",
    "filter_subnet_network_zone",
    "filter_subnet_az_index",
    "filter_tags",
    "filter_to_json",
    "filter_to_yaml",
    "filter_regex_replace",
    "filter_format_date",
    "load_filters",
]


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
