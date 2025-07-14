"""
Unit tests for the custom Jinja2 filters in core_renderer.filters.
"""

import pytest
import jinja2
from jinja2 import Environment
from jinja2.runtime import Context
from datetime import date
import core_framework as util
from core_renderer.filters import (
    filter_aws_tags,
    filter_docker_image,
    filter_ebs_encrypt,
    filter_ensure_list,
    filter_extract,
    filter_iam_rules,
    filter_image_alias_to_id,
    filter_image_id,
    filter_image_name,
    filter_ip_rules,
    filter_lookup,
    filter_min_int,
    filter_output_name,
    filter_parse_port_spec,
    filter_policy_statements,
    filter_process_cfn_init,
    filter_regex_replace,
    filter_format_date,
    filter_rstrip,
    filter_shorten_unique,
    filter_snapshot_id,
    filter_snapshot_name,
    filter_split_cidr,
    filter_subnet_az_index,
    filter_subnet_network_zone,
    filter_tags,
    filter_to_json,
    filter_to_yaml,
    __file_url,
    __format_arn,
    __create_resource_arn,
    load_filters,
    raise_exception,
)
from core_framework.constants import *


@pytest.fixture
def render_context() -> Context:
    """
    Provides a mock Jinja2 render context populated with common test data.
    This simulates the context available during a template rendering process.
    """
    env = Environment()
    context_data = {
        CTX_CONTEXT: {
            DD_PORTFOLIO: "test-portfolio",
            DD_APP: "test-app",
            DD_BRANCH: "feature-branch",
            DD_BRANCH_SHORT_NAME: "feature",
            DD_BUILD: "build-123",
            DD_ENVIRONMENT: "dev",
            DD_SCOPE: SCOPE_BUILD,
            DD_ECR: {ECR_REGISTRY_URI: "123456789012.dkr.ecr.us-east-1.amazonaws.com"},
            "ImageAliases": {"ubuntu-20.04": "ami-12345"},
            "SecurityAliases": {
                "office-vpn": [
                    {
                        "Type": "cidr",
                        "Value": "192.168.1.0/24",
                        "Description": "Office VPN",
                    }
                ]
            },
            CTX_SNAPSHOT_ALIASES: {
                "rds": {
                    "prod-snapshot": {
                        "SnapshotIdentifier": "snap-abc",
                        "AccountAlias": "prod-account",
                    }
                }
            },
            CTX_ACCOUNT_ALIASES: {"prod-account": "987654321098"},
            "AwsRegion": "us-east-1",
            "AwsAccountId": "123456789012",
            CTX_FILES_BUCKET_URL: "eits-core-automation-ap-southeast-1",
            CTX_SHARED_FILES_PREFIX: "files/shared",
            CTX_PORTFOLIO_FILES_PREFIX: "files/portfolio",
            CTX_APP_FILES_PREFIX: "files/app",
            CTX_BRANCH_FILES_PREFIX: "files/branch",
            CTX_BUILD_FILES_PREFIX: "files/build",
            DD_TAGS: {"CustomTag": "CustomValue"},
        },
        CTX_COMPONENT_NAME: "test-component",
        CTX_APP: {
            "component-a": {"Type": "aws-lambda-function"},
            "component-b": {"Type": "aws-ec2-instance"},
        },
    }
    return env.context_class(env, parent=context_data, name="test", blocks={})


def test_filter_aws_tags(render_context):
    """
    Tests the filter_aws_tags function.
    Verifies that it correctly converts a dictionary of tags into the AWS-specific
    list format of {"Key": key, "Value": value}.
    """
    scope = SCOPE_BUILD
    component_name = "web-server"

    # This filter relies on filter_tags, so we assume filter_tags works correctly.
    # The main purpose is to test the format conversion.
    result = filter_aws_tags(render_context, scope, component_name)

    assert isinstance(result, list)
    assert {"Key": TAG_PORTFOLIO, "Value": "test-portfolio"} in result
    assert {"Key": TAG_APP, "Value": "test-app"} in result
    assert {"Key": TAG_COMPONENT, "Value": "web-server"} in result
    assert {"Key": "CustomTag", "Value": "CustomValue"} in result
    assert (
        len(result) == 8
    )  # portfolio, app, branch, build, env, name, component, custom


