"""This module contains the DeploySpec class which provides a model for how CloudFormation templates are to be deployed by core-automation."""

from typing import Self
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict


class ActionSpecParams(BaseModel):
    """
    Parameters for the DeploySpec.  This inclukdes tempalte locations and CloudFormation parameters.

    User deployments are a little special.  They can only be done in one zone at a time.  For security reasons.
    Therefore, the username, account and region are the only fields allowed for user add/delete actions.


    Attributes:
        template (str): The URL of the CloudFormation template to use for the action.  Some actions don't require a template
        stack_name (str): The name of the stack or action reference. You will see this in the CloudFormation console
        parameters (dict): The parameters to pass to the CloudFormation stack
        accounts (list[str]): The account to prform the action on.  Multiple accounts can be specified at one time
        regions (list[str]): The region to use for the action in the account.  Multiple regions can be specified at one time
        stack_policy (str | dict): The policy statments that can be used within the ActionDefinition for its own purpose
        user_name (str): The user name to perform the action on.  Ussers are special deployspecs in that they are not CloudFormation stacks
        account (str): The account to use for the user action.  This is used for user_name updates
        region (str): The region to use for the user action in the account.  This is used for user_name updates

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    template: str | None = Field(
        alias="template",
        description="The URL of the CloudFormation template to use for the action.  Some actions don't require a template",
        default=None,
    )
    stack_name: str | None = Field(
        alias="stack_name",
        description="The name of the stack or action reference. You will see this in the CloudFormation console",
        default=None,
    )
    parameters: dict | None = Field(
        alias="parameters",
        description="The parameters to pass to the CloudFormation stack",
        default=None,
    )
    accounts: list[str] | None = Field(
        alias="accounts",
        description="The account to prform the action on.  Multiple accounts can be specified at one time",
        default=None,
    )
    regions: list[str] | None = Field(
        alias="regions",
        description="The region to use for the action in the account.  Multiple regions can be specified at one time",
        default=None,
    )
    stack_policy: str | dict | None = Field(
        alias="stack_policy",
        description="The policy statments that can be used within the action for its own purpose",
        default=None,
    )
    user_name: str | None = Field(
        alias="user_name",
        description="The user name to perform the action on.  Ussers are special deployspecs in that they are not CloudFormation stacks",
        default=None,
    )
    account: str | None = Field(
        alias="account",
        description="The account to use for the user action.  This is used for user_name updates",
        default=None,
    )
    region: str | None = Field(
        alias="region",
        description="The region to use for the user action in the account.  This is used for user_name updates",
        default=None,
    )

    @field_validator("accounts", mode="before")
    def validate_accounts(cls, value) -> list[str] | None:
        if value:
            if isinstance(value, str):
                value = value.split(",")
            if isinstance(value, list):
                for i in range(len(value)):
                    if not isinstance(value[i], str):
                        value[i] = str(value[i])
        return value

    @field_validator("regions", mode="before")
    def validate_regions(cls, value) -> list[str] | None:
        if value:
            if isinstance(value, str):
                value = value.split(",")
            if isinstance(value, list):
                for i in range(len(value)):
                    if not isinstance(value[i], str):
                        value[i] = str(value[i])
        return value

    @model_validator(mode="after")
    def validate_params(self) -> Self:
        if not self.accounts and not self.account:
            raise ValueError("Missing account or accounts")
        if not self.regions and not self.region:
            raise ValueError("Missing region or regions")
        if self.user_name:
            if not self.account:
                raise ValueError("Missing account from user_name update action")
            if not self.region:
                raise ValueError("Missing region from user_name update action")
        return self

    @field_validator("account", mode="before")
    def validate_account(cls, value) -> str | None:
        if value:
            if not isinstance(value, str):
                value = str(value)
        return value

    @field_validator("region", mode="before")
    def validate_region(cls, value) -> str | None:
        if value:
            if not isinstance(value, str):
                value = str(value)
        return value

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)


class ActionSpec(BaseModel):
    """
    Defines the ActionSpec that will be used to generate the final Actions to perform for this deployment.

    The "action to perform" is described in the "action" attribute and will ultimately generate an :class:`ActionDefinition` object.

    Attributes:
        label (str): The label of the action.  A unique identifier for the action spec
        type (str): The action type.  This is the name of the action spec (e.g. create_user, create_stack, etc.)
        action (str): The action to perform as defined by the execute.actionlib module
        scope (str): The scope of the action (optional). Examples: portfolio, app, branch, or build.
        params (ParamsSpec): The parameters for the action.  This is a dictionary of parameters that the action requires
        depends_on (list[str]): A list of labels of actions that this action depends on.  Scoped to the single deployspec.yaml

    """

    label: str = Field(
        description="The label of the action.  A unique identifier for the action spec",
    )
    type: str = Field(
        description="The action type.  This is the name of the action spec (e.g. create_user, create_stack, etc.)",
    )
    action: str | None = Field(
        description="The action to perform as defined by the execute.actionlib module",
        default=None,
    )
    scope: str | None = Field(
        description="The scope of the action (optional). Examples: portfolio, app, branch, or build.",
        default=None,
    )
    params: ActionSpecParams = Field(
        description="The parameters for the action.  This is a dictionary of parameters that the action requires",
    )
    depends_on: list[str] | None = Field(
        description="A list of labels of actions that this action depends on.  Scoped to the single deployspec.yaml",
        default=None,
    )

    @field_validator("depends_on", mode="before")
    def validate_depends_on(cls, value) -> list[str] | None:
        if value:
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
            type_list = cls.get_type_list()
            if value not in type_list:
                raise ValueError(
                    f"Invalid action type: {value}. Must be one of: {type_list}"
                )
        return value

    @field_validator("scope", mode="before")
    def validate_scope(cls, value) -> str | None:
        if value:
            scope_list = cls.get_scope_list()
            if value not in scope_list:
                raise ValueError(
                    f"Invalid scope: {value}. Must be one of: {scope_list}"
                )
        return value

    @model_validator(mode="after")
    def validate_depends_on_labels(self) -> Self:
        self.action = self.get_exucutor_list().get(self.type, None)
        return self

    @classmethod
    def get_scope_list(cls) -> list[str]:
        return ["build", "branch", "app", "portfolio"]

    @classmethod
    def get_type_list(cls) -> list[str]:
        return list(cls.get_exucutor_list().keys())

    @classmethod
    def get_exucutor_list(cls) -> dict[str, str]:
        return {
            "create_user": "AWS::CreateUser",
            "delete_user": "AWS::DeleteUser",
            "delete_stack": "AWS::DeleteStack",
            "create_stack": "AWS::CreateStack",
            "create_change_set": "AWS::CreateChangeSet",
            "apply_change_set": "AWS::ApplyChangeSet",
            "delete_change_set": "AWS::DeleteChangeSet",
        }

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)


class DeploySpec(BaseModel):

    action_specs: list[ActionSpec] = Field(alias="actions", default_factory=lambda: [])

    @model_validator(mode="before")
    def validate_actions(cls, values) -> dict:
        if values.get("actions") is None:
            raise ValueError("No actions provided")
        return values

    @model_validator(mode="after")
    def validate_deployspecs(self) -> Self:
        """
        Checks to see if the deploysepc will create any duplicate stack names.  If it does, it will raise a ValueError.

        It's only duplicate if it's the same action.type (command, such as: create_stack)

        Raises:
            ValueError: if there are duplicate stack names
        """
        names = []
        for action in self.action_specs:

            # Only do this if we are referencing a stack (user action specs will not have a stack name necessrily)
            if not action.params.stack_name:
                continue

            accounts = action.params.accounts or []
            regions = action.params.regions or []

            if action.params.account and action.params.account not in accounts:
                accounts.append(action.params.account)
            if action.params.region and action.params.region not in regions:
                regions.append(action.params.region)
            for account in accounts:
                for region in regions:
                    name = (
                        f"{action.type}/{account}/{region}/{action.params.stack_name}"
                    )
                    if name in names:
                        raise ValueError(f"Duplicate stack name: {name}")
                    names.append(name)

        return self

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
