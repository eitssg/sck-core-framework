"""Constants module for the Core-Automation framework.

Provides a single source of truth for values used throughout the framework,
preventing mistyping and ensuring consistency across Task Payload, Task Results,
and other framework objects.
"""

# Good to go
HTTP_OK = 200
"""HTTP 200 OK status code."""

HTTP_CREATED = 201
"""HTTP 201 Created status code."""

HTTP_ACCEPTED = 202
"""HTTP 202 Accepted status code."""

HTTP_NO_CONTENT = 204
"""HTTP 204 No Content status code."""

# Bad to go
HTTP_BAD_REQUEST = 400
"""HTTP 400 Bad Request status code."""

HTTP_UNAUTHORIZED = 401
"""HTTP 401 Unauthorized status code."""

HTTP_PAYMENT_REQUIRED = 402
"""HTTP 402 Payment Required status code."""

HTTP_FORBIDDEN = 403
"""HTTP 403 Forbidden status code."""

HTTP_NOT_FOUND = 404
"""HTTP 404 Not Found status code."""

HTTP_METHOD_NOT_ALLOWED = 405
"""HTTP 405 Method Not Allowed status code."""

HTTP_NOT_ACCEPTABLE = 406
"""HTTP 406 Not Acceptable status code."""

HTTP_PROXY_AUTHENTICATION_REQUIRED = 407
"""HTTP 407 Proxy Authentication Required status code."""

HTTP_REQUEST_TIMEOUT = 408
"""HTTP 408 Request Timeout status code."""

HTTP_CONFLICT = 409
"""HTTP 409 Conflict status code."""

# Can't process data
HTTP_UNPROCESSABLE_ENTITY = 422
"""HTTP 422 Unprocessable Entity status code."""

# Server Error
HTTP_INTERNAL_SERVER_ERROR = 500
"""HTTP 500 Internal Server Error status code."""

HTTP_NOT_IMPLEMENTED = 501
"""HTTP 501 Not Implemented status code."""

# Task Types
TASK_PACKAGE = "package"
"""Package task type identifier."""

TASK_UPLOAD = "upload"
"""Upload task type identifier."""

TASK_COMPILE = "compile"
"""Compile task type identifier."""

TASK_DEPLOY = "deploy"
"""Deploy task type identifier."""

TASK_PLAN = "plan"
"""Plan task type identifier."""

TASK_APPLY = "apply"
"""Apply task type identifier."""

TASK_RELEASE = "release"
"""Release task type identifier."""

TASK_TEARDOWN = "teardown"
"""Teardown task type identifier."""

# Field values
V_CORE_AUTOMATION = "automation"
"""Core automation service identifier."""

V_PACKAGE_ZIP = "package.zip"
"""ZIP package filename."""

V_PACKAGE_TAR = "package.tar"
"""TAR package filename."""

V_PIPELINE = "pipeline"
"""Pipeline automation type."""

V_DEPLOYSPEC = "deployspec"
"""Deployspec automation type."""

V_PLANSPEC = "planspec"
"""Planspec automation type."""

V_APPLYSPEC = "applyspec"
"""Applyspec automation type."""

V_TEARDOWNSPEC = "teardownspec"
"""Teardownspec automation type."""

V_DEPLOYSPEC_FILE_YAML = "deployspec.yaml"
"""YAML deployspec filename."""

V_PLANSPEC_FILE_YAML = "planspec.yaml"
"""YAML planspec filename."""

V_APPLYSPEC_FILE_YAML = "applyspec.yaml"
"""YAML applyspec filename."""

V_DEPLOYSPEC_FILE_JSON = "deployspec.json"
"""JSON deployspec filename."""

V_PLANSPEC_FILE_JSON = "planspec.json"
"""JSON planspec filename."""

V_APPLYSPEC_FILE_JSON = "applyspec.json"
"""JSON applyspec filename."""

V_TEARDOWNSPEC_FILE_YAML = "teardownspec.yaml"
"""YAML teardownspec filename."""

V_TEARDOWNSPEC_FILE_JSON = "teardownspec.json"
"""JSON teardownspec filename."""

V_LAMBDA_MODULES_FILE = "lambda_modules.txt"
"""Lambda modules requirements filename."""

V_SERVICE = "service"
"""Service deployment mode."""

V_LOCAL = "local"
"""Local deployment mode."""

V_FULL = "full"
"""Full deployment type."""

