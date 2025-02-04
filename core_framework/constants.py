"""
This module provides a list of constants that are used throughout the Core-Automation framework.

The constants prevent mistyping and provide a single source of truth for the values used in the framework.

This includes values for the Task Payload, Task Results, Task Result, and other objects used in the framework.

"""

# Good to go
HTTP_OK = 200
""" \\- "200 OK" """
HTTP_CREATED = 201
""" \\- "201 Created" " """
HTTP_ACCEPTED = 202
""" \\- "202 Accepted" " """
HTTP_NO_CONTENT = 204
""" \\- "204 No Content" """

# Bad to go
HTTP_BAD_REQUEST = 400
""" \\- "400 Bad Request" """
HTTP_UNAUTHORIZED = 401
""" \\- "401 Unauthorized" """
HTTP_PAYMENT_REQUIRED = 402
""" \\- "402 Payment Required" """
HTTP_FORBIDDEN = 403
""" \\- "403 Forbidden" """
HTTP_NOT_FOUND = 404
""" \\- "404 Not Found" """
HTTP_METHOD_NOT_ALLOWED = 405
""" \\- "405 Method Not Allowed" """
HTTP_NOT_ACCEPTABLE = 406
""" \\- "406 Not Acceptable" """
HTTP_PROXY_AUTHENTICATION_REQUIRED = 407
""" \\- "407 Proxy Authentication Required" """
HTTP_REQUEST_TIMEOUT = 408
""" \\- "408 Request Timeout" """
HTTP_CONFLICT = 409
""" \\- "409 Conflict" """

# Can't process data
HTTP_UNPROCESSABLE_ENTITY = 422
""" \\- "422 Unprocessable Entity" """

# Server Error
HTTP_INTERNAL_SERVER_ERROR = 500
""" \\- "500 Internal Server Error" """
HTTP_NOT_IMPLEMENTED = 501
""" \\- "501 Not Implemented" """

# Task Types
TASK_PACKAGE = "package"
""" \\- "package" """
TASK_UPLOAD = "upload"
""" \\- "upload" """
TASK_COMPILE = "compile"
""" \\- "compile" """
TASK_DEPLOY = "deploy"
""" \\- "deploy" """
TASK_PLAN = "plan"
""" \\- "plan" """
TASK_APPLY = "apply"
""" \\- "apply" """
TASK_RELEASE = "release"
""" \\- "release" """
TASK_TEARDOWN = "teardown"
""" \\- "teardown" """

# Feild values
V_CORE_AUTOMATION = "core-automation"
""" \\- "core-automation" """
V_PACKAGE_ZIP = "package.zip"
""" \\- "package.zip" """
V_PACKAGE_TAR = "package.tar"
""" \\- "package.tar" """
V_PIPELINE = "pipeline"
""" \\- "pipeline" """
V_DEPLOYSPEC = "deployspec"
""" \\- "deployspec" """
V_PLANSPEC = "planspec"
""" \\- "planspec" """
V_APPLYSPEC = "applyspec"
""" \\- "applyspec" """
V_TEARDOWNSPEC = "teardownspec"
""" \\- "teardownspec" """
V_DEPLOYSPEC_FILE_YAML = "deployspec.yaml"
""" \\- "deployspec.yaml" """
V_PLANSPEC_FILE_YAML = "planspec.yaml"
""" \\- "planspec.yaml" """
V_APPLYSPEC_FILE_YAML = "applyspec.yaml"
""" \\- "applyspec.yaml" """
V_DEPLOYSPEC_FILE_JSON = "deployspec.json"
""" \\- "deployspec.json" """
V_PLANSPEC_FILE_JSON = "planspec.json"
""" \\- "planspec.json" """
V_APPLYSPEC_FILE_JSON = "applyspec.json"
""" \\- "applyspec.json" """
V_TEARDOWNSPEC_FILE_YAML = "teardownspec.yaml"
""" \\- "teardownspec.yaml" """
V_TEARDOWNSPEC_FILE_JSON = "teardownspec.json"
""" \\- "teardownspec.json" """
V_LAMBDA_MODULES_FILE = "lambda_modules.txt"
""" \\- "lambda_modules.txt" """
V_SERVICE = "service"
""" \\- "service" """
V_LOCAL = "local"
""" \\- "local" """
V_FULL = "full"
""" \\- "full" """
V_PLATFORM = "platform"
""" \\- "platform" """
V_CREATE_STACK = "create_stack"
""" \\- "create_stack" """
V_DEFAULT_REGION = "us-east-1"
""" \\- "ap-southeast-1" """
V_DEFAULT_REGION_NAME = "US East (N. Virginia)"
""" \\- "Singapore" """
V_DEFAULT_REGION_ALIAS = "use"
""" \\- "sin" """
V_DEFAULT_BRANCH = "master"
""" \\- "master" """
V_DEFAULT_ENVIRONMENT = "prod"
""" \\- "prod" """
V_TRUE = "true"
""" \\- "true" """
V_FALSE = "false"
""" \\- "false" """
V_EMPTY = ""
""" \\- "" """

