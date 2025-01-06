from datetime import date
from unittest.mock import patch
import pytest
import jinja2
from core_renderer.filters import (
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
    load_filters,
)
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
    CTX_TAGS,
    DD_APP,
    DD_BRANCH,
    DD_BRANCH_SHORT_NAME,
    DD_BUILD,
    DD_ECR,
    DD_ENVIRONMENT,
    DD_PORTFOLIO,
    DD_TAGS,
    ECR_REGISTRY_URI,
    SCOPE_BUILD,
    ST_CIDR,
    ST_COMPONENT,
    ST_IP_ADDRESS,
    ST_PREFIX,
    ST_SECURITY_GROUP,
)


@pytest.fixture
def render_context():

    # render_context has the fields for the context of the jninj2 template filters

    return {
        CTX_CONTEXT: {  # DeploymentDetails
            DD_PORTFOLIO: "example-portfolio",
            DD_APP: "example-app",
            DD_BRANCH: "main",
            DD_BRANCH_SHORT_NAME: "main",
            DD_BUILD: "123",
            DD_ENVIRONMENT: "prod",
            DD_ECR: {ECR_REGISTRY_URI: "123456789012.dkr.ecr.us-west-2.amazonaws.com"},
            DD_TAGS: {"Key1": "Value1", "Key2": "Value2"},
            "AwsRegion": "us-west-2",
            "AwsAccountId": "123456789012",
            "SecurityAliases": {
                "some-other-app": [
                    "192.168.200.0/24",  # for convenience, we allow simple CIDR ranges in the value of an alias
                    {
                        "Type": ST_CIDR,
                        "Value": "192.168.1.0/24",
                        "Description:": "My App CIDR Range",
                    },
                    {
                        "Type": ST_COMPONENT,
                        "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
                        "Description": "Some component name or ARN",
                    },
                    {
                        "Type": ST_PREFIX,
                        "Value": "some-prefix",
                        "Description": "Some prefix",
                    },
                    {
                        "Type": ST_SECURITY_GROUP,
                        "Value": "sg-security-group",
                        "Description": "Security Group Attachment",
                    },
                    {
                        "Type": ST_IP_ADDRESS,
                        "Value": "192.168.1.111",
                        "Description": "IP Address",
                    },
                ]
            },
            CTX_FILES_BUCKET_URL: "s3://example-bucket/files",
            CTX_SHARED_FILES_PREFIX: "shared_files",
            CTX_PORTFOLIO_FILES_PREFIX: "portfolio_files",
            CTX_APP_FILES_PREFIX: "app_files",
            CTX_BRANCH_FILES_PREFIX: "branch_files",
            CTX_BUILD_FILES_PREFIX: "build_files",
            CTX_SNAPSHOT_ALIASES: {
                "ebs": {
                    "alias-name": {
                        "SnapshotIdentifier": "snap-12345678",
                        "AccountAlias": "other-account-name",
                    }
                }
            },
            CTX_ACCOUNT_ALIASES: {"other-account-name": "123456789012"},
        },
        CTX_COMPONENT_NAME: "context-example-component",
        CTX_APP: {
            "myapp": {"Type": "security-type"},
            "some-other-app": {"Type": "security-type"},
        },
        CTX_TAGS: {
            "Portfolio": "example-portfolio",
            "App": "example-app",
            "Branch": "main",
            "Build": "123",
        },
    }


def test_filter_aws_tags(render_context):
    scope = SCOPE_BUILD

    component_name = "example-component"

    expected_tags = [
        {"Key": "Portfolio", "Value": "example-portfolio"},
        {"Key": "App", "Value": "example-app"},
        {"Key": "Key1", "Value": "Value1"},
        {"Key": "Key2", "Value": "Value2"},
        {"Key": "Branch", "Value": "main"},
        {"Key": "Build", "Value": "123"},
        {"Key": "Environment", "Value": "prod"},
        {"Key": "Component", "Value": "example-component"},
        {
            "Key": "Name",
            "Value": "example-portfolio-example-app-main-123-example-component",
        },
    ]

    tags = filter_aws_tags(render_context, scope, component_name)

    assert tags == expected_tags


