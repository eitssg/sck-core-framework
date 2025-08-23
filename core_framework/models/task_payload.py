"""TaskPayload model for Core Automation framework operations.

The TaskPayload serves as the primary data structure passed between Core Automation
components, containing all information necessary to perform cloud operations.
It acts as the top-level object for Lambda function events and workflow coordination.

Key Components:
    - **Task Configuration**: Operation type, execution flags, and control flow
    - **Deployment Context**: Portfolio, app, branch, and build information
    - **Resource Details**: Package, actions, and state management
    - **Client Configuration**: Multi-tenant client identification and settings

Workflow Integration:
    TaskPayload objects are serialized and passed to Lambda functions as event
    payloads, enabling distributed task execution across the automation pipeline.
"""

from typing import Self, Any, List
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    field_validator,
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

FLOW_CONTROLS = ["execute", "success", "failure"]
"""Valid flow control values for task execution."""


def get_valid_tasks() -> List[str]:
    """Get the list of valid task values for TaskPayload operations.

    Returns:
        List of valid task names that can be used in TaskPayload.

    Examples:
        >>> valid_tasks = get_valid_tasks()
        >>> print(valid_tasks)
        ['package', 'upload', 'compile', 'plan', 'deploy', 'apply', 'release', 'teardown']
        >>> 'deploy' in valid_tasks
        True
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
    """Primary payload for Core Automation task execution.

    The TaskPayload contains all information necessary to perform cloud operations
    and serves as the event object passed to core Lambda functions. It encapsulates
    deployment context, resource details, and execution configuration.

    This object represents the complete state needed for distributed task execution
    across the automation pipeline, ensuring consistency and traceability.

    Attributes:
        client: Client identifier for multi-tenant operations.
        task: Operation type (package, deploy, release, etc.).
        force: Force execution regardless of deployment state.
        dry_run: Perform validation without executing operations.
        identity: User identity for audit and permissions.
        deployment_details: Deployment context (portfolio, app, branch, build).
        package: Package artifact details and storage location.
        actions: Task-specific actions and configuration.
        state: Current task state and execution history.
        flow_control: Workflow control directive (execute, success, failure).
        type: Automation type (pipeline or deployspec).

    Examples:
        >>> from core_framework.models.deployment_details import DeploymentDetails
        >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> payload = TaskPayload(
        ...     task="deploy",
        ...     deployment_details=dd
        ... )
        >>> print(payload.task)
        'deploy'
        >>> print(payload.deployment_details.portfolio)
        'ecommerce'

        >>> # Command line integration
        >>> payload = TaskPayload.from_arguments(
        ...     task="deploy",
        ...     portfolio="ecommerce",
        ...     app="web",
        ...     build="1.0.0",
        ...     force=True
        ... )
        >>> print(payload.force)
        True

        >>> # Lambda function usage
        >>> def lambda_handler(event, context):
        ...     payload = TaskPayload(**event)
        ...     return process_task(payload)
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="Client identifier for multi-tenant operations",
        default=V_EMPTY,
    )
    task: str = Field(
        ...,
        alias="Task",
        description="Operation type: package, upload, compile, plan, deploy, apply, release, teardown",
    )
    force: bool = Field(
        alias="Force",
        description="Force execution regardless of deployment state",
        default=False,
    )
    dry_run: bool = Field(
        alias="DryRun",
        description="Perform validation without executing operations",
        default=False,
    )
    identity: str = Field(
        alias="Identity",
        description="User identity for audit and permissions",
        default=V_EMPTY,
    )
    deployment_details: DeploymentDetails = Field(
        ...,
        alias="DeploymentDetails",
        description="Deployment context including portfolio, app, branch, build",
    )
    package: PackageDetails = Field(
        alias="Package",
        description="Package artifact details and storage location",
        default_factory=lambda: PackageDetails(),
    )
    actions: ActionDetails = Field(
        alias="Actions",
        description="Task-specific actions and configuration",
        default_factory=lambda: ActionDetails(),
    )
    state: StateDetails = Field(
        alias="State",
        description="Current task state and execution history",
        default_factory=lambda: StateDetails(),
    )
    flow_control: str | None = Field(
        alias="FlowControl",
        description="Workflow control directive (execute, success, failure)",
        default=None,
    )
    type: str = Field(
        alias="Type",
        description="Automation type (pipeline or deployspec)",
        default=V_PIPELINE,
    )

    @property
    def temp_dir(self) -> str:
        """Get the temporary directory for this task.

        Returns:
            Path to the temporary directory for task operations.

        Examples:
            >>> payload = TaskPayload(task="deploy", deployment_details=dd)
            >>> temp_path = payload.temp_dir
            >>> print(temp_path)
            '/tmp/core-automation'
        """
        return util.get_temp_dir()

    @field_validator("task")
    @classmethod
    def validate_task_value(cls, value: str) -> str:
        """Validate that the task is one of the allowed values.

        Args:
            value: The task value to validate.

        Returns:
            The validated task value.

        Raises:
            ValueError: If the task is not one of the valid values.

        Examples:
            >>> TaskPayload.validate_task_value("deploy")
            'deploy'
            >>> TaskPayload.validate_task_value("invalid")
            ValueError: Task must be one of package, upload, compile, plan, deploy, apply, release, teardown, got 'invalid'
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
        """Validate and normalize values before model creation.

        Ensures proper client propagation to nested objects and validates
        flow control and type values against allowed options.

        Args:
            values: The input values to validate.

        Returns:
            The validated and normalized values.

        Raises:
            ValueError: If FlowControl or Type values are invalid.

        Examples:
            >>> values = {"task": "deploy", "client": "test"}
            >>> validated = TaskPayload.validate_model_before(values)
            >>> # Client is propagated to nested objects
        """
        if isinstance(values, dict):
            client = values.get("Client") or values.get("client") or util.get_client()

            dd = values.get("DeploymentDetails", None) or values.get(
                "deployment_details", None
            )

            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails(client=client)

            # If we supplied a client, then push it to deployment details
            dd.client = client

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
        """Validate and finalize the task after model creation.

        Ensures all required fields are properly set and generates keys
        for package, actions, and state based on deployment details.

        Returns:
            The validated TaskPayload instance.

        Examples:
            >>> payload = TaskPayload(task="deploy", deployment_details=dd)
            >>> # Identity and keys are automatically generated
            >>> print(payload.identity)
            'prn:portfolio:app:branch:build'
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
            if not self.package.key:
                self.package.set_key(self.deployment_details, "package.zip")
        if self.actions:
            # force any supplied client in actions to be the same as the task client
            self.actions.client = self.client
            if not self.actions.key:
                self.actions.set_key(self.deployment_details, self.task + ".actions")
        if self.state:
            # force any supplied client in state to be the same as the task client
            self.state.client = self.client
            if not self.state.key:
                self.state.set_key(self.deployment_details, self.task + ".state")

        return self

    def set_task(self, task: str, reset_keys: bool = True) -> None:
        """Set the task for this TaskPayload and optionally reset resource keys.

        Updates the task type and regenerates storage keys for package, actions,
        and state objects based on the new task name.

        Args:
            task: The task to set (must be valid task value).
            reset_keys: Whether to regenerate storage keys for resources.

        Raises:
            ValueError: If the task is not one of the valid values.

        Examples:
            >>> payload = TaskPayload(task="deploy", deployment_details=dd)
            >>> payload.set_task("release")
            >>> print(payload.task)
            'release'
            >>> # Keys are automatically updated for the new task
        """
        self.task = task
        if reset_keys:
            if self.package:
                self.package.set_key(self.deployment_details, "package.zip")
            if self.actions:
                self.actions.set_key(self.deployment_details, self.task + ".actions")
            if self.state:
                self.state.set_key(self.deployment_details, self.task + ".state")

    @staticmethod
    def from_arguments(**kwargs: Any) -> "TaskPayload":
        """Create TaskPayload from command line arguments or flat parameters.

        Constructs a TaskPayload from flat keyword arguments, automatically
        creating nested objects and handling parameter aliases. Supports both
        CamelCase and snake_case parameter names for flexibility.

        Args:
            **kwargs: Keyword arguments including:
                - **Core Parameters**:
                    - task/Task (str): Operation type (required)
                    - client/Client (str): Client identifier
                    - force/Force (bool): Force execution flag
                    - dry_run/DryRun (bool): Dry run flag
                    - identity/Identity (str): User identity
                    - type/Type/automation_type (str): Automation type
                    - flow_control/FlowControl (str): Flow control setting
                - **DeploymentDetails Parameters**:
                    - deployment_details/DeploymentDetails: Deployment context
                    - portfolio/Portfolio (str): Portfolio name
                    - app/App (str): Application name
                    - build/Build (str): Build version
                    - branch/Branch (str): Branch name
                - **Additional Parameters**: Any parameters for nested objects

        Returns:
            A new TaskPayload instance with properly initialized nested objects.

        Raises:
            ValueError: If task parameter is missing or invalid.
            ValidationError: If deployment_details parameter is invalid.

        Examples:
            >>> # From command line args
            >>> payload = TaskPayload.from_arguments(
            ...     task="deploy",
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0",
            ...     force=True
            ... )
            >>> print(payload.task)
            'deploy'

            >>> # From mixed case parameters
            >>> payload = TaskPayload.from_arguments(
            ...     Task="release",
            ...     Portfolio="ecommerce",
            ...     dry_run=True
            ... )
            >>> print(payload.dry_run)
            True

        Parameter Aliases:
            This method accepts both CamelCase and snake_case parameter names
            for compatibility (e.g., both 'dry_run' and 'DryRun' are accepted).

        Nested Object Creation:
            If deployment_details is not provided, it will be created from the
            provided kwargs. Similarly, PackageDetails, ActionDetails, and
            StateDetails objects are created automatically.
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
        """Serialize model to dictionary with optimized defaults.

        Overrides default behavior to exclude None values and use field aliases
        by default for cleaner serialization output.

        Args:
            **kwargs: Keyword arguments for serialization options.
                     All standard Pydantic model_dump parameters are supported.

        Returns:
            Dictionary representation with None values excluded and aliases used.

        Examples:
            >>> payload = TaskPayload(task="deploy", deployment_details=dd)
            >>> data = payload.model_dump()
            >>> # Uses aliases like "Task" instead of "task"
            >>> print("Task" in data)
            True
            >>> # None values are excluded
            >>> print("FlowControl" in data)
            False  # Because flow_control is None
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)
