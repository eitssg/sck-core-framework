"""
This module contains the Action class, which is the base class for all actions in the framework.
"""

from typing import Any
from collections import OrderedDict
from pydantic import BaseModel, Field, ConfigDict, model_serializer


from .params import ActionParams


class Action(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    Label: str = Field(
        description="The label of the action.  A unique identifier for the action"
    )
    Type: str = Field(
        description="The action type.  This is the name of the action in core_execute.actionlib",
    )
    DependsOn: list[str] = Field(
        [], description="A list of labels of actions that this action depends on"
    )
    Params: ActionParams = Field(..., description="The parameters for the action")
    Scope: str = Field(
        description="The scope of the action.  This is used to group actions together. Project/Portfolio, App, Branch, or Build",
    )

    @model_serializer
    def ser_model(self) -> OrderedDict:

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

        return OrderedDict(fields)
