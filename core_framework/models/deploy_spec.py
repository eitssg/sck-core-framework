"""
DeploySpec Model Module
=======================

This module contains the DeploySpec class which provides a model for how CloudFormation templates
are to be deployed by core-automation.

The DeploySpec represents a collection of ActionSpec objects that define the actions to be performed
during a deployment. It provides validation to ensure no duplicate stack names and methods for
serialization to JSON and YAML formats.

Classes
-------
DeploySpec : BaseModel
    Model for deployment specifications containing a list of ActionSpec objects.

Examples
--------
Creating a DeploySpec with multiple actions::

    >>> from core_framework.models import ActionSpec
    >>> deploy_spec = DeploySpec(actions=[
    ...     ActionSpec(
    ...         name="create-vpc",
    ...         kind="create_stack",
    ...         params={"stack_name": "vpc-stack"}),
    ...     ActionSpec(
    ...         name="create-app",
    ...         kind="create_stack",
    ...         params={"stack_name": "app-stack"})
    ... ])

Loading from YAML stream and converting to JSON::

    >>> with open("deploy.actions", "r") as f:
    ...     deploy_spec = DeploySpec.from_yaml(f)
    >>> json_content = deploy_spec.to_json()
"""

from typing import Self, Any, TextIO
import warnings
from pydantic import BaseModel, ConfigDict, Field, model_validator

import core_framework as util

from .action_spec import ActionSpec


