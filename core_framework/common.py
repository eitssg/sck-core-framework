"""The common module provides a suite of functions that are used throughout the Core Automation framework.

These functions assist with generating and using model instances as well as environment variables and
other very common tasks.

"""

import warnings
from typing import Any, IO, Dict
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
    """Split PRN into deployment hierarchy components.

    Parses PRN format: prn:portfolio:app:branch:build:component
    Returns up to 5 components after 'prn:' prefix.

    Args:
        prn: The PRN to split (e.g., "prn:portfolio:app:branch:build").

    Returns:
        Tuple containing (portfolio, app, branch, build, component).

    Raises:
        ValueError: If PRN is empty, None, or doesn't start with 'prn:'.

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
    """Split portfolio into component parts.

    .. deprecated::
        This function is deprecated and will be removed in a future version.
        It was a bad idea and should not be used.

    Args:
        portfolio: Name of the portfolio to parse.

    Returns:
        A tuple containing (Company, Group, Owner, Application)

    Raises:
        ValueError: If portfolio name is not specified or has invalid format

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
    """Split branch into environment and data center parts.

    Args:
        branch: The branch name to split.
        default_region_alias: Default region alias if not specified.

    Returns:
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
    """Generate PRN with specified delimiter and scope.

    Args:
        portfolio: Business application (portfolio) name.
        app: Deployment part of the business application.
        branch: Source code repository branch.
        build: Build number or commit ID.
        component: Component part of the deployment.
        scope: Scope determining how many parts to include.
        delim: Delimiter between PRN parts.

    Returns:
        The Pipeline Reference Number (PRN).

    Examples:
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
    """Generate S3 bucket name from client, region, and scope.

    Args:
        client: The client name.
        region: The region name.
        scope_prefix: The automation scope prefix.

    Returns:
        The generated bucket name in format: {scope_prefix}{client}-{V_CORE_AUTOMATION}-{region}

    Examples:
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
    """Get bucket name from environment or generate one.

    If BUCKET_NAME is not specified, generates a bucket name based on the client name,
    region, and automation scope prefix.

    Args:
        client: The client name.
        region: The region name.

    Returns:
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
    """Get document bucket name from environment or fallback.

    Args:
        client: The client name.

    Returns:
        The bucket name for the documents

    Examples
    --------
    >>> get_document_bucket_name("myclient")
    'myclient-documents'
    """
    return os.environ.get(ENV_DOCUMENT_BUCKET_NAME, V_EMPTY) or get_bucket_name(client)


def get_ui_bucket_name(client: str | None = None) -> str:
    """Get UI bucket name from environment or fallback.

    Args:
        client: The client name.

    Returns:
        The bucket name for the UI

    Examples
    --------
    >>> get_ui_bucket_name("myclient")
    'myclient-ui'
    """
    return os.environ.get(ENV_UI_BUCKET_NAME, V_EMPTY) or get_bucket_name(client)


def get_artefact_bucket_name(client: str | None = None, region: str | None = None) -> str:
    """Get artefact bucket name from environment or fallback.

    Args:
        client: The client name.
        region: The region name.

    Returns:
        The bucket name for the artefacts

    Examples
    --------
    >>> get_artefact_bucket_name("myclient", "us-east-1")
    'myclient-artefacts-us-east-1'
    """
    return os.environ.get(ENV_ARTEFACT_BUCKET_NAME, V_EMPTY) or get_bucket_name(client, region)