def test_filter_docker_image(render_context):
    object = {"Fn::Pipeline::DockerImage": {"Name": "example-image"}}
    expected_image = "123456789012.dkr.ecr.us-west-2.amazonaws.com/private/example-portfolio-example-app-main-123-context-example-component:example-image"

    image = filter_docker_image(render_context, object)

    assert image == expected_image


def test_filter_docker_image_undefined_error(render_context):
    object = {}
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_docker_image(render_context, object)


def test_filter_ensure_list():
    assert filter_ensure_list([1, 2, 3]) == [1, 2, 3]
    assert filter_ensure_list(None) == []
    assert filter_ensure_list(jinja2.Undefined()) == []
    assert filter_ensure_list(1) == [1]


def test_filter_extract():
    object = {"a": {"b": {"c": "value"}}}
    path = "a.b.c"
    default = "default_value"
    assert filter_extract(object, path, default) == "value"
    assert filter_extract(object, "a.b.d", default) == "default_value"


def test_filter_min_int():
    assert filter_min_int(3, 1) == 1
    assert filter_min_int(1, 2, 3) == 1


def test_filter_iam_rules(render_context):

    # Allow some other app (or alias such as "internet" or "intranet") access to my app
    resource = {
        "Pipeline::Security": [{"Source": "some-other-app", "Allow": "*"}],
    }

    rules = [
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-some-other-app-security:RoleName",
            "Description": "Component some-other-app",
            "Allow": ["*"],
            "SourceType": "security-type",
            "SecurityGroupId": "example-portfolio-example-app-main-some-other-app-security:SecurityGroupId",
        }
    ]

    derrived_rules = filter_iam_rules(render_context, resource)

    assert derrived_rules == rules


def test_filter_policy_statements(render_context):

    action_statement = {"Action": ["dynamodb:*", "s3:*"], "Effect": "Allow"}

    statements = filter_policy_statements(render_context, action_statement)

    check = {
        "Action": ["dynamodb:*", "s3:*"],
        "Effect": "Allow",
        "Resource": [
            "arn:aws:dynamodb:us-west-2:123456789012:table/example-portfolio-example-app-main-*",
            "arn:aws:s3:::example-portfolio-example-app-main-*",
        ],
    }

    assert statements == check


def test_filter_ebs_encrypt(render_context):
    o = [{"Ebs": {"Encrypted": "false"}}]
    result = filter_ebs_encrypt(render_context, o)

    assert result[0]["Ebs"]["Encrypted"] == "true"


def test_filter_image_alias_to_id(render_context):

    render_context[CTX_CONTEXT]["ImageAliases"] = {"alias1": "ami-12345678"}

    result = filter_image_alias_to_id(render_context, "alias1")
    assert result == "ami-12345678"

    try:
        filter_image_alias_to_id(render_context, "alias2")
        pytest.fail("Expected jinja2.exceptions.UndefinedError")
    except jinja2.exceptions.UndefinedError:
        pass


def test_filter_image_id(render_context):

    render_context[CTX_CONTEXT]["ImageAliases"] = {"alias1": "ami-12345678"}

    result = filter_image_id(
        render_context, {"Fn::Pipeline::ImageId": {"Name": "alias1"}}
    )
    assert result == "ami-12345678"


def test_filter_image_name(render_context):
    result = filter_image_name(
        render_context, {"Fn::Pipeline::ImageId": {"Name": "alias1"}}
    )
    assert result == "alias1"


