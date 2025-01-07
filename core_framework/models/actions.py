"""
This module contains the AcActionDefinitiontion class which provides a model for how Tasks or Actions are to
be provided to the core-execute library.
"""

from typing import Any
from collections import OrderedDict
from pydantic import BaseModel, Field, ConfigDict, model_serializer


# Give constants for the keys in the definition
LABEL = "Label"
""" The name of the label field in the Actions object.

    Value: Label
"""
TYPE = "Type"
""" The name of the type field in the Actions object.

    Value: Type
"""
DEPENDS_ON = "DependsOn"
""" The name of the depends_on field in the Actions object.

    Value: DependsOn
"""
PARAMS = "Params"
""" The name of the params field in the Actions object.

    Value: Params
"""
SCOPE = "Scope"
""" The name of the scope field in the Actions object.

    Value: Scope
"""
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
    def ser_model(self) -> OrderedDict:  # noqa: C901
        """
        Serialize the model to an OrderedDict.  I like order.

        Returns:
            OrderedDict: The parameters sorted the way I want.
        """
        fields: list[tuple[str, Any]] = []
        if self.Account is not None:
            fields.append(("Account", self.Account))
        if self.UserName is not None:
            fields.append(("UserName", self.UserName))
        if self.StackName is not None:
            fields.append(("StackName", self.StackName))
        if self.Region is not None:
            fields.append(("Region", self.Region))
        if self.TemplateUrl is not None:
            fields.append(("TemplateUrl", self.TemplateUrl))
        if self.StackParameters is not None:
            fields.append(("StackParameters", OrderedDict(self.StackParameters)))
        if self.Tags is not None:
            fields.append(("Tags", self.Tags))
        if self.StackPolicy is not None:
            fields.append(("StackPolicy", OrderedDict(self.StackPolicy)))
        if self.TimeoutInMinutes is not None:
            fields.append(("TimeoutInMinutes", self.TimeoutInMinutes))
        if self.OnFailure is not None:
            fields.append(("OnFailure", self.OnFailure))
        if self.DestinationImageName is not None:
            fields.append(("DestinationImageName", self.DestinationImageName))
        if self.ImageName is not None:
            fields.append(("ImageName", self.ImageName))
        if self.KmsKeyArn is not None:
            fields.append(("KmsKeyArn", self.KmsKeyArn))
        if self.KmsKeyId is not None:
            fields.append(("KmsKeyId", self.KmsKeyId))
        if self.GranteePrincipals is not None:
            fields.append(("GrantPrincipals", self.GranteePrincipals))
        if self.Operations is not None:
            fields.append(("Operations", self.Operations))
        if self.IgnoreFailedGrants is not None:
            fields.append(("IgnoreFailedGrants", self.IgnoreFailedGrants))
        if self.Variables is not None:
            fields.append(("Variables", self.Variables))
        if self.DistributionId is not None:
            fields.append(("DistributionId", self.DistributionId))
        if self.Paths is not None:
            fields.append(("Paths", self.Paths))
        if self.InstanceId is not None:
            fields.append(("InstanceId", self.InstanceId))
        if self.RepositoryName is not None:
            fields.append(("RepositoryName", self.RepositoryName))
        if self.SecurityGroupId is not None:
            fields.append(("SecurityGroupId", self.SecurityGroupId))
        if self.SuccessStatuses is not None:
            fields.append(("SuccessStatuses", self.SuccessStatuses))
        if self.AccountsToShare is not None:
            fields.append(("AccountsToShare", self.AccountsToShare))
        if self.Siblings is not None:
            fields.append(("Siblings", self.Siblings))
        if self.BucketName is not None:
            fields.append(("BucketName", self.BucketName))
        if self.OutputName is not None:
            fields.append(("OutputName", self.OutputName))
        if self.Type is not None:
            fields.append(("Type", self.Type))
        if self.Status is not None:
            fields.append(("Status", self.Status))
        if self.Message is not None:
            fields.append(("Message", self.Message))
        if self.Identity is not None:
            fields.append(("Identity", self.Identity))
        if self.Namespace is not None:
            fields.append(("Namespace", self.Namespace))
        if self.Metrics is not None:
            fields.append(("Metrics", self.Metrics))
        if self.LoadBalancer is not None:
            fields.append(("LoadBalancer", self.LoadBalancer))
        if self.Prefix is not None:
            fields.append(("Prefix", self.Prefix))
        if self.ApiParams is not None:
            fields.append(("ApiParams", self.ApiParams))

        return OrderedDict(fields)


class ActionDefinition(BaseModel):
    """
    The ActionDefinition class defines an "action" or "task" that Core Automation will perform when deploying infrastructure to your Cloud.

    Tasks could include adding tags to resources, ajdusting DNS entries, etc.  Tasks are excuted by core-execute
    and are defined in the core-execute.actionlib library.

    Attributes:
        Label (str): The label of the action. A unique identifier for the action.
        Type (str): The action type. This is the name of the action in core_execute.actionlib.
        DependsOn (list[str]): A list of labels of actions that this action depends on.
        Params (ActionParams | None): The parameters for the action. See :class:`ActionParams` for more information.
        Scope (str): The scope of the action. This is used to group actions together.

    """

    model_config = ConfigDict(populate_by_name=True)

    Label: str = Field(
        ..., description="The label of the action.  A unique identifier for the action"
    )

    Type: str = Field(
        ...,
        description="The action type.  This is the name of the action in core_execute.actionlib",
    )

    DependsOn: list[str] = Field(
        [],
        description="A list of labels of actions that this action depends on",
    )

    Params: ActionParams = Field(
        ...,
        description="The parameters for the action.  See :class:`ActionParams` for more information on the parameters for the action",
    )

    Scope: str = Field(
        description="The scope of the action.  This is used to group actions together. Project/Portfolio, App, Branch, or Build",
        default="build",
    )

    Condition: str | None = Field(
        description="Condition clauses.  In code, the default is 'True'", default=None
    )

    Before: list | None = Field(
        description="Before is a list of actions that should be perfomred before this one",
        default=None,
    )
    After: list | None = Field(
        description="After is a list of actions that should be perfomred after this one",
        default=None,
    )
    SaveOutputs: bool = Field(
        description="SaveOutputs is a flag to save the outputs of the action",
        default=False,
    )
    LifecycleHooks: list | None = Field(
        description="Lifecycle Hooks.  Although I don't specify for typing, "
        "this is a list of ActionDefinition objects",
        default=None,
    )

    @model_serializer
    def ser_model(self) -> OrderedDict:  # noqa C901
        """
        Serialize the model to an OrderedDict.  I like order.

        Returns:
            OrderedDict: The attributes sorted the way I want.
        """
        fields: list[tuple[str, Any]] = []
        if self.Label:
            fields.append(("Label", self.Label))
        if self.Type:
            fields.append(("Type", self.Type))
        if self.DependsOn:
            fields.append(("DependsOn", tuple(self.DependsOn)))
        if self.Params:
            fields.append(("Params", self.Params.model_dump()))
        if self.Scope:
            fields.append(("Scope", self.Scope))
        if self.Condition:
            fields.append(("Condition", self.Condition))
        if self.Before:
            fields.append(("Before", self.Before))
        if self.After:
            fields.append(("After", self.After))
        if self.SaveOutputs:
            fields.append(("SaveOutputs", self.SaveOutputs))
        if self.LifecycleHooks:
            fields.append(("LifecycleHooks", self.LifecycleHooks))

        return OrderedDict(fields)