def test_filter_docker_image(render_context):
    """
    Tests the filter_docker_image function.
    Verifies it constructs the correct ECR image URI from context and input object.
    Also tests error conditions.
    """
    # Happy path
    obj = {"Fn::Pipeline::DockerImage": {"Name": "my-image:latest"}}
    expected_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/private/test-portfolio-test-app-feature-build-123-test-component:my-image:latest"
    assert filter_docker_image(render_context, obj) == expected_uri

    # Error case: Missing 'Fn::Pipeline::DockerImage'
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_docker_image(render_context, {})

    # Edge case: No context
    render_context.vars[CTX_CONTEXT] = None
    assert filter_docker_image(render_context, obj) is None


def test_filter_ebs_encrypt():
    """
    Tests the filter_ebs_encrypt function.
    Ensures that it correctly enforces encryption on EBS volume specifications.
    """
    ebs_spec = [
        {"DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": "10"}},
        {"DeviceName": "/dev/sdb1"},  # No Ebs key
    ]
    result = filter_ebs_encrypt(ebs_spec)  # Context is not used
    assert result[0]["Ebs"]["Encrypted"] == "true"
    assert "Ebs" not in result[1]


def test_filter_ensure_list():
    """
    Tests the filter_ensure_list utility.
    Verifies it correctly wraps non-list items in a list and leaves lists unchanged.
    """
    assert filter_ensure_list([1, 2]) == [1, 2]
    assert filter_ensure_list("a") == ["a"]
    assert filter_ensure_list(None) == []
    assert filter_ensure_list(jinja2.Undefined()) == []


def test_filter_extract():
    """
    Tests the filter_extract function, which uses JMESPath to query objects.
    """
    obj = {"a": {"b": {"c": "value"}}}
    # Happy path
    assert filter_extract(obj, "a.b.c") == "value"
    # Path not found with default
    assert filter_extract(obj, "a.x.y", default="default-val") == "default-val"
    # Path not found with no default (error)
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_extract(obj, "a.x.y")
    # Edge cases
    assert filter_extract(None, "a.b", default="d") == "d"
    assert filter_extract(jinja2.Undefined(), "a.b", default="d") == "d"


def test_filter_iam_rules(render_context):
    """
    Tests the filter_iam_rules function.
    Verifies it correctly generates IAM rule structures from security definitions.
    """
    resource = {
        "Pipeline::Security": [
            {"Source": "component-a", "Allow": ["s3:GetObject"]},
            {
                "Source": ["component-b"],
                "Allow": ["sqs:SendMessage", "sqs:ReceiveMessage"],
            },
        ]
    }
    result = filter_iam_rules(render_context, resource)
    assert len(result) == 2
    assert (
        result[0]["Value"]
        == "test-portfolio-test-app-feature-component-a-security:RoleName"
    )
    assert result[0]["Allow"] == ["s3:GetObject"]
    assert result[1]["SourceType"] == "aws-ec2-instance"
    assert result[1]["Allow"] == ["sqs:SendMessage", "sqs:ReceiveMessage"]

    # Error case: Invalid source
    resource_invalid = {"Pipeline::Security": [{"Source": "invalid-component"}]}
    with pytest.raises(jinja2.exceptions.FilterArgumentError):
        filter_iam_rules(render_context, resource_invalid)

    # delete the app context to test edge case
    render_context.vars[CTX_APP] = None
    result = filter_iam_rules(render_context, resource)
    assert len(result) == 0

    # delete the facts from the context to test edge case
    render_context.vars[CTX_CONTEXT] = None
    result = filter_iam_rules(render_context, resource)
    assert len(result) == 0


def test_filter_image_alias_to_id(render_context):
    """
    Tests filter_image_alias_to_id.
    Verifies it correctly resolves an image alias to its AMI ID from the context.
    """
    # Happy path
    assert filter_image_alias_to_id(render_context, "ubuntu-20.04") == "ami-12345"
    # Error case: Unknown alias
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_image_alias_to_id(render_context, "unknown-alias")
    # Edge case: No context
    render_context.vars[CTX_CONTEXT] = None
    assert filter_image_alias_to_id(render_context, "ubuntu-20.04") is None


