from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class ComponentConfiguration(dict):
    pass


class ComponentResource(BaseModel):
    """A resource within a component."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str = Field(description="Resource name", alias="Name")
    type: str = Field(description="Resource type", alias="Type")

    depends_on: list[str] | None = Field(
        description="List of component names this resource depends on",
        alias="DependsOn",
        default=None,
    )
    persist: bool | None = Field(
        description="Whether the resource should persist after the component is deleted",
        alias="Persist",
        default=None,
    )
    configuration: ComponentConfiguration = Field(
        description="Resource configuration details",
        alias="Configuration",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary with aliases.

        Where name is "MyResource", the output will be:

        Example:
            >>> # Component Resource
            {
                "MyResource": {
                    "Type": "AWS::S3::Bucket",
                    "DependsOn": ["OtherComponent"],
                    "Persist": true,
                    "Configuration": { ... }
                }
            }

        """
        data = self.model_dump()
        name = data.pop("name", "<unknown>")
        return {name: data}

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Dump the model to a dictionary with aliases."""
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("include_none", False)
        return self.model_dump(**kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, type={self.type})>"
