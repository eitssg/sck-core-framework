"""The common module provides a suite of functions that are used throughout the Core Automation framework.

These functions assist with generating and using model instances as well as environment variables and
other very common tasks.

"""

import warnings
from typing import Any, IO
import uuid
import tempfile
import json
import datetime
from decimal import Decimal
import os
import re
import boto3
from botocore.exceptions import ProfileNotFound

from .constants import (
    # Environment Variables
    ENV_AUTOMATION_ACCOUNT,
    ENV_AUTOMATION_REGION,
    ENV_API_LAMBDA_NAME,
    ENV_API_LAMBDA_ARN,
    ENV_API_HOST_URL,
    ENV_COMPONENT_COMPILER_LAMBDA_ARN,
    ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN,
    ENV_START_RUNNER_LAMBDA_ARN,
    ENV_EXECUTE_LAMBDA_ARN,
    ENV_INVOKER_LAMBDA_ARN,
    ENV_INVOKER_LAMBDA_NAME,
    ENV_INVOKER_LAMBDA_REGION,
    ENV_ENFORCE_VALIDATION,
    ENV_LOCAL_MODE,
    ENV_AWS_PROFILE,
    ENV_AWS_REGION,
    ENV_CLIENT,
    ENV_CLIENT_NAME,
    ENV_CLIENT_REGION,
    ENV_DYNAMODB_REGION,
    ENV_DYNAMODB_HOST,
    ENV_BUCKET_NAME,
    ENV_DOCUMENT_BUCKET_NAME,
    ENV_UI_BUCKET_NAME,
    ENV_BUCKET_REGION,
    ENV_ARTEFACT_BUCKET_NAME,
    ENV_MASTER_REGION,
    ENV_CDK_DEFAULT_ACCOUNT,
    ENV_CDK_DEFAULT_REGION,
    ENV_ENVIRONMENT,
    ENV_ORGANIZATION_EMAIL,
    ENV_SCOPE,
    ENV_DOMAIN,
    ENV_VOLUME,
    ENV_DELIVERED_BY,
    ENV_LOG_DIR,
    ENV_USE_S3,
    ENV_LOG_AS_JSON,
    ENV_LOG_LEVEL,
    ENV_CORRELATION_ID,
    ENV_ORGANIZATION_ID,
    ENV_ORGANIZATION_NAME,
    ENV_ORGANIZATION_ACCOUNT,
    ENV_AUDIT_ACCOUNT,
    ENV_SECURITY_ACCOUNT,
    ENV_NETWORK_ACCOUNT,
    ENV_AUTOMATION_TYPE,
    ENV_IAM_ACCOUNT,
    ENV_PORTFOLIO,
    ENV_APP,
    ENV_BRANCH,
    ENV_BUILD,
    ENV_PROJECT,
    ENV_BIZAPP,
    ENV_CONSOLE_LOG,
    ENV_CONSOLE,
    ENV_AWS_ENDPOINT_URL,
    # Data Values
    V_CORE_AUTOMATION,
    V_DEFAULT_REGION,
    V_DEFAULT_BRANCH,
    V_DEFAULT_REGION_ALIAS,
    V_FALSE,
    V_TRUE,
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
    V_PIPELINE,
    V_INTERACTIVE,
    # Deployment Scopes (NOT Automation SCOPE.  That's different!  ENV_SCOPE is a "prefix" to all automation objects)
    SCOPE_PORTFOLIO,
    SCOPE_APP,
    SCOPE_BRANCH,
    SCOPE_BUILD,
    SCOPE_COMPONENT,
    CORE_AUTOMATION_PIPELINE_PROVISIONING_ROLE,
    CORE_AUTOMATION_API_WRITE_ROLE,
    CORE_AUTOMATION_API_READ_ROLE,
)


def generate_branch_short_name(branch: str | None) -> str | None:
    """
    Generate a shortened version of the branch name.

    FIRST: the entire thing is converted to lowercase.
    THEN: Anything that is not a-z or 0-9 is replaced with a dash.
    THEN: only the 1st 20 characters of the branch name are used.
    Trailing hyphens are removed.

    Parameters
    ----------
    branch : str | None
        The branch name to shorten

    Returns
    -------
    str | None
        The shortened branch name, or None if input is None

    Examples
    --------
    >>> generate_branch_short_name("feature/USER-123-awesome-feature")
    'feature-user-123-awes'
    >>> generate_branch_short_name(None)
    None
    """
    if branch is None:
        return None

    return re.sub(r"[^a-z0-9-]", "-", branch.lower())[0:20].rstrip("-")


