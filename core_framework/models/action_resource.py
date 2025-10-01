"""ActionResource Model for Core Automation Framework.

This module defines the ActionResource class for specifying automation tasks
that can be performed by the Core Automation framework, such as creating AWS
resources, managing user permissions, and other operations.

Classes:
    ActionSpec: Base parameters model for action configuration.
    ActionResource: Complete action specification with validation and execution metadata.
"""

from os import name
from typing import Any, Dict
import re
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
from .action_hook import HookResource


class ActionMetadata(BaseModel):
    """Action metadata following Kubernetes/Helm conventions."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True, extra="allow")

    name: str | None = Field(description="Action name", alias="Name", default=None)

    namespace: str | None = Field(description="Action namespace", alias="Namespace", default=None)
    labels: Dict[str, str] | None = Field(description="Key-value labels", alias="Labels", default=None)
    annotations: Dict[str, str] | None = Field(description="Additional annotations", alias="Annotations", default=None)

    # SCK-specific extensions
    description: str | None = Field(description="Human-readable description", alias="Description", default=None)
    save_outputs: bool | None = Field(description="Override save_outputs behavior", alias="SaveOutputs", default=None)

    @property
    def label(self) -> str:
        """Get full action name including namespace if present."""
        if self.namespace:
            return f"{self.namespace}:action/{self.name}"
        return self.name or "unnamed-action"

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate name follows AWS/Kubernetes resource naming conventions."""

        if not value:
            return value

        # Length validation (AWS/K8s standard)
        if len(value) > 63:
            raise ValueError(f"Name '{value}' exceeds 63 character limit")

        if len(value) < 1:
            raise ValueError("Name cannot be empty")

        # AWS/K8s naming pattern: alphanumeric and hyphens only
        if not re.match(r"^[a-zA-Z0-9-]+$", value):
            raise ValueError(f"Name '{value}' can only contain letters, numbers, and hyphens")

        # Must start and end with alphanumeric (handles single chars correctly)
        if value.startswith("-") or value.endswith("-"):
            raise ValueError(f"Name '{value}' must start and end with letter or number")

        # No consecutive hyphens
        if "--" in value:
            raise ValueError(f"Name '{value}' cannot contain consecutive hyphens")

        return value

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class ActionSpec(BaseModel):
    """Base parameters model for action configuration.

    Provides common parameters required by most actions, particularly AWS-related
    actions that need account and region specification.
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    account: str = Field(
        ...,
        alias="Account",
        description="AWS account ID where this action executes",
    )
    region: str = Field(
        ...,
        alias="Region",
        description="AWS region where this action executes",
    )

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Serialize model with optimized defaults."""
        kwargs.setdefault("exclude_unset", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class ActionResource(BaseModel):
    """Complete specification for Core Automation actions.

    Defines an automation task that Core Automation will perform when deploying
    infrastructure. Tasks include creating CloudFormation stacks, managing resources,
    updating configurations, etc.

    The class provides validation for action integrity, dependency management,
    and output organization to ensure reliable automation workflows.

    Examples::

        # Returns: Basic action:
        action = ActionResource(
        kind="AWS::CreateStack",
        metadata=ActionMetadata(name="create-vpc"),
        spec={"stack_name": "vpc-stack", "template": "vpc.yaml"}
        )

        # Returns: Action with dependencies:
        action = ActionResource(
        kind="AWS::CreateStack",
        metadata=ActionMetadata(name="create-database"),
        spec={"stack_name": "db-stack"},
        depends_on=["create-vpc"]
        )
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    apiVersion: str = Field(
        alias="ApiVersion",
        description="API version (default: v1)",
        default="v1",
    )

    name: str | None = Field(
        alias="Name",
        description="DEPRECATED: Use metadata.name instead",
        deprecated=True,
        default=None,
    )

    kind: str = Field(
        ...,
        alias="Kind",
        description="Action type (e.g., 'AWS::CreateStack', 'send-email')",
        min_length=1,
    )

    metadata: ActionMetadata | None = Field(
        description="Action metadata and documentation",
        alias="Metadata",
        default=None,
    )

    depends_on: list[str] = Field(
        alias="DependsOn",
        description="Actions that must complete successfully before this action",
        default=[],
    )

    spec: dict[str, Any] = Field(
        ...,
        alias="Spec",
        description="Action-specific parameters (supports Jinja2 variables)",
    )

    scope: str = Field(
        alias="Scope",
        description="Execution scope: 'portfolio', 'app', 'branch', or 'build'",
        default="build",
    )

    condition: str | None = Field(
        alias="Condition",
        description="Python expression for conditional execution",
        default=None,
    )

    before: list[str] | None = Field(
        alias="Before",
        description="Actions that should execute after this action (soft ordering)",
        default=None,
    )

    after: list[str] | None = Field(
        alias="After",
        description="Actions that should execute before this action (soft ordering)",
        default=None,
    )

    save_outputs: bool | None = Field(
        alias="SaveOutputs",
        description="Save action outputs to state system for other actions",
        default=None,
    )

    lifecycle_hooks: list[HookResource] | None = Field(
        alias="LifecycleHooks",
        description="Additional hooks actions to execute at lifecycle points",
        default=None,
    )

    @property
    def action_name(self) -> str:
        """Get the action name, extracting from metadata or name field."""
        if self.metadata and self.metadata.name:
            return self.metadata.name
        return self.name.split("/")[-1] if self.name else ""

    @property
    def action_key(self) -> str:
        """Get the full action key including namespace if present."""
        if self.metadata and self.metadata.name:
            if self.metadata.namespace:
                return f"{self.metadata.namespace}/{self.metadata.name}"
            return self.metadata.name
        return self.name if self.name else ""

    @property
    def output_namespace(self) -> str | None:
        """Calculate output namespace for organizing action results."""
        if self.save_outputs is False:
            return None

        if self.metadata:
            if self.metadata.namespace:
                return f"{self.metadata.namespace}:output"
            else:
                return "output"

        # Get the namespace for the action, defaults to name
        namespace_part = self.action_name.split("/")[0]
        return namespace_part.replace(":action", ":output")

    @property
    def state_namespace(self) -> str | None:
        """Get state namespace for variable storage."""

        if self.metadata:
            if self.metadata.namespace:
                return f"{self.metadata.namespace}:var/{self.metadata.name}"
            elif self.metadata.name:
                return f"var/{self.metadata.name}"

        if not self.name:
            return None
        return self.name.replace(":action/", ":var/")

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: Any) -> Any:  # noqa: C901
        """Handle metadata creation and deprecated field migration."""
        if not isinstance(values, dict):
            return values

        # Handle deprecated fields first
        label_value = values.pop("label", None) or values.pop("Label", None)
        name_value = values.pop("name", None) or values.pop("Name", None)
        type_value = values.pop("type", None) or values.pop("Type", None)
        kind_value = values.pop("kind", None) or values.pop("Kind", None)

        # Handle deprecated label -> name
        if label_value:
            warnings.warn("The 'label' field is deprecated. Use 'name' instead.", DeprecationWarning, stacklevel=2)
            if not name_value:
                name_value = label_value
            elif name_value and label_value != name_value:
                raise ValueError(f"Conflicting label='{label_value}' and name='{name_value}'")

        # Handle deprecated type -> kind
        if type_value:
            warnings.warn("The 'type' field is deprecated. Use 'kind' instead.", DeprecationWarning, stacklevel=2)
            if not kind_value:
                kind_value = type_value
            elif type_value and kind_value and type_value != kind_value:
                raise ValueError(f"Conflicting type='{type_value}' and kind='{kind_value}'")

        if name_value:
            warnings.warn("The 'name' field is deprecated. Use 'metadata.name' instead.", DeprecationWarning, stacklevel=2)
            parts = name_value.split("/")
            if len(parts) > 1:
                namespace = parts[0].replace(":action", "")
                name = "/".join(parts[1:])
            else:
                namespace = None
                name = parts[0].replace(":action", "")
        else:
            namespace = None
            name = None

        # Handle metadata creation
        metadata = values.pop("metadata", None) or values.pop("Metadata", None)
        if not metadata:
            if name:
                metadata = ActionMetadata(Name=name, Namespace=namespace)
            else:
                raise ValueError("Action must have a name via metadata.name or the deprecated name field")

        if isinstance(metadata, dict):
            metadata = ActionMetadata.model_validate(metadata)

        if isinstance(metadata, ActionMetadata):
            if name and not metadata.name:
                metadata.name = name
            if namespace and not metadata.namespace:
                metadata.namespace = namespace

        if not name_value:
            name_value = metadata.label

        values["metadata"] = metadata
        values["name"] = name_value  # Keep for backward compatibility (for how long?)
        values["kind"] = kind_value

        spec = values.pop("spec", None) or values.pop("Spec", None)
        if isinstance(spec, dict):
            values["spec"] = spec
        elif isinstance(spec, ActionSpec):
            values["spec"] = spec.model_dump()

        return values

    @model_validator(mode="after")
    def validate_no_self_dependency(self) -> "ActionResource":
        """Validate action doesn't depend on itself."""
        action_name = self.action_name  # Uses metadata.name with fallback

        if action_name and action_name in self.depends_on:
            raise ValueError(f"Action '{action_name}' cannot depend on itself")
        if self.before and action_name and action_name in self.before:
            raise ValueError(f"Action '{action_name}' cannot be before itself")
        if self.after and action_name and action_name in self.after:
            raise ValueError(f"Action '{action_name}' cannot be after itself")
        return self

    @field_validator("depends_on", mode="before")
    @classmethod
    def validate_depends_on(cls, value) -> list[str]:
        """Normalize depends_on to list of strings."""
        if value is None or value == "null":
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(f"All depends_on items must be strings, got {type(item)}")
            return value
        raise ValueError("depends_on must be a string or list of strings")

    @field_validator("kind", mode="before")
    @classmethod
    def validate_action_kind(cls, value) -> str:
        """Remove legacy 'aws.' prefix for backward compatibility."""
        if value and isinstance(value, str) and value.startswith("aws."):
            value = value.lstrip("aws.")
        return value

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value) -> str:
        """Validate scope is one of allowed values."""
        scope_list = ["build", "branch", "app", "portfolio"]
        if value not in scope_list:
            raise ValueError(f"Invalid scope: {value}. Must be one of: {scope_list}")
        return value

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, value: str) -> str:  # noqa: C901
        """Validate name format for hierarchical namespaces."""
        if value is None:
            return value

        # Name is now deprecated.  However, if you DO provide it,
        # it will be used and MUST follow the format
        # <namespace>/<name>.  Complicated.  Which is why
        # we've deprecated it.
        #
        # please use fiels:
        #     metadata.name, metadata.namespace intead.
        #

        if not value.strip():
            raise ValueError("Name cannot be empty")

        # Allow alphanumeric, hyphens, underscores, colons, slashes
        if not re.match(r"^[a-zA-Z0-9_:/-]+$", value):
            raise ValueError(f"Name '{value}' contains invalid characters")

        # Cannot start/end with hyphen or slash
        if value.startswith(("-", "/")) or value.endswith(("-", "/")):
            raise ValueError(f"Name '{value}' cannot start/end with hyphen or slash")

        # No consecutive separators
        if "//" in value or ":/" in value or "/:" in value:
            raise ValueError(f"Name '{value}' cannot contain consecutive separators")

        # Validate path components
        parts = value.split("/")
        for i, part in enumerate(parts):
            if not part:
                raise ValueError(f"Name '{value}' cannot contain empty path components")

            # Only first part can contain colons (namespace)
            if i > 0 and ":" in part:
                raise ValueError(f"Name '{value}' cannot contain colons in action name '{part}'")

            # No leading/trailing hyphens in parts
            if part.startswith("-") or part.endswith("-"):
                raise ValueError(f"Name part '{part}' cannot start/end with hyphen")

        # Length limit for AWS compatibility
        name_only = parts[-1]
        if len(name_only) > 63:
            raise ValueError(f"Name '{name_only}' exceeds 63 character limit")

        return value

    @field_validator("before", "after", mode="before")
    @classmethod
    def validate_action_lists(cls, value) -> list[str] | None:
        """Validate before/after action lists."""
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(f"All items must be strings, got {type(item)}")
            return value
        raise ValueError("Must be a string or list of strings")

    # Utility methods
    def has_dependencies(self) -> bool:
        """Check if action has dependencies."""
        return bool(self.depends_on)

    def is_conditional(self) -> bool:
        """Check if action has a condition."""
        return self.condition is not None

    def get_execution_order_dependencies(self) -> list[str]:
        """Get all dependencies affecting execution order."""
        dependencies = self.depends_on.copy()
        if self.before:
            dependencies.extend(self.before)
        return dependencies

    # Backward compatibility properties
    @property
    def label(self) -> str:
        """DEPRECATED: Use 'name' instead."""
        warnings.warn("Use 'name' instead of deprecated 'label'", DeprecationWarning, stacklevel=2)
        return (
            f"{self.metadata.namespace or ''}:action/{self.metadata.name or ''}"
            if self.metadata
            else self.name or "unnamed:action/unnamed-action"
        )

    @property
    def type(self) -> str:
        """DEPRECATED: Use 'kind' instead."""
        warnings.warn("Use 'kind' instead of deprecated 'type'", DeprecationWarning, stacklevel=2)
        return self.kind

    @property
    def action(self) -> str:
        """The action to perform (alias for kind)."""
        return self.kind

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Serialize with exclude_none and by_alias defaults."""
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)

    @model_serializer
    def ser_model(self, info: SerializationInfo) -> OrderedDict:
        """Serialize in consistent field order."""
        exclude_none = info.exclude_none
        by_alias = info.by_alias

        field_order = [
            "apiVersion",
            "kind",
            "metadata",
            "depends_on",
            "spec",
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

            # Use alias if requested
            if by_alias:
                field_info = ActionResource.model_fields.get(field)
                key = field_info.alias if field_info and field_info.alias else field
            else:
                key = field

            # Handle nested models
            if hasattr(value, "model_dump"):
                value = value.model_dump(exclude_none=exclude_none, by_alias=by_alias)  # type: ignore
            elif isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                value = [item.model_dump(exclude_none=exclude_none, by_alias=by_alias) for item in value]

            out[key] = value

        return out

    def __repr__(self) -> str:
        """String representation for debugging."""
        name = self.name if self.name else (self.metadata.name if self.metadata and self.metadata.name else "")
        return f"ActionResource(Kind='{self.kind}',Name='{name}')"