def test_filter_image_id(render_context):
    """
    Tests filter_image_id.
    Verifies it extracts an image alias from an object and resolves it to an AMI ID.
    """
    obj = {"Fn::Pipeline::ImageId": {"Name": "ubuntu-20.04"}}
    assert filter_image_id(render_context, obj) == "ami-12345"
    # Error case: Missing lookup key
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_image_id(render_context, {})
    # Error case: Unknown alias
    obj_unknown = {"Fn::Pipeline::ImageId": {"Name": "unknown-alias"}}
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_image_id(render_context, obj_unknown)

    # delete the facts from the context to test edge case
    render_context.vars[CTX_CONTEXT] = None
    assert filter_image_id(render_context, obj) is None


def test_filter_image_name(render_context):
    """
    Tests filter_image_name.
    Verifies it correctly extracts the image alias name from an object.
    """
    obj = {"Fn::Pipeline::ImageId": {"Name": "ubuntu-20.04"}}
    assert filter_image_name(obj) == "ubuntu-20.04"
    # Error case: Missing lookup key
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_image_name({})


def test_filter_ip_rules(render_context):
    """
    Tests the filter_ip_rules function.
    Verifies it correctly processes security rules from aliases and components.
    """
    resource = {
        "Pipeline::Security": [
            {"Source": "office-vpn", "Allow": "TCP:443"},
            {"Source": "component-a", "Allow": "TCP:8080-8090"},
            {"Source": {}, "Allow": "Skipped rule because source is not a string"},
            {"Source": "office-vpn", "Allow": 1234},
        ]
    }
    result = filter_ip_rules(render_context, resource)

    # The second VPN is not in the list because the allow is not a string
    assert len(result) == 2

    # From alias
    assert result[0]["Type"] == "cidr"
    assert result[0]["Value"] == "192.168.1.0/24"
    assert result[0]["Protocol"] == "TCP"
    assert result[0]["ToPort"] == "443"
    assert result[0]["Description"] == "Office VPN"

    # From component
    assert result[1]["Type"] == "component"
    assert (
        result[1]["Value"]
        == "test-portfolio-test-app-feature-component-a-security:SecurityGroupId"
    )
    assert result[1]["FromPort"] == "8080"
    assert result[1]["ToPort"] == "8090"
    assert result[1]["Description"] == "Component component-a"

    # Error case: Invalid source
    resource_invalid = {"Pipeline::Security": [{"Source": "invalid-source"}]}
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_ip_rules(render_context, resource_invalid)

    # Set the paramter source_only to true
    result = filter_ip_rules(render_context, resource, source_only=True)

    # This time the second VPN is included because source_only=True
    assert len(result) == 3

    # From alias
    assert result[0]["Type"] == "cidr"
    assert result[0]["Value"] == "192.168.1.0/24"
    assert result[0]["Description"] == "Office VPN"

    # From component
    assert result[1]["Type"] == "component"
    assert (
        result[1]["Value"]
        == "test-portfolio-test-app-feature-component-a-security:SecurityGroupId"
    )
    assert result[1]["Description"] == "Component component-a"

    # delete the app context to test edge case
    render_context.vars[CTX_APP] = None
    result = filter_ip_rules(render_context, resource)
    assert len(result) == 0

    # delete the facts from the context to test edge case
    render_context.vars[CTX_CONTEXT] = None
    result = filter_ip_rules(render_context, resource)
    assert len(result) == 0


def test_filter_lookup(render_context):
    """
    Tests the filter_lookup function.
    Verifies it can retrieve values from the render context.
    """
    assert filter_lookup(render_context, CTX_COMPONENT_NAME) == "test-component"

    # wrap the text in double-quotes so the dash wont be interpreted as a minus sign
    assert (
        filter_lookup(render_context, '"non-existent-key"', default="default")
        == "default"
    )
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_lookup(render_context, '"non-existent-key"')


