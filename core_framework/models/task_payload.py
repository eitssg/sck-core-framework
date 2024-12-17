""" This module provides the TaskPaylaod class that is used throughout Core-Automation to identify the operating Task to perform. """

from pydantic import BaseModel, Field, ConfigDict


from core_framework.constants import (
    V_DEPLOYSPEC,
    V_PIPELINE,
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

    Task: str | None = Field(
        None, description="The task to perform.  See the ACT_ constants in constants.py"
    )
    Force: bool = Field(
        False,
        description=" Force the task to be performed regardless of the state of the deployment",
    )
    DryRun: bool = Field(
        False, description="Perform a dry run of the task.  Don't actually do anything."
    )
    Identity: str | None = Field(
        None,
        description="The identity of the user performing the task.  Derrived from DeploymentDetails",
    )
    DeploymentDetails: DeploymentDetailsClass = Field(
        ..., description="The deployment details such as Portfolio, App, Branch, Build"
    )
    Package: PackageDetailsClass = Field(
        ...,
        description="The package details.  Usually stored in packages/**/package.zip",
    )
    Actions: ActionDetailsClass | None = Field(
        None,
        description="The actions to perform.  Usually stored in artefacts/**/{task}.actions",
    )
    State: StateDetailsClass | None = Field(
        None,
        description="The state of the task.  Usually stored in artefacts/**/{task}.state",
    )

    @property
    def Type(self) -> str:
        return V_DEPLOYSPEC if self.Package.DeploySpec is not None else V_PIPELINE

    @staticmethod
    def from_arguments(**kwargs):

        dd = kwargs.get("deployment_details", kwargs)
        if not isinstance(dd, DeploymentDetailsClass):
            dd = DeploymentDetailsClass.from_arguments(**dd)

            # DeplymentDetailsClass is needed for Package/Action/StateDetailsClass
            kwargs["deployment_details"] = dd

        return TaskPayload(
            Task=kwargs.get("task"),
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