# Authorization Context Object
AUTH_CREDENTIALS = "Credentials"
""" \\- "Credentials" """
AUTH_ROLE = "Role"
""" \\- "Role" """
AUTH_ACCOUNT = "Account"
""" \\- "Account" """
AUTH_USER = "User"
""" \\- "User" """
AUTH_ACCESS_KEY = "AccessKey"
""" \\- "AccessKey" """
AUTH_SECRET_KEY = "SecretKey"
""" \\- "SecretKey" """
AUTH_TOKEN = "Token"
""" \\- "Token" """
AUTH_ACCESS_KEY_ID = "AccessKeyId"
""" \\- "AccessKeyId" """
AUTH_SECRET_ACCESS_KEY = "SecretAccessKey"
""" \\- "SecretAccessKey" """
AUTH_SESSION_TOKEN = "SessionToken"
""" \\- "SessionToken" """

# Account object in Authorization Context
ACCOUNT_ID = "Id"
""" \\- "Id" """
ACCOUNT_REGION = "Region"
""" \\- "Region" """
ACCOUNT_USER_ARN = "UserArn"
""" \\- "UserArn" """
ACCOUNT_USER_ID = "UserId"
""" \\- "UserId" """

# Task Payload Object
TP_TASK = "Task"
""" \\- "Task" """
TP_FORCE = "Force"
""" \\- "Force" """
TP_DRY_RUN = "DryRun"
""" \\- "DryRun" """
TP_IDENTITY = "Identity"
""" \\- "Identity" """
TP_TYPE = "Type"
""" \\- "Type" """
TP_DEPLOYMENT_DETAILS = "DeploymentDetails"
""" \\- "DeploymentDetails" """
TP_PACKAGE_DETAILS = "Package"
""" \\- "Package" """
TP_FACTS = "Facts"
""" \\- "Facts" """
TP_ACTIONS = "Actions"
""" \\- "Actions" """
TP_DEPLOY_ACTIONS = "DeployActions"
""" \\- "DeployActions" """
TP_STATE = "State"
""" \\- "State" """
TP_FLOW_CONTROL = "FlowControl"
""" \\- "FlowControl" """

# TP_ACTIONS/TP_STATE Actions Object Attributes
ACT_VERSION = "VersionId"
""" \\- "VersionId" """
ACT_BUCKETNAME = "BucketName"
""" \\- "BucketName" """
ACT_BUCKET_REGION = "BucketRegion"
""" \\- "BucketRegion" """
ACT_KEY = "Key"
""" \\- "Key" """
ACT_MIME_TYPE = "ContentType"
""" \\- "ContentType" """

# Deployment Details object
DD_CLIENT = "Client"
""" \\- "Client" """
DD_APP = "App"
""" \\- "App" """
DD_PORTFOLIO = "Portfolio"
""" \\- "Portfolio" """
DD_BRANCH = "Branch"
""" \\- "Branch" """
DD_BRANCH_SHORT_NAME = "BranchShortName"
""" \\- "BranchShortName" """
DD_BUILD = "Build"
""" \\- "Build" """
DD_COMPONENT = "Component"
""" \\- "Component" """
DD_ENVIRONMENT = "Environment"
""" \\- "Environment" """
DD_DATA_CENTER = "DataCenter"
""" \\- "DataCenter" """
DD_SCOPE = "Scope"
""" \\- "Scope" """
DD_ECR = "Ecr"  # ECR object for docker containers
""" \\- "Ecr" """
DD_TAGS = "Tags"  # A place to hold tags for the deployment
""" \\- "Tags" """

# Docker Image
ECR_REGISTRY_URI = "RegistryUri"
""" \\- "RegistryUri" """