def test_filter_min_int():
    """
    Tests the filter_min_int function.
    """
    assert filter_min_int(10, 20, 5) == 5
    assert filter_min_int(-1, 0, 1) == -1
    assert filter_min_int(100) == 100
    assert filter_min_int() is None


def test_filter_output_name(render_context):
    """
    Tests the filter_output_name function.
    Verifies it constructs the correct CloudFormation Output export name.
    """
    obj = {
        "Fn::Pipeline::GetOutput": {
            "Scope": SCOPE_BUILD,
            "Component": "my-db",
            "OutputName": "DBEndpoint",
        }
    }
    expected = "test-portfolio-test-app-feature-build-123-my-db-pointers:DBEndpoint"
    result = filter_output_name(render_context, obj)
    assert result == expected, f"Expected {expected}, got {result}"

    # Error case: Not implemented scope
    obj_invalid_scope = {
        "Fn::Pipeline::GetOutput": {
            "Scope": SCOPE_APP,  # Not implemented yet
            "Component": "my-db",
            "OutputName": "DBEndpoint",
        }
    }
    with pytest.raises(NotImplementedError):
        filter_output_name(render_context, obj_invalid_scope)

    # Test when no GetOutput key is present
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_output_name(render_context, {})

    # delete the facts from the context to test edge case
    render_context.vars[CTX_CONTEXT] = None
    result = filter_output_name(render_context, obj)
    assert result is None


def test_filter_parse_port_spec():
    """
    Tests the filter_parse_port_spec function.
    Verifies it correctly parses various port specifications.
    """
    assert filter_parse_port_spec("TCP:80") == {
        "Protocol": "TCP",
        "FromPort": "80",
        "ToPort": "80",
    }
    assert filter_parse_port_spec("UDP:1024-2048") == {
        "Protocol": "UDP",
        "FromPort": "1024",
        "ToPort": "2048",
    }
    assert filter_parse_port_spec("ICMP:*") == {
        "Protocol": "ICMP",
        "FromPort": "-1",
        "ToPort": "-1",
    }
    assert filter_parse_port_spec("ALL:*") == {
        "Protocol": "-1",
        "FromPort": "0",
        "ToPort": "65535",
    }
    assert filter_parse_port_spec("TCP:") == {
        "Protocol": "TCP",
        "FromPort": "0",
        "ToPort": "65535",
    }

    with pytest.raises(jinja2.exceptions.FilterArgumentError):
        filter_parse_port_spec("invalid-spec")


def test_filter_policy_statements(render_context):
    """
    Tests the filter_policy_statements function.
    Verifies it creates valid AWS IAM policy statements with correct ARNs.
    """
    statement = {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject", "sqs:SendMessage"],
    }
    result = filter_policy_statements(render_context, statement)
    assert result["Effect"] == "Allow"
    assert len(result["Resource"]) == 2  # s3 and sqs are grouped
    assert "arn:aws:s3:::test-portfolio-test-app-feature-*" in result["Resource"]
    assert (
        "arn:aws:sqs:us-east-1:123456789012:test-portfolio-test-app-feature-*"
        in result["Resource"]
    )

    # Remove the facts from the context to test edge case
    render_context.vars[CTX_CONTEXT] = None

    result = filter_policy_statements(render_context, statement)
    assert len(result) == 0  # No resources should be returned if context is empty