V_INCREMENTAL = "incremental"
"""Incremental deployment type."""

V_PLATFORM = "platform"
"""Platform deployment scope."""

V_CREATE_STACK = "create_stack"
"""Create stack operation type."""

V_DEFAULT_REGION = "us-east-1"
"""Default AWS region."""

V_DEFAULT_REGION_NAME = "US East (N. Virginia)"
"""Default AWS region display name."""

V_DEFAULT_REGION_ALIAS = "use"
"""Default region alias abbreviation."""

V_DEFAULT_BRANCH = "master"
"""Default repository branch name."""

V_DEFAULT_ENVIRONMENT = "prod"
"""Default deployment environment."""

V_TRUE = "true"
"""String representation of boolean true."""

V_FALSE = "false"
"""String representation of boolean false."""

V_EMPTY = ""
"""Empty string constant."""

V_INTERACTIVE = "interactive"
"""Interactive console mode."""

# Authorization Context Object
AUTH_CREDENTIALS = "Credentials"
"""Authorization credentials field."""

AUTH_ROLE = "Role"
"""Authorization role field."""

AUTH_ACCOUNT = "Account"
"""Authorization account field."""

AUTH_USER = "User"
"""Authorization user field."""

AUTH_ACCESS_KEY = "AccessKey"
"""AWS access key field."""

AUTH_SECRET_KEY = "SecretKey"
"""AWS secret key field."""

AUTH_TOKEN = "Token"
"""Authorization token field."""

AUTH_ACCESS_KEY_ID = "AccessKeyId"
"""AWS access key ID field."""

AUTH_SECRET_ACCESS_KEY = "SecretAccessKey"
"""AWS secret access key field."""

AUTH_SESSION_TOKEN = "SessionToken"
"""AWS session token field."""

# Account object in Authorization Context
ACCOUNT_ID = "Id"
"""Account ID field."""

ACCOUNT_REGION = "Region"
"""Account region field."""

ACCOUNT_USER_ARN = "UserArn"
"""Account user ARN field."""

ACCOUNT_USER_ID = "UserId"
"""Account user ID field."""

# Task Payload Object
TP_TASK = "Task"
"""Task payload task field."""

TP_FORCE = "Force"
"""Task payload force flag."""

TP_DRY_RUN = "DryRun"
"""Task payload dry run flag."""

TP_IDENTITY = "Identity"
"""Task payload identity field."""

TP_TYPE = "Type"
"""Task payload type field."""

TP_DEPLOYMENT_DETAILS = "DeploymentDetails"
"""Task payload deployment details field."""

TP_PACKAGE_DETAILS = "Package"
"""Task payload package details field."""

TP_FACTS = "Facts"
"""Task payload facts field."""

TP_ACTIONS = "Actions"
"""Task payload actions field."""

TP_DEPLOY_ACTIONS = "DeployActions"
"""Task payload deploy actions field."""

TP_STATE = "State"
"""Task payload state field."""

TP_FLOW_CONTROL = "FlowControl"
"""Task payload flow control field."""

# Actions Object Attributes
ACT_VERSION = "VersionId"
"""Action version ID field."""

ACT_BUCKETNAME = "BucketName"
"""Action bucket name field."""

ACT_BUCKET_REGION = "BucketRegion"
"""Action bucket region field."""

ACT_KEY = "Key"
"""Action key field."""

ACT_MIME_TYPE = "ContentType"
"""Action MIME type field."""

# Deployment Details object
DD_CLIENT = "Client"
"""Deployment details client field."""

DD_APP = "App"
"""Deployment details app field."""

DD_PORTFOLIO = "Portfolio"
"""Deployment details portfolio field."""

DD_BRANCH = "Branch"
"""Deployment details branch field."""

DD_BRANCH_SHORT_NAME = "BranchShortName"
"""Deployment details short branch name field."""

DD_BUILD = "Build"
"""Deployment details build field."""

DD_COMPONENT = "Component"
"""Deployment details component field."""

DD_ENVIRONMENT = "Environment"
"""Deployment details environment field."""

DD_DATA_CENTER = "DataCenter"
"""Deployment details data center field."""

DD_SCOPE = "Scope"
"""Deployment details scope field."""

DD_ECR = "Ecr"
"""Deployment details ECR object field."""

DD_TAGS = "Tags"
"""Deployment details tags field."""