# Standard Tags / Tagging Policy
TAG_NAME = "Name"  # This is actually the PRN or component name with PRN prefix
""" \\- "Name" """
TAG_CLIENT = "Client"
""" \\- "Client" """
TAG_PORTFOLIO = "Portfolio"
""" \\- "Portfolio" """
TAG_APP = "App"
""" \\- "App" """
TAG_BRANCH = "Branch"
""" \\- "Branch" """
TAG_BUILD = "Build"
""" \\- "Build" """
TAG_SCOPE = "Scope"
""" \\- "Scope" """

# Prod/NotProd/Dev/UAT1/UAT2 (a.k.a. Zone or Data Center)
TAG_ENVIRONMENT = "Environment"
""" \\- "Environment" """

TAG_COMPONENT = "Component"
""" \\- "Component" """
TAG_ZONE = "Zone"
""" \\- "Zone" """
TAG_REGION = "Region"
""" \\- "Region" """
TAG_CAPEX_CODE = "CapexCode"
""" \\- "CapexCode" """
TAG_OPEX_CODE = "OpexCode"
""" \\- "OpexCode" """
TAG_JIRA_CODE = "JiraCode"
""" \\- "JiraCode" """
TAG_OWNER = "Owner"
""" \\- "Owner" """
TAG_CONTACTS = "Contacts"
""" \\- "Contacts" """

# Package Object
PKG_BUCKET_REGION = "BucketRegion"
""" \\- "BucketRegion" """
PKG_BUCKET_NAME = "BucketName"
""" \\- "BucketName" """
PKG_S3_KEY = "Key"
""" \\- "Key" """
PKG_VERSION_ID = "VersionId"
""" \\- "VersionId" """
PKG_MODE = "Mode"
""" \\- "Mode" """
PKG_DATA_PATH = "DataPath"
""" \\- "DataPath" """
PKG_COMPILE_MODE = "CompileMode"
""" \\- "CompileMode" """
PKG_DEPLOYSPEC = "DeploySpec"
""" \\- "DeploySpec" """
PKG_TEMPDIR = "TempDir"
""" \\- "TempDir" """


# Deployspec Object
DS_LABEL = "label"
""" \\- "label" """
DS_TYPE = "type"
""" \\- "type" """
DS_PARAMS = "params"
""" \\- "params" """
# array of DS_LABEL (only useful in deployspec with more than one deployment)
DS_DEPENDS_ON = "depends_on"
""" \\- "depends_on" """

# Deployspec Types
DS_TYPE_AWS_CREATE_STACK = "aws.create_stack"
""" \\- "aws.create_stack" """
DS_TYPE_CREATE_STACK = "create_stack"
""" \\- "create_stack" """
DS_TYPE_AWS_DELETE_STACK = "aws.delete_stack"
""" \\- "aws.delete_stack" """
DS_TYPE_DELETE_STACK = "delete_stack"
""" \\- "delete_stack" """
DS_TYPE_AWS_DELETE_USER = "aws.delete_user"
""" \\- "aws.delete_user" """
DS_TYPE_DELETE_USER = "delete_user"
""" \\- "delete_user" """
DS_TYPE_AWS_CREATE_USER = "aws.create_user"
""" \\- "aws.create_user" """
DS_TYPE_CREATE_USER = "create_user"
""" \\- "create_user" """

# Deployspec Params Object
DSP_TEMPLATE = "template"
""" \\- "template" """
DSP_STACK_NAME = "stack_name"
""" \\- "stack_name" """
DSP_PARAMETERS = "parameters"
""" \\- "parameters" """
DSP_ACCOUNT = "account"
""" \\- "account" """
DSP_ACCOUNTS = "accounts"
""" \\- "accounts" """
DSP_REGION = "region"
""" \\- "region" """
DSP_REGIONS = "regions"
""" \\- "regions" """
DSP_USER_NAME = "user_name"
""" \\- "user_name" """
DSP_STACK_POLICY = "stack_policy"
""" \\- "stack_policy" """

# Scopes
SCOPE_CLIENT = "client"
""" \\- "client" """
SCOPE_ZONE = "zone"
""" \\- "zone" """
SCOPE_PORTFOLIO = "portfolio"
""" \\- "portfolio" """
SCOPE_APP = "app"
""" \\- "app" """
SCOPE_BRANCH = "branch"
""" \\- "branch" """
SCOPE_BUILD = "build"
""" \\- "build" """
SCOPE_COMPONENT = "component"
""" \\- "component" """
SCOPE_ENVIRONMENT = "environment"
""" \\- "environment" """
SCOPE_SHARED = "shared"
""" \\- "shared" """
SCOPE_RELEASE = "release"
""" \\- "release" """

