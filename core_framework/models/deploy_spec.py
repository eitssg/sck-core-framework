"""This module contains the DeploySpec class which provides a model for how CloudFormation templates are to be deployed by core-automation."""

from typing import Self
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .action_spec import ActionSpec


class DeploySpec(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    action_specs: list[ActionSpec] = Field(alias="actions", default_factory=lambda: [])

    @model_validator(mode="after")
    def validate_deployspecs(self) -> Self:
        """
        Checks to see if the deploysepc will create any duplicate stack names.  If it does, it will raise a ValueError.

        It's only duplicate if it's the same action.type (command, such as: create_stack)

        Returns:
            Self: The DeploySpec instance itself, for method chaining.

        Raises:
            ValueError: if there are duplicate stack names
        """
        # When we pass in more than one action spec, we need to ensure that the stack names are unique.
        names = []
        for action in self.action_specs:

            stack_name = action.params.get(
                "stack_name", action.params.get("StackName", None)
            )

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

            for account in accounts:
                for region in regions:
                    name = f"{action.type}/{account}/{region}/{stack_name}"
                    if name in names:
                        raise ValueError(f"Duplicate stack name: {name}")
                    names.append(name)

        return self

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)