# Docker Image
ECR_REGISTRY_URI = "RegistryUri"
"""ECR registry URI field."""

# Standard Tags / Tagging Policy
TAG_NAME = "Name"
"""Name tag key."""

TAG_CLIENT = "Client"
"""Client tag key."""

TAG_PORTFOLIO = "Portfolio"
"""Portfolio tag key."""

TAG_APP = "App"
"""App tag key."""

TAG_BRANCH = "Branch"
"""Branch tag key."""

TAG_BUILD = "Build"
"""Build tag key."""

TAG_SCOPE = "Scope"
"""Scope tag key."""

TAG_ENVIRONMENT = "Environment"
"""Environment tag key."""

TAG_COMPONENT = "Component"
"""Component tag key."""

TAG_ZONE = "Zone"
"""Zone tag key."""

TAG_REGION = "Region"
"""Region tag key."""

TAG_CAPEX_CODE = "CapexCode"
"""CAPEX code tag key."""

TAG_OPEX_CODE = "OpexCode"
"""OPEX code tag key."""

TAG_JIRA_CODE = "JiraCode"
"""JIRA code tag key."""

TAG_OWNER = "Owner"
"""Owner tag key."""

TAG_CONTACTS = "Contacts"
"""Contacts tag key."""

# Package Object
PKG_BUCKET_REGION = "BucketRegion"
"""Package bucket region field."""

PKG_BUCKET_NAME = "BucketName"
"""Package bucket name field."""

PKG_S3_KEY = "Key"
"""Package S3 key field."""

PKG_VERSION_ID = "VersionId"
"""Package version ID field."""

PKG_MODE = "Mode"
"""Package mode field."""

PKG_DATA_PATH = "DataPath"
"""Package data path field."""

PKG_COMPILE_MODE = "CompileMode"
"""Package compile mode field."""

PKG_DEPLOYSPEC = "DeploySpec"
"""Package deployspec field."""

PKG_TEMPDIR = "TempDir"
"""Package temporary directory field."""

# Deployspec Object
DS_LABEL = "label"
"""Deployspec label field."""

DS_TYPE = "type"
"""Deployspec type field."""

DS_PARAMS = "params"
"""Deployspec parameters field."""

DS_DEPENDS_ON = "depends_on"
"""Deployspec dependencies field."""

# Deployspec Types
DS_TYPE_AWS_CREATE_STACK = "aws.create_stack"
"""AWS create stack deployspec type."""

DS_TYPE_CREATE_STACK = "create_stack"
"""Create stack deployspec type."""

DS_TYPE_AWS_DELETE_STACK = "aws.delete_stack"
"""AWS delete stack deployspec type."""

DS_TYPE_DELETE_STACK = "delete_stack"
"""Delete stack deployspec type."""

DS_TYPE_AWS_DELETE_USER = "aws.delete_user"
"""AWS delete user deployspec type."""

DS_TYPE_DELETE_USER = "delete_user"
"""Delete user deployspec type."""

DS_TYPE_AWS_CREATE_USER = "aws.create_user"
"""AWS create user deployspec type."""

DS_TYPE_CREATE_USER = "create_user"
"""Create user deployspec type."""

# Deployspec Params Object
DSP_TEMPLATE = "template"
"""Deployspec template parameter."""

DSP_STACK_NAME = "stack_name"
"""Deployspec stack name parameter."""

DSP_PARAMETERS = "parameters"
"""Deployspec parameters field."""

DSP_ACCOUNT = "account"
"""Deployspec account parameter."""

DSP_ACCOUNTS = "accounts"
"""Deployspec accounts parameter."""

DSP_REGION = "region"
"""Deployspec region parameter."""

DSP_REGIONS = "regions"
"""Deployspec regions parameter."""

DSP_USER_NAME = "user_name"
"""Deployspec user name parameter."""

DSP_STACK_POLICY = "stack_policy"
"""Deployspec stack policy parameter."""

# Scopes
SCOPE_CLIENT = "client"
"""Client scope level."""

SCOPE_ZONE = "zone"
"""Zone scope level."""

SCOPE_PORTFOLIO = "portfolio"
"""Portfolio scope level."""

SCOPE_APP = "app"
"""App scope level."""

SCOPE_BRANCH = "branch"
"""Branch scope level."""

SCOPE_BUILD = "build"
"""Build scope level."""

SCOPE_COMPONENT = "component"
"""Component scope level."""

