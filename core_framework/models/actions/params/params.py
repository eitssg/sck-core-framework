from typing import Any

from collections import OrderedDict

from pydantic import BaseModel, Field, ConfigDict, model_serializer


class ActionParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    Account: str = Field(
        ...,
        description="The account to use for the action.  You MUST specify the account",
    )
    StackName: str | None = Field(
        None,
        description="The name of the stack or action reference.  Not every action deploys "
        "a CloudFromation stack, so this is optional",
    )
    Region: str | None = Field(
        None,
        description="The region to use for the action in the account.  Some actions are global and don't have regins.",
    )

    TemplateUrl: str | None = Field(
        None,
        description="The URL of the CloudFormation template to use for the action.  Some actions don't require a template",
    )
    StackParameters: dict | None = Field(
        None,
        description="The parameters to pass to the CloudFormation stack.  Remember, you can use Jinja. "
        "See the state documentation for variables reference.",
    )
    Tags: dict | None = Field(
        None,
        description="The tags to apply to the CloudFormation stack Resources and to the stack itself",
    )
    StackPolicy: dict | None = Field(
        None,
        description="The policy statments that can be used within the Action for its own purpose",
    )
    UserName: str | None = Field(None, description="The user name to create/delete")

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