def test_filter_process_cfn_init(render_context):
    """
    Tests the filter_process_cfn_init function.
    Verifies it correctly prepends S3 URLs to sources and files in a cfn-init block.
    """
    cfn_init = {
        "install_packages": {
            "sources": {
                "/etc/yum.repos.d": {"Fn::Pipeline::FileUrl": {"Path": "my.repo"}}
            },
            "files": {
                "/etc/portfolio-config.conf": {
                    "source": {
                        "Fn::Pipeline::FileUrl": {
                            "Path": "portfolio-config.conf",
                            "Scope": SCOPE_PORTFOLIO,
                        }
                    },
                    "mode": "000644",
                },
                "/etc/my-config.conf": {
                    "source": {
                        "Fn::Pipeline::FileUrl": {
                            "Path": "config.conf",
                            "Scope": SCOPE_APP,
                        }
                    },
                    "mode": "000644",
                },
                "/etc/another-config.conf": {
                    "source": {
                        "Fn::Pipeline::FileUrl": {
                            "Path": "another-config.conf",
                            "Scope": SCOPE_BRANCH,
                        }
                    },
                    "mode": "000644",
                },
                "/etc/some-other-config.conf": {
                    "source": {
                        "Fn::Pipeline::FileUrl": {
                            "Path": "some-other-config.conf",
                            "Scope": SCOPE_BUILD,
                        }
                    },
                    "mode": "000644",
                },
                "/tmp/content.txt": {"content": "some content"},  # should be ignored
            },
        },
        "configSets": {"default": ["install_packages"]},
    }
    result = filter_process_cfn_init(render_context, cfn_init)

    assert (
        result["install_packages"]["sources"]["/etc/yum.repos.d"]
        == "eits-core-automation-ap-southeast-1/files/build/my.repo"
    )
    assert (
        result["install_packages"]["files"]["/etc/portfolio-config.conf"]["source"]
        == "eits-core-automation-ap-southeast-1/files/portfolio/portfolio-config.conf"
    )
    assert (
        result["install_packages"]["files"]["/etc/my-config.conf"]["source"]
        == "eits-core-automation-ap-southeast-1/files/app/config.conf"
    )
    assert (
        result["install_packages"]["files"]["/etc/another-config.conf"]["source"]
        == "eits-core-automation-ap-southeast-1/files/branch/another-config.conf"
    )
    assert (
        result["install_packages"]["files"]["/etc/some-other-config.conf"]["source"]
        == "eits-core-automation-ap-southeast-1/files/build/some-other-config.conf"
    )
    # The content file should not have a source
    assert "source" not in result["install_packages"]["files"]["/tmp/content.txt"]

    # Delete the context to test edge case
    render_context.vars[CTX_CONTEXT] = None
    result = filter_process_cfn_init(render_context, cfn_init)
    assert result is None  # Should return None if context is empty


def test_filter_regex_replace():
    """
    Tests the filter_regex_replace function.
    """
    assert filter_regex_replace("hello 123 world", r"\d+", "NUM") == "hello NUM world"


def test_filter_format_date():
    """
    Tests the filter_format_date function.
    """
    # Test default format.  If you specify "now", it should return today's date in the default format.
    assert filter_format_date("now") == date.today().strftime("%d-%b-%y")
    # Test custom format.  If you specify "now", it should return today's date in the specified format.
    assert filter_format_date("now", "%Y/%m/%d") == date.today().strftime("%Y/%m/%d")


def test_filter_rstrip():
    """
    Tests the filter_rstrip function.
    """
    assert filter_rstrip("test-string---", "-") == "test-string"
    assert filter_rstrip("  hello  ", " ") == "  hello"


def test_filter_shorten_unique():
    """
    Tests the filter_shorten_unique function.
    Ensures strings are shortened correctly and predictably.
    """
    long_string = "this-is-a-very-long-string-that-needs-to-be-shortened"
    # Shorten with unique suffix
    shortened = filter_shorten_unique(long_string, 20, 4)
    assert len(shortened) == 20
    assert shortened.startswith("this-is-a-very-l")
    # Test idempotency (same input -> same output)
    assert filter_shorten_unique(long_string, 20, 4) == shortened
    # Test with no shortening needed
    assert filter_shorten_unique("short", 10, 2) == "short"


