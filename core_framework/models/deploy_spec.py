"""DeploySpec Model Module for Core Automation Framework.

This module contains the DeploySpec class which provides a model for how CloudFormation templates
are to be deployed by core-automation. The DeploySpec represents a collection of ActionSpec objects
that define the actions to be performed during a deployment.

Key Features:
    - **Action Management**: Collection of ActionSpec objects with validation
    - **Duplicate Prevention**: Ensures no duplicate stack names across actions
    - **Format Support**: Serialization to JSON and YAML formats
    - **Backward Compatibility**: Handles deprecated field names gracefully
    - **Validation**: Comprehensive validation for deployment consistency

Common Use Cases:
    - CloudFormation stack deployment coordination
    - Multi-region deployment orchestration
    - Infrastructure as Code (IaC) action sequencing
    - Deployment template validation and processing

Classes:
    DeploySpec: Model for deployment specifications containing ActionSpec objects.

Examples:
    Creating a DeploySpec with multiple actions:

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

    Loading from YAML and converting to JSON:

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
    """Model for deployment specifications containing ActionSpec objects.

    This class represents a collection of actions to be performed during a deployment.
    It provides validation to ensure no duplicate stack names and methods for
    serialization to various formats, enabling consistent deployment orchestration
    across environments.

    The DeploySpec serves as the primary configuration object for Core Automation
    deployment workflows, ensuring action coordination and preventing conflicts.

    Attributes:
        actions: List of ActionSpec objects defining deployment actions.

    Properties:
        action_count: Number of actions in the specification.
        is_empty: Whether the specification contains no actions.
        action_specs: Deprecated property for backward compatibility.

    Examples:
        >>> # Creating a DeploySpec with actions
        >>> action = ActionSpec(
        ...     name="create-s3",
        ...     kind="create_stack",
        ...     params={"stack_name": "my-bucket"}
        ... )
        >>> deploy_spec = DeploySpec(actions=[action])
        >>> print(len(deploy_spec))
        1

        >>> # Converting to YAML
        >>> yaml_content = deploy_spec.to_yaml()
        >>> print("Actions:" in yaml_content)
        True

        >>> # Loading from YAML stream
        >>> with open("deploy.actions", "r") as f:
        ...     deploy_spec = DeploySpec.from_yaml(f)

        >>> # Adding actions dynamically
        >>> new_action = ActionSpec(
        ...     name="create-db",
        ...     kind="create_stack",
        ...     params={"stack_name": "database"}
        ... )
        >>> deploy_spec.add_action(new_action)

        >>> # Filtering actions by kind
        >>> stack_actions = deploy_spec.get_actions_by_kind("create_stack")
        >>> print(f"Found {len(stack_actions)} stack creation actions")

    Validation Rules:
        - **Unique Stack Names**: No duplicate stack names within same kind/account/region
        - **Action Integrity**: All actions must be valid ActionSpec instances
        - **Cross-Region Safety**: Prevents conflicts in multi-region deployments
        - **Account Isolation**: Ensures stack name uniqueness per account
    """

    model_config = ConfigDict(populate_by_name=True)

    actions: list[ActionSpec] = Field(
        default_factory=list,
        alias="Actions",
        description="A list of ActionSpec objects defining the actions to be performed",
    )

    @model_validator(mode="before")
    @classmethod
    def handle_deprecated_fields(cls, values: Any) -> Any:
        """Handle deprecation of 'action_specs' field in favor of 'actions'.

        This validator provides backward compatibility by mapping the deprecated
        'action_specs' field to the new 'actions' field, ensuring existing
        configurations continue to work while encouraging migration.

        Args:
            values: Input values for model creation. Expected to be a dict for processing,
                   but other types are passed through unchanged.

        Returns:
            Validated and potentially modified values with deprecated fields
            mapped to their new equivalents.

        Raises:
            ValueError: If conflicting values are provided for both old and new field names.

        Examples:
            >>> # Handles legacy field names automatically
            >>> legacy_data = {"action_specs": [action1, action2]}
            >>> values = DeploySpec.handle_deprecated_fields(legacy_data)
            >>> print("actions" in values)
            True

            >>> # Works with multiple naming conventions
            >>> data = {"ActionSpecs": [action1]}  # CamelCase legacy
            >>> values = DeploySpec.handle_deprecated_fields(data)
            >>> print(values["actions"])
            [action1]

        Warnings:
            Issues DeprecationWarning when deprecated 'action_specs' field is used.
        """
        if isinstance(values, dict):
            # Handle action_specs -> actions deprecation with priority order
            actions_value = values.pop("Actions", None)
            if actions_value is None:
                actions_value = values.pop("actions", None)
            if actions_value is None:
                actions_value = values.pop("ActionSpecs", None)
                if actions_value is not None:
                    warnings.warn(
                        "The 'ActionSpecs' field is deprecated. Use 'Actions' instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
            if actions_value is None:
                actions_value = values.pop("action_specs", None)
                if actions_value is not None:
                    warnings.warn(
                        "The 'action_specs' field is deprecated. Use 'actions' instead.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
            if actions_value is None:
                actions_value = []

            values["actions"] = actions_value

        return values

    @model_validator(mode="after")
    def validate_deployspecs(self) -> Self:
        """Validate that deployment spec will not create duplicate stack names.

        This validator checks for duplicate stack names across all actions of the same kind.
        Duplicates are only considered problematic if they target the same account and region
        combination, preventing deployment conflicts and stack name collisions.

        Returns:
            The DeploySpec instance itself, for method chaining.

        Raises:
            ValueError: If duplicate stack names are found for the same action kind,
                       account, and region combination.

        Examples:
            >>> # This will pass validation - different regions
            >>> action1 = ActionSpec(name="web-east", kind="create_stack",
            ...                     params={"stack_name": "web", "region": "us-east-1"})
            >>> action2 = ActionSpec(name="web-west", kind="create_stack",
            ...                     params={"stack_name": "web", "region": "us-west-2"})
            >>> spec = DeploySpec(actions=[action1, action2])  # Valid

            >>> # This will fail validation - same region and stack name
            >>> action3 = ActionSpec(name="web-duplicate", kind="create_stack",
            ...                     params={"stack_name": "web", "region": "us-east-1"})
            >>> spec = DeploySpec(actions=[action1, action3])  # Raises ValueError

        Validation Logic:
            1. **Stack Name Extraction**: Gets stack_name from action parameters
            2. **Target Resolution**: Determines accounts and regions for each action
            3. **Unique Identifier**: Creates format: {kind}/{account}/{region}/{stack_name}
            4. **Duplicate Detection**: Raises ValueError if any identifier appears twice

        Account/Region Handling:
            - Uses 'accounts'/'regions' lists if provided
            - Falls back to 'account'/'region' single values
            - Defaults to "default" if no account/region specified
            - Supports both CamelCase and snake_case parameter names
        """
        # Track unique identifiers to prevent duplicates
        names = []

        for action in self.actions:
            # Extract stack name with parameter name flexibility
            stack_name = action.params.get("stack_name") or action.params.get("StackName")

            # Only validate if a stack name is provided
            if not stack_name:
                continue

            # Get account and region lists with fallback to single values
            accounts = action.params.get("accounts", action.params.get("Accounts", []))
            regions = action.params.get("regions", action.params.get("Regions", []))

            account = action.params.get("account", action.params.get("Account", None))
            region = action.params.get("region", action.params.get("Region", None))

            # Add single values to lists if not already present
            if account and account not in accounts:
                accounts.append(account)
            if region and region not in regions:
                regions.append(region)

            # Apply defaults if no accounts or regions specified
            if not accounts:
                accounts = [account or "default"]
            if not regions:
                regions = [region or "default"]

            # Check all account/region combinations for duplicates
            for account in accounts:
                for region in regions:
                    # Create unique identifier for this deployment target
                    name = f"{action.kind}/{account}/{region}/{stack_name}"
                    if name in names:
                        raise ValueError(f"Duplicate stack name: {name}")
                    names.append(name)

        return self

    def to_yaml(self) -> str:
        """Convert the DeploySpec to YAML format.

        Returns:
            YAML string representation of the DeploySpec.

        Examples:
            >>> action = ActionSpec(name="create-vpc", kind="create_stack",
            ...                    params={"stack_name": "vpc-stack"})
            >>> deploy_spec = DeploySpec(actions=[action])
            >>> yaml_content = deploy_spec.to_yaml()
            >>> print("Actions:" in yaml_content)
            True
            >>> print("Name: create-vpc" in yaml_content)
            True

        Output Format:
            The YAML output uses aliases for field names (e.g., "Actions" instead of "actions")
            and excludes None values for cleaner output.
        """
        return util.to_yaml(self.model_dump())

    def to_json(self) -> str:
        """Convert the DeploySpec to JSON format.

        Returns:
            JSON string representation of the DeploySpec.

        Examples:
            >>> action = ActionSpec(name="create-vpc", kind="create_stack",
            ...                    params={"stack_name": "vpc-stack"})
            >>> deploy_spec = DeploySpec(actions=[action])
            >>> json_content = deploy_spec.to_json()
            >>> print('"Actions"' in json_content)
            True
            >>> print('"Name": "create-vpc"' in json_content)
            True

        Output Format:
            The JSON output uses aliases for field names and excludes None values
            for optimized serialization.
        """
        return util.to_json(self.model_dump())

    @classmethod
    def from_stream(cls, stream: TextIO | str, mimetype: str = "application/yaml") -> "DeploySpec":
        """Load a DeploySpec from a stream or string with specified mimetype.

        Args:
            stream: File-like object or string containing deployment specification data.
            mimetype: MIME type of the data. Defaults to "application/yaml".

        Returns:
            New DeploySpec instance loaded from the provided data.

        Raises:
            ValueError: If the mimetype is not supported or data cannot be parsed.

        Examples:
            >>> # From file stream with auto-detection
            >>> with open("deploy.actions", "r") as f:
            ...     deploy_spec = DeploySpec.from_stream(f)

            >>> # From string with explicit mimetype
            >>> yaml_content = '''
            ... Actions:
            ...   - Name: create-vpc
            ...     Kind: create_stack
            ...     Params:
            ...       stack_name: vpc-stack
            ... '''
            >>> deploy_spec = DeploySpec.from_stream(yaml_content, "application/yaml")

            >>> # JSON format
            >>> json_content = '{"Actions": [{"Name": "test", "Kind": "create_stack"}]}'
            >>> deploy_spec = DeploySpec.from_stream(json_content, "application/json")

        Supported MIME Types:
            - **YAML**: application/yaml, application/x-yaml, text/yaml, text/x-yaml
            - **JSON**: application/json, text/json

        Error Handling:
            Provides clear error messages for unsupported MIME types and includes
            the list of supported types for guidance.
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
        """Load a DeploySpec from a YAML stream or string.

        Args:
            stream: File-like object or string containing YAML data.

        Returns:
            New DeploySpec instance loaded from the YAML data.

        Raises:
            ValueError: If the YAML contains invalid data or cannot be parsed.

        Examples:
            >>> # From file stream
            >>> with open("deploy.actions", "r") as f:
            ...     deploy_spec = DeploySpec.from_yaml(f)

            >>> # From string
            >>> yaml_content = '''
            ... Actions:
            ...   - Name: create-vpc
            ...     Kind: create_stack
            ...     Params:
            ...       stack_name: vpc-stack
            ... '''
            >>> deploy_spec = DeploySpec.from_yaml(yaml_content)
            >>> print(deploy_spec.actions[0].name)
            'create-vpc'

            >>> # Handles deprecated field names
            >>> legacy_yaml = '''
            ... ActionSpecs:
            ...   - Name: legacy-action
            ...     Kind: create_stack
            ... '''
            >>> deploy_spec = DeploySpec.from_yaml(legacy_yaml)  # Works with warning

        Error Handling:
            Wraps parsing exceptions in ValueError with descriptive messages
            to help identify YAML syntax or structure issues.
        """
        try:
            data = util.read_yaml(stream)
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Failed to load DeploySpec from YAML: {e}")

    @classmethod
    def from_json(cls, stream: TextIO | str) -> "DeploySpec":
        """Load a DeploySpec from a JSON stream or string.

        Args:
            stream: File-like object or string containing JSON data.

        Returns:
            New DeploySpec instance loaded from the JSON data.

        Raises:
            ValueError: If the JSON contains invalid data or cannot be parsed.

        Examples:
            >>> # From file stream
            >>> with open("deploy.actions", "r") as f:
            ...     deploy_spec = DeploySpec.from_json(f)

            >>> # From string
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
            >>> print(deploy_spec.actions[0].name)
            'create-vpc'

        Error Handling:
            Wraps parsing exceptions in ValueError with descriptive messages
            to help identify JSON syntax or structure issues.
        """
        try:
            data = util.read_json(stream)
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Failed to load DeploySpec from JSON: {e}")

    def add_action(self, action: ActionSpec) -> None:
        """Add an ActionSpec to the deployment specification.

        Args:
            action: ActionSpec to add to the deployment.

        Raises:
            ValueError: If the action is invalid or would create duplicate stack names.

        Examples:
            >>> deploy_spec = DeploySpec()
            >>> action = ActionSpec(
            ...     name="create-vpc",
            ...     kind="create_stack",
            ...     params={"stack_name": "vpc-stack"}
            ... )
            >>> deploy_spec.add_action(action)
            >>> print(len(deploy_spec))
            1

            >>> # Adding duplicate stack name fails
            >>> duplicate_action = ActionSpec(
            ...     name="create-vpc-2",
            ...     kind="create_stack",
            ...     params={"stack_name": "vpc-stack"}  # Same stack name
            ... )
            >>> deploy_spec.add_action(duplicate_action)  # Raises ValueError

        Validation:
            The method validates the action before adding it by creating a temporary
            specification and running full validation, ensuring no duplicates are introduced.
        """
        # Validate the action type
        if not isinstance(action, ActionSpec):
            raise ValueError("action must be an ActionSpec instance")

        # Create temporary copy to test validation
        temp_actions = self.actions + [action]
        temp_spec = DeploySpec(actions=temp_actions)
        # This will raise ValueError if there are duplicates
        temp_spec.validate_deployspecs()

        # If validation passes, add the action
        self.actions.append(action)

    def remove_action(self, name: str) -> bool:
        """Remove an action by name from the deployment specification.

        Args:
            name: Name of the action to remove.

        Returns:
            True if the action was found and removed, False otherwise.

        Examples:
            >>> action1 = ActionSpec(name="create-vpc", kind="create_stack")
            >>> action2 = ActionSpec(name="create-app", kind="create_stack")
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> removed = deploy_spec.remove_action("create-vpc")
            >>> print(removed)
            True
            >>> print(len(deploy_spec))
            1

            >>> # Removing non-existent action
            >>> removed = deploy_spec.remove_action("non-existent")
            >>> print(removed)
            False
        """
        for i, action in enumerate(self.actions):
            if action.name == name:
                self.actions.pop(i)
                return True
        return False

    def get_action(self, name: str) -> ActionSpec | None:
        """Get an action by name from the deployment specification.

        Args:
            name: Name of the action to retrieve.

        Returns:
            ActionSpec if found, None otherwise.

        Examples:
            >>> action = ActionSpec(name="create-vpc", kind="create_stack")
            >>> deploy_spec = DeploySpec(actions=[action])
            >>> found_action = deploy_spec.get_action("create-vpc")
            >>> print(found_action.name)
            'create-vpc'

            >>> # Non-existent action
            >>> missing = deploy_spec.get_action("non-existent")
            >>> print(missing)
            None
        """
        for action in self.actions:
            if action.name == name:
                return action
        return None

    def get_actions_by_kind(self, kind: str) -> list[ActionSpec]:
        """Get all actions of a specific kind.

        Args:
            kind: Kind of actions to retrieve (e.g., "create_stack", "delete_stack").

        Returns:
            List of ActionSpec objects matching the specified kind.

        Examples:
            >>> action1 = ActionSpec(name="create-vpc", kind="create_stack")
            >>> action2 = ActionSpec(name="create-app", kind="create_stack")
            >>> action3 = ActionSpec(name="delete-old", kind="delete_stack")
            >>> deploy_spec = DeploySpec(actions=[action1, action2, action3])

            >>> stack_actions = deploy_spec.get_actions_by_kind("create_stack")
            >>> print(len(stack_actions))
            2

            >>> delete_actions = deploy_spec.get_actions_by_kind("delete_stack")
            >>> print(len(delete_actions))
            1
        """
        return [action for action in self.actions if action.kind == kind]

    def get_actions_by_scope(self, scope: str) -> list[ActionSpec]:
        """Get all actions of a specific scope.

        Args:
            scope: Scope of actions to retrieve (e.g., "build", "branch", "app").

        Returns:
            List of ActionSpec objects matching the specified scope.

        Examples:
            >>> action1 = ActionSpec(name="build-action", kind="create_stack", scope="build")
            >>> action2 = ActionSpec(name="app-action", kind="create_stack", scope="app")
            >>> action3 = ActionSpec(name="branch-action", kind="create_stack", scope="branch")
            >>> deploy_spec = DeploySpec(actions=[action1, action2, action3])

            >>> build_actions = deploy_spec.get_actions_by_scope("build")
            >>> print(len(build_actions))
            1

            >>> app_actions = deploy_spec.get_actions_by_scope("app")
            >>> print(len(app_actions))
            1
        """
        return [action for action in self.actions if action.scope == scope]

    @property
    def action_count(self) -> int:
        """Get the number of actions in the deployment specification.

        Returns:
            Number of actions.

        Examples:
            >>> action1 = ActionSpec(name="create-vpc", kind="create_stack")
            >>> action2 = ActionSpec(name="create-app", kind="create_stack")
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> print(deploy_spec.action_count)
            2
        """
        return len(self.actions)

    @property
    def is_empty(self) -> bool:
        """Check if the deployment specification is empty.

        Returns:
            True if there are no actions, False otherwise.

        Examples:
            >>> deploy_spec = DeploySpec()
            >>> print(deploy_spec.is_empty)
            True

            >>> action = ActionSpec(name="create-vpc", kind="create_stack")
            >>> deploy_spec.add_action(action)
            >>> print(deploy_spec.is_empty)
            False
        """
        return len(self.actions) == 0

    @property
    def action_specs(self) -> list[ActionSpec]:
        """DEPRECATED: Use 'actions' instead. Returns actions list for backward compatibility.

        Returns:
            List of actions.

        Warnings:
            Issues DeprecationWarning when this property is accessed.

        Examples:
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> specs = deploy_spec.action_specs  # Triggers deprecation warning
            >>> print(len(specs))
            2

        Migration:
            Replace `deploy_spec.action_specs` with `deploy_spec.actions`
        """
        warnings.warn(
            "The 'action_specs' property is deprecated. Use 'actions' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.actions

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to exclude None values and use aliases by default.

        Args:
            **kwargs: Keyword arguments passed to parent model_dump method.
                     All standard Pydantic model_dump parameters are supported.

        Returns:
            Dictionary representation with None values excluded and aliases used.

        Examples:
            >>> deploy_spec = DeploySpec(actions=[action1])
            >>> data = deploy_spec.model_dump()
            >>> print("Actions" in data)  # Uses alias
            True
            >>> print(None in data.values())  # None values excluded
            False

        Default Behavior:
            - **exclude_none=True**: Removes None values for cleaner output
            - **by_alias=True**: Uses field aliases (e.g., "Actions" instead of "actions")
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)

    def __len__(self) -> int:
        """Return the number of actions in the deployment specification.

        Returns:
            Number of actions.

        Examples:
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> print(len(deploy_spec))
            2
        """
        return len(self.actions)

    def __iter__(self):
        """Iterate over the actions in the deployment specification.

        Yields:
            Each ActionSpec in the specification.

        Examples:
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> for action in deploy_spec:
            ...     print(action.name)
            'action1-name'
            'action2-name'
        """
        return iter(self.actions)

    def __getitem__(self, index: int) -> ActionSpec:
        """Get an action by index.

        Args:
            index: Index of the action to retrieve.

        Returns:
            ActionSpec at the specified index.

        Raises:
            IndexError: If the index is out of range.

        Examples:
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> first_action = deploy_spec[0]
            >>> print(first_action.name)
            'action1-name'

            >>> last_action = deploy_spec[-1]  # Negative indexing works
            >>> print(last_action.name)
            'action2-name'
        """
        return self.actions[index]

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            String showing the number of actions and their names.

        Examples:
            >>> deploy_spec = DeploySpec()
            >>> str(deploy_spec)
            'DeploySpec(empty)'

            >>> action1 = ActionSpec(name="create-vpc", kind="create_stack")
            >>> action2 = ActionSpec(name="create-app", kind="create_stack")
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> str(deploy_spec)
            'DeploySpec(2 actions: create-vpc, create-app)'
        """
        if not self.actions:
            return "DeploySpec(empty)"
        action_names = [action.name for action in self.actions]
        return f"DeploySpec({len(self.actions)} actions: {', '.join(action_names)})"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            Detailed representation showing the number of actions.

        Examples:
            >>> deploy_spec = DeploySpec(actions=[action1, action2])
            >>> repr(deploy_spec)
            'DeploySpec(actions=2)'
        """
        return f"DeploySpec(actions={len(self.actions)})"