def get_artefact_bucket_region() -> str:
    """Get artefact bucket region from environment.

    Returns:
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
    """Generate PRN with hyphen delimiter.

    Args:
        portfolio: Portfolio name.
        app: App name.
        branch: Branch name.
        build: Build reference.
        component: Component name.
        scope: PRN scope.

    Returns:
        PRN with hyphen delimiters.

    Examples:
        >>> get_prn_alt("ecommerce", "web", "main", "1.0.0")
        'ecommerce-web-main-1.0.0'
    """
    return get_prn(portfolio, app, branch, build, component, scope, delim="-")


def get_automation_scope() -> str:
    """Get automation scope prefix from SCOPE environment variable.

    Returns:
        The prefix for all automation objects

    Examples
    --------
    >>> get_automation_scope()
    'dev-'
    """
    return os.getenv(ENV_SCOPE, V_EMPTY)


def get_automation_type() -> str:
    """Get automation engine type from AUTOMATION_TYPE environment variable.

    Returns:
        The type of automation engine to use (deployspec or pipeline)

    Examples
    --------
    >>> get_automation_type()
    'pipeline'
    """
    return os.getenv(ENV_AUTOMATION_TYPE, V_EMPTY) or V_PIPELINE


def get_portfolio() -> str | None:
    """Get portfolio name from PORTFOLIO environment variable.

    Returns:
        The portfolio name or None if not set

    Examples
    --------
    >>> get_portfolio()
    'ecommerce'
    """
    return os.getenv(ENV_PORTFOLIO, None)


def get_app() -> str | None:
    """Get app name from APP environment variable.

    Returns:
        The app name or None if not set

    Examples
    --------
    >>> get_app()
    'web'
    """
    return os.getenv(ENV_APP, None)


def get_branch() -> str | None:
    """Get branch name from BRANCH environment variable.

    Returns:
        The branch name or None if not set

    Examples
    --------
    >>> get_branch()
    'main'
    """
    return os.getenv(ENV_BRANCH, None)


def get_build() -> str | None:
    """Get build name from BUILD environment variable.

    Returns:
        The build name or None if not set

    Examples
    --------
    >>> get_build()
    '1.0.0'
    """
    return os.getenv(ENV_BUILD, None)


def get_provisioning_role_arn(account: str | None = None) -> str:
    """Get provisioning role ARN for specified account.

    Args:
        account: AWS account number.

    Returns:
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
    """Get automation API role ARN.

    Args:
        account: AWS account number.
        write: Whether to get write role (True) or read role (False).

    Returns:
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
    """Get organization ID from ORGANIZATION_ID environment variable.

    Returns:
        The organization ID or None if not set

    Examples
    --------
    >>> get_organization_id()
    'o-123456789'
    """
    return os.getenv(ENV_ORGANIZATION_ID, None)


def get_organization_name() -> str | None:
    """Get organization name from ORGANIZATION_NAME environment variable.

    Returns:
        The organization name or None if not set

    Examples
    --------
    >>> get_organization_name()
    'Acme Corporation'
    """
    return os.getenv(ENV_ORGANIZATION_NAME, None)


def get_organization_account() -> str | None:
    """Get organization account from ORGANIZATION_ACCOUNT environment variable.

    Returns:
        The organization account number or None if not set

    Examples
    --------
    >>> get_organization_account()
    '123456789012'
    """
    return os.getenv(ENV_ORGANIZATION_ACCOUNT, None)


def get_organization_email() -> str | None:
    """Get organization email from ORGANIZATION_EMAIL environment variable.

    Returns:
        The organization email address or None if not set

    Examples
    --------
    >>> get_organization_email()
    'admin@acme.com'
    """
    return os.getenv(ENV_ORGANIZATION_EMAIL, None)


def get_iam_account() -> str | None:
    """Get IAM account from IAM_ACCOUNT environment variable.

    Returns:
        The IAM account number or None if not set

    Examples
    --------
    >>> get_iam_account()
    '123456789012'
    """
    return os.getenv(ENV_IAM_ACCOUNT, None)


def get_audit_account() -> str | None:
    """Get audit account from AUDIT_ACCOUNT environment variable.

    Returns:
        The audit account number or None if not set

    Examples
    --------
    >>> get_audit_account()
    '123456789012'
    """
    return os.getenv(ENV_AUDIT_ACCOUNT, None)


def get_security_account() -> str | None:
    """Get security account from SECURITY_ACCOUNT environment variable.

    Returns:
        The security account number or None if not set

    Examples
    --------
    >>> get_security_account()
    '123456789012'
    """
    return os.getenv(ENV_SECURITY_ACCOUNT, None)


def get_domain() -> str:
    """Get domain name from DOMAIN environment variable.

    Returns:
        The domain name, defaults to "example.com"

    Examples
    --------
    >>> get_domain()
    'acme.com'
    """
    return os.getenv(ENV_DOMAIN, "example.com")


def get_network_account() -> str | None:
    """Get network account from NETWORK_ACCOUNT environment variable.

    Returns:
        The network account number or None if not set

    Examples
    --------
    >>> get_network_account()
    '123456789012'
    """
    return os.getenv(ENV_NETWORK_ACCOUNT, None)


def get_cdk_default_account() -> str | None:
    """Get CDK default account from CDK_DEFAULT_ACCOUNT environment variable.

    Returns:
        The CDK default account or None if not set

    Examples
    --------
    >>> get_cdk_default_account()
    '123456789012'
    """
    return os.getenv(ENV_CDK_DEFAULT_ACCOUNT, None)


def get_cdk_default_region() -> str | None:
    """Get CDK default region from CDK_DEFAULT_REGION environment variable.

    Returns:
        The CDK default region or None if not set

    Examples
    --------
    >>> get_cdk_default_region()
    'us-east-1'
    """
    return os.getenv(ENV_CDK_DEFAULT_REGION, None)


def get_console_mode() -> str:
    """Get console mode from CONSOLE environment variable.

    Returns:
        The console mode if set to V_INTERACTIVE, otherwise None

    Examples
    --------
    >>> get_console_mode()
    'interactive'
    """
    mode = os.getenv(ENV_CONSOLE, "")
    return mode if mode == V_INTERACTIVE else None


def is_use_s3() -> bool:
    """Check if deployment uses S3 storage.

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
    """Check if log output is in JSON format.

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
    """Check if log output goes to console.

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
    """Get log level from LOG_LEVEL environment variable.

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
    """Check if deployment is in local mode.

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
    """Get storage volume path for automation objects.

    Args:
        region: AWS region.

    Returns:
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
    """Get temporary directory path.

    Args:
        path: Path to append to temp directory.

    Returns:
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
    """Get deployment mode.

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
    """Check if validation enforcement is enabled.

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
    """Get client name from CLIENT or AWS_PROFILE environment variable.

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
    """Get client name from CLIENT_NAME environment variable.

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
    """Get log directory from LOG_DIR environment variable.

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
    """Get delivered by value from DELIVERED_BY environment variable.

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
    """Get AWS profile name or "default" if not found.

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
    """Get AWS region from profile configuration.

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
    """Get AWS region from AWS_REGION environment variable.

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
    """Get client region from CLIENT_REGION environment variable.

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
    """Get master region from MASTER_REGION environment variable.

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
    """Get deployment region from AWS_REGION environment variable.

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
    """Get automation region from AUTOMATION_REGION environment variable.

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
    """Get bucket region from BUCKET_REGION environment variable.

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
    """Get DynamoDB region from DYNAMODB_REGION environment variable.

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
    """Get invoker lambda region from INVOKER_LAMBDA_REGION environment variable.

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
    """Get automation account from AUTOMATION_ACCOUNT environment variable.

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
    """Get DynamoDB host URL from DYNAMODB_HOST environment variable.

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
    """Get Core Automation Step Function ARN.

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
    """Get invoker lambda name from INVOKER_LAMBDA_NAME environment variable.

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
    """Get API lambda name from API_LAMBDA_NAME environment variable.

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
    """Get API lambda ARN from API_LAMBDA_ARN environment variable.

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
    """Get API Gateway URL from API_HOST_URL environment variable.

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
    """Get invoker lambda ARN from INVOKER_LAMBDA_ARN environment variable.

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
    """Get execute lambda ARN from EXECUTE_LAMBDA_ARN environment variable.

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
    """Get start runner lambda ARN from START_RUNNER_LAMBDA_ARN environment variable.

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
    """Get project name from PROJECT environment variable.

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
    """Get business application name from BIZAPP environment variable.

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
    """Get deployspec compiler lambda ARN.

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
    """Get component compiler lambda ARN.

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
    """Get correlation ID from CORRELATION_ID environment variable.

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
    """Get environment name from ENVIRONMENT environment variable.

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
    """Get list of supported MIME types for action files.

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
        "application/octet-stream",
    ]


def is_yaml_mimetype(mimetype: str) -> bool:
    """Check if MIME type is valid YAML.

    Args:
        mimetype: MIME type to check.

    Returns:
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
    """Check if MIME type is valid JSON.

    Args:
        mimetype: MIME type to check.

    Returns:
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
    """Check if MIME type is valid ZIP.

    Args:
        mimetype: MIME type to check.

    Returns:
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
    """Custom serializer for objects not serializable by default json code.

    Args:
        obj: The object to serialize.

    Returns:
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
    """JSON serializer with custom datetime handling.

    Args:
        data: Data object to serialize.
        pretty: Pretty print indent level.

    Returns:
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
    """Write JSON data to output stream.

    Args:
        data: Data to write.
        output_stream: Output stream.
        pretty: Pretty print indent level.

    Examples:
        >>> with open('output.json', 'w') as f:
        ...     write_json({"name": "test"}, f, pretty=2)
    """
    json.dump(data, output_stream, indent=pretty, default=__custom_serializer)