# Object Types
OBJ_FILES = "files"
""" \\- "files" """
OBJ_ARTEFACTS = "artefacts"
""" \\- " artefacts " """
OBJ_PACKAGES = "packages"
""" \\- "packages" """

# Task Results Object
TASK_RESULTS = "Results"
""" \\- "Results" """

# Task Result Object
TR_COMPILE_RESULTS = "CompileResults"
""" \\- "CompileResults" """
TR_STATUS = "Status"
""" \\- "Status" """
TR_MESSAGE = "Message"
""" \\- "Message" """
TR_DETAILS = "Details"
""" \\- "Details" """
TR_ERRORS = "Errors"
""" \\- "Errors" """
TR_WARNINGS = "Warnings"
""" \\- "Warnings" """
TR_RESPONSE = "Response"
""" \\- "Response" """

# Step Function Execution Object
SF_EXECUTION_ARN = "StepFunctionArn"
""" \\- "StepFunctionArn" """
SF_INPUT = "Input"
""" \\- "Input" """

# Environment Variables
ENV_AWS_PROFILE = "AWS_PROFILE"
""" \\- "AWS_PROFILE". AWS Profile to use for UI and Commandline """
ENV_AWS_REGION = "AWS_REGION"
""" \\- "AWS_REGION". Master Region where the automation is running """
ENV_CLIENT = "CLIENT"
""" \\- "CLIENT".  The slug for the AWS orgnization """
ENV_CLIENT_NAME = "CLIENT_NAME"
""" \\- "CLIENT_NAME". The full name of the AWS orgnization """
ENV_CLIENT_REGION = "CLIENT_REGION"
""" \\- "CLIENT_REGION". The primary or default region for this AWS Organization (i.e. Client) """
ENV_SCOPE = "SCOPE"
""" \\- "SCOPE". Prefix or 'scope' of the core automation installation in the AWS Organization """
ENV_PORTFOLIO = "PORTFOLIO"
""" \\- "PORTFOLIO".  The portfolio name. Equal to the -p or --portfolio flag """
ENV_APP = "APP"
""" \\- "APP". The deployment app name. Equal to the -a or --app flag """
ENV_BRANCH = "BRANCH"
""" \\- "BRANCH". The app repository branch name. Equal to the -b or --branch flag """
ENV_BUILD = "BUILD"
""" \\- "BUILD". The build number, app version, or git commit hash. Equal to the -n or --build flag """
ENV_COMPONENT = "COMPONENT"
""" \\- "COMPONENT". The name of the component being deployed """
ENV_ENVIRONMENT = "ENVIRONMENT"
""" \\- "ENVIRONMENT". The environment being deployed to. Example: prod, dev, uat1, uat2. """
ENV_TASKS = "TASKS"
""" \\- "TASKS". Default tasks to perform on the CLI.  Tasks are separated by a comma. Values:  upload, compile, deploy, plan, apply, release, teardown """
ENV_UNITS = "UNITS"
""" \\- "UNITS". The default list of core automation deployment units to update in the CLI.  Default is 'all' """
ENV_ENFORCE_VALIDATION = "ENFORCE_VALIDATION"
""" \\- "ENFORCE_VALIDATION" """
ENV_LOCAL_MODE = "LOCAL_MODE"
""" \\- "LOCAL_MODE".  Run the automation in local mode.  Default is 'false'.  Supports container operation. No Lambda, No S3."""
ENV_API_HOST_URL = "API_HOST_URL"
""" \\- "API_HOST_URL". The URL of the API Gateway """
ENV_API_LAMBDA_ARN = "API_LAMBDA_ARN"
""" \\- "API_LAMBDA_ARN".  The ARN of the API Lambda function.  Used for the FastAPI server or the AWS API Gateway """
ENV_API_LAMBDA_NAME = "API_LAMBDA_NAME"
""" \\- "API_LAMBDA_NAME".  The Name of the Lambda function. Used for the AWS API Gateway deployment """
ENV_INVOKER_LAMBDA_ARN = "INVOKER_LAMBDA_ARN"
""" \\- "INVOKER_LAMBDA_ARN". The ARN of the Invoker Lambda function.  The Invoker ensures security and RBAC controls """
ENV_INVOKER_LAMBDA_NAME = "INVOKER_LAMBDA_NAME"
""" \\- "INVOKER_LAMBDA_NAME". The Name of the Invoker Lambda function. Called by the API Lambda """
ENV_INVOKER_LAMBDA_REGION = "INVOKER_LAMBDA_REGION"
""" \\- "INVOKER_LAMBDA_REGION". The Region of the Invoker Lambda function """
ENV_DYNAMODB_REGION = "DYNAMODB_REGION"
""" \\- "DYNAMODB_REGION". The Region of the DynamoDB service. """
ENV_DYNAMODB_HOST = "DYNAMODB_HOST"
""" \\- "DYNAMODB_HOST". THe URL of the DynamoDB service.  (Endpoint Service) """
ENV_AUTOMATION_TYPE = "AUTOMATION_TYPE"
""" \\- "AUTOMATION_TYPE". The type of automation being run.  Values:  pipeline, deployspec """
ENV_BUCKET_NAME = "BUCKET_NAME"
""" \\- "BUCKET_NAME". The name of the bucket to use for the automation artefacts """
ENV_BUCKET_REGION = "BUCKET_REGION"
""" \\- "BUCKET_REGION". The bucket region to use for the automation artefacts """
ENV_EXECUTE_LAMBDA_ARN = "EXECUTE_LAMBDA_ARN"
""" \\- "EXECUTE_LAMBDA_ARN". The ARN of the Core Execute Engine Lambda Step Function """
ENV_START_RUNNER_LAMBDA_ARN = "START_RUNNER_LAMBDA_ARN"
""" \\- "RUNNER_LAMBDA_ARN". The ARN of the Step Function Runner Lambda (function that runs the Step Function) """
ENV_DEPLOYSPEC_COMPILER_LAMBDA_ARN = "DEPLOYSPEC_COMPILER_LAMBDA_ARN"
""" \\- "DEPLOYSPEC_COMPILER_LAMBDA_ARN".  The ARN of the Deployspec Compiler Lambda """
ENV_COMPONENT_COMPILER_LAMBDA_ARN = "COMPONENT_COMPILER_LAMBDA_ARN"
""" \\- "COMPONENT_COMPILER_LAMBDA_ARN". The ARN of the Component Compiler Lambda """
ENV_RUNNER_STEP_FUNCTION_ARN = "RUNNER_STEP_FUNCTION_ARN"
""" \\- "RUNNER_STEP_FUNCTION_ARN". The ARN of the Step Function Runner """
ENV_MASTER_REGION = "MASTER_REGION"
""" \\- "MASTER_REGION". The master region for the Core automation services. """
ENV_CDK_DEFAULT_ACCOUNT = "CDK_DEFAULT_ACCOUNT"
""" \\- "CDK_DEFAULT_ACCOUNT". The default AWS Account ID for the CDK """
ENV_CDK_DEFAULT_REGION = "CDK_DEFAULT_REGION"
""" \\- "CDK_DEFAULT_REGION". The default AWS Region for the CDK """
ENV_ORGANIZATION_ACCOUNT = "ORGANIZATION_ACCOUNT"
""" \\- "ORGANIZATION_ACCOUNT". The AWS Account ID of the AWS Organization """
ENV_ORGANIZATION_EMAIL = "ORGANIZATION_EMAIL"
""" \\- "ORGANIZATION_EMAIL". The email address of the AWS Organization """
ENV_ORGANIZATION_NAME = "ORGANIZATION_NAME"
""" \\- "ORGANIZATION_NAME". The name of the AWS Organization """
ENV_ORGANIZATION_ID = "ORGANIZATION_ID"
""" \\- "ORGANIZATION_ID". The AWS Organization ID """
ENV_AUTOMATION_ACCOUNT = "AUTOMATION_ACCOUNT"
""" \\- "AUTOMATION_ACCOUNT". The AWS Account ID where the Core Automation services are deployed"""
ENV_AUTOMATION_REGION = "AUTOMATION_REGION"
""" \\- "AUTOMATION_REGION". The AWS Region where the Core Automation services are deployed """
ENV_ARTEFACT_BUCKET_NAME = "ARTEFACT_BUCKET_NAME"
""" \\- "ARTEFACT_BUCKET_NAME".  The name of the artefact bucket if different than the BUCKET_NAME """
ENV_LOG_AS_JSON = "LOG_AS_JSON"
""" \\- "LOG_AS_JSON". If set to True, the log output will be in JSON format """
ENV_VOLUME = "VOLUME"
""" \\- "VOLUME". If LOCAL_MODE=true, the VOLUME is where artefacts are stored.  Defaults to f"{os.getcwd()}/local" """
ENV_DELIVERED_BY = "DELIVERED_BY"
""" \\- "DELIVERED_BY". The name of the person, team, or system that ran a Task.  Defaults to 'automation'. """
ENV_LOG_DIR = "LOG_DIR"
""" \\- "LOG_DIR". if LOCAL_MODE=true, the LOG_DIR is where logs are stored.  Defaults to f"{os.getcwd()}/local/logs" """
ENV_USE_S3 = "USE_S3"
""" \\- "USE_S3". If set to True, the automation will use S3 for artefacts.  Defaults to "not LOCAL_MODE" """
ENV_CORRELATION_ID = "CORRELATION_ID"
""" \\- "CORRELATION_ID". The unique ID for the automation run.  Used for tracking and logging """
ENV_IAM_ACCOUNT = "IAM_ACCOUNT"
""" \\- "IAM_ACCOUNT". The AWS Account ID where the IAM logs are stored """
ENV_AUDIT_ACCOUNT = "AUDIT_ACCOUNT"
""" \\- "AUDIT_ACCOUNT". The AWS Account ID where the audit logs are stored """
ENV_SECURITY_ACCOUNT = "SECURITY_ACCOUNT"
""" \\- "SECURITY_ACCOUNT". The AWS Account ID where the security logs are stored """
ENV_NETWORK_ACCOUNT = "NETWORK_ACCOUNT"
""" \\- "NETWORK_ACCOUNT". The AWS Account ID where the network logs are stored """
ENV_DOMAIN = "DOMAIN"
""" \\- "DOMAIN". The domain name for the AWS Organization """
ENV_DOCUMENT_BUCKET_NAME = "DOCUMENT_BUCKET_NAME"
""" \\- "DOCUMENT_BUCKET_NAME". The name of the bucket where documents are stored """
ENV_UI_BUCKET_NAME = "UI_BUCKET_NAME"
""" \\- "UI_BUCKET_NAME". The name of the bucket where the UI is stored """
ENV_CURRENT_ACCOUNT = "CURRENT_ACCOUNT"
""" \\- "CURRENT_ACCOUNT". The AWS Account ID of the account running the automation """
ENV_CDK_DEFAULT_ACCOUNT = "CDK_DEFAULT_ACCOUNT"
""" \\- "CDK_DEFAULT_ACCOUNT". The default AWS Account ID for the CDK """
ENV_CDK_DEFAULT_REGION = "CDK_DEFAULT_REGION"
""" \\- "CDK_DEFAULT_REGION". The default AWS Region for the CDK """

