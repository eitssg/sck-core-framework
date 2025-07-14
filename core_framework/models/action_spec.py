"""
ActionSpec Model Module
=======================

This module contains the ActionSpec class which provides a model for how Tasks or Actions are to
be provided to the core-execute library.

The ActionSpec class defines actions that can be performed by the Core Automation framework. 
These actions can include creating or deleting AWS resources, updating user permissions, and more.

Things that you wouldn't necessarily do in a CloudFormation template.

Classes
-------
ActionSpec : BaseModel
    Model for action specifications with fields for name, kind, parameters, dependencies, and metadata.

Constants
---------
NAME : str
    The name field constant
LABEL : str
    DEPRECATED: Use NAME instead
TYPE : str
    DEPRECATED: Use KIND instead
KIND : str
    The kind field constant
DEPENDS_ON : str
    The depends_on field constant
PARAMS : str
    The params field constant
SCOPE : str
    The scope field constant

Note
----
Consider moving this to the core-execute library as it is used almost exclusively by the core-execute library.
"""

from typing import Any
import warnings
from collections import OrderedDict
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    SerializationInfo,
    model_serializer,
    field_validator,
    model_validator,
)


# Give constants for the keys in the definition
NAME = "name"
""" The name of the name field in the Actions object.

    Value: name
"""

LABEL = "label"  # DEPRECATED: Use NAME instead
""" DEPRECATED: Use NAME instead. The name of the label field in the Actions object.

    Value: label
"""
TYPE = "type"  # DEPRECATED: Use KIND instead
""" DEPRECATED: Use KIND instead. The name of the type field in the Actions object.

    Value: type
"""

KIND = "kind"
""" The name of the kind field in the Actions object.

    Value: kind
"""
DEPENDS_ON = "depends_on"
""" The name of the depends_on field in the Actions object.

    Value: depends_on
"""
PARAMS = "params"
""" The name of the params field in the Actions object.

    Value: params
"""
SCOPE = "scope"
""" The name of the scope field in the Actions object.

    Value: scope
"""
ACCOUNT = "account"
""" The name of the account field in the Actions object.

    Core automation uses the value of this field to determine which account to deploy the stack to.
    If Core does not have access to the account with the appropriate role, deployments will fail.

    Value: account
"""
REGION = "region"
""" The name of the region field in the Actions object.

    Core automation uses the value of this field to determine which region to deploy the stack to.

    Value: region
"""
TAGS = "tags"
""" tags can be defined on the action that will be added to all resources in the deployment.  BaseAction implementations
    can use these tags as necessary.
"""
USER_NAME = "user_name"
""" The name of the user_name field in the Actions object.

    Core automation uses the value of this field to determine which user to deploy in IAM.

    There is a special action for add/delete/update users.  This is the Username to be applied to the action.

    Value: user_name
"""