def test_filter_ip_rules(render_context):

    # This resource will allow 'some-other-app' to connect to it on the specified ports
    resource = {
        "Pipeline::Security": [
            {
                "Source": "some-other-app",
                "Allow": ["TCP:443", "TCP:80", "UDP:6320-6330", "ICMP:8"],
            }
        ]
    }

    # Default resource type = cidr, component, prefix
    # there are 4 rules of these three types in the context 4 'some-other-app'
    # this source, 'myapp', has 4 Allow ports in the pipeline security.
    # The result should be 4 rules of each instace of the allowed types, 16 rules in total.
    result = filter_ip_rules(render_context, resource)

    rules = [
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
    ]

    assert result == rules

    source_types = [ST_CIDR, ST_COMPONENT, ST_PREFIX, ST_IP_ADDRESS, ST_SECURITY_GROUP]

    # resource type = cidr, component, prefix, ip, security-group (turn on the 5)
    # there are 6 rules of these three types in the context 4 'some-other-app'
    # this source, 'myapp', has 4 Allow ports in the pipeline security.
    # The result should be 4 rules of each instace of the allowed types, 21 rules in total. (secruity group only has 1 rule, not 4)
    # By specifying 'security group' we will take the security group name from the alias and make it 'allow'
    result = filter_ip_rules(render_context, resource, source_types=source_types)

    rules = [
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "cidr",
            "Value": "192.168.1.0/24",
            "Description:": "My App CIDR Range",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "component",
            "Value": "example-portfolio-example-app-main-myapp-security:RoleName",
            "Description": "Some component name or ARN",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "prefix",
            "Value": "some-prefix",
            "Description": "Some prefix",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
        {
            "Type": "sg-attachment",
            "Value": "sg-security-group",
            "Description": "Security Group Attachment",
        },
        {
            "Type": "ip",
            "Value": "192.168.1.111",
            "Description": "IP Address",
            "Protocol": "TCP",
            "FromPort": "443",
            "ToPort": "443",
        },
        {
            "Type": "ip",
            "Value": "192.168.1.111",
            "Description": "IP Address",
            "Protocol": "TCP",
            "FromPort": "80",
            "ToPort": "80",
        },
        {
            "Type": "ip",
            "Value": "192.168.1.111",
            "Description": "IP Address",
            "Protocol": "UDP",
            "FromPort": "6320",
            "ToPort": "6330",
        },
        {
            "Type": "ip",
            "Value": "192.168.1.111",
            "Description": "IP Address",
            "Protocol": "ICMP",
            "FromPort": "8",
            "ToPort": "-1",
        },
    ]

    assert result == rules


def test_filter_lookup(render_context):

    # check if CTX_CONTEXT has been provided

    result = filter_lookup(render_context, CTX_CONTEXT)

    assert result == render_context[CTX_CONTEXT]

    result = filter_lookup(render_context, "non-existent-key", "bogus")

    assert result == "bogus"

    try:
        filter_lookup(render_context, "non-existent-key")
        pytest.fail("Expected jinja2.exceptions.UndefinedError")
    except jinja2.exceptions.UndefinedError:
        pass


def test_filter_output_name(render_context):

    output = {
        "Fn::Pipeline::GetOutput": {
            "Component": "mycomponent",
            "OutputName": "myoutput",
        }
    }

    result = filter_output_name(render_context, output)

    assert (
        result == "example-portfolio-example-app-main-123-mycomponent-pointers:myoutput"
    )

    try:
        filter_output_name(render_context, {})
        pytest.fail("Expected jinja2.exceptions.UndefinedError")
    except jinja2.exceptions.UndefinedError:
        pass
    else:
        pytest.fail("Expected jinja2.exceptions.UndefinedError")


def test_filter_parse_port_spec(render_context):

    result = filter_parse_port_spec("TCP:80-80")

    check = {"Protocol": "TCP", "FromPort": "80", "ToPort": "80"}

    assert result == check

    try:
        filter_parse_port_spec("ANYTHING:80")
        pytest.fail("Expected ValueError")
    except jinja2.exceptions.UndefinedError:
        pass
    else:
        pytest.fail("Expected jinja2.exceptions.UndefinedError")


def test_filter_process_cfn_init(render_context):

    cfn_init = {
        "Fn::Pipeline::CfnInit": {
            "configSets": [],  # list of configSets.  Skipped
            "sources": {
                "source1": {
                    "Fn::Pipeline::FileUrl": {"Path": "filename1", "Scope": "build"}
                },
                "source2": {
                    "Fn::Pipeline::FileUrl": {"Path": "filename2", "Scope": "build"}
                },
            },
            "files": {
                "file1": {
                    "source": {
                        "Fn::Pipeline::FileUrl": {
                            "Path": "filename_file1",
                            "Scope": "build",
                        }
                    }
                },
                "file2": {
                    "source": {
                        "Fn::Pipeline::FileUrl": {
                            "Path": "filename_file2",
                            "Scope": "build",
                        }
                    }
                },
            },
        }
    }

    result = filter_process_cfn_init(render_context, cfn_init)

    assert (
        result["Fn::Pipeline::CfnInit"]["sources"]["source1"]
        == "s3://example-bucket/files/build_files/filename1"
    )
    assert (
        result["Fn::Pipeline::CfnInit"]["sources"]["source2"]
        == "s3://example-bucket/files/build_files/filename2"
    )

    assert (
        result["Fn::Pipeline::CfnInit"]["files"]["file1"]["source"]
        == "s3://example-bucket/files/build_files/filename_file1"
    )
    assert (
        result["Fn::Pipeline::CfnInit"]["files"]["file2"]["source"]
        == "s3://example-bucket/files/build_files/filename_file2"
    )