# Jina2 Context Fitler Constants
CTX_TAGS = "tags"
""" \\- "tags" """
CTX_APP = "app"
""" \\- "app" """
CTX_CONTEXT = "context"
""" \\- "context" """
CTX_VARS = "vars"
""" \\- "vars" """
CTX_COMPONENT_NAME = "component_name"
""" \\- "component_name" """
CTX_FILES_BUCKET_URL = "FilesBucketUrl"
""" \\- "FilesBucketUrl" """
CTX_SHARED_FILES_PREFIX = "SharedFilesPrefix"
""" \\- "SharedFilesPrefix" """
CTX_PORTFOLIO_FILES_PREFIX = "PortfolioFilesPrefix"
""" \\- "PortfolioFilesPrefix" """
CTX_APP_FILES_PREFIX = "AppFilesPrefix"
""" \\- "AppFilesPrefix" """
CTX_BRANCH_FILES_PREFIX = "BranchFilesPrefix"
""" \\- "BranchFilesPrefix" """
CTX_BUILD_FILES_PREFIX = "BuildFilesPrefix"
""" \\- "BuildFilesPrefix" """
CTX_SNAPSHOT_ALIASES = "SnapshotAliases"
""" \\- "SnapshotAliases" """
CTX_ACCOUNT_ALIASES = "AccountAliases"
""" \\- "AccountAliases" """