SCOPE_ENVIRONMENT = "environment"
"""Environment scope level."""

SCOPE_SHARED = "shared"
"""Shared scope level."""

SCOPE_RELEASE = "release"
"""Release scope level."""

# Object Types
OBJ_FILES = "files"
"""Files object type."""

OBJ_ARTEFACTS = "artefacts"
"""Artefacts object type."""

OBJ_PACKAGES = "packages"
"""Packages object type."""

# Task Results Object
TASK_RESULTS = "Results"
"""Task results field."""

# Task Result Object
TR_COMPILE_RESULTS = "CompileResults"
"""Task result compile results field."""

TR_STATUS = "Status"
"""Task result status field."""

TR_MESSAGE = "Message"
"""Task result message field."""

TR_DETAILS = "Details"
"""Task result details field."""

TR_ERRORS = "Errors"
"""Task result errors field."""

TR_WARNINGS = "Warnings"
"""Task result warnings field."""

TR_RESPONSE = "Response"
"""Task result response field."""

# Step Function Execution Object
SF_EXECUTION_ARN = "StepFunctionArn"
"""Step function execution ARN field."""

SF_INPUT = "Input"
"""Step function input field."""

# Environment Variables
ENV_AWS_PROFILE = "AWS_PROFILE"
"""AWS Profile environment variable."""

ENV_AWS_REGION = "AWS_REGION"
"""AWS Region environment variable."""

ENV_CLIENT = "CLIENT"
"""Client environment variable."""

ENV_CLIENT_NAME = "CLIENT_NAME"
"""Client name environment variable."""

ENV_CLIENT_REGION = "CLIENT_REGION"
"""Client region environment variable."""

ENV_SCOPE = "SCOPE"
"""Scope environment variable."""

ENV_PORTFOLIO = "PORTFOLIO"
"""Portfolio environment variable."""

ENV_APP = "APP"
"""App environment variable."""

ENV_BRANCH = "BRANCH"
"""Branch environment variable."""

ENV_BUILD = "BUILD"
"""Build environment variable."""

ENV_COMPONENT = "COMPONENT"
"""Component environment variable."""

ENV_ENVIRONMENT = "ENVIRONMENT"
"""Environment environment variable."""

ENV_TASKS = "TASKS"
"""Tasks environment variable."""

ENV_UNITS = "UNITS"
"""Units environment variable."""

ENV_ENFORCE_VALIDATION = "ENFORCE_VALIDATION"
"""Enforce validation environment variable."""

ENV_LOCAL_MODE = "LOCAL_MODE"
"""Local mode environment variable."""

ENV_API_HOST_URL = "API_HOST_URL"
"""API host URL environment variable."""

ENV_API_LAMBDA_ARN = "API_LAMBDA_ARN"
"""API Lambda ARN environment variable."""

ENV_API_LAMBDA_NAME = "API_LAMBDA_NAME"
"""API Lambda name environment variable."""

ENV_INVOKER_LAMBDA_ARN = "INVOKER_LAMBDA_ARN"
"""Invoker Lambda ARN environment variable."""

ENV_INVOKER_LAMBDA_NAME = "INVOKER_LAMBDA_NAME"
"""Invoker Lambda name environment variable."""

ENV_INVOKER_LAMBDA_REGION = "INVOKER_LAMBDA_REGION"
"""Invoker Lambda region environment variable."""

ENV_DYNAMODB_REGION = "DYNAMODB_REGION"
"""DynamoDB region environment variable."""

ENV_DYNAMODB_HOST = "DYNAMODB_HOST"
"""DynamoDB host environment variable."""

ENV_AUTOMATION_TYPE = "AUTOMATION_TYPE"
"""Automation type environment variable."""

ENV_BUCKET_NAME = "BUCKET_NAME"
"""Bucket name environment variable."""

ENV_BUCKET_REGION = "BUCKET_REGION"
"""Bucket region environment variable."""

ENV_EXECUTE_LAMBDA_ARN = "EXECUTE_LAMBDA_ARN"
"""Execute Lambda ARN environment variable."""

ENV_START_RUNNER_LAMBDA_ARN = "START_RUNNER_LAMBDA_ARN"
"""Start runner Lambda ARN environment variable."""

ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN = "DEPLOYSPEC_COMPILER_LAMBDA_ARN"
"""Deployspec compiler Lambda ARN environment variable."""

