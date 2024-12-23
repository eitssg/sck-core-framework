""" This module provides the TaskPaylaod class that is used throughout Core-Automation to identify the operating Task to perform. """
from typing import Self
from pydantic import BaseModel, Field, ConfigDict, model_validator


from core_framework.constants import (
    V_DEPLOYSPEC,
    V_PIPELINE,
    V_EMPTY,
)

from .deployment_details import DeploymentDetails as DeploymentDetailsClass
from .package_details import PackageDetails as PackageDetailsClass
from .action_details import ActionDetails as ActionDetailsClass
from .state_details import StateDetails as StateDetailsClass


class TaskPayload(BaseModel):
    """
    The TaskPayload is the primary artefact that is passed between the various components of Core Automation. You may
    consider this the "Top Level" object that contains all of the information needed to perform a task.  This object
    contains all of the information necessary to perform perations on the cloud and is the artefact that is passed
    to all core "Lambda Functions" in the event method (except DB and API).

    TaskPayload == Lambda Fuction *event* object for core lambda

    Attributes:
        Task (str): The task to perform.  See the ACT\\_ constants in constants.py
        Force (bool): Force the task to be performed regardless of the state of the deployment
        DryRun (bool): Perform a dry run of the task.  Don't actually do anything.
        Identity (str): The identity of the user performing the task.  Derrived from DeploymentDetails
        DeploymentDetails (DeploymentDetails): The deployment details such as Portfolio, App, Branch, Build
        Package (PackageDetails): The package details.  Usually stored in packages/\\*\\*/package.zip
        Actions (ActionDetails | None): The actions to perform.  Usually stored in artefacts/\\*\\*/{task}.actions
        State (StateDetails | None): The state of the task.  Usually stored in artefacts/\\*\\*/{task}.state
        Type (str): The type of the task.  Either "deployspec" or "pipeline" (automatically generated)

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    Task: str = Field(
        ..., description="The task to perform.  See the ACT_ constants in constants.py"
    )
    Force: bool = Field(
        description=" Force the task to be performed regardless of the state of the deployment",
        default=False,
    )
    DryRun: bool = Field(
        description="Perform a dry run of the task.  Don't actually do anything.",
        default=False,
    )
    Identity: str = Field(
        description="The identity of the user performing the task.  Derrived from DeploymentDetails",
        default=V_EMPTY,
    )
    DeploymentDetails: DeploymentDetailsClass = Field(
        ..., description="The deployment details such as Portfolio, App, Branch, Build"
    )
    Package: PackageDetailsClass = Field(
        ...,
        description="The package details.  Usually stored in packages/**/package.zip",
    )
    Actions: ActionDetailsClass | None = Field(
        description="The actions to perform.  Usually stored in artefacts/**/{task}.actions",
        default=None,
    )
    State: StateDetailsClass | None = Field(
        description="The state of the task.  Usually stored in artefacts/**/{task}.state",
        default=None,
    )
    FlowControl: str = Field(description="The flow control of the task", default="execute")

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values):
        if values:
            if not values.get("DeploymentDetails"):
                values["DeploymentDetails"] = DeploymentDetailsClass()
            if not values.get("Package"):
                values["Package"] = PackageDetailsClass()
            if not values.get("Actions"):
                values["Actions"] = ActionDetailsClass()
            if not values.get("State"):
                values["State"] = StateDetailsClass()
            if not values.get("FlowControl"):
                values["FlowControl"] = "execute"
            if values.get("FlowControl") not in ["execute", "wait", "success", "failure"]:
                raise ValueError("FlowControl must be 'execute', 'wait', 'success', or 'failure'")
        return values

    @model_validator(mode="after")
    def validate_task(self) -> Self:
        if not self.Identity:
            self.Identity = self.DeploymentDetails.get_identity()
        if self.Package and not self.Package.Key:
            self.Package.set_key(self.DeploymentDetails, "package.zip")
        if self.Actions and not self.Actions.Key:
            self.Actions.set_key(self.DeploymentDetails, self.Task + ".actions")
        if self.State and not self.State.Key:
            self.State.set_key(self.DeploymentDetails, self.Task + ".state")
        return self

    @property
    def Type(self) -> str:
        return V_DEPLOYSPEC if self.Package and self.Package.DeploySpec else V_PIPELINE

    @staticmethod
    def from_arguments(**kwargs):

        dd = kwargs.get("deployment_details", kwargs)
        if not isinstance(dd, DeploymentDetailsClass):
            dd = DeploymentDetailsClass.from_arguments(**dd)

            # DeplymentDetailsClass is needed for Package/ActionDefinition/StateDetailsClass
            kwargs["deployment_details"] = dd

        return TaskPayload(
            Task=kwargs.get("task", ""),
            Force=kwargs.get("force", False),
            DryRun=kwargs.get("dry_run", False),
            Identity=kwargs.get("identity", dd.get_identity()),
            DeploymentDetails=dd,
            Package=PackageDetailsClass.from_arguments(**kwargs),
            Actions=ActionDetailsClass.from_arguments(**kwargs),
            State=StateDetailsClass.from_arguments(**kwargs),
        )

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