# Source Types for security rules
ST_CIDR = "cidr"
""" \\- "cidr" """
ST_IP_ADDRESS = "ip"
""" \\- "ip" """
ST_COMPONENT = "component"
""" \\- "component" """
ST_PREFIX = "prefix"
""" \\- "prefix" """
ST_SECURITY_GROUP = "sg-attachment"
""" \\- "sg-attachment" """

# Facts
FACTS_ACCOUNT = "AccountFacts"
""" \\- "AccountFacts" """
FACTS_REGION = "RegionFacts"
""" \\- "RegionFacts" """
FACTS_IMAGE = "ImageAliases"
""" \\- "ImageAliases" """
FACTS_TAGS = "Tags"
""" \\- "Tags" """
FACTS_VPC = "VpcAliases"
""" \\- "VpcAliases" """
FACTS_SUBNET = "SubnetAliases"
""" \\- "SubnetAliases" """
FACTS_ENVIRONMENT = "Environment"
""" \\- "Environment" """
FACTS_SECURITY = "SecurityAliases"
""" \\- "SecurityAliases" """
FACTS_SECURITY_GROUP = "SecurityGroupAliases"
""" \\- "SecurityGroupAliases" """

# In Development
CORE_AUTOMATION_ADMIN_ROLE = "Administrator"
""" \\- "Administrator" """
CORE_AUTOMATION_API_WRITE_ROLE = "CoreAutomationApiWrite"
""" \\- "CoreAutomationApiWrite" """
CORE_AUTOMATION_API_READ_ROLE = "CoreAutomationApiRead"
""" \\- "CoreAutomationApiRead" """
CORE_AUTOMATION_DEPLOYMENT_WRITE_ROLE = "CoreAutomationDeploymentWrite"
""" \\- "CoreAutomationDeploymentWrite" """
CORE_AUTOMATION_DEPLOYMENT_READ_ROLE = "CoreAutomationDeploymentRead"
""" \\- "CoreAutomationDeploymentRead" """
CORE_AUTOMATION_SESSION_ID_PREFIX = "Pipeline"
""" \\- "Pipeline" """
CORE_AUTOMATION_PIPELINE_PROVISIONING_ROLE = "PipelineProvisioning"
""" \\- "PipelineProvisioning" """