def __iso8601_parser(data: Any) -> Any:
    """Parse ISO8601 datetime strings back to datetime objects.

    Recursively processes dictionaries and lists to convert ISO8601 strings.

    Args:
        data: The data to parse.

    Returns:
        The parsed data with datetime objects converted from ISO8601 strings.

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
    """JSON deserializer with automatic datetime parsing.

    Args:
        data: JSON string to deserialize.

    Returns:
        The deserialized data object with datetime strings converted to datetime objects

    Examples
    --------
    >>> from_json('{"created": "2023-01-01T12:00:00"}')
    {'created': datetime.datetime(2023, 1, 1, 12, 0)}
    """
    return json.loads(data, object_hook=__iso8601_parser)


def read_json(input_stream: IO) -> Any:
    """Load JSON data from input stream with datetime parsing.

    Args:
        input_stream: Input stream to read from.

    Returns:
        JSON data with datetime objects.

    Examples:
        >>> with open('input.json', 'r') as f:
        ...     data = read_json(f)
    """
    return json.load(input_stream, object_hook=__iso8601_parser)


def get_current_timestamp() -> str:
    """Get current timestamp in ISO8601 format.

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
    """Get Cognito endpoint URL from COGNITO_ENDPOINT environment variable.

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
    """Generate short timestamp for AWS resource naming.

    Returns a compact timestamp in format: YYYYMMDD-HHMMSS
    Example: "20250720-143052"

    Returns:
        Short timestamp in format YYYYMMDD-HHMMSS.
    """

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")


def pascal_case_to_snake_case(value: Dict[str, Any]) -> Dict[str, Any]:
    """Convert PascalCase field names to snake_case field names.

    Returns:
        Dict[str, Any]: Dictionary with snake_case field names

    """

    def snake_case_key(key: str) -> str:
        """Convert a PascalCase key to snake_case."""
        return "".join(["_" + i.lower() if i.isupper() else i for i in key]).lstrip("_")

    result = {}
    for k, v in value.items():
        key = snake_case_key(k)
        if isinstance(v, dict):
            result[key] = pascal_case_to_snake_case(v)
        elif isinstance(v, list):
            result[key] = [pascal_case_to_snake_case(item) if isinstance(item, dict) else item for item in v]
        else:
            result[key] = v
    return result


def snake_case_to_pascal_case(value: Dict[str, Any]) -> Dict[str, Any]:
    """Convert snake_case field names to PascalCase field names.

    Returns:
        Dict[str, Any]: Dictionary with PascalCase field names

    """

    def pascal_case_key(key: str) -> str:
        """Convert a snake_case key to PascalCase."""
        return "".join(word.capitalize() for word in key.split("_"))

    result = {}
    for k, v in value.items():
        key = pascal_case_key(k)
        if isinstance(v, dict):
            result[key] = snake_case_to_pascal_case(v)
        elif isinstance(v, list):
            result[key] = [snake_case_to_pascal_case(item) if isinstance(item, dict) else item for item in v]
        else:
            result[key] = v
    return result
