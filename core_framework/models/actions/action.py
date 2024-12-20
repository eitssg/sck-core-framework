"""
This module contains the AcActionDefinitiontion class which provides a model for how Tasks or Actions are to
be provided to the core-execute library.
"""

from typing import Any
from collections import OrderedDict
from pydantic import BaseModel, Field, ConfigDict, model_serializer


from .action_params import ActionParams

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
        ...,
        description="The scope of the action.  This is used to group actions together. Project/Portfolio, App, Branch, or Build",
    )

    Condition: str = Field(description="Condition clauses", default="True")

    Before: list = Field(
        description="Before is a list of actions that should be perfomred before this one",
        default=[],
    )
    After: list = Field(
        description="After is a list of actions that should be perfomred after this one",
        default=[],
    )
    SaveOutputs: bool = Field(
        description="SaveOutputs is a flag to save the outputs of the action",
        default=False,
    )
    LifecycleHooks: list = Field(
        description="Lifecycle Hooks",
        default=[],
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