def test_filter_snapshot_id(render_context):
    """
    Tests the filter_snapshot_id function.
    Verifies it resolves a snapshot alias to a parameter dictionary for CloudFormation.
    """
    spec = {"Fn::Pipeline::SnapshotId": {"Name": "prod-snapshot"}}
    result = filter_snapshot_id(render_context, spec, "rds")
    expected = {"SnapshotIdentifier": "snap-abc", "OwnerAccount": "987654321098"}
    assert result == expected
    # Error cases
    with pytest.raises(
        jinja2.exceptions.UndefinedError,
        match='Must specify {"Fn::Pipeline::SnapshotId": {}} dictionary for lookup',
    ):
        filter_snapshot_id(
            render_context, {"Fn::Pipeline::SnapshotId": "invalid"}, "rds"
        )

    # Set the facts facts account aliases to None to test edge case
    render_context[CTX_CONTEXT][CTX_ACCOUNT_ALIASES] = None
    expected = {"SnapshotIdentifier": "snap-abc"}
    result = filter_snapshot_id(render_context, spec, "rds")
    assert result == expected

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES]["rds"]["prod-snapshot"][
        "SnapshotIdentifier"
    ] = None
    result = filter_snapshot_id(render_context, spec, "rds")
    assert result is None

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES]["rds"]["prod-snapshot"] = None
    result = filter_snapshot_id(render_context, spec, "rds")
    assert result is None  # Should return None if snapshot alias is missing

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES]["rds"] = None
    result = filter_snapshot_id(render_context, spec, "rds")
    assert result is None  # Should return None if snapshot alias is missing

    # Test with invalid snapshot aliases

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES] = "invalid-aliases"
    with pytest.raises(
        jinja2.exceptions.UndefinedError,
        match="Invalid snapshot aliases defined in context",
    ):
        filter_snapshot_id(render_context, spec, "unknown-type")

    # Remove the facts from the context to test edge case
    render_context.vars[CTX_CONTEXT] = None
    result = filter_snapshot_id(render_context, spec, "rds")
    assert result is None  # Should return None if context is empty


def test_filter_snapshot_name(render_context):
    """
    Tests the filter_snapshot_name function.
    Verifies it resolves a snapshot alias to just the snapshot identifier string.
    """
    spec = {"Fn::Pipeline::SnapshotId": {"Name": "prod-snapshot"}}
    assert filter_snapshot_name(render_context, spec, "rds") == "snap-abc"

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES]["rds"]["prod-snapshot"] = None
    result = filter_snapshot_name(render_context, spec, "rds")
    assert result is None

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES]["rds"] = None
    result = filter_snapshot_name(render_context, spec, "rds")
    assert result is None

    render_context[CTX_CONTEXT][CTX_SNAPSHOT_ALIASES] = None
    result = filter_snapshot_name(render_context, spec, "rds")
    assert result is None  # Should return None if snapshot aliases are missing

    # Error cases are similar to filter_snapshot_id and are assumed to be covered.
    spec = {"Fn::Pipeline::SnapshotId": None}
    with pytest.raises(
        jinja2.exceptions.FilterArgumentError,
        match="Must specify Fn::Pipeline::SnapshotId lookup",
    ):
        filter_snapshot_name(render_context, spec, "rds")

    # Set the facts facts account aliases to None to test edge case
    render_context.vars[CTX_CONTEXT] = None
    result = filter_snapshot_name(render_context, spec, "rds")
    assert result is None  # Should return None if context is empty


def test_filter_split_cidr():
    """
    Tests the filter_split_cidr function.
    Verifies it correctly splits a larger CIDR block into smaller subnets.
    """
    # No split needed
    assert filter_split_cidr("10.0.0.0/16", [16, 24]) == ["10.0.0.0/16"]
    # Split needed
    assert filter_split_cidr("10.0.0.0/24", [26]) == [
        "10.0.0.0/26",
        "10.0.0.64/26",
        "10.0.0.128/26",
        "10.0.0.192/26",
    ]
    # Error cases
    with pytest.raises(jinja2.exceptions.FilterArgumentError, match="Invalid CIDR"):
        filter_split_cidr("invalid-cidr", [24])

    with pytest.raises(
        jinja2.exceptions.FilterArgumentError,
        match="Failed to split CIDR '10.0.0.0/24', prefix 24 is larger than any allowed prefix length \\[22, 20\\]",
    ):
        filter_split_cidr("10.0.0.0/24", [22, 20])


def test_filter_subnet_network_zone():
    """
    Tests the filter_subnet_network_zone function.
    """
    obj = {"Fn::Pipeline::SubnetId": {"NetworkZone": "public"}}
    assert filter_subnet_network_zone(obj) == "public"
    # Default cases
    assert filter_subnet_network_zone({"Fn::Pipeline::SubnetId": {}}) == "private"
    assert filter_subnet_network_zone(None) == "private"
    # Error case
    assert (
        filter_subnet_network_zone({}) == "private"
    )  # Should return default if no NetworkZone