class DeploySpec(BaseModel):
    """
    DeploySpec: A model for deployment specifications containing ActionSpec objects.

    This class represents a collection of actions to be performed during a deployment.
    It provides validation to ensure no duplicate stack names and methods for
    serialization to various formats.

    Attributes
    ----------
    actions : list[ActionSpec]
        A list of ActionSpec objects defining the actions to be performed.
        Previously named 'action_specs' (deprecated).

    Examples
    --------
    Creating a DeploySpec with actions::

        >>> action = ActionSpec(name="create-s3", kind="create_stack",
        ...                    params={"stack_name": "my-bucket"})
        >>> deploy_spec = DeploySpec(actions=[action])

    Converting to YAML::

        >>> yaml_content = deploy_spec.to_yaml()

    Converting to JSON::

        >>> json_content = deploy_spec.to_json()

    Loading from YAML stream::

        >>> with open("deploy.actions", "r") as f:
        ...     deploy_spec = DeploySpec.from_yaml(f)

    Loading from JSON stream::

        >>> with open("deploy.actions", "r") as f:
        ...     deploy_spec = DeploySpec.from_json(f)
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    actions: list[ActionSpec] = Field(
        default_factory=list,
        alias="Actions",
        description="A list of ActionSpec objects defining the actions to be performed",
    )

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_fields(cls, values: Any) -> Any:
        """
        Handle the deprecation of 'action_specs' field in favor of 'actions'.

        This validator provides backward compatibility by mapping the deprecated
        'action_specs' field to the new 'actions' field.

        Parameters
        ----------
        values : Any
            The input values for model creation. Expected to be a dict for processing,
            but other types are passed through unchanged.

        Returns
        -------
        Any
            The validated and potentially modified values with deprecated fields
            mapped to their new equivalents.

        Raises
        ------
        ValueError
            If conflicting values are provided for both old and new field names.

        Warnings
        --------
        DeprecationWarning
            When the deprecated 'action_specs' field is used.
        """
        if isinstance(values, dict):
            # Handle action_specs -> actions deprecation
            actions_value = values.pop("Actions", None)
            if actions_value is None:
                actions_value = values.pop("actions", None)
            if actions_value is None:
                actions_value = values.pop("ActionSpecs", None)
            if actions_value is None:
                actions_value = values.pop("action_specs", None)
            if actions_value is None:
                actions_value = []

            values["actions"] = actions_value

        return values

    @model_validator(mode="after")
    def validate_deployspecs(self) -> Self:
        """
        Validate that the deployment spec will not create duplicate stack names.

        This validator checks for duplicate stack names across all actions of the same kind.
        Duplicates are only considered problematic if they are the same action kind
        (e.g., create_stack) targeting the same account and region.

        Returns
        -------
        Self
            The DeploySpec instance itself, for method chaining.

        Raises
        ------
        ValueError
            If duplicate stack names are found for the same action kind,
            account, and region combination.

        Notes
        -----
        The validation logic:
        1. Extracts stack_name from action parameters
        2. Determines target accounts and regions for each action
        3. Creates unique identifiers in format: {action.kind}/{account}/{region}/{stack_name}
        4. Raises ValueError if any identifier appears more than once
        """
        # When we pass in more than one action spec, we need to ensure that the stack names are unique.
        names = []
        for action in self.actions:

            stack_name = action.params.get("stack_name") or action.params.get("StackName")

            # Only do this if a stack name is provided.
            if not stack_name:
                continue

            accounts = action.params.get("accounts", action.params.get("Accounts", []))
            regions = action.params.get("regions", action.params.get("Regions", []))

            account = action.params.get("account", action.params.get("Account", None))
            region = action.params.get("region", action.params.get("Region", None))

            if account and account not in accounts:
                accounts.append(account)
            if region and region not in regions:
                regions.append(region)

            # If no accounts or regions specified, use defaults
            if not accounts:
                accounts = [account or "default"]
            if not regions:
                regions = [region or "default"]

            for account in accounts:
                for region in regions:
                    # Fixed: use action.kind instead of action.type
                    name = f"{action.kind}/{account}/{region}/{stack_name}"
                    if name in names:
                        raise ValueError(f"Duplicate stack name: {name}")
                    names.append(name)

        return self

    def to_yaml(self) -> str:
        """
        Convert the DeploySpec to YAML format.

        Returns
        -------
        str
            YAML string representation of the DeploySpec.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> yaml_content = deploy_spec.to_yaml()
            >>> print(yaml_content)
            Actions:
              - Name: create-vpc
                Kind: create_stack
                ...
        """
        return util.to_yaml(self.model_dump())

    def to_json(self) -> str:
        """
        Convert the DeploySpec to JSON format.

        Returns
        -------
        str
            JSON string representation of the DeploySpec.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> json_content = deploy_spec.to_json()
            >>> print(json_content)
            {
              "Actions": [
                {
                  "Name": "create-vpc",
                  "Kind": "create_stack",
                  ...
                }
              ]
            }
        """
        return util.to_json(self.model_dump())

    @classmethod
    def from_stream(cls, stream: TextIO | str, mimetype: str = "application/yaml") -> "DeploySpec":
        """
        Load a DeploySpec from a stream or string with specified mimetype.

        Parameters
        ----------
        stream : TextIO | str
            A file-like object or string containing the deployment specification data.
        mimetype : str, optional
            The MIME type of the data. Defaults to "application/yaml".
            Supported types: "application/yaml", "application/x-yaml", "text/yaml",
            "application/json", "text/json".

        Returns
        -------
        DeploySpec
            A new DeploySpec instance loaded from the provided data.

        Raises
        ------
        ValueError
            If the mimetype is not supported or if the data cannot be parsed.

        Examples
        --------
        From file stream::

            >>> with open("deploy.actions", "r") as f:
            ...     deploy_spec = DeploySpec.from_stream(f)

        From string with explicit mimetype::

            >>> yaml_content = '''
            ... Actions:
            ...   - Name: create-vpc
            ...     Kind: create_stack
            ...     Params:
            ...       stack_name: vpc-stack
            ... '''
            >>> deploy_spec = DeploySpec.from_stream(yaml_content, mimetype="application/yaml")
        """
        yaml_types = [
            "application/yaml",
            "application/x-yaml",
            "text/yaml",
            "text/x-yaml",
        ]
        json_types = ["application/json", "text/json"]

        if mimetype in yaml_types:
            return cls.from_yaml(stream)
        elif mimetype in json_types:
            return cls.from_json(stream)
        else:
            supported_types = yaml_types + json_types
            raise ValueError(f"Unsupported mimetype: {mimetype}. Supported types: {supported_types}")

    @classmethod
    def from_yaml(cls, stream: TextIO | str) -> "DeploySpec":
        """
        Load a DeploySpec from a YAML stream or string.

        Parameters
        ----------
        stream : TextIO | str
            A file-like object or string containing YAML data.

        Returns
        -------
        DeploySpec
            A new DeploySpec instance loaded from the YAML data.

        Raises
        ------
        ValueError
            If the YAML contains invalid data or cannot be parsed into a DeploySpec.

        Examples
        --------
        From file stream::

            >>> with open("deploy.actions", "r") as f:
            ...     deploy_spec = DeploySpec.from_yaml(f)

        From string::

            >>> yaml_content = '''
            ... Actions:
            ...   - Name: create-vpc
            ...     Kind: create_stack
            ...     Params:
            ...       stack_name: vpc-stack
            ... '''
            >>> deploy_spec = DeploySpec.from_yaml(yaml_content)
        """
        try:
            data = util.read_yaml(stream)
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Failed to load DeploySpec from YAML: {e}")

    @classmethod
    def from_json(cls, stream: TextIO | str) -> "DeploySpec":
        """
        Load a DeploySpec from a JSON stream or string.

        Parameters
        ----------
        stream : TextIO | str
            A file-like object or string containing JSON data.

        Returns
        -------
        DeploySpec
            A new DeploySpec instance loaded from the JSON data.

        Raises
        ------
        ValueError
            If the JSON contains invalid data or cannot be parsed into a DeploySpec.

        Examples
        --------
        From file stream::

            >>> with open("deploy.actions", "r") as f:
            ...     deploy_spec = DeploySpec.from_json(f)

        From string::

            >>> json_content = '''
            ... {
            ...   "Actions": [
            ...     {
            ...       "Name": "create-vpc",
            ...       "Kind": "create_stack",
            ...       "Params": {
            ...         "stack_name": "vpc-stack"
            ...       }
            ...     }
            ...   ]
            ... }
            ... '''
            >>> deploy_spec = DeploySpec.from_json(json_content)
        """
        try:
            data = util.read_json(stream)
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Failed to load DeploySpec from JSON: {e}")

    def add_action(self, action: ActionSpec) -> None:
        """
        Add an ActionSpec to the deployment specification.

        Parameters
        ----------
        action : ActionSpec
            The ActionSpec to add to the deployment.

        Raises
        ------
        ValueError
            If adding the action would create a duplicate stack name.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec()
            >>> action = ActionSpec(name="create-vpc", kind="create_stack",
            ...                    params={"stack_name": "vpc-stack"})
            >>> deploy_spec.add_action(action)
        """
        # Validate the action itself first
        if not isinstance(action, ActionSpec):
            raise ValueError("action must be an ActionSpec instance")

        # Create a temporary copy to test validation
        temp_actions = self.actions + [action]
        temp_spec = DeploySpec(actions=temp_actions)
        # This will raise ValueError if there are duplicates
        temp_spec.validate_deployspecs()

        # If validation passes, add the action
        self.actions.append(action)

    def remove_action(self, name: str) -> bool:
        """
        Remove an action by name from the deployment specification.

        Parameters
        ----------
        name : str
            The name of the action to remove.

        Returns
        -------
        bool
            True if the action was found and removed, False otherwise.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> removed = deploy_spec.remove_action("create-vpc")
            >>> print(removed)  # True if action was found and removed
        """
        for i, action in enumerate(self.actions):
            if action.name == name:
                self.actions.pop(i)
                return True
        return False

    def get_action(self, name: str) -> ActionSpec | None:
        """
        Get an action by name from the deployment specification.

        Parameters
        ----------
        name : str
            The name of the action to retrieve.

        Returns
        -------
        ActionSpec | None
            The ActionSpec if found, None otherwise.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> action = deploy_spec.get_action("create-vpc")
            >>> if action:
            ...     print(f"Found action: {action.name}")
        """
        for action in self.actions:
            if action.name == name:
                return action
        return None

    def get_actions_by_kind(self, kind: str) -> list[ActionSpec]:
        """
        Get all actions of a specific kind.

        Parameters
        ----------
        kind : str
            The kind of actions to retrieve (e.g., "create_stack", "delete_stack").

        Returns
        -------
        list[ActionSpec]
            List of ActionSpec objects matching the specified kind.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> stack_actions = deploy_spec.get_actions_by_kind("create_stack")
            >>> print(f"Found {len(stack_actions)} create_stack actions")
        """
        return [action for action in self.actions if action.kind == kind]

    def get_actions_by_scope(self, scope: str) -> list[ActionSpec]:
        """
        Get all actions of a specific scope.

        Parameters
        ----------
        scope : str
            The scope of actions to retrieve (e.g., "build", "branch", "app").

        Returns
        -------
        list[ActionSpec]
            List of ActionSpec objects matching the specified scope.

        Examples
        --------
        ::

            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> build_actions = deploy_spec.get_actions_by_scope("build")
            >>> print(f"Found {len(build_actions)} build scope actions")
        """
        return [action for action in self.actions if action.scope == scope]

    @property
    def action_count(self) -> int:
        """
        Get the number of actions in the deployment specification.

        Returns
        -------
        int
            The number of actions.
        """
        return len(self.actions)

    @property
    def is_empty(self) -> bool:
        """
        Check if the deployment specification is empty.

        Returns
        -------
        bool
            True if there are no actions, False otherwise.
        """
        return len(self.actions) == 0

    # Backward compatibility property
    @property
    def action_specs(self) -> list[ActionSpec]:
        """
        DEPRECATED: Use 'actions' instead. Returns the actions list for backward compatibility.

        Returns
        -------
        list[ActionSpec]
            The list of actions.

        Warnings
        --------
        DeprecationWarning
            When this property is accessed.
        """
        warnings.warn(
            "The 'action_specs' property is deprecated. Use 'actions' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.actions

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Override to exclude None values by default.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments passed to the parent model_dump method.
            All standard Pydantic model_dump parameters are supported.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the model with None values excluded by default.
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)

    def __len__(self) -> int:
        """
        Return the number of actions in the deployment specification.

        Returns
        -------
        int
            The number of actions.
        """
        return len(self.actions)

    def __iter__(self):
        """
        Iterate over the actions in the deployment specification.

        Yields
        ------
        ActionSpec
            Each action in the specification.
        """
        return iter(self.actions)

    def __getitem__(self, index: int) -> ActionSpec:
        """
        Get an action by index.

        Parameters
        ----------
        index : int
            The index of the action to retrieve.

        Returns
        -------
        ActionSpec
            The action at the specified index.

        Raises
        ------
        IndexError
            If the index is out of range.
        """
        return self.actions[index]

    def __str__(self) -> str:
        """
        Return a human-readable string representation.

        Returns
        -------
        str
            String showing the number of actions and their names.
        """
        if not self.actions:
            return "DeploySpec(empty)"
        action_names = [action.name for action in self.actions]
        return f"DeploySpec({len(self.actions)} actions: {', '.join(action_names)})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            Detailed representation showing the number of actions.
        """
        return f"DeploySpec(actions={len(self.actions)})"