def split_prn(
    prn: str,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """
    Split the PRN and return the parts relevant to the deployment details.

    The PRN is in the format: prn:portfolio:app:branch:build:component

    If you have too many colons, at most it will return the first 5 parts after prn:

    Parameters
    ----------
    prn : str
        The PRN to split (ex: prn:portfolio:app:branch:build)

    Returns
    -------
    tuple[str | None, str | None, str | None, str | None, str | None]
        A tuple containing (portfolio, app, branch, build, component)

    Raises
    ------
    ValueError
        If PRN is empty, None, or doesn't start with 'prn:'

    Examples
    --------
    >>> split_prn("prn:ecommerce:web:main:1.0.0:frontend")
    ('ecommerce', 'web', 'main', '1.0.0', 'frontend')
    >>> split_prn("prn:ecommerce:web")
    ('ecommerce', 'web', None, None, None)
    """
    if not prn or not prn.startswith("prn:"):
        raise ValueError("PRN must start with 'prn:'")

    parts = prn.split(":")

    if len(parts) <= 2:
        return parts[1], None, None, None, None
    if len(parts) <= 3:
        return parts[1], parts[2], None, None, None
    if len(parts) <= 4:
        return parts[1], parts[2], parts[3], None, None
    if len(parts) <= 5:
        return parts[1], parts[2], parts[3], parts[4], None

    return parts[1], parts[2], parts[3], parts[4], parts[5]


def split_portfolio(
    portfolio: str | None,
) -> tuple[str | None, str | None, str | None, str]:
    """
    Split the portfolio into its component parts: Company, Group, Owner, Application.

    The portfolio must have at least 2 parts separated by a hyphen('-').

    For:
       owner-bizapp -> returns Owner and BizApp parts. Company and Group is None
       group-owner-bizapp -> returns Group and Owner and BizApp parts. Company is None
       company-group-owner-bizapp -> returns Company, Group, Owner and BizApp parts

    .. deprecated::
        This function is deprecated and will be removed in a future version.
        It was a bad idea and should not be used.

    Parameters
    ----------
    portfolio : str | None
        Name of the portfolio to parse

    Returns
    -------
    tuple[str | None, str | None, str | None, str]
        A tuple containing (Company, Group, Owner, Application)

    Raises
    ------
    ValueError
        If portfolio name is not specified or has invalid format

    Examples
    --------
    >>> split_portfolio("acme-ecommerce-web-frontend")
    ('acme', 'ecommerce', 'web', 'frontend')
    >>> split_portfolio("owner-bizapp")
    (None, None, 'owner', 'bizapp')
    """
    warnings.warn(
        "The split_portfolio function is deprecated and will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not portfolio:
        raise ValueError("Portfolio name must be specified.")

    parts = portfolio.split("-")
    if len(parts) == 1:
        return None, None, None, parts[0]
    if len(parts) == 2:
        return None, None, parts[0], parts[1]
    if len(parts) == 3:
        return None, parts[0], parts[1], parts[2]
    if len(parts) == 4:
        return parts[0], parts[1], parts[2], parts[3]

    raise ValueError('Portfolio should have 1 to 4 segments separated by a dash "-"')


def split_branch(branch: str, default_region_alias: str | None = None) -> tuple[str, str | None]:
    """
    Split the branch into the environment and data_center parts.

    If the data center is not specified, the DEFAULT_DATA_CENTER is used.
    Currently, this is the value "sin" to identify the Singapore data center.

    Parameters
    ----------
    branch : str
        The branch name to split
    default_region_alias : str | None, optional
        The default region alias to use if the data center (region) is not specified

    Returns
    -------
    tuple[str, str | None]
        A tuple containing (branch, region_alias) for environment and data center parts

    Examples
    --------
    >>> split_branch("main-sin")
    ('main', 'sin')
    >>> split_branch("develop", "sin")
    ('develop', 'sin')
    >>> split_branch("")
    ('main', 'sin')
    """
    if not branch:
        return (V_DEFAULT_BRANCH, default_region_alias or V_DEFAULT_REGION_ALIAS)
    parts = branch.split("-")
    if len(parts) < 2:
        return (branch, default_region_alias or V_DEFAULT_REGION_ALIAS)
    return (parts[0], default_region_alias) if len(parts) < 2 else (parts[0], parts[1])


def get_prn(
    portfolio: str,
    app: str | None = None,
    branch: str | None = None,
    build: str | None = None,
    component: str | None = None,
    scope: str = SCOPE_BUILD,
    delim: str = ":",
) -> str:
    """
    Generate a PRN with a delimiter between the parts as specified in the 'delim' parameter.

    The "Scope" argument is used to determine how many parts of the PRN are included in the result.

    Parameters
    ----------
    portfolio : str
        Business application (portfolio) name
    app : str | None, optional
        Deployment part of the Business application (app), by default None
    branch : str | None, optional
        Branch of the source-code repository, by default None
    build : str | None, optional
        Build Number or Commit ID of the deployment, by default None
    component : str | None, optional
        Component Part of the deployment, by default None
    scope : str, optional
        Scope of the PRN, by default SCOPE_BUILD
    delim : str, optional
        Delimiter of the parts of the PRN, by default ":"

    Returns
    -------
    str
        The Pipeline Reference Number (PRN)

    Examples
    --------
    >>> get_prn("ecommerce", "web", "main", "1.0.0", scope=SCOPE_BUILD)
    'ecommerce:web:main:1.0.0'
    >>> get_prn("ecommerce", "web", scope=SCOPE_APP)
    'ecommerce:web'
    >>> get_prn("ecommerce", "web", "main", "1.0.0", delim="-")
    'ecommerce-web-main-1.0.0'
    """
    result = portfolio
    if scope == SCOPE_PORTFOLIO:
        return result
    if app:
        result = f"{result}{delim}{app}"
        if scope == SCOPE_APP:
            return result
    if branch:
        result = f"{result}{delim}{branch}"
        if scope == SCOPE_BRANCH:
            return result
    if build:
        result = f"{result}{delim}{build}"
        if scope == SCOPE_BUILD:
            return result
    if component:
        result = f"{result}{delim}{component}"
        if scope == SCOPE_COMPONENT:
            return result
    return result


def generate_bucket_name(
    client: str | None = None,
    region: str | None = None,
    scope_prefix: str | None = None,
) -> str:
    """
    Generate a bucket name from the client, region, and scope prefix.

    Parameters
    ----------
    client : str | None, optional
        The client name, by default None (uses get_client())
    region : str | None, optional
        The region name, by default None (uses get_bucket_region())
    scope_prefix : str | None, optional
        The scope prefix, by default None (uses get_automation_scope())

    Returns
    -------
    str
        The generated bucket name in format: {scope_prefix}{client}-{V_CORE_AUTOMATION}-{region}

    Examples
    --------
    >>> generate_bucket_name("myclient", "us-east-1", "dev-")
    'dev-myclient-core-automation-us-east-1'
    >>> generate_bucket_name()  # Uses defaults from environment
    'myclient-core-automation-us-east-1'
    """
    if not client:
        client = get_client() or V_EMPTY

    if not region:
        region = get_bucket_region()

    if scope_prefix is None:
        scope_prefix = get_automation_scope() or V_EMPTY

    return f"{scope_prefix}{client}-{V_CORE_AUTOMATION}-{region}".lower().strip("-")


def get_bucket_name(client: str | None = None, region: str | None = None) -> str:
    """
    Get the bucket name from environment variable BUCKET_NAME or generate one.

    If BUCKET_NAME is not specified, generates a bucket name based on the client name,
    region, and automation scope prefix.

    Parameters
    ----------
    client : str | None, optional
        The client name, by default None (uses get_client())
    region : str | None, optional
        The region name, by default None (uses get_bucket_region())

    Returns
    -------
    str
        The bucket name for the core automation objects

    Examples
    --------
    >>> get_bucket_name("myclient", "us-east-1")
    'myclient-core-automation-us-east-1'
    """
    if not client:
        client = get_client() or V_EMPTY

    if not region:
        region = get_bucket_region()

    automation_scope_prefix = get_automation_scope() or V_EMPTY

    return os.environ.get(
        ENV_BUCKET_NAME,
        generate_bucket_name(client, region, automation_scope_prefix),
    )


def get_document_bucket_name(client: str | None = None) -> str:
    """
    Get the bucket name for documents from environment variable DOCUMENT_BUCKET_NAME.

    If not specified, falls back to the core automation bucket name.

    Parameters
    ----------
    client : str | None, optional
        The client name, by default None

    Returns
    -------
    str
        The bucket name for the documents

    Examples
    --------
    >>> get_document_bucket_name("myclient")
    'myclient-documents'
    """
    return os.environ.get(ENV_DOCUMENT_BUCKET_NAME, V_EMPTY) or get_bucket_name(client)


def get_ui_bucket_name(client: str | None = None) -> str:
    """
    Get the bucket name for UI from environment variable UI_BUCKET_NAME.

    If not specified, falls back to the core automation bucket name.

    Parameters
    ----------
    client : str | None, optional
        The client name, by default None

    Returns
    -------
    str
        The bucket name for the UI

    Examples
    --------
    >>> get_ui_bucket_name("myclient")
    'myclient-ui'
    """
    return os.environ.get(ENV_UI_BUCKET_NAME, V_EMPTY) or get_bucket_name(client)


def get_artefact_bucket_name(client: str | None = None, region: str | None = None) -> str:
    """
    Get the bucket name for artefacts from environment variable ARTEFACT_BUCKET_NAME.

    If not specified, falls back to the core automation bucket name.

    Parameters
    ----------
    client : str | None, optional
        The client name, by default None
    region : str | None, optional
        The region name, by default None

    Returns
    -------
    str
        The bucket name for the artefacts

    Examples
    --------
    >>> get_artefact_bucket_name("myclient", "us-east-1")
    'myclient-artefacts-us-east-1'
    """
    return os.environ.get(ENV_ARTEFACT_BUCKET_NAME, V_EMPTY) or get_bucket_name(client, region)


def get_artefact_bucket_region() -> str:
    """
    Get the region of the artefact bucket from environment variable ARTEFACT_BUCKET_REGION.

    If not specified, falls back to the core automation bucket region.

    Returns
    -------
    str
        Region of the artefact bucket

    Examples
    --------
    >>> get_artefact_bucket_region()
    'us-east-1'
    """
    return os.environ.get(ENV_BUCKET_REGION, V_EMPTY) or get_bucket_region()


def get_prn_alt(
    portfolio: str,
    app: str | None = None,
    branch: str | None = None,
    build: str | None = None,
    component: str | None = None,
    scope: str = SCOPE_BUILD,
) -> str:
    """
    Generate a PRN with a hyphen delimiter.

    Helper function to generate a PRN with a hyphen delimiter instead of colon.
    Returns a result like: portfolio-app-branch-build-component

    Parameters
    ----------
    portfolio : str
        Portfolio Business Application Name
    app : str | None, optional
        Deployment component of the Business Application Portfolio, by default None
    branch : str | None, optional
        Repository Branch for the source code, by default None
    build : str | None, optional
        Branch build reference or Commit ID, by default None
    component : str | None, optional
        Infrastructure Component part, by default None
    scope : str, optional
        Scope of the Pipeline Reference Number, by default SCOPE_BUILD

    Returns
    -------
    str
        The Pipeline Reference Number (PRN) with hyphen delimiters

    Examples
    --------
    >>> get_prn_alt("ecommerce", "web", "main", "1.0.0")
    'ecommerce-web-main-1.0.0'
    """
    return get_prn(portfolio, app, branch, build, component, scope, delim="-")


def get_automation_scope() -> str:
    """
    Get the automation scope prefix from environment variable SCOPE.

    The automation scope is a prefix on all automation objects. This is typically
    an empty string or None. This is NOT the same thing as the deployment scope.
    The deployment scope is a part of the PRN.

    This is the "Automation Scope" typically used to differentiate multiple
    core automation engines in the same AWS account.

    Returns
    -------
    str
        The prefix for all automation objects

    Examples
    --------
    >>> get_automation_scope()
    'dev-'
    """
    return os.getenv(ENV_SCOPE, V_EMPTY)


def get_automation_type() -> str:
    """
    Get the type of automation engine to execute for the project.

    Values will be V_DEPLOYSPEC or V_PIPELINE from environment variable AUTOMATION_TYPE.

    Returns
    -------
    str
        The type of automation engine to use (deployspec or pipeline)

    Examples
    --------
    >>> get_automation_type()
    'pipeline'
    """
    return os.getenv(ENV_AUTOMATION_TYPE, V_EMPTY) or V_PIPELINE


def get_portfolio() -> str | None:
    """
    Get the portfolio name from environment variable PORTFOLIO.

    Returns
    -------
    str | None
        The portfolio name or None if not set

    Examples
    --------
    >>> get_portfolio()
    'ecommerce'
    """
    return os.getenv(ENV_PORTFOLIO, None)


def get_app() -> str | None:
    """
    Get the app name from environment variable APP.

    Returns
    -------
    str | None
        The app name or None if not set

    Examples
    --------
    >>> get_app()
    'web'
    """
    return os.getenv(ENV_APP, None)


def get_branch() -> str | None:
    """
    Get the branch name from environment variable BRANCH.

    Returns
    -------
    str | None
        The branch name or None if not set

    Examples
    --------
    >>> get_branch()
    'main'
    """
    return os.getenv(ENV_BRANCH, None)


def get_build() -> str | None:
    """
    Get the build name from environment variable BUILD.

    Returns
    -------
    str | None
        The build name or None if not set

    Examples
    --------
    >>> get_build()
    '1.0.0'
    """
    return os.getenv(ENV_BUILD, None)


def get_provisioning_role_arn(account: str | None = None) -> str:
    """
    Get the provisioning role ARN for the specified account.

    Constructs the ARN using the automation scope prefix and account number.

    Parameters
    ----------
    account : str | None, optional
        The AWS account number, by default None (uses get_automation_account())

    Returns
    -------
    str
        The ARN for the provisioning role

    Examples
    --------
    >>> get_provisioning_role_arn("123456789012")
    'arn:aws:iam::123456789012:role/CoreAutomationPipelineProvisioningRole'
    """
    scope_prefix = get_automation_scope() or V_EMPTY

    if account is None:
        account = get_automation_account() or V_EMPTY

    return "arn:aws:iam::{}:role/{}{}".format(account, scope_prefix, CORE_AUTOMATION_PIPELINE_PROVISIONING_ROLE)


def get_automation_api_role_arn(account: str | None = None, write: bool = False) -> str:
    """
    Get the automation API role ARN for the specified account.

    Constructs the ARN for either read or write API role.

    Parameters
    ----------
    account : str | None, optional
        The AWS account number, by default None (uses get_automation_account())
    write : bool, optional
        Whether to get the write role (True) or read role (False), by default False

    Returns
    -------
    str
        The ARN for the automation API role, or None if account cannot be determined

    Examples
    --------
    >>> get_automation_api_role_arn("123456789012", write=True)
    'arn:aws:iam::123456789012:role/CoreAutomationApiWriteRole'
    >>> get_automation_api_role_arn("123456789012", write=False)
    'arn:aws:iam::123456789012:role/CoreAutomationApiReadRole'
    """
    scope_prefix = get_automation_scope()

    if account is None:
        account = get_automation_account() or V_EMPTY

    if not account:
        return None

    if write:
        return "arn:aws:iam::{}:role/{}{}".format(account, scope_prefix, CORE_AUTOMATION_API_WRITE_ROLE)

    return "arn:aws:iam::{}:role/{}{}".format(account, scope_prefix, CORE_AUTOMATION_API_READ_ROLE)


def get_organization_id() -> str | None:
    """
    Get the organization ID from environment variable ORGANIZATION_ID.

    Returns
    -------
    str | None
        The organization ID or None if not set

    Examples
    --------
    >>> get_organization_id()
    'o-123456789'
    """
    return os.getenv(ENV_ORGANIZATION_ID, None)


def get_organization_name() -> str | None:
    """
    Get the organization name from environment variable ORGANIZATION_NAME.

    Returns
    -------
    str | None
        The organization name or None if not set

    Examples
    --------
    >>> get_organization_name()
    'Acme Corporation'
    """
    return os.getenv(ENV_ORGANIZATION_NAME, None)


def get_organization_account() -> str | None:
    """
    Get the organization account number from environment variable ORGANIZATION_ACCOUNT.

    Returns
    -------
    str | None
        The organization account number or None if not set

    Examples
    --------
    >>> get_organization_account()
    '123456789012'
    """
    return os.getenv(ENV_ORGANIZATION_ACCOUNT, None)


def get_organization_email() -> str | None:
    """
    Get the organization email address from environment variable ORGANIZATION_EMAIL.

    Returns
    -------
    str | None
        The organization email address or None if not set

    Examples
    --------
    >>> get_organization_email()
    'admin@acme.com'
    """
    return os.getenv(ENV_ORGANIZATION_EMAIL, None)


def get_iam_account() -> str | None:
    """
    Get the IAM account number from environment variable IAM_ACCOUNT.

    Returns
    -------
    str | None
        The IAM account number or None if not set

    Examples
    --------
    >>> get_iam_account()
    '123456789012'
    """
    return os.getenv(ENV_IAM_ACCOUNT, None)


def get_audit_account() -> str | None:
    """
    Get the audit account number from environment variable AUDIT_ACCOUNT.

    Returns
    -------
    str | None
        The audit account number or None if not set

    Examples
    --------
    >>> get_audit_account()
    '123456789012'
    """
    return os.getenv(ENV_AUDIT_ACCOUNT, None)


def get_security_account() -> str | None:
    """
    Get the security account number from environment variable SECURITY_ACCOUNT.

    Returns
    -------
    str | None
        The security account number or None if not set

    Examples
    --------
    >>> get_security_account()
    '123456789012'
    """
    return os.getenv(ENV_SECURITY_ACCOUNT, None)


def get_domain() -> str:
    """
    Get the domain name from environment variable DOMAIN.

    Returns
    -------
    str
        The domain name, defaults to "example.com"

    Examples
    --------
    >>> get_domain()
    'acme.com'
    """
    return os.getenv(ENV_DOMAIN, "example.com")


def get_network_account() -> str | None:
    """
    Get the network account number from environment variable NETWORK_ACCOUNT.

    Returns
    -------
    str | None
        The network account number or None if not set

    Examples
    --------
    >>> get_network_account()
    '123456789012'
    """
    return os.getenv(ENV_NETWORK_ACCOUNT, None)


def get_cdk_default_account() -> str | None:
    """
    Get the CDK default account from environment variable CDK_DEFAULT_ACCOUNT.

    Returns
    -------
    str | None
        The CDK default account or None if not set

    Examples
    --------
    >>> get_cdk_default_account()
    '123456789012'
    """
    return os.getenv(ENV_CDK_DEFAULT_ACCOUNT, None)


def get_cdk_default_region() -> str | None:
    """
    Get the CDK default region from environment variable CDK_DEFAULT_REGION.

    Returns
    -------
    str | None
        The CDK default region or None if not set

    Examples
    --------
    >>> get_cdk_default_region()
    'us-east-1'
    """
    return os.getenv(ENV_CDK_DEFAULT_REGION, None)


def get_console_mode() -> str:
    """
    Get the console mode from environment variable CONSOLE.

    Returns
    -------
    str
        The console mode if set to V_INTERACTIVE, otherwise None

    Examples
    --------
    >>> get_console_mode()
    'interactive'
    """
    mode = os.getenv(ENV_CONSOLE, "")
    return mode if mode == V_INTERACTIVE else None


def is_use_s3() -> bool:
    """
    Check if the deployment is using S3 for storage.

    Returns True if not in local mode, or if USE_S3 environment variable is set to true.

    Returns
    -------
    bool
        True if the deployment is using S3 for storage

    Examples
    --------
    >>> is_use_s3()
    True
    """
    if not is_local_mode():
        return True

    return os.getenv(ENV_USE_S3, V_FALSE).lower() == V_TRUE


def is_json_log() -> bool:
    """
    Check if the log output is in JSON format from environment variable LOG_AS_JSON.

    Returns
    -------
    bool
        True if the log output is in JSON format

    Examples
    --------
    >>> is_json_log()
    False
    """
    return os.getenv(ENV_LOG_AS_JSON, V_FALSE).lower() == V_TRUE


def is_console_log() -> bool:
    """
    Check if the log output is to the console from environment variable CONSOLE_LOG.

    Returns
    -------
    bool
        True if the log output is to the console

    Examples
    --------
    >>> is_console_log()
    True
    """
    return os.getenv(ENV_CONSOLE_LOG, V_FALSE).lower() == V_TRUE


def get_log_level() -> str:
    """
    Get the log level from environment variable LOG_LEVEL.

    Returns
    -------
    str
        The log level, defaults to "INFO"

    Examples
    --------
    >>> get_log_level()
    'INFO'
    """
    return os.getenv(ENV_LOG_LEVEL, "INFO")


def is_local_mode() -> bool:
    """
    Check if the deployment is in local mode from environment variable LOCAL_MODE.

    Returns
    -------
    bool
        True if the mode is local

    Examples
    --------
    >>> is_local_mode()
    False
    """
    return os.getenv(ENV_LOCAL_MODE, V_FALSE).lower() == V_TRUE


def get_storage_volume(region: str | None = None) -> str:
    """
    Get the storage volume path for core automation objects.

    If LOCAL_MODE=true, you can specify a local storage volume via the VOLUME
    environment variable. If not specified, the current working directory is used.
    When using docker, this is your volume mount point.

    Example:
        export LOCAL_MODE=true
        export VOLUME=/mnt/data/core

    Then the engine will use /mnt/data/core/artefacts/**, /mnt/data/core/packages/**,
    /mnt/data/core/files/** as the storage locations.

    Setting LOCAL_MODE=false will store artefacts on S3.
    The storage volume is then the S3 URL https://s3-{region}.amazonaws.com.

    Parameters
    ----------
    region : str | None, optional
        The AWS region, by default None (uses get_bucket_region())

    Returns
    -------
    str
        Storage Volume Path

    Examples
    --------
    >>> get_storage_volume("us-east-1")
    'https://s3-us-east-1.amazonaws.com'
    >>> get_storage_volume()  # In local mode
    '/mnt/data/core'
    """
    if is_use_s3():
        if not region:
            region = get_bucket_region()
        return f"https://s3-{region}.amazonaws.com"

    return os.getenv(ENV_VOLUME, os.path.join(os.getcwd(), V_LOCAL))


def get_temp_dir(path: str | None = None) -> str:
    """
    Get the temporary directory for the application from environment variable TEMP_DIR.

    Parameters
    ----------
    path : str | None, optional
        The path to append to the temporary directory, by default None

    Returns
    -------
    str
        The temporary directory path

    Examples
    --------
    >>> get_temp_dir()
    '/tmp'
    >>> get_temp_dir("uploads")
    '/tmp/uploads'
    """
    folder = os.getenv("TEMP_DIR", os.getenv("TEMP", tempfile.gettempdir()))
    return os.path.join(folder, path) if path else folder


def get_mode() -> str:
    """
    Get the deployment mode from environment variable LOCAL_MODE.

    Returns
    -------
    str
        The mode of the deployment ("local" or "service")

    Examples
    --------
    >>> get_mode()
    'service'
    """
    return V_LOCAL if is_local_mode() else V_SERVICE


def is_enforce_validation() -> bool:
    """
    Check if validation enforcement is enabled from environment variable ENFORCE_VALIDATION.

    Returns
    -------
    bool
        True if validation should be enforced, defaults to True

    Examples
    --------
    >>> is_enforce_validation()
    True
    """
    return os.environ.get(ENV_ENFORCE_VALIDATION, V_TRUE).lower() == V_TRUE


def get_client() -> str | None:
    """
    Get the client name from environment variable CLIENT or AWS_PROFILE.

    Returns
    -------
    str | None
        The client name or None if not set

    Examples
    --------
    >>> get_client()
    'myclient'
    """
    return os.getenv(ENV_CLIENT, os.getenv(ENV_AWS_PROFILE, None))


def get_client_name() -> str | None:
    """
    Get the client name from environment variable CLIENT_NAME.

    Returns
    -------
    str | None
        The client name or None if not set

    Examples
    --------
    >>> get_client_name()
    'My Client Company'
    """
    return os.getenv(ENV_CLIENT_NAME, None)


def get_log_dir() -> str:
    """
    Get the log directory for the core automation engine from environment variable LOG_DIR.

    If not specified, defaults to "local/logs" in the current working directory.

    Returns
    -------
    str
        The log directory path

    Examples
    --------
    >>> get_log_dir()
    '/app/local/logs'
    """
    return os.getenv(ENV_LOG_DIR, os.path.join(os.getcwd(), "local", "logs"))


def get_delivered_by() -> str:
    """
    Get the delivered by value from environment variable DELIVERED_BY.

    Returns
    -------
    str
        The delivered by value, defaults to "automation"

    Examples
    --------
    >>> get_delivered_by()
    'automation'
    """
    return os.getenv(ENV_DELIVERED_BY, "automation")


def get_aws_profile() -> str:
    """
    Get the AWS profile name from environment variable AWS_PROFILE or client name.

    If the profile is not found in boto3 session credentials, returns "default".

    Returns
    -------
    str
        Value of the environment variable, client name, or "default"

    Examples
    --------
    >>> get_aws_profile()
    'myclient'
    """
    profile = os.getenv(ENV_AWS_PROFILE, "") or get_client()

    try:
        # if the profile is not in the boto3.session credentials, then return "default"
        boto3.session.Session(profile_name=profile)
    except ProfileNotFound:
        return "default"

    return profile


def get_aws_profile_region() -> str:
    """
    Get the AWS region from the AWS CLI configuration for the current profile.

    Returns
    -------
    str
        The AWS region from the profile configuration

    Examples
    --------
    >>> get_aws_profile_region()
    'us-east-1'
    """
    profile = get_aws_profile()

    try:
        # if the profile is not in the boto3.session credentials, then return "default"
        session = boto3.session.Session(profile_name=profile)
        return session.region_name
    except ProfileNotFound:
        return V_DEFAULT_REGION


def get_aws_region() -> str:
    """
    Get the AWS region from environment variable AWS_REGION.

    This is the region where the core automation engine is running.
    Falls back to profile region or default region.

    Returns
    -------
    str
        The AWS region

    Examples
    --------
    >>> get_aws_region()
    'us-east-1'
    """
    return os.getenv(ENV_AWS_REGION) or get_aws_profile_region() or V_DEFAULT_REGION


def get_client_region() -> str:
    """
    Get the client region from environment variable CLIENT_REGION.

    This is the BASE region where all other regions are derived from.
    Falls back to AWS region if not set.

    Returns
    -------
    str
        The AWS region for the client

    Examples
    --------
    >>> get_client_region()
    'us-east-1'
    """
    return os.getenv(ENV_CLIENT_REGION, "") or get_aws_region()


def get_master_region() -> str:
    """
    Get the AWS region of the Core-Automation engine from environment variable MASTER_REGION.

    If not specified, it will be derived from the client region.

    Returns
    -------
    str
        The AWS region for the Core Automation Engine

    Examples
    --------
    >>> get_master_region()
    'us-east-1'
    """
    return os.getenv(ENV_MASTER_REGION, "") or get_client_region()


def get_region() -> str:
    """
    Get the AWS region for the Deployment from environment variable AWS_REGION.

    If not specified, the region will be derived from the master region.

    Returns
    -------
    str
        The AWS region for the deployment

    Examples
    --------
    >>> get_region()
    'us-east-1'
    """
    return os.getenv(ENV_AWS_REGION, get_master_region())


def get_automation_region() -> str:
    """
    Get the automation region from environment variable AUTOMATION_REGION.

    Falls back to the main region if not set.

    Returns
    -------
    str
        The AWS region for the automation engine

    Examples
    --------
    >>> get_automation_region()
    'us-east-1'
    """
    return os.getenv(ENV_AUTOMATION_REGION, get_region())


def get_bucket_region() -> str:
    """
    Get the bucket region from environment variable BUCKET_REGION.

    Falls back to the master region if not set.

    Returns
    -------
    str
        The AWS region for the bucket where core automation objects are stored

    Examples
    --------
    >>> get_bucket_region()
    'us-east-1'
    """
    return os.environ.get(ENV_BUCKET_REGION, "") or get_master_region()


def get_dynamodb_region() -> str:
    """
    Get the DynamoDB region from environment variable DYNAMODB_REGION.

    Falls back to the master region if not set.

    Returns
    -------
    str
        The AWS region for the DynamoDB table

    Examples
    --------
    >>> get_dynamodb_region()
    'us-east-1'
    """
    return os.getenv(ENV_DYNAMODB_REGION, get_master_region())


def get_invoker_lambda_region() -> str:
    """
    Get the invoker lambda region from environment variable INVOKER_LAMBDA_REGION.

    Falls back to the master region if not set.

    Returns
    -------
    str
        The AWS region for the invoker lambda

    Examples
    --------
    >>> get_invoker_lambda_region()
    'us-east-1'
    """
    return os.getenv(ENV_INVOKER_LAMBDA_REGION, get_master_region())


def get_automation_account() -> str | None:
    """
    Get the AWS account number for the automation account from environment variable AUTOMATION_ACCOUNT.

    Returns
    -------
    str | None
        The AWS account number for the automation account where the core automation is installed, or None

    Examples
    --------
    >>> get_automation_account()
    '123456789012'
    """
    return os.getenv(ENV_AUTOMATION_ACCOUNT, None)


def get_dynamodb_host() -> str:
    """
    Get the URL for the DynamoDB host from environment variable DYNAMODB_HOST.

    This is typically the AWS DynamoDB endpoint for the region. However, you can
    specify a different endpoint if you are using a local DynamoDB instance or
    a different DynamoDB service.

    Returns
    -------
    str
        URL for the DynamoDB host

    Examples
    --------
    >>> get_dynamodb_host()
    'https://dynamodb.us-east-1.amazonaws.com'
    """
    region = get_dynamodb_region()
    return os.getenv(ENV_DYNAMODB_HOST, f"https://dynamodb.{region}.amazonaws.com")


def get_step_function_arn() -> str:
    """
    Get the Core Automation Step Function ARN from environment variable START_RUNNER_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation Step Function

    Examples
    --------
    >>> get_step_function_arn()
    'arn:aws:states:us-east-1:123456789012:stateMachine:CoreAutomationRunner'
    """
    region = get_region()

    if is_local_mode():
        return f"arn:aws:states:{region}:local:execution:stateMachineName:CoreAutomationRunner"

    account = get_automation_account()
    return os.environ.get(
        ENV_START_RUNNER_LAMBDA_ARN,
        f"arn:aws:states:{region}:{account}:stateMachine:CoreAutomationRunner",
    )


def get_invoker_lambda_name() -> str:
    """
    Get the name of the invoker lambda from environment variable INVOKER_LAMBDA_NAME.

    Returns
    -------
    str
        The name of the invoker lambda, defaults to "core-automation-invoker"

    Examples
    --------
    >>> get_invoker_lambda_name()
    'core-automation-invoker'
    """
    return os.getenv(ENV_INVOKER_LAMBDA_NAME, f"{V_CORE_AUTOMATION}-invoker")


def get_api_lambda_name() -> str:
    """
    Get the name of the Core Automation API Lambda from environment variable API_LAMBDA_NAME.

    Returns
    -------
    str
        The name of the Core Automation API Lambda, defaults to "core-automation-api"

    Examples
    --------
    >>> get_api_lambda_name()
    'core-automation-api'
    """
    return os.getenv(ENV_API_LAMBDA_NAME, f"{V_CORE_AUTOMATION}-api")


def get_api_lambda_arn() -> str:
    """
    Get the ARN of the Core Automation API Lambda from environment variable API_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation API Lambda

    Examples
    --------
    >>> get_api_lambda_arn()
    'arn:aws:lambda:us-east-1:123456789012:function:core-automation-api'
    """
    region = get_region()
    account = get_automation_account()
    name = get_api_lambda_name()
    return os.getenv(
        ENV_API_LAMBDA_ARN,
        f"arn:aws:lambda:{region}:{account}:function:{name}",
    )


def get_api_host_url() -> str | None:
    """
    Get the URL for the API Gateway from environment variable API_HOST_URL.

    If not specified, returns None.

    Returns
    -------
    str | None
        The URL for the API Gateway or None if not set

    Examples
    --------
    >>> get_api_host_url()
    'https://api.acme.com'
    """
    return os.getenv(ENV_API_HOST_URL, None)


def get_invoker_lambda_arn() -> str:
    """
    Get the ARN of the invoker lambda from environment variable INVOKER_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation Invoker lambda

    Examples
    --------
    >>> get_invoker_lambda_arn()
    'arn:aws:lambda:us-east-1:123456789012:function:core-automation-invoker'
    """
    region = get_region()
    account = get_automation_account()
    invoker_name = get_invoker_lambda_name()
    return os.getenv(
        ENV_INVOKER_LAMBDA_ARN,
        f"arn:aws:lambda:{region}:{account}:function:{invoker_name}",
    )


def get_execute_lambda_arn() -> str:
    """
    Get the ARN of the execute lambda from environment variable EXECUTE_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation Execute lambda

    Examples
    --------
    >>> get_execute_lambda_arn()
    'arn:aws:lambda:us-east-1:123456789012:function:core-automation-execute'
    """
    region = get_region()
    account = get_automation_account()
    return os.getenv(
        ENV_EXECUTE_LAMBDA_ARN,
        f"arn:aws:lambda:{region}:{account}:function:{V_CORE_AUTOMATION}-execute",
    )


def get_start_runner_lambda_arn() -> str:
    """
    Get the ARN of the start runner lambda from environment variable START_RUNNER_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation Start Runner lambda

    Examples
    --------
    >>> get_start_runner_lambda_arn()
    'arn:aws:lambda:us-east-1:123456789012:function:core-automation-runner'
    """
    region = get_region()
    account = get_automation_account()
    return os.getenv(
        ENV_START_RUNNER_LAMBDA_ARN,
        f"arn:aws:lambda:{region}:{account}:function:{V_CORE_AUTOMATION}-runner",
    )


def get_project() -> str | None:
    """
    Get the project name from environment variable PROJECT.

    Returns
    -------
    str | None
        The project name or None if not set

    Examples
    --------
    >>> get_project()
    'ecommerce-platform'
    """
    return os.getenv(ENV_PROJECT, None)


def get_bizapp() -> str | None:
    """
    Get the business application name from environment variable BIZAPP.

    Returns
    -------
    str | None
        The business application name or None if not set

    Examples
    --------
    >>> get_bizapp()
    'ecommerce'
    """
    return os.getenv(ENV_BIZAPP, None)


def get_deployspec_compiler_lambda_arn() -> str:
    """
    Get the ARN of the deployspec compiler lambda from environment variable DEPLOYSPEC_COMPILER_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation Deployspec Compiler lambda

    Examples
    --------
    >>> get_deployspec_compiler_lambda_arn()
    'arn:aws:lambda:us-east-1:123456789012:function:core-automation-deployspec-compiler'
    """
    region = get_region()
    account = get_automation_account()
    return os.getenv(
        ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN,
        f"arn:aws:lambda:{region}:{account}:function:{V_CORE_AUTOMATION}-deployspec-compiler",
    )


def get_component_compiler_lambda_arn() -> str:
    """
    Get the ARN of the component compiler lambda from environment variable COMPONENT_COMPILER_LAMBDA_ARN.

    If not specified, the default value is used based on the region and account number.

    Returns
    -------
    str
        The ARN for the Core Automation Component Compiler lambda

    Examples
    --------
    >>> get_component_compiler_lambda_arn()
    'arn:aws:lambda:us-east-1:123456789012:function:core-automation-component-compiler'
    """
    region = get_region()
    account = get_automation_account()
    return os.getenv(
        ENV_COMPONENT_COMPILER_LAMBDA_ARN,
        f"arn:aws:lambda:{region}:{account}:function:{V_CORE_AUTOMATION}-component-compiler",
    )


def get_correlation_id() -> str:
    """
    Get the correlation id from environment variable CORRELATION_ID.

    If not specified, generates a new UUID.

    Returns
    -------
    str
        The correlation id, defaults to a new UUID

    Examples
    --------
    >>> get_correlation_id()
    '12345678-1234-1234-1234-123456789012'
    """
    return os.getenv(ENV_CORRELATION_ID, str(uuid.uuid4()))


def get_environment() -> str:
    """
    Get the environment name from environment variable ENVIRONMENT.

    Returns
    -------
    str
        The environment name, defaults to "prod"

    Examples
    --------
    >>> get_environment()
    'prod'
    """
    return os.getenv(ENV_ENVIRONMENT, "prod")


def get_valid_mimetypes() -> list[str]:
    """
    Returns the list of supported MIME types for action files.

    Returns
    -------
    list[str]
        A list of valid YAML and JSON MIME types.
    """
    return [
        "application/json",
        "application/x-yaml",
        "application/yaml",
        "text/yaml",
        "text/x-yaml",
        "application/zip",
        "application/x-zip",
        "application/x-zip-compressed",
    ]


def is_yaml_mimetype(mimetype: str) -> bool:
    """
    Check if the provided MIME type is a valid YAML MIME type.

    Parameters
    ----------
    mimetype : str
        The MIME type to check

    Returns
    -------
    bool
        True if the MIME type is a valid YAML MIME type, False otherwise

    Examples
    --------
    >>> is_yaml_mimetype("application/x-yaml")
    True
    >>> is_yaml_mimetype("application/json")
    False
    """
    return mimetype.lower() in [
        "application/x-yaml",
        "application/yaml",
        "text/yaml",
        "text/x-yaml",
    ]


def is_json_mimetype(mimetype: str) -> bool:
    """
    Check if the provided MIME type is a valid JSON MIME type.

    Parameters
    ----------
    mimetype : str
        The MIME type to check

    Returns
    -------
    bool
        True if the MIME type is a valid JSON MIME type, False otherwise

    Examples
    --------
    >>> is_json_mimetype("application/json")
    True
    >>> is_json_mimetype("application/x-yaml")
    False
    """
    return mimetype.lower() in ["application/json", "application/x-json", "text/json"]


def is_zip_mimetype(mimetype: str) -> bool:
    """
    Check if the provided MIME type is a valid ZIP MIME type.

    Parameters
    ----------
    mimetype : str
        The MIME type to check

    Returns
    -------
    bool
        True if the MIME type is a valid ZIP MIME type, False otherwise

    Examples
    --------
    >>> is_zip_mimetype("application/zip")
    True
    >>> is_zip_mimetype("application/json")
    False
    """
    return mimetype.lower() in [
        "application/zip",
        "application/x-zip",
        "application/x-zip-compressed",
    ]


def __custom_serializer(obj: Any) -> Any:
    """
    Custom serializer for objects not serializable by default json code.

    Handles datetime objects, dates, times, and Decimal objects for JSON serialization.

    Parameters
    ----------
    obj : Any
        The object to serialize

    Returns
    -------
    Any
        The serialized object

    Raises
    ------
    TypeError
        If the object type is not serializable

    Examples
    --------
    >>> from datetime import datetime
    >>> __custom_serializer(datetime(2023, 1, 1))
    '2023-01-01T00:00:00'
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)  # or str(obj) if precision is important
    # No need to handle strings, ints, lists, dicts, etc. as they are already supported
    raise TypeError(f"Type {type(obj)} not serializable")


def to_json(data: Any, pretty: int | None = None) -> str:
    """
    JSON serializer for data objects with custom datetime handling.

    This function will convert datetime objects to strings in the ISO8601 format.

    Parameters
    ----------
    data : Any
        The data object to serialize
    pretty : int | None, optional
        The pretty print indent level, by default None

    Returns
    -------
    str
        JSON string representation of the data

    Examples
    --------
    >>> to_json({"name": "test", "created": datetime.now()})
    '{"name": "test", "created": "2023-01-01T12:00:00"}'
    >>> to_json({"name": "test"}, pretty=2)
    '{\n  "name": "test"\n}'
    """
    if data is None:
        return V_EMPTY  # or should we return "[]" or "{}"?

    return json.dumps(data, indent=pretty, default=__custom_serializer)


def write_json(data: Any, output_stream: IO, pretty: int | None = None) -> None:
    """
    Write JSON data to an output stream with custom datetime handling.

    This function will convert datetime objects to strings in the ISO8601 format.

    Parameters
    ----------
    data : Any
        The data to write to the output stream
    output_stream : IO
        The output stream to write the data to
    pretty : int | None, optional
        The pretty print indent level, by default None

    Examples
    --------
    >>> with open('output.json', 'w') as f:
    ...     write_json({"name": "test"}, f, pretty=2)
    """
    json.dump(data, output_stream, indent=pretty, default=__custom_serializer)


def __iso8601_parser(data: Any) -> Any:
    """
    Parse ISO8601 datetime strings back to datetime objects.

    Recursively processes dictionaries and lists to convert ISO8601 strings.

    Parameters
    ----------
    data : Any
        The data to parse

    Returns
    -------
    Any
        The parsed data with datetime objects converted from ISO8601 strings

    Examples
    --------
    >>> __iso8601_parser("2023-01-01T12:00:00")
    datetime.datetime(2023, 1, 1, 12, 0)
    >>> __iso8601_parser({"created": "2023-01-01T12:00:00"})
    {"created": datetime.datetime(2023, 1, 1, 12, 0)}
    """
    if isinstance(data, str):
        try:
            return datetime.datetime.fromisoformat(data)
        except ValueError:
            return data
    elif isinstance(data, dict):
        return {key: __iso8601_parser(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [__iso8601_parser(item) for item in data]
    return data


def from_json(data: str) -> Any:
    """
    JSON deserializer with automatic datetime parsing.

    This function will convert datetime strings in the JSON data to datetime objects.

    .. warning::
        This function will convert datetime strings in the JSON data to datetime objects.
        If you want strings, you will have to convert them back to strings yourself.

    Parameters
    ----------
    data : str
        The JSON string to deserialize

    Returns
    -------
    Any
        The deserialized data object with datetime strings converted to datetime objects

    Examples
    --------
    >>> from_json('{"created": "2023-01-01T12:00:00"}')
    {'created': datetime.datetime(2023, 1, 1, 12, 0)}
    """
    return json.loads(data, object_hook=__iso8601_parser)


def read_json(input_stream: IO) -> Any:
    """
    Load JSON data from an input stream with automatic datetime parsing.

    .. warning::
        This function will convert datetime strings in the JSON data to datetime objects.
        If you want strings, you will have to convert them back to strings yourself.

    Parameters
    ----------
    input_stream : IO
        The input stream to read the JSON data from

    Returns
    -------
    Any
        The JSON data as a dict or list object with datetime strings converted to datetime objects

    Examples
    --------
    >>> with open('input.json', 'r') as f:
    ...     data = read_json(f)
    """
    return json.load(input_stream, object_hook=__iso8601_parser)


def get_current_timestamp() -> str:
    """
    Get the current timestamp as a string in ISO8601 format.

    Returns
    -------
    str
        The current timestamp in ISO8601 format

    Examples
    --------
    >>> get_current_timestamp()
    '2023-01-01T12:00:00+00:00'
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_cognito_endpoint(default: str = None) -> str | None:
    """
    Get the Cognito endpoint URL from environment variable COGNITO_ENDPOINT.

    Returns
    -------
    str | None
        The Cognito endpoint URL or None if not set

    Examples
    --------
    >>> get_cognito_endpoint()
    'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_123456789'
    """
    return os.getenv(ENV_AWS_ENDPOINT_URL, default)


def get_current_timestamp_short() -> str:
    """
    Generate a short timestamp string suitable for AWS resource naming.

    Returns a compact timestamp in format: YYYYMMDD-HHMMSS
    Example: "20250720-143052"

    :return: Short timestamp string
    :rtype: str
    """

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