def test_filter_subnet_az_index():
    """
    Tests the filter_subnet_az_index function.
    """
    obj = {"Fn::Pipeline::SubnetId": {"AzIndex": 2}}
    assert filter_subnet_az_index(obj) == 2
    # Default cases
    assert filter_subnet_az_index({"Fn::Pipeline::SubnetId": {}}) == 0
    assert filter_subnet_az_index(None) == 0
    # Error case
    assert filter_subnet_az_index({}) == 0  # Should return default if no AzIndex


def test_filter_tags(render_context):
    """
    Tests the filter_tags function for various scopes.
    Verifies that the correct set of tags is generated based on the scope.
    """
    # SCOPE_BUILD (default)
    tags = filter_tags(render_context, SCOPE_BUILD, "comp-build")
    assert tags[TAG_NAME] == "test-portfolio-test-app-feature-build-123-comp-build"
    assert tags[TAG_COMPONENT] == "comp-build"
    assert tags[TAG_APP] == "test-app"
    assert tags[TAG_BRANCH] == "feature-branch"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert TAG_ENVIRONMENT in tags
    assert TAG_BUILD in tags

    # SCOPE_BRANCH
    tags = filter_tags(render_context, SCOPE_BRANCH, "comp-branch")
    assert tags[TAG_NAME] == "test-portfolio-test-app-feature-branch-comp-branch"
    assert tags[TAG_COMPONENT] == "comp-branch"
    assert tags[TAG_APP] == "test-app"
    assert tags[TAG_BRANCH] == "feature-branch"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert TAG_ENVIRONMENT in tags
    assert TAG_BUILD not in tags

    # SCOPE_APP
    tags = filter_tags(render_context, SCOPE_APP, "comp-app")
    assert tags[TAG_NAME] == "test-portfolio-test-app-comp-app"
    assert tags[TAG_COMPONENT] == "comp-app"
    assert tags[TAG_APP] == "test-app"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert TAG_BUILD not in tags
    assert TAG_BRANCH not in tags
    assert TAG_ENVIRONMENT in tags
    assert TAG_APP in tags

    # SCOPE_PORTFOLIO
    tags = filter_tags(render_context, SCOPE_PORTFOLIO, "comp-portfolio")
    assert tags[TAG_NAME] == "test-portfolio-comp-portfolio"
    assert tags[TAG_COMPONENT] == "comp-portfolio"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert TAG_APP not in tags
    assert TAG_BRANCH not in tags
    assert TAG_BUILD not in tags
    assert TAG_ENVIRONMENT in tags
    assert TAG_PORTFOLIO in tags

    # SCOPE_ENVIRONMENT
    tags = filter_tags(render_context, SCOPE_ENVIRONMENT, "comp-env")
    assert tags[TAG_NAME] == "test-portfolio-test-app-dev-comp-env"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert TAG_COMPONENT not in tags
    assert TAG_APP not in tags
    assert TAG_BRANCH not in tags
    assert TAG_BUILD not in tags
    assert TAG_ENVIRONMENT in tags

    # component in the context is 'test-component'
    tags = filter_tags(render_context, SCOPE_BUILD)
    assert tags[TAG_NAME] == "test-portfolio-test-app-feature-build-123-test-component"
    assert tags[TAG_COMPONENT] == "test-component"
    assert tags[TAG_APP] == "test-app"
    assert tags[TAG_BRANCH] == "feature-branch"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert tags[TAG_BUILD] == "build-123"
    assert TAG_ENVIRONMENT in tags

    # scope from the context is 'build' and the compenent is 'test-component'
    tags = filter_tags(render_context)
    assert tags[TAG_NAME] == "test-portfolio-test-app-feature-build-123-test-component"
    assert tags[TAG_COMPONENT] == "test-component"
    assert tags[TAG_APP] == "test-app"
    assert tags[TAG_BRANCH] == "feature-branch"
    assert tags[TAG_PORTFOLIO] == "test-portfolio"
    assert tags[TAG_BUILD] == "build-123"
    assert TAG_ENVIRONMENT in tags

    # Set the factgs from the context to None to test edge case
    render_context.vars[CTX_CONTEXT] = None
    tags = filter_tags(render_context, SCOPE_BUILD, "comp-build")
    assert len(tags) == 0  # Should return empty dict if context is None