ENV_COMPONENT_COMPILER_LAMBDA_ARN = "COMPONENT_COMPILER_LAMBDA_ARN"
"""Component compiler Lambda ARN environment variable."""

ENV_MASTER_REGION = "MASTER_REGION"
"""Master region environment variable."""

ENV_CDK_DEFAULT_ACCOUNT = "CDK_DEFAULT_ACCOUNT"
"""CDK default account environment variable."""

ENV_CDK_DEFAULT_REGION = "CDK_DEFAULT_REGION"
"""CDK default region environment variable."""

ENV_ORGANIZATION_ACCOUNT = "ORGANIZATION_ACCOUNT"
"""Organization account environment variable."""

ENV_ORGANIZATION_EMAIL = "ORGANIZATION_EMAIL"
"""Organization email environment variable."""

ENV_ORGANIZATION_NAME = "ORGANIZATION_NAME"
"""Organization name environment variable."""

ENV_ORGANIZATION_ID = "ORGANIZATION_ID"
"""Organization ID environment variable."""

ENV_AUTOMATION_ACCOUNT = "AUTOMATION_ACCOUNT"
"""Automation account environment variable."""

ENV_AUTOMATION_REGION = "AUTOMATION_REGION"
"""Automation region environment variable."""

ENV_ARTEFACT_BUCKET_NAME = "ARTEFACT_BUCKET_NAME"
"""Artefact bucket name environment variable."""

ENV_LOG_AS_JSON = "LOG_AS_JSON"
"""Log as JSON environment variable."""

ENV_LOG_LEVEL = "LOG_LEVEL"
"""Log level environment variable."""

ENV_VOLUME = "VOLUME"
"""Volume environment variable."""

ENV_DELIVERED_BY = "DELIVERED_BY"
"""Delivered by environment variable."""

ENV_LOG_DIR = "LOG_DIR"
"""Log directory environment variable."""

ENV_USE_S3 = "USE_S3"
"""Use S3 environment variable."""

ENV_CORRELATION_ID = "CORRELATION_ID"
"""Correlation ID environment variable."""

ENV_IAM_ACCOUNT = "IAM_ACCOUNT"
"""IAM account environment variable."""

ENV_AUDIT_ACCOUNT = "AUDIT_ACCOUNT"
"""Audit account environment variable."""

ENV_SECURITY_ACCOUNT = "SECURITY_ACCOUNT"
"""Security account environment variable."""

ENV_NETWORK_ACCOUNT = "NETWORK_ACCOUNT"
"""Network account environment variable."""

ENV_DOMAIN = "DOMAIN"
"""Domain environment variable."""

ENV_DOCUMENT_BUCKET_NAME = "DOCUMENT_BUCKET_NAME"
"""Document bucket name environment variable."""

ENV_UI_BUCKET_NAME = "UI_BUCKET_NAME"
"""UI bucket name environment variable."""

ENV_CURRENT_ACCOUNT = "CURRENT_ACCOUNT"
"""Current account environment variable."""

ENV_PROJECT = "PROJECT"
"""Project environment variable."""

ENV_BIZAPP = "BIZAPP"
"""Business application environment variable."""

ENV_CONSOLE_LOG = "CONSOLE_LOG"
"""Console log environment variable."""

ENV_CONSOLE = "CONSOLE"
"""Console environment variable."""

ENV_AWS_ENDPOINT_URL = "AWS_ENDPOINT_URL"
"""AWS endpoint URL environment variable."""

# Jinja2 Context Filter Constants
CTX_TAGS = "tags"
"""Context tags field."""

CTX_APP = "app"
"""Context app field."""

CTX_CONTEXT = "context"
"""Context context field."""

CTX_VARS = "vars"
"""Context vars field."""

CTX_COMPONENT_NAME = "component_name"
"""Context component name field."""

CTX_FILES_BUCKET_URL = "FilesBucketUrl"
"""Context files bucket URL field."""

CTX_SHARED_FILES_PREFIX = "SharedFilesPrefix"
"""Context shared files prefix field."""

CTX_PORTFOLIO_FILES_PREFIX = "PortfolioFilesPrefix"
"""Context portfolio files prefix field."""

CTX_APP_FILES_PREFIX = "AppFilesPrefix"
"""Context app files prefix field."""

CTX_BRANCH_FILES_PREFIX = "BranchFilesPrefix"
"""Context branch files prefix field."""

