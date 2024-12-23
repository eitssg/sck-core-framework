""" The params module contains the ActionParams class which provides a model for how parameters are to
be based to actions in the ActionLib library """

from typing import Any

from collections import OrderedDict

from pydantic import BaseModel, Field, ConfigDict, model_serializer

# Give constants for the keys in the definition
STACKNAME = "StackName"
""" The name of the stack field in the Actions object.

    This value of this field will show in AWS Cloudformation dashboards

    Value: StackName
"""
ACCOUNT = "Account"
""" The name of the account field in the Actions object.

    Core automation uses the value of this field to determine which account to deploy the stack to.
    If Core does not have access to the account with the appropriate role, deployments will fail.

    Value: Account
"""
REGION = "Region"
""" The name of the region field in the Actions object.

    Core automation uses the value of this field to determine which region to deploy the stack to.

    Value: Region
"""
TEMPLATE_URL = "TemplateUrl"
""" The name of the template_url field in the Actions object.

    Core automation uses the value of this field to determine the location of the Cloudformation template.

    Value: TemplateUrl
"""
STACK_PARAMETERS = "StackParameters"
""" The name of the stack_parameters field in the Actions object.

    Core automation uses the value of this field to determine the parameters to pass to the Cloudformation template.
    This is in addition to the Jinja2 context FACTS.  Every Cloudformation template is passed through Jinja2 allowing
    the template to be modified by the context FACTS.

    Value: StackParameters
"""
TAGS = "Tags"
""" Tags can be defined on the action that will be added to all resources in the deployment.  BaseAction implmentations
    can use these tags as necessary.
"""
STACK_POLICY = "StackPolicy"
""" Certain stack deployments may require a stack policy.  This is a JSON document that defines the permissions
    that the stack needs.  In order for this to work, Core must have access to the IAM services in the target
    account.
"""
USER_NAME = "UserName"
""" The name of the user_name field in the Actions object.

    Core automation uses the value of this field to determine which user to deploy in IAM.

    There is a special action for add/delete/update users.  This is the Username to be applied to the action.

    Value: UserName
"""


class ActionParams(BaseModel):
    """
    ActionParams is a model for the parameters that are passed to the BaseAction object in the ActionLib library.
    """

    model_config = ConfigDict(populate_by_name=True)

    Account: str | None = Field(
        description="The account to use for the action.  You MUST specify the account",
        default=None,
    )
    StackName: str | None = Field(
        description="The name of the stack or action reference.  Not every action deploys "
        "a CloudFromation stack, so this is optional",
        default=None,
    )
    Region: str | None = Field(
        description="The region to use for the action in the account.  Some actions are global and don't have regins.",
        default=None,
    )
    TemplateUrl: str | None = Field(
        description="The URL of the CloudFormation template to use for the action.  Some actions don't require a template",
        default=None,
    )
    TimeoutInMinutes: int | None = Field(
        description="The timeout in minutes for the stack creation.  Default is 60 minutes",
        default=None,
    )
    OnFailure: str | None = Field(
        description="The action to take on failure of the stack creation.  Default is DELETE",
        default=None,
    )
    StackParameters: dict | None = Field(
        description="The parameters to pass to the CloudFormation stack.  Remember, you can use Jinja. "
        "See the state documentation for variables reference.",
        default=None,
    )
    Tags: dict | None = Field(
        description="The tags to apply to the CloudFormation stack Resources and to the stack itself",
        default=None,
    )
    StackPolicy: dict | None = Field(
        description="The policy statments that can be used within the action for its own purpose",
        default=None,
    )
    UserName: str | None = Field(
        description="The user name to create/delete", default=None
    )
    DestinationImageName: str | None = Field(
        description="The name of the destination App SOE image", default=None
    )
    ImageName: str | None = Field(
        description="The name of the source App SOE image", default=None
    )
    KmsKeyArn: str | None = Field(
        description="The KMS key to use for encryption of the resources", default=None
    )
    KmsKeyId: str | None = Field(
        description="The KMS key ID to use for encryption of the resources",
        default=None,
    )
    GranteePrincipals: list[str] | None = Field(
        description="The principals to grant access to the KMS key", default=None
    )
    Operations: list[str] | None = Field(
        description="The list of operation to be granted to the Principals for the KmsKey",
        default=None,
    )
    IgnoreFailedGrants: bool | None = Field(
        description="The flag to ignore failed grants when granting permission to Kms Keys",
        default=None,
    )
    Variables: dict[str, str] | None = Field(
        description="BaseAction variables, name/value pairs", default=None
    )
    DistributionId: str | None = Field(
        description="The CloudFront distribution ID", default=None
    )
    Paths: list[str] | None = Field(
        description="The paths to invalidate on CloudFront distribution", default=None
    )
    InstanceId: str | None = Field(
        description="The instance ID of an EC2", default=None
    )
    RepositoryName: str | None = Field(
        description="The name of a repository to use for the action", default=None
    )
    SecurityGroupId: str | None = Field(
        description="The security group to reference for the action", default=None
    )
    SuccessStatuses: list[str] | None = Field(
        description="The status values that will indicate the operation was successful",
        default=None,
    )
    AccountsToShare: list[str] | None = Field(
        description="The account to share the image with", default=None
    )
    Siblings: list[str] | None = Field(
        description="The sibling accounts that the image can be shared with",
        default=None,
    )
    BucketName: str | None = Field(
        description="The name of the S3 bucket to perform the action on", default=None
    )
    OutputName: str | None = Field(
        description="The name of the output or export name for the stack", default=None
    )
    Type: str | None = Field(description="The type of evebt", default=None)
    Status: str | None = Field(description="The status of the event", default=None)
    Message: str | None = Field(description="The message of the event", default=None)
    Identity: str | None = Field(
        description="The identity or PRN of the event that will be logged", default=None
    )
    Namespace: str | None = Field(
        description="The namespace that the action is modifying", default=None
    )
    Metrics: list[dict] | None = Field(
        description="The metrics that are being collected in the action", default=None
    )
    LoadBalancer: str | None = Field(
        description="The load balancer ARN for the action", default=None
    )
    Prefix: str | None = Field(description="The prefix for the S3 bucket", default=None)
    ApiParams: dict | None = Field(
        description="The parameters for the RDS API for RDS modifications", default=None
    )

    @model_serializer
    def ser_model(self) -> OrderedDict:
        fields: list[tuple[str, Any]] = []
        if self.Account:
            fields.append(("Account", self.Account))
        if self.UserName:
            fields.append(("UserName", self.UserName))
        if self.StackName:
            fields.append(("StackName", self.StackName))
        if self.Region:
            fields.append(("Region", self.Region))
        if self.TemplateUrl:
            fields.append(("TemplateUrl", self.TemplateUrl))
        if self.StackParameters:
            fields.append(("StackParameters", OrderedDict(self.StackParameters)))
        if self.Tags:
            fields.append(("Tags", self.Tags))
        if self.StackPolicy:
            fields.append(("StackPolicy", OrderedDict(self.StackPolicy)))
        return OrderedDict(fields)