class ActionSpec(BaseModel):
    """
    The ActionSpec class defines an "action" or "task" that Core Automation will perform when deploying infrastructure to your Cloud.

    Tasks could include adding tags to resources, adjusting DNS entries, etc. Tasks are executed by core-execute
    and are defined in the core-execute.actionlib library.

    Attributes
    ----------
    name : str
        The name of the action. A unique identifier for the action spec
    kind : str
        The action kind. This is the name of the action spec (e.g. create_user, create_stack, etc.)
    action : str | None
        The action to perform as defined by the execute.actionlib module
    scope : str
        The scope of the action (optional). Examples: portfolio, app, branch, or build.
    params : dict[str, Any]
        The parameters for the action. This is a dictionary of parameters that the action requires
    depends_on : list[str]
        A list of names of actions that this action depends on. Scoped to the single deployspec.yaml
    condition : str | None
        Condition clauses. In code, the default is 'True'
    before : list[str] | None
        Before is a list of actions that should be performed before this one
    after : list[str] | None
        After is a list of actions that should be performed after this one
    save_outputs : bool
        SaveOutputs is a flag to save the outputs of the action
    lifecycle_hooks : list['ActionSpec'] | None
        Lifecycle Hooks. A list of ActionSpec objects

    Examples
    --------
    Creating a simple CloudFormation stack action::

        >>> action = ActionSpec(
        ...     name="create-s3-bucket",
        ...     kind="create_stack",
        ...     params={
        ...         "stack_name": "my-s3-bucket",
        ...         "template": "s3-bucket-template.yaml"
        ...     }
        ... )

    Creating an action with dependencies::

        >>> action = ActionSpec(
        ...     name="create-lambda",
        ...     kind="create_stack",
        ...     depends_on=["create-s3-bucket"],
        ...     params={
        ...         "stack_name": "my-lambda-function",
        ...         "template": "lambda-template.yaml"
        ...     }
        ... )

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    name: str = Field(
        ...,
        alias="Name",
        description="The name of the action.  A unique identifier for the action",
        min_length=1,
    )

    kind: str = Field(
        ...,
        alias="Kind",
        description="The action kind.  This is the snake_case of the action in core_execute.actionlib",
        min_length=1,
    )

    action: str | None = Field(
        alias="Action",
        description="The action to perform as defined by the execute.actionlib module",
        default=None,
    )

    depends_on: list[str] = Field(
        alias="DependsOn",
        description="A list of names of actions that this action depends on",
        default_factory=list,
    )

    params: dict[str, Any] = Field(
        ...,
        alias="Params",
        description="The parameters for the action",
    )

    scope: str = Field(
        alias="Scope",
        description="The scope of the action.  This is used to group actions together. Project/Portfolio, App, Branch, or Build",
        default="build",
    )

    # Optional fields that are not required for the action

    condition: str | None = Field(
        alias="Condition",
        description="Condition clauses.  In code, the default is 'True'",
        default=None,
    )

    before: list[str] | None = Field(
        alias="Before",
        description="Before is a list of actions that should be performed before this one",
        default=None,
    )

    after: list[str] | None = Field(
        alias="After",
        description="After is a list of actions that should be performed after this one",
        default=None,
    )

    save_outputs: bool = Field(
        alias="SaveOutputs",
        description="SaveOutputs is a flag to save the outputs of the action",
        default=False,
    )

    lifecycle_hooks: list["ActionSpec"] | None = Field(
        alias="LifecycleHooks",
        description="Lifecycle Hooks.  A list of ActionSpec objects",
        default=None,
    )

    @model_validator(mode="before")
    @classmethod
    def handle_deprecations(cls, values: Any) -> Any:
        """
        Handle the deprecation of 'label' and 'type' fields in favor of 'name' and 'kind'.

        This validator provides backward compatibility by mapping deprecated field names
        to their new equivalents and issuing appropriate warnings.

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
            When deprecated field names are used.
        """
        if isinstance(values, dict):
            # Handle label -> name deprecation
            label_value = values.get("label") or values.get("Label")
            name_value = values.get("name") or values.get("Name")

            if label_value and not name_value:
                warnings.warn(
                    "The 'label' field is deprecated and will be removed in a future version. "
                    "Please use 'name' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                values["name"] = label_value
                values["Name"] = label_value
            elif label_value and name_value:
                if label_value != name_value:
                    raise ValueError(
                        f"Conflicting values: label='{label_value}' and name='{name_value}'. "
                        "Please use only 'name' as 'label' is deprecated."
                    )
                warnings.warn(
                    "The 'label' field is deprecated. Please use only 'name'.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            # Handle type -> kind deprecation
            type_value = values.get("type") or values.get("Type")
            kind_value = values.get("kind") or values.get("Kind")

            if type_value and not kind_value:
                warnings.warn(
                    "The 'type' field is deprecated and will be removed in a future version. "
                    "Please use 'kind' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                values["kind"] = type_value
                values["Kind"] = type_value
            elif type_value and kind_value:
                if type_value != kind_value:
                    raise ValueError(
                        f"Conflicting values: type='{type_value}' and kind='{kind_value}'. "
                        "Please use only 'kind' as 'type' is deprecated."
                    )
                warnings.warn(
                    "The 'type' field is deprecated. Please use only 'kind'.",
                    DeprecationWarning,
                    stacklevel=2,
                )
        return values

    @field_validator("depends_on", mode="before")
    @classmethod
    def validate_depends_on(cls, value) -> list[str]:
        """
        Validate and normalize depends_on field values.

        Parameters
        ----------
        value : str | list[str] | None
            The depends_on value to validate. Can be a string, list of strings, or None.

        Returns
        -------
        list[str]
            A list of dependency names. Empty list if None was provided.

        Raises
        ------
        ValueError
            If value is not a string, list of strings, or None.
            If any item in a list is not a string.
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            # Validate all items are strings
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(
                        f"All items in depends_on must be strings, got {type(item)}"
                    )
            return value
        raise ValueError(
            f"Invalid depends_on value: {value}. Must be a string or a list of strings"
        )

    @field_validator("kind", mode="before")
    @classmethod
    def validate_action_kind(cls, value) -> str:
        """
        Validate and normalize action kind values.

        Removes 'aws.' prefix from kind values for backward compatibility.

        Parameters
        ----------
        value : str
            The kind value to validate and normalize.

        Returns
        -------
        str
            The normalized kind value with 'aws.' prefix removed if present.
        """
        if value and isinstance(value, str):
            if value.startswith("aws."):
                value = value.lstrip("aws.")
        return value

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value) -> str:
        """
        Validate that scope is one of the allowed values.

        Parameters
        ----------
        value : str
            The scope value to validate.

        Returns
        -------
        str
            The validated scope value.

        Raises
        ------
        ValueError
            If scope is not one of the allowed values.
        """
        scope_list = cls.get_scope_list()
        if value not in scope_list:
            raise ValueError(f"Invalid scope: {value}. Must be one of: {scope_list}")
        return value

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, value: str) -> str:
        """
        Validate that name contains only alphanumeric characters, hyphens, and underscores.

        Parameters
        ----------
        value : str
            The name value to validate.

        Returns
        -------
        str
            The validated name value.

        Raises
        ------
        ValueError
            If name is empty, contains invalid characters, starts/ends with hyphen,
            or exceeds maximum length.
        """
        import re

        if not value or not value.strip():
            raise ValueError("Name cannot be empty or whitespace")
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError(
                f"Name '{value}' must contain only alphanumeric characters, hyphens, and underscores. "
                f"No spaces or special characters allowed."
            )
        if value.startswith("-") or value.endswith("-"):
            raise ValueError(f"Name '{value}' cannot start or end with a hyphen")
        if len(value) > 63:  # AWS resource name limit
            raise ValueError(
                f"Name '{value}' is too long. Maximum length is 63 characters."
            )
        return value

    @field_validator("before", "after", mode="before")
    @classmethod
    def validate_action_lists(cls, value) -> list[str] | None:
        """
        Validate before/after action lists.

        Parameters
        ----------
        value : str | list[str] | None
            The before/after value to validate. Can be a string, list of strings, or None.

        Returns
        -------
        list[str] | None
            A list of action names or None if input was None.

        Raises
        ------
        ValueError
            If value is not a string, list of strings, or None.
            If any item in a list is not a string.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            # Validate all items are strings
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(
                        f"All items in list must be strings, got {type(item)}"
                    )
            return value
        raise ValueError("Must be a string or a list of strings")

    @model_validator(mode="after")
    def validate_no_self_dependency(self) -> "ActionSpec":
        """
        Validate that action doesn't depend on itself.

        Returns
        -------
        ActionSpec
            The validated instance.

        Raises
        ------
        ValueError
            If the action depends on itself through depends_on, before, or after fields.
        """
        if self.name in self.depends_on:
            raise ValueError(f"Action '{self.name}' cannot depend on itself")
        if self.before and self.name in self.before:
            raise ValueError(f"Action '{self.name}' cannot be before itself")
        if self.after and self.name in self.after:
            raise ValueError(f"Action '{self.name}' cannot be after itself")
        return self

    @classmethod
    def get_scope_list(cls) -> list[str]:
        """
        Get the list of valid scopes.

        Returns
        -------
        list[str]
            List of valid scope values.
        """
        return ["build", "branch", "app", "portfolio"]

    def has_dependencies(self) -> bool:
        """
        Check if this action has any dependencies.

        Returns
        -------
        bool
            True if the action has dependencies, False otherwise.
        """
        return bool(self.depends_on)

    def is_conditional(self) -> bool:
        """
        Check if this action has a condition.

        Returns
        -------
        bool
            True if the action has a condition, False otherwise.
        """
        return self.condition is not None

    def get_execution_order_dependencies(self) -> list[str]:
        """
        Get all dependencies that affect execution order.

        Returns
        -------
        list[str]
            List of dependency names including depends_on and before dependencies.
        """
        dependencies = self.depends_on.copy()
        if self.before:
            dependencies.extend(self.before)
        return dependencies

    # Backward compatibility properties
    @property
    def label(self) -> str:
        """
        DEPRECATED: Use 'name' instead. Returns the name value for backward compatibility.

        Returns
        -------
        str
            The name value.

        Warnings
        --------
        DeprecationWarning
            When this property is accessed.
        """
        warnings.warn(
            "The 'label' property is deprecated. Use 'name' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.name

    @property
    def type(self) -> str:
        """
        DEPRECATED: Use 'kind' instead. Returns the kind value for backward compatibility.

        Returns
        -------
        str
            The kind value.

        Warnings
        --------
        DeprecationWarning
            When this property is accessed.
        """
        warnings.warn(
            "The 'type' property is deprecated. Use 'kind' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.kind

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

    @model_serializer
    def ser_model(self, info: SerializationInfo) -> OrderedDict:
        """
        Serialize the model to an OrderedDict in a specific order.

        Respects exclude_none and by_alias parameters, and uses Field aliases.

        Parameters
        ----------
        info : SerializationInfo
            Serialization information containing exclude_none and by_alias settings.

        Returns
        -------
        OrderedDict
            Serialized model data in the specified field order.
        """
        exclude_none = info.exclude_none
        by_alias = info.by_alias

        # Only specify the field names in the desired order
        field_order = [
            "name",
            "kind",  # Changed from "type" to "kind"
            "action",
            "depends_on",
            "params",
            "scope",
            "condition",
            "before",
            "after",
            "save_outputs",
            "lifecycle_hooks",
        ]

        out = OrderedDict()
        for field in field_order:
            value = getattr(self, field)
            if exclude_none and value is None:
                continue
            if exclude_none and isinstance(value, list) and len(value) == 0:
                continue

            # Get the alias from the Field definition if by_alias is True
            if by_alias:
                field_info = ActionSpec.model_fields.get(field)
                if field_info and field_info.alias:
                    key = field_info.alias
                else:
                    key = field
            else:
                key = field

            # For nested models, call their model_dump if needed
            if hasattr(value, "model_dump"):
                value = value.model_dump(exclude_none=exclude_none, by_alias=by_alias)
            elif isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                value = [
                    item.model_dump(exclude_none=exclude_none, by_alias=by_alias)
                    for item in value
                ]

            out[key] = value
        return out

    def __str__(self) -> str:
        """
        String representation of the action.

        Returns
        -------
        str
            Human-readable string representation showing key attributes.
        """
        return (
            f"ActionSpec(name='{self.name}', kind='{self.kind}', scope='{self.scope}')"
        )

    def __repr__(self) -> str:
        """
        Detailed string representation of the action.

        Returns
        -------
        str
            Detailed representation for debugging showing name, kind, scope, and dependencies.
        """
        return f"ActionSpec(name='{self.name}', kind='{self.kind}', scope='{self.scope}', depends_on={self.depends_on})"