CTX_BUILD_FILES_PREFIX = "BuildFilesPrefix"
"""Context build files prefix field."""

CTX_SNAPSHOT_ALIASES = "SnapshotAliases"
"""Context snapshot aliases field."""

CTX_ACCOUNT_ALIASES = "AccountAliases"
"""Context account aliases field."""

# Source Types for security rules
ST_CIDR = "cidr"
"""CIDR source type."""

ST_IP_ADDRESS = "ip"
"""IP address source type."""

ST_COMPONENT = "component"
"""Component source type."""

ST_PREFIX = "prefix"
"""Prefix source type."""

ST_SECURITY_GROUP = "sg-attachment"
"""Security group attachment source type."""

# Facts
FACTS_ACCOUNT = "AccountFacts"
"""Account facts field."""

FACTS_REGION = "RegionFacts"
"""Region facts field."""

FACTS_IMAGE = "ImageAliases"
"""Image aliases facts field."""

FACTS_TAGS = "Tags"
"""Tags facts field."""

FACTS_VPC = "VpcAliases"
"""VPC aliases facts field."""

FACTS_SUBNET = "SubnetAliases"
"""Subnet aliases facts field."""

FACTS_ENVIRONMENT = "Environment"
"""Environment facts field."""

FACTS_SECURITY = "SecurityAliases"
"""Security aliases facts field."""

FACTS_SECURITY_GROUP = "SecurityGroupAliases"
"""Security group aliases facts field."""

# Core Automation Roles
CORE_AUTOMATION_ADMIN_ROLE = "Administrator"
"""Core automation administrator role."""

CORE_AUTOMATION_API_WRITE_ROLE = "CoreAutomationApiWrite"
"""Core automation API write role."""

CORE_AUTOMATION_API_READ_ROLE = "CoreAutomationApiRead"
"""Core automation API read role."""

CORE_AUTOMATION_DEPLOYMENT_WRITE_ROLE = "CoreAutomationDeploymentWrite"
"""Core automation deployment write role."""

CORE_AUTOMATION_DEPLOYMENT_READ_ROLE = "CoreAutomationDeploymentRead"
"""Core automation deployment read role."""

CORE_AUTOMATION_SESSION_ID_PREFIX = "Pipeline"
"""Core automation session ID prefix."""

CORE_AUTOMATION_PIPELINE_PROVISIONING_ROLE = "PipelineProvisioning"
"""Core automation pipeline provisioning role."""

# Properties (snake_case for CLI and API)
P_AWS_PROFILE = "aws_profile"
"""AWS profile property."""

P_AWS_REGION = "aws_region"
"""AWS region property."""

P_SCOPE = "scope"
"""Scope property."""

P_CLIENT = "client"
"""Client property."""

P_CLIENT_NAME = "client_name"
"""Client name property."""

P_DOMAIN = "domain"
"""Domain property."""

P_CLIENT_REGION = "client_region"
"""Client region property."""

P_ORGANIZATION_ID = "organization_id"
"""Organization ID property."""

P_USERNAME = "username"
"""Username property."""

P_CURRENT_ACCOUNT = "current_account"
"""Current account property."""

P_CDK_DEFAULT_ACCOUNT = "cdk_default_account"
"""CDK default account property."""

P_CDK_DEFAULT_REGION = "cdk_default_region"
"""CDK default region property."""

P_IAM_ACCOUNT = "iam_account"
"""IAM account property."""

P_AUTOMATION_ACCOUNT = "automation_account"
"""Automation account property."""

P_SECURITY_ACCOUNT = "security_account"
"""Security account property."""

P_AUDIT_ACCOUNT = "audit_account"
"""Audit account property."""

P_NETWORK_ACCOUNT = "network_account"
"""Network account property."""

P_IDENTITY = "identity"
"""Identity property."""

P_CREDENTIALS = "credentials"
"""Credentials property."""

P_REGION = "region"
"""Region property."""

P_MASTER_REGION = "master_region"
"""Master region property."""

P_DOCUMENT_BUCKET_NAME = "docs_bucket_name"
"""Document bucket name property."""

P_UI_BUCKET_NAME = "ui_bucket_name"
"""UI bucket name property."""

P_ARTEFACT_BUCKET_NAME = "artefact_bucket_name"
"""Artefact bucket name property."""