def test_filter_rstrip():
    assert filter_rstrip("string   ", " ") == "string"


def test_filter_shorten_unique():

    # Specify the string must be 5 characters long

    assert filter_shorten_unique("string", 5) == "strin"

    # Specify the string must be 10 characters long and only keep the first 4 digits
    # Specify 6 charcters must be unique.  Make sure to supply the placeholders

    result = filter_shorten_unique("res-xxxxxx", 10, 6)

    assert result.startswith("res-")
    assert len(result) == 10


def test_filter_snapshot_id(render_context):

    snapshot_spec = {
        "Fn::Pipeline::SnapshotId": {
            "Name": "alias-name",
        }
    }

    result = filter_snapshot_id(render_context, snapshot_spec, "ebs")

    assert result == {
        "SnapshotIdentifier": "snap-12345678",
        "OwnerAccount": "123456789012",
    }

    # Try looking up undefined snapshot alias component type
    try:
        filter_snapshot_id(render_context, {}, "other")
        pytest.fail("Expected jinja2.exceptions.UndefinedError")
    except jinja2.exceptions.UndefinedError:
        pass


def test_filter_snapshot_name(render_context):

    snapshot_spec = {
        "Fn::Pipeline::SnapshotId": {
            "Name": "alias-name",
        }
    }

    result = filter_snapshot_name(render_context, snapshot_spec, "ebs")

    assert result == "snap-12345678"


def test_filter_split_cidr():

    cidr = "10.0.0.0/24"

    # Split this cider into 4 cider ranges of /26
    result = filter_split_cidr(cidr, [26])

    assert result == ["10.0.0.0/26", "10.0.0.64/26", "10.0.0.128/26", "10.0.0.192/26"]


def test_filter_subnet_network_zone():
    object = {"Fn::Pipeline::SubnetId": {"NetworkZone": "public"}}
    assert filter_subnet_network_zone(object) == "public"
    assert filter_subnet_network_zone(None) == "private"
    assert filter_subnet_network_zone(jinja2.Undefined()) == "private"
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_subnet_network_zone({})


def test_filter_subnet_az_index():
    object = {"Fn::Pipeline::SubnetId": {"AzIndex": 1}}
    assert filter_subnet_az_index(object) == 1
    assert filter_subnet_az_index(None) == 0
    assert filter_subnet_az_index(jinja2.Undefined()) == 0
    with pytest.raises(jinja2.exceptions.UndefinedError):
        filter_subnet_az_index({})


def test_filter_tags(render_context):

    render_context["tags"] = {
        "environment": {"example-component": {"Key1": "Value1", "Key2": "Value2"}}
    }
    expected_tags = {
        "Key1": "Value1",
        "Key2": "Value2",
        "Portfolio": "example-portfolio",
        "App": "example-app",
        "Environment": "prod",
        "Name": "example-portfolio-example-app-prod-example-component",
    }

    component_name = "example-component"
    scope = "environment"

    tags = filter_tags(render_context, scope, component_name)

    assert tags == expected_tags


def test_filter_to_json():
    data = {"key1": "value1"}
    assert filter_to_json(data) == '{"key1": "value1"}'


def test_filter_to_yaml():

    data = {"key1": "value1"}

    result = filter_to_yaml(data)

    assert result == "key1: value1"


def test_filter_regex_replace():
    assert filter_regex_replace("string", "s", "S") == "String"


def test_filter_format_date():
    with patch("core_renderer.filters.date") as mock_today:
        mock_today.today.return_value = date(2021, 7, 1)
        mock_today.strftime = date.strftime
        df = filter_format_date("%Y-%m-%d")
        assert df == "2021-07-01"


def test_load_filters():
    env = jinja2.Environment()

    load_filters(env)

    assert "aws_tags" in env.filters
    assert "docker_image" in env.filters


if __name__ == "__main__":
    pytest.main()
