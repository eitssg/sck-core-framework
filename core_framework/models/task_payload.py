"""This module provides the TaskPayload class that is used throughout Core-Automation to identify the operating Task to perform."""

from typing import Self, Any, Optional, List
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
    ValidationError,
)

import core_framework as util
from core_framework.constants import (
    V_DEPLOYSPEC,
    V_PIPELINE,
    V_EMPTY,
)

from .deployment_details import DeploymentDetails
from .package_details import PackageDetails
from .action_details import ActionDetails
from .state_details import StateDetails

FLOW_CONTROLS = ["execute", "wait", "success", "failure"]


def get_valid_tasks() -> List[str]:
    """
    Get the list of valid task values.

    Returns
    -------
    List[str]
        List of valid task names that can be used in TaskPayload.

    Examples
    --------
    >>> valid_tasks = get_valid_tasks()
    >>> print(valid_tasks)  # ['package', 'upload', 'compile', 'plan', 'deploy', 'apply', 'release', 'teardown']
    """
    return [
        "package",
        "upload",
        "compile",
        "plan",
        "deploy",
        "apply",
        "release",
        "teardown",
    ]


class TaskPayload(BaseModel):
    """
    The TaskPayload is the primary artefact that is passed between the various components of Core Automation.

    You may consider this the "Top Level" object that contains all of the information needed to perform a task.
    This object contains all of the information necessary to perform operations on the cloud and is the artefact
    that is passed to all core "Lambda Functions" in the event method (except DB and API).

    TaskPayload == Lambda Function *event* object for core lambda

    Attributes
    ----------
    client : str
        The client to perform the task for. Usually stored in client-vars.yaml
    task : str
        The task to perform. Must be one of: package, upload, compile, plan, deploy, apply, release, teardown
    force : bool
        Force the task to be performed regardless of the state of the deployment
    dry_run : bool
        Perform a dry run of the task. Don't actually do anything.
    identity : str
        The identity of the user performing the task. Derived from DeploymentDetails
    deployment_details : DeploymentDetailsClass
        The deployment details such as Portfolio, App, Branch, Build
    package : PackageDetailsClass
        The package details. Usually stored in packages/**/package.zip
    actions : ActionDetailsClass
        The actions to perform. Usually stored in artefacts/**/{task}.actions
    state : StateDetailsClass
        The state of the task. Usually stored in artefacts/**/{task}.state
    flow_control : str | None
        The flow control of the task
    type : str
        The type of the task. Either "deployspec" or "pipeline" (automatically generated)

    Examples
    --------
    Create a basic TaskPayload::

        >>> from core_framework.models.deployment_details import DeploymentDetails
        >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> payload = TaskPayload(
        ...     task="deploy",
        ...     deployment_details=dd
        ... )
        >>> print(payload.task)  # deploy

    Create from command line arguments::

        >>> payload = TaskPayload.from_arguments(
        ...     task="deploy",
        ...     portfolio="ecommerce",
        ...     app="web",
        ...     build="1.0.0",
        ...     force=True
        ... )
        >>> print(payload.force)  # True
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="The client to perform the task for. Usually stored in client-vars.yaml",
        default=V_EMPTY,
    )
    task: str = Field(
        ...,
        alias="Task",
        description="The task to perform. Must be one of: package, upload, compile, plan, deploy, apply, release, teardown",
    )
    force: bool = Field(
        alias="Force",
        description="Force the task to be performed regardless of the state of the deployment",
        default=False,
    )
    dry_run: bool = Field(
        alias="DryRun",
        description="Perform a dry run of the task. Don't actually do anything.",
        default=False,
    )
    identity: str = Field(
        alias="Identity",
        description="The identity of the user performing the task. Derived from DeploymentDetails",
        default=V_EMPTY,
    )
    deployment_details: DeploymentDetails = Field(
        ...,
        alias="DeploymentDetails",
        description="The deployment details such as Portfolio, App, Branch, Build",
    )
    package: PackageDetails = Field(
        alias="Package",
        description="The package details. Usually stored in packages/**/package.zip",
        default_factory=lambda: PackageDetails(),
    )
    actions: ActionDetails = Field(
        alias="Actions",
        description="The actions to perform. Usually stored in artefacts/**/{task}.actions",
        default_factory=lambda: ActionDetails(),
    )
    state: StateDetails = Field(
        alias="State",
        description="The state of the task. Usually stored in artefacts/**/{task}.state",
        default_factory=lambda: StateDetails(),
    )
    flow_control: str | None = Field(
        alias="FlowControl",
        description="The flow control of the task",
        default=None,
    )
    type: str = Field(
        alias="Type",
        description="The type of templates to use (pipeline/deployspec)",
        default=V_PIPELINE,
    )

    @field_validator("task")
    @classmethod
    def validate_task_value(cls, value: str) -> str:
        """
        Validate that the task is one of the allowed values.

        Parameters
        ----------
        value : str
            The task value to validate

        Returns
        -------
        str
            The validated task value

        Raises
        ------
        ValueError
            If the task is not one of the valid values
        """
        valid_tasks = get_valid_tasks()
        if value not in valid_tasks:
            raise ValueError(
                f"Task must be one of {', '.join(valid_tasks)}, got '{value}'"
            )
        return value

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: Any) -> Any:
        """
        Validate and normalize values before model creation.

        Parameters
        ----------
        values : Any
            The input values to validate

        Returns
        -------
        Any
            The validated and normalized values

        Raises
        ------
        ValueError
            If FlowControl or Type values are invalid
        """
        if isinstance(values, dict):
            client = values.get("Client", values.get("client", V_EMPTY))

            dd = values.get("DeploymentDetails", values.get("deployment_details", None))

            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
                # If we supplied a client, then push it to deployment details
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails(client=client)

            # If we supplied a client, then push it to deployment details
            if client:
                dd.client = client
            else:
                client = dd.client

            # These lines are ESSENTIAL - they ensure client is passed to nested objects
            if not (values.get("Package") or values.get("package")):
                values["package"] = PackageDetails(client=client)
            if not (values.get("Actions") or values.get("actions")):
                values["actions"] = ActionDetails(client=client)
            if not (values.get("State") or values.get("state")):
                values["state"] = StateDetails(client=client)

            fc = values.get("FlowControl", values.get("flow_control"))
            if fc and fc not in FLOW_CONTROLS:
                raise ValueError(
                    f"FlowControl must be one of {', '.join(FLOW_CONTROLS)}, got '{fc}'"
                )

            typ = values.get("Type", values.get("type", V_PIPELINE))
            if typ and typ not in [V_PIPELINE, V_DEPLOYSPEC]:
                raise ValueError(
                    f"Type must be one of {V_PIPELINE}, {V_DEPLOYSPEC}, got '{typ}'"
                )

        return values

    @model_validator(mode="after")
    def validate_task(self) -> Self:
        """
        Validate and finalize the task after model creation.

        This method ensures that all required fields are properly set and
        that keys are generated based on deployment details.

        Returns
        -------
        Self
            The validated TaskPayload instance
        """
        if not self.client:
            self.client = self.deployment_details.client
        else:
            self.deployment_details.client = self.client

        # Identity is 'required', so if you have not yet supplied one, we will
        # generate one from the deployment details
        if not self.identity:
            self.identity = self.deployment_details.get_identity()

        if self.package:
            # force any supplied client in package to be the same as the task client
            self.package.client = self.client
            self.package.set_key(self.deployment_details, "package.zip")
        if self.actions:
            # force any supplied client in actions to be the same as the task client
            self.actions.client = self.client
            self.actions.set_key(self.deployment_details, self.task + ".actions")
        if self.state:
            # force any supplied client in state to be the same as the task client
            self.state.client = self.client
            self.state.set_key(self.deployment_details, self.task + ".state")

        return self

    @staticmethod
    def from_arguments(**kwargs: Any) -> "TaskPayload":
        """
        Create a TaskPayload object from the given keyword arguments.

        This method is used to create a TaskPayload from command line arguments.
        Arguments are typically from the command line. "from_arguments" means
        "from command line arguments".

        Command line arguments are the lowercase 'snake_case' version of the
        TaskPayload, DeploymentDetails, PackageDetails, ActionDetails, and
        StateDetails attributes.

        Since there is no object hierarchy in the command line arguments,
        this method attempts to make sense of that by creating the appropriate
        nested objects.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments that can include:

            Core Parameters:
                task/Task (str): The task to perform (required). Must be one of:
                               package, upload, compile, plan, deploy, apply, release, teardown
                client/Client (str): Client identifier
                force/Force (bool): Force execution flag
                dry_run/DryRun (bool): Dry run flag
                identity/Identity (str): User identity
                type/Type/automation_type (str): Automation type (pipeline/deployspec)
                flow_control/FlowControl (str): Flow control setting

            DeploymentDetails Parameters:
                deployment_details/DeploymentDetails (DeploymentDetails): Deployment context
                portfolio/Portfolio (str): Portfolio name
                app/App (str): Application name
                build/Build (str): Build version
                branch/Branch (str): Branch name

            Package/Action/State Parameters:
                Any parameters accepted by PackageDetails.from_arguments(),
                ActionDetails.from_arguments(), or StateDetails.from_arguments()

        Returns
        -------
        TaskPayload
            A new TaskPayload instance with all nested objects properly initialized

        Raises
        ------
        ValidationError
            If the deployment_details parameter is not a DeploymentDetails instance
            when provided, or if required parameters are missing
        ValueError
            If task parameter is missing, invalid, or not one of the valid task values

        Examples
        --------
        Create from minimal arguments::

            >>> payload = TaskPayload.from_arguments(**command_line_args)
            >>> print(payload.task)  # deploy

        Notes
        -----
        Parameter Aliases:
            This method accepts both CamelCase and snake_case parameter names for
            compatibility (e.g., both 'dry_run' and 'DryRun' are accepted).

        Nested Object Creation:
            If deployment_details is not provided, it will be created from the
            provided kwargs. Similarly, PackageDetails, ActionDetails, and
            StateDetails objects are created with their respective from_arguments
            methods.

        Valid Tasks:
            The task parameter must be one of: package, upload, compile, plan,
            deploy, apply, release, teardown. Use get_valid_tasks() to get the
            current list of valid task values.
        """

        def _get(key1: str, key2: str, defualt: Any, can_be_empty: bool = False) -> Any:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else defualt

        # Validate required task parameter
        task = _get("task", "Task", None)
        if not task:
            raise ValueError("Task parameter is required")

        # Validate task value early
        valid_tasks = get_valid_tasks()
        if task not in valid_tasks:
            raise ValueError(
                f"Task must be one of {', '.join(valid_tasks)}, got '{task}'"
            )

        # Handle deployment details
        dd = _get("deployment_details", "DeploymentDetails", None)
        if isinstance(dd, dict):
            dd = DeploymentDetails(**dd)
        elif not isinstance(dd, DeploymentDetails):
            dd = DeploymentDetails.from_arguments(**kwargs)

        if "DeploymentDetails" in kwargs:
            del kwargs["DeploymentDetails"]
        kwargs["deployment_details"] = dd

        pkg = _get("package", "Package", None)
        if isinstance(pkg, dict):
            pkg = PackageDetails(**pkg)
        elif not isinstance(pkg, PackageDetails):
            pkg = PackageDetails.from_arguments(**kwargs)

        act = _get("actions", "Actions", None)
        if isinstance(act, dict):
            act = ActionDetails(**act)
        elif not isinstance(act, ActionDetails):
            act = ActionDetails.from_arguments(**kwargs)

        st = _get("state", "State", None)
        if isinstance(st, dict):
            st = StateDetails(**st)
        elif not isinstance(st, StateDetails):
            st = StateDetails.from_arguments(**kwargs)

        typ = _get(
            "type", "Type", _get("automation_type", "AutomationType", V_PIPELINE)
        )

        force = _get("force", "Force", False)

        dry_run = _get("dry_run", "DryRun", False)

        identity = _get("identity", "Identity", V_EMPTY)

        flow_control = _get("flow_control", "FlowControl", None)

        return TaskPayload(
            client=dd.client,
            task=task,
            force=force,
            dry_run=dry_run,
            identity=identity,
            type=typ,
            flow_control=flow_control,
            deployment_details=dd,
            package=pkg,
            actions=act,
            state=st,
        )

    def model_dump(self, **kwargs: Any) -> dict:
        """
        Override to exclude None values by default.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments passed to the parent model_dump method.
            All standard Pydantic model_dump parameters are supported.

        Returns
        -------
        dict
            Dictionary representation of the model with None values excluded by default.
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)
