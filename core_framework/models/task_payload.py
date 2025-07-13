"""This module provides the TaskPaylaod class that is used throughout Core-Automation to identify the operating Task to perform."""

from typing import Self
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationError

import core_framework as util
from core_framework.constants import (
    OBJ_PACKAGES,
    OBJ_ARTEFACTS,
    V_DEPLOYSPEC,
    V_PIPELINE,
    V_EMPTY,
)

from .deployment_details import DeploymentDetails as DeploymentDetailsClass
from .package_details import PackageDetails as PackageDetailsClass
from .action_details import ActionDetails as ActionDetailsClass
from .state_details import StateDetails as StateDetailsClass

FLOW_CONTROLS = ["execute", "wait", "success", "failure"]


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

    client: str = Field(
        alias="Client",  # Alias for PascalCase compatibility
        description="The client to perform the task for.  Usually stored in client-vars.yaml",
        default=V_EMPTY,
    )
    task: str = Field(
        ...,
        alias="Task",  # Alias for PascalCase compatibility
        description="The task to perform.  See the ACT_ constants in constants.py",
    )
    force: bool = Field(
        alias="Force",  # Alias for PascalCase compatibility
        description=" Force the task to be performed regardless of the state of the deployment",
        default=False,
    )
    dry_run: bool = Field(
        alias="DryRun",  # Alias for PascalCase compatibility
        description="Perform a dry run of the task.  Don't actually do anything.",
        default=False,
    )
    identity: str = Field(
        alias="Identity",  # Alias for PascalCase compatibility
        description="The identity of the user performing the task.  Derrived from DeploymentDetails",
        default=V_EMPTY,
    )
    deployment_details: DeploymentDetailsClass = Field(
        ...,
        alias="DeploymentDetails",  # Alias for PascalCase compatibility
        description="The deployment details such as Portfolio, App, Branch, Build",
    )
    package: PackageDetailsClass = Field(
        alias="Package",  # Alias for PascalCase compatibility
        description="The package details.  Usually stored in packages/**/package.zip",
        default_factory=lambda: PackageDetailsClass(),
    )
    actions: ActionDetailsClass = Field(
        alias="Actions",  # Alias for PascalCase compatibility
        description="The actions to perform.  Usually stored in artefacts/**/{task}.actions",
        default_factory=lambda: ActionDetailsClass(),
    )
    state: StateDetailsClass = Field(
        alias="State",  # Alias for PascalCase compatibility
        description="The state of the task.  Usually stored in artefacts/**/{task}.state",
        default_factory=lambda: StateDetailsClass(),
    )
    flow_control: str | None = Field(
        alias="FlowControl",  # Alias for PascalCase compatibility
        description="The flow control of the task",
        default=None,
    )
    type: str = Field(
        alias="Type",  # Alias for PascalCase compatibility
        description="The type of templates to use (pipeline/deployspec)",
        default=V_PIPELINE,
    )

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values):
        if isinstance(values, dict):

            client = values.get("Client", values.get("client", V_EMPTY))
            dd = values.get("DeploymentDetails", values.get("deployment_details", None))
            if not client:
                if dd:
                    client = dd.get("client", dd.get("Client", V_EMPTY))
                if not client:
                    client = util.get_client()
                values["client"] = client

            if not dd:
                values["deployment_details"] = DeploymentDetailsClass(client=client)

            if not (values.get("Package") or values.get("package")):
                values["package"] = PackageDetailsClass(client=client)
            if not (values.get("Actions") or values.get("actions")):
                values["actions"] = ActionDetailsClass(client=client)
            if not (values.get("State") or values.get("state")):
                values["state"] = StateDetailsClass(client=client)

            fc = values.get("FlowControl", values.get("flow_control"))
            if fc and fc not in FLOW_CONTROLS:
                raise ValueError(
                    f"FlowControl must be one of {",".join(FLOW_CONTROLS)}"
                )

            typ = values.get("Type", values.get("type", V_PIPELINE))
            if typ and typ not in [V_PIPELINE, V_DEPLOYSPEC]:
                raise ValueError(f"Type must be one of {V_PIPELINE},{V_DEPLOYSPEC}")

        return values

    @model_validator(mode="after")
    def validate_task(self) -> Self:

        if not self.client:
            self.client = self.deployment_details.client
        if not self.identity:
            self.identity = self.deployment_details.get_identity()

        # Force keys to be set based on the deployment details
        if self.package:
            self.package.set_key(self.deployment_details, "package.zip")
        if self.actions:
            self.actions.set_key(self.deployment_details, self.task + ".actions")
        if self.state:
            self.state.set_key(self.deployment_details, self.task + ".state")

        return self

    def _generate_deployment_details(self) -> DeploymentDetailsClass:
        """Generate a DeploymentDetails object based on the client and task."""
        return DeploymentDetailsClass(**{"Client": self.client})

    @staticmethod
    def from_arguments(**kwargs) -> "TaskPayload":
        """
        Create a TaskPayload object from the given keyword arguments. This method is used to create a TaskPayload

        Areguments are typically from the command line.  "from_arguments" is "from command line arguments"

        Command line arguments are the lowercase 'snake_case' version of the TaskPayload, DeploymentDetails,
        PackageDetails, ActionDetails, and StateDetails attributes.

        Since there is no object hierarchy in the command line arguments, this method attempt to make sense of that.

        """
        dd = kwargs.get("deployment_details", kwargs.get("DeploymentDetails", None))
        if dd is None:
            dd = DeploymentDetailsClass.from_arguments(**kwargs)
            kwargs["deployment_details"] = dd
        if not isinstance(dd, DeploymentDetailsClass):
            raise ValidationError(
                "DeploymentDetails must be an instance of DeploymentDetails"
            )
        return TaskPayload(
            client=dd.client,
            task=kwargs.get("task", kwargs.get("Task", V_EMPTY)),
            force=kwargs.get("force", kwargs.get("Force", False)),
            dry_run=kwargs.get("dry_run", kwargs.get("DryRun", False)),
            identity=kwargs.get("identity", kwargs.get("Identity", V_EMPTY)),
            type=kwargs.get(
                "automation_type", kwargs.get("type", kwargs.get("Type", V_PIPELINE))
            ),
            deployment_details=dd,
            package=PackageDetailsClass.from_arguments(**kwargs),
            actions=ActionDetailsClass.from_arguments(**kwargs),
            state=StateDetailsClass.from_arguments(**kwargs),
        )

    # Override
    def model_dump(self, **kwargs) -> dict:
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