P_BUCKET_NAME = "bucket_name"
"""Bucket name property."""

P_BUCKET_REGION = "bucket_region"
"""Bucket region property."""

P_TEMPLATE = "template"
"""Template property."""

P_STACK_NAME = "stack_name"
"""Stack name property."""

P_STACK_PARAMETERS = "stack_parameters"
"""Stack parameters property."""

P_ORGANIZATION_NAME = "organization_name"
"""Organization name property."""

P_ORGANIZATION_EMAIL = "organization_email"
"""Organization email property."""

P_ORGANIZATION_ACCOUNT = "organization_account"
"""Organization account property."""

P_AUTOMATION_TYPE = "automation_type"
"""Automation type property."""

P_TASKS = "tasks"
"""Tasks property."""

P_UNITS = "units"
"""Units property."""

P_PORTFOLIO = "portfolio"
"""Portfolio property."""

P_APP = "app"
"""App property."""

P_BRANCH = "branch"
"""Branch property."""

P_BUILD = "build"
"""Build property."""

P_COMPONENT = "component"
"""Component property."""

P_ENVIRONMENT = "environment"
"""Environment property."""

P_DYNAMODB_HOST = "dynamodb_host"
"""DynamoDB host property."""

P_DYNAMODB_REGION = "dynamodb_region"
"""DynamoDB region property."""

P_LOG_AS_JSON = "log_as_json"
"""Log as JSON property."""

P_VOLUME = "volume"
"""Volume property."""

P_LOG_DIR = "log_dir"
"""Log directory property."""

P_DELIVERED_BY = "delivered_by"
"""Delivered by property."""

P_LOCAL_MODE = "local_mode"
"""Local mode property."""

P_USE_S3 = "use_s3"
"""Use S3 property."""

P_ENFORCE_VALIDATION = "enforce_validation"
"""Enforce validation property."""

P_INVOKER_ARN = "invoker_arn"
"""Invoker ARN property."""

P_INVOKER_NAME = "invoker_name"
"""Invoker name property."""

P_INVOKER_REGION = "invoker_region"
"""Invoker region property."""

P_API_LAMBDA_ARN = "api_lambda_arn"
"""API Lambda ARN property."""

P_API_LAMBDA_NAME = "api_lambda_name"
"""API Lambda name property."""

P_API_HOST_URL = "api_host_url"
"""API host URL property."""

P_EXECUTE_LAMBDA_ARN = "execute_lambda_arn"
"""Execute Lambda ARN property."""

P_START_RUNNER_LAMBDA_ARN = "start_runner_lambda_arn"
"""Start runner Lambda ARN property."""

P_DEPLOYSPEC_COMPILER_LAMBDA_ARN = "deployspec_compiler_lambda_arn"
"""Deployspec compiler Lambda ARN property."""

P_COMPONENT_COMPILER_LAMBDA_ARN = "component_compiler_lambda_arn"
"""Component compiler Lambda ARN property."""

P_START_RUNNER_STEP_FUNCTION_ARN = "runner_step_function_arn"
"""Start runner Step Function ARN property."""

P_TAGS = "tags"
"""Tags property."""

P_CORRELATION_ID = "correlation_id"
"""Correlation ID property."""

P_PROJECT = "project"
"""Project property."""

P_BIZAPP = "bizapp"
"""Business application property."""

P_PRN = "prn"
"""PRN property."""

P_CONSOLE_LOG = "console_log"
"""Console log property."""

P_CONSOLE = "console"
"""Console property."""

P_LOG_LEVEL = "log_level"
"""Log level property."""

P_CLIENT_TABLE_NAME = "clients_table_name"
"""Client table name property - {scope}core-automation-clients.

Global table.  Does not include {client} name in scope.
"""

P_PORTFOLIOS_TABLE_NAME = "portfolios_table_name"
"""Portfolios table name property - {scope}{client}-core-automation-portfolios."""

P_APPS_TABLE_NAME = "apps_table_name"
"""Apps table name property - {scope}{client}-core-automation-apps."""

P_ZONES_TABLE_NAME = "zones_table_name"
"""Zones table name property - {scope}{client}-core-automation-zones."""

P_ITEMS_TABLE_NAME = "items_table_name"
"""Items table name property - {scope}{client}-core-automation-items."""

P_EVENTS_TABLE_NAME = "events_table_name"
"""Events table name property - {scope}{client}-core-automation-events."""