# Properties in snake-case. Also used in argparse "dest" parameter.
# Used as snake_case function paramter names (especially in **kwargs)
P_AWS_PROFILE = "aws_profile"
""" \\- "aws_profile" """
P_AWS_REGION = "aws_region"
""" \\- "aws_region" """
P_SCOPE = "scope"
""" \\- "scope" """
P_CLIENT = "client"
""" \\- "client" """
P_CLIENT_NAME = "client_name"
""" \\- "client_name" """
P_DOMAIN = "domain"
""" \\- "domain" """
P_CLIENT_REGION = "client_region"
""" \\- "client_region" """
P_ORGANIZATION_ID = "organization_id"
""" \\- "organization_id" """
P_USERNAME = "username"
""" \\- "username" """
P_CURRENT_ACCOUNT = "current_account"
""" \\- "current_account" """
P_CDK_DEFAULT_ACCOUNT = "cdk_default_account"
""" \\- "cdk_default_account" """
P_CDK_DEFAULT_REGION = "cdk_default_region"
""" \\- "cdk_default_region" """
P_IAM_ACCOUNT = "iam_account"
""" \\- "iam_account" """
P_AUTOMATION_ACCOUNT = "automation_account"
""" \\- "automation_account" """
P_SECURITY_ACCOUNT = "security_account"
""" \\- "security_account" """
P_AUDIT_ACCOUNT = "audit_account"
""" \\- "audit_account" """
P_NETWORK_ACCOUNT = "network_account"
""" \\- "network_account" """
P_IDENTITY = "identity"
""" \\- "identity" """
P_CREDENTIALS = "credentials"
""" \\- "credentials" """
P_REGION = "region"
""" \\- "region" """
P_MASTER_REGION = "master_region"
""" \\- "master_region" """
P_DOCUMENT_BUCKET_NAME = "docs_bucket_name"
""" \\- "docs_bucket_name" """
P_UI_BUCKET_NAME = "ui_bucket_name"
""" \\- "ui_bucket_name" """
P_ARTEFACT_BUCKET_NAME = "artefact_bucket_name"
""" \\- "artefact_bucket_name" """
P_BUCKET_NAME = "bucket_name"
""" \\- "bucket_name" """
P_BUCKET_REGION = "bucket_region"
""" \\- "bucket_region" """
P_TEMPLATE = "template"
""" \\- "template" """
P_STACK_NAME = "stack_name"
""" \\- "stack_name" """
P_STACK_PARAMETERS = "stack_parameters"
""" \\- "stack_parameters" """
P_ORGANIZATION_ID = "organization_id"
""" \\- "organization_id" """
P_ORGANIZATION_NAME = "organization_name"
""" \\- "organization_name" """
P_ORGANIZATION_EMAIL = "organization_email"
""" \\- "organization_email" """
P_ORGANIZATION_ACCOUNT = "organization_account"
""" \\- "organization_account" """
P_AUTOMATION_TYPE = "automation_type"
""" \\- "automation_type" """
P_TASKS = "tasks"
""" \\- "tasks" """
P_UNITS = "units"
""" \\- "units" """
P_PORTFOLIO = "portfolio"
""" \\- "portfolio" """
P_APP = "app"
""" \\- "app" """
P_BRANCH = "branch"
""" \\- "branch" """
P_BUILD = "build"
""" \\- "build" """
P_COMPONENT = "component"
""" \\- "component" """
P_ENVIRONMENT = "environment"
""" \\- "environment" """
P_DYNAMODB_HOST = "dynamodb_host"
""" \\- "dynamodb_host" """
P_DYNAMODB_REGION = "dynamodb_region"
""" \\- "dynamodb_region" """
P_LOG_AS_JSON = "log_as_json"
""" \\- "log_as_json" """
P_VOLUME = "volume"
""" \\- "volume" """
P_LOG_DIR = "log_dir"
""" \\- "log_dir" """
P_DELIVERED_BY = "delivered_by"
""" \\- "delivered_by" """
P_LOCAL_MODE = "local_mode"
""" \\- "local_mode" """
P_USE_S3 = "use_s3"
""" \\- "use_s3" """
P_ENFORCE_VALIDATION = "enforce_validation"
""" \\- "enforce_validation" """
P_INVOKER_ARN = "invoker_arn"
""" \\- "invoker_lambda_arn" """
P_INVOKER_NAME = "invoker_name"
""" \\- "invoker_lambda_name" """
P_INVOKER_REGION = "invoker_region"
""" \\- "invoker_lambda_region" """
P_API_LAMBDA_ARN = "api_lambda_arn"
""" \\- "api_lambda_arn" """
P_API_LAMBDA_NAME = "api_lambda_name"
""" \\- "api_lambda_name" """
P_API_HOST_URL = "api_host_url"
""" \\- "api_host_url" """
P_EXECUTE_LAMBDA_ARN = "execute_lambda_arn"
""" \\- "execute_lambda_arn" """
P_START_RUNNER_LAMBDA_ARN = "start_runner_lambda_arn"
""" \\- "start_runner_lambda_arn" """
P_DEPLOYSPEC_COMPILER_LAMBDA_ARN = "deployspec_compiler_lambda_arn"
""" \\- "deployspec_compiler_lambda_arn" """
P_COMPONENT_COMPILER_LAMBDA_ARN = "component_compiler_lambda_arn"
""" \\- "component_compiler_lambda_arn" """
P_RUNNER_STEP_FUNCTION_ARN = "runner_step_function_arn"
""" \\- "runner_step_function_arn" """
P_TAGS = "tags"
""" \\- "tags" """
P_CORRELATION_ID = "correlation_id"
""" \\- "correlation_id" """
P_PROJECT = "project"
""" \\- "project" """
P_BIZAPP = "bizapp"
""" \\- "bizapp" """
P_PRN = "prn"
""" \\- "prn" """