def test_filter_to_json():
    """
    Tests the filter_to_json function.
    """
    data = {"key": "value", "num": 1}
    # This filter relies on core_framework.to_json, so we just test the wrapper
    assert filter_to_json(data) == util.to_json(data)
    assert isinstance(filter_to_json(jinja2.Undefined()), jinja2.Undefined)


def test_filter_to_yaml():
    """
    Tests the filter_to_yaml function.
    """

    # Test 1
    data = {"key": "value", "items": [1, 2]}
    expected_yaml = "key: value\nitems:\n  - 1\n  - 2"
    result = filter_to_yaml(data)
    assert result == expected_yaml

    # Test 2
    data = {
        "key": "value",
        "items": [
            {"name": "name1", "size": "large"},
            {"name": "name2", "size": "small"},
        ],
        "empty": None,
    }
    expected_yaml = "key: value\nitems:\n  - name: name1\n    size: large\n  - name: name2\n    size: small\nempty:"
    result = filter_to_yaml(data)
    assert result == expected_yaml

    # Test 3
    result = filter_to_yaml(None)
    assert result == ""  # Should return empty string for None input

    # Test 4
    assert isinstance(filter_to_yaml(jinja2.Undefined()), jinja2.Undefined)


def test_private_file_url(render_context):
    """
    Tests the internal __file_url helper function.
    """
    facts = render_context.get(CTX_CONTEXT)
    spec = {"Fn::Pipeline::FileUrl": {"Path": "script.sh", "Scope": SCOPE_SHARED}}
    assert (
        __file_url(facts, spec)
        == "eits-core-automation-ap-southeast-1/files/shared/script.sh"
    )

    # Test non-FileUrl spec (should return unchanged)
    assert __file_url(facts, {"key": "value"}) == {"key": "value"}

    # Test invalid scope
    invalid_spec = {
        "Fn::Pipeline::FileUrl": {"Path": "script.sh", "Scope": "invalid-scope"}
    }
    with pytest.raises(jinja2.exceptions.UndefinedError):
        __file_url(facts, invalid_spec)


def test_private_format_arn():
    """
    Tests the internal __format_arn helper function.
    """
    arn = __format_arn("s3", "", "", "my-bucket")
    assert arn == "arn:aws:s3:::my-bucket"
    arn_with_type = __format_arn(
        "dynamodb", "us-west-2", "111122223333", "my-table", "table"
    )
    assert arn_with_type == "arn:aws:dynamodb:us-west-2:111122223333:table/my-table"


def test_private_create_resource_arn():
    """
    Tests the internal __create_resource_arn helper function.
    """
    # Standard ARN from map
    arn = __create_resource_arn("sqs", "us-east-1", "12345", "p-a-b")
    assert arn == "arn:aws:sqs:us-east-1:12345:p-a-b-*"
    # S3 ARN from map
    arn_s3 = __create_resource_arn("s3", "us-east-1", "12345", "p-a-b")
    assert arn_s3 == "arn:aws:s3:::p-a-b-*"
    # Fallback to generic format
    arn_fallback = __create_resource_arn("ec2", "us-east-1", "12345", "p-a-b")
    assert arn_fallback == "arn:aws:ec2:us-east-1:12345:p-a-b"


def test_load_filters():
    """
    Tests the load_filters function.
    Verifies that all expected filters and globals are registered with the Jinja2 Environment.
    """
    env = Environment()
    load_filters(env)
    # Check a few filters
    assert "aws_tags" in env.filters
    assert "to_yaml" in env.filters
    assert "split_cidr" in env.filters
    # Check the global
    assert "raise" in env.globals


def test_raise_exception():
    """
    Tests the raise_exception global function.
    """
    with pytest.raises(Exception, match="This is a test exception"):
        raise_exception("This is a test exception")
