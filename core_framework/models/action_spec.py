"""
This module contains the AcActionSpection class which provides a model for how Tasks or Actions are to
be provided to the core-execute library.

CONSIDERRATION:

Consider moving this to the core-execute library as it is used almost excusivly by the core-execute library.

This module defines the ActionSpec class, which are used to define actions that can
be performed by the Core Automation framework. These actions can include creating or deleting AWS resources,
updating user permissions, and more.

Things that you wouldn't necessarily do in a CloudFormation template.

The ActionSpec class includes fields for the action label,
type, parameters, dependencies, and other metadata.
"""

from typing import Any, Self
from collections import OrderedDict
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    SerializationInfo,
    model_serializer,
    model_validator,
    field_validator,
)


# Give constants for the keys in the definition
LABEL = "label"
""" The name of the label field in the Actions object.

    Value: label
"""
TYPE = "type"
""" The name of the type field in the Actions object.

    Value: type
"""
DEPENDS_ON = "depends_on"
""" The name of the depends_on field in the Actions object.

    Value: depends_on
"""
PARAMS = "params"
""" The name of the params field in the Actions object.

    Value: params
"""
SCOPE = "scope"
""" The name of the scope field in the Actions object.

    Value: scope
"""
# Give constants for the keys in the definition
STACKNAME = "stack_name"
""" The name of the stack field in the Actions object.

    This value of this field will show in AWS Cloudformation dashboards

    Value: stack_name
"""
ACCOUNT = "account"
""" The name of the account field in the Actions object.

    Core automation uses the value of this field to determine which account to deploy the stack to.
    If Core does not have access to the account with the appropriate role, deployments will fail.

    Value: account
"""
REGION = "region"
""" The name of the region field in the Actions object.

    Core automation uses the value of this field to determine which region to deploy the stack to.

    Value: region
"""
TEMPLATE_URL = "template"
""" The name of the template field in the Actions object.

    Core automation uses the value of this field to determine the location of the Cloudformation template.

    Value: template
"""
STACK_PARAMETERS = "parameters"
""" The name of the parameters field in the Actions object.

    Core automation uses the value of this field to determine the parameters to pass to the Cloudformation template.
    This is in addition to the Jinja2 context FACTS.  Every Cloudformation template is passed through Jinja2 allowing
    the template to be modified by the context FACTS.

    Value: parameters
"""
TAGS = "tags"
""" tags can be defined on the action that will be added to all resources in the deployment.  BaseAction implmentations
    can use these tags as necessary.
"""
STACK_POLICY = "stack_policy"
""" Certain stack deployments may require a stack policy.  This is a JSON document that defines the permissions
    that the stack needs.  In order for this to work, Core must have access to the IAM services in the target
    account.
"""
USER_NAME = "user_name"
""" The name of the user_name field in the Actions object.

    Core automation uses the value of this field to determine which user to deploy in IAM.

    There is a special action for add/delete/update users.  This is the Username to be applied to the action.

    Value: user_name
"""


class ActionSpec(BaseModel):
    """
    The ActionSpec class defines an "action" or "task" that Core Automation will perform when deploying infrastructure to your Cloud.

    Tasks could include adding tags to resources, adjusting DNS entries, etc.  Tasks are excuted by core-execute
    and are defined in the core-execute.actionlib library.

    Attributes:
        label (str): The label of the action.  A unique identifier for the action spec
        type (str): The action type.  This is the name of the action spec (e.g. create_user, create_stack, etc.)
        action (str): The action to perform as defined by the execute.actionlib module
        scope (str): The scope of the action (optional). Examples: portfolio, app, branch, or build.
        params (ParamsSpec): The parameters for the action.  This is a dictionary of parameters that the action requires
        depends_on (list[str]): A list of labels of actions that this action depends on.  Scoped to the single deployspec.yaml

    """

    model_config = ConfigDict(populate_by_name=True)

    label: str = Field(
        ...,
        alias="Label",
        description="The label of the action.  A unique identifier for the action",
    )

    type: str = Field(
        ...,
        alias="Type",
        description="The action type.  This is the snake_case of the action in core_execute.actionlib",
    )

    action: str | None = Field(
        description="The action to perform as defined by the execute.actionlib module",
        default=None,
    )

    depends_on: list[str] = Field(
        alias="DependsOn",
        description="A list of labels of actions that this action depends on",
        default_factory=list,
    )

    params: dict = Field(
        ...,
        alias="Params",
        description="The parameters for the action",
    )

    scope: str = Field(
        alias="Scope",
        description="The scope of the action.  This is used to group actions together. Project/Portfolio, App, Branch, or Build",
        default="build",
    )

    # Optional fields that are not required for the action

    condition: str | None = Field(
        alias="Condition",
        description="Condition clauses.  In code, the default is 'True'",
        default=None,
    )

    before: list | None = Field(
        alias="Before",
        description="Before is a list of actions that should be perfomred before this one",
        default=None,
    )

    after: list | None = Field(
        alias="After",
        description="After is a list of actions that should be perfomred after this one",
        default=None,
    )

    save_outputs: bool = Field(
        alias="SaveOutputs",
        description="SaveOutputs is a flag to save the outputs of the action",
        default=False,
    )

    lifecycle_hooks: list | None = Field(
        alias="LifecycleHooks",
        description="Lifecycle Hooks.  Although I don't specify for typing, "
        "this is a list of ActionSpec objects",
        default=None,
    )

    @field_validator("depends_on", mode="before")
    def validate_depends_on(cls, value) -> list[str] | None:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if not isinstance(value, list):
            raise ValueError(
                f"Invalid depends_on value: {value}. Must be a string or a list of strings"
            )
        return value

    @field_validator("type", mode="before")
    def validate_action_type(cls, value) -> str:
        if value and isinstance(value, str):
            if value.startswith("aws."):
                value = value.lstrip("aws.")
        return value

    @field_validator("scope", mode="before")
    def validate_scope(cls, value) -> str:
        scope_list = cls.get_scope_list()
        if value not in scope_list:
            raise ValueError(f"Invalid scope: {value}. Must be one of: {scope_list}")
        return value

    @classmethod
    def get_scope_list(cls) -> list[str]:
        return ["build", "branch", "app", "portfolio"]

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    @model_serializer
    def ser_model(self, info: SerializationInfo) -> OrderedDict:
        """
        Serialize the model to an OrderedDict in a specific order,
        respecting exclude_none and by_alias parameters, and using Field aliases.
        """
        exclude_none = info.exclude_none
        by_alias = info.by_alias

        # Only specify the field names in the desired order
        field_order = [
            "label",
            "type",
            "depends_on",
            "params",
            "scope",
            "condition",
            "before",
            "after",
            "save_outputs",
            "lifecycle_hooks",
        ]

        out = OrderedDict()
        for field in field_order:
            value = getattr(self, field)
            if exclude_none and value is None:
                continue
            # Get the alias from the Field definition if by_alias is True
            if by_alias:
                alias = ActionSpec.model_fields[field].alias
                key = alias
            else:
                key = field
            # For nested models, call their model_dump if needed (not callable in the base ActionSpec... but might be in subclasses)
            if hasattr(value, "model_dump"):  # pragma: no cover
                value = value.model_dump(exclude_none=exclude_none, by_alias=by_alias)
            out[key] = value
        return out