# I've created some constants just to help pass data.  Table names CANNOT be overridden.
# They are hardcoded to f"{scope}{client}-core-automation-{name}"
P_CLIENT_TABLE_NAME = "clients_table_name"
""" \\- "clients_table_name" == f"{scope}core-automation-clients"

You cannot override this value.  See the SCOPE environment variable.
"""
P_PORTFOLIOS_TABLE_NAME = "portfolios_table_name"
""" \\- "portfolios_table_name" == f"{scope}core-automation-portfolios"

You cannot override this value.  See the SCOPE environment variable.
"""
P_APPS_TABLE_NAME = "apps_table_name"
""" \\- "apps_table_name" == f"{scope}core-automation-apps"

You cannot override this value.  See the SCOPE environment variable.
"""
P_ZONES_TABLE_NAME = "zones_table_name"
""" \\- "zones_table_name" == f"{scope}core-automation-zones"

You cannot override this value.  See the SCOPE environment variable.
"""
P_ITEMS_TABLE_NAME = "items_table_name"
""" \\- "items_table_name" == f"{scope}{client}-core-automation-items"

You cannot override this value.  See the SCOPE and CLIENT environment variable.
"""
P_EVENTS_TABLE_NAME = "events_table_name"
""" \\- "events_table_name" == f"{scope}{client}-core-automation-events"

You cannot override this value.  See the SCOPE and CLIENT environment variable.
"""
