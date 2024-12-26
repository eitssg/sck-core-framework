""" module contains the DeploymentDetails class which provides a model for how deployment details are to be provided to the core-execute library. """

from typing import Self
import os

from pydantic import BaseModel, Field, model_validator, ConfigDict

import core_framework as util

from core_framework.constants import (
    ENV_SCOPE,
    SCOPE_BUILD,
    SCOPE_BRANCH,
    SCOPE_APP,
    SCOPE_PORTFOLIO,
    ENV_PORTFOLIO,
    ENV_AWS_PROFILE,
    ENV_APP,
    ENV_BRANCH,
    ENV_BUILD,
    ENV_CLIENT,
    V_EMPTY,
)


class DeploymentDetails(BaseModel):
    """
    DeploymentDetails is the class that identifies the Client, Portfolio, App, Branch, Build, Component, Environment, DataCenter, Scope, Tags, and StackFile for a deployment.

    Attributes:

        Client (str): The name of the client or customer (installation or AWS Organizatoion)
        Portfolio (str): Portfolio name is the BizApp name
        App (str): The name of the part of the BizApp.  The deployment unit.
        Branch (str): The name of the branch of the deployment unit being deployed
        BranchShortName (str): The short name of the branch of the deployment unit being deployed.
        Build (str): The build number, version number.  Or repo tag.  May even have the repository commit ID in the name.  (Ex. 0.0.6-pre.204+f9908cc6)
        Component (str): The item deployed (EC2, Volumne, ResourceGrooup, etc).  These are parts of the deploment unit.
        Environment (str): Related to the Zone.  Examples are Prod, Dev, Non-Prod, UAT, PEN, PERF, PT, etc
        DataCenter (str): This is the physical location.  This is almost identical to an AWS region.  Examples are us-east-1, us-west-2, etc
        Scope (str): The deployment scope from the values: portfolio, app, branch, build.  It does not include the component or environment. It's primarily used to determine the location in S3 folder hierarchy to store packages, artefacts, and files for the deployment.
        Tags (dict[str, str]): Tags are key value pairs that can be applied to resources.  These values can come from the FACTS database from Apps or Zone defaults.  Your deployment may specify additional tags.
        StackFile (str): The name of the CloudFormation stack file that was used in the deployment.

    """

    def __init__(self, **data):
        """
        If you do not provide a value for a field, sane defaults will calculated based on the environment

        Example - Certain enviroment variables are examined:
            CLIENT
            PORTFOLIO
            APP
            BRANCH
            BUILD
            ENVIRONMENT
            SCOPE

        Other values are calculated.  Some will remain None.

        """
        super().__init__(**data)

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    Client: str = Field(
        description="Client is the name of the client or customer (installation or AWS Organizatoion)",
        default="",
    )

    Portfolio: str = Field(description="Portfolio name is the BizApp name")

    App: str | None = Field(
        description="App is the name of the part of the BizApp.  The deployment unit.",
        default=None,
    )

    Branch: str | None = Field(
        description="Branch is the name of the branch of the deployment unit being deployed",
        default=None,
    )

    BranchShortName: str | None = Field(
        description="BranchShortName is the short name of the branch of the deployment unit being deployed.  "
        "Done because of special characters that cannot be used as AWS resource names",
        default=None,
    )

    Build: str | None = Field(
        description="Build is the build number, version number.  Or repo tag.  May even have the repository "
        "commit ID in the name.  (Ex. 0.0.6-pre.204+f9908cc6)",
        default=None,
    )

    Component: str | None = Field(
        description="Component is the item deployed (EC2, Volumne, ResourceGrooup, etc).  "
        "These are parts of the deploment unit.",
        default=None,
    )

    Environment: str | None = Field(
        description="Environment is related to the Zone.  Examples are Prod, Dev, Non-Prod, UAT, PEN, PERF, PT, etc",
        default=None,
    )

    DataCenter: str | None = Field(
        description="DataCenter is the physical location.  This is almost identical to an AWS region, but different.  "
        "Examples are us-east-1, us-west-2, etc",
        default=None,
    )

    Scope: str | None = Field(
        description="Scope is the deployment scope from the values: portfolio, app, branch, build.  It does not "
        "include the component or environment. It's primarily used to determine the location in S3 folder hierarchy "
        "to store packages, artefacts, and files for the deployment.",
        default=None,
    )

    Tags: dict[str, str] | None = Field(
        description="Tags are key value pairs that can be applied to resources.  These values can come from the "
        "FACTS database from Apps or Zone defaults.  Your deployment may specify additional tags.",
        default=None,
    )

    StackFile: str | None = Field(
        description="StackFile is the name of the CloudFormation stack file that was used in the deployment.",
        default=None,
    )

    DeliveredBy: str | None = Field(
        description="DeliveredBy is the name of the person or system that delivered the deployment.",
        default=None,
    )

    def get_portfolio_prn(self) -> str:
        return f"prn:{self.Portfolio}".lower()

    def get_app_prn(self) -> str:
        return f"prn:{self.Portfolio}:{self.App}".lower()

    def get_branch_prn(self) -> str:
        return f"prn:{self.Portfolio}:{self.App}:{self.BranchShortName}".lower()

    def get_build_prn(self) -> str:
        return f"prn:{self.Portfolio}:{self.App}:{self.BranchShortName}:{self.Build}".lower()

    def get_component_prn(self) -> str:
        return f"prn:{self.Portfolio}:{self.App}:{self.BranchShortName}:{self.Build}:{self.Component}".lower()

    @model_validator(mode="before")
    @classmethod
    def validate_incoming(cls, values):
        if isinstance(values, dict):
            if not values.get("Client"):
                values["Client"] = os.getenv(
                    ENV_CLIENT, os.getenv(ENV_AWS_PROFILE, "default")
                )
            branch = values.get("Branch")
            if branch:
                values["BranchShortName"] = util.branch_short_name(branch)
            else:
                values["BranchShortName"] = branch  # branch might by V_EMPTY
            if not values.get("DeliveredBy"):
                values["DeliveredBy"] = util.get_delivered_by()
        return values

    @model_validator(mode="after")
    def check_conditional_fields(self) -> Self:

        if self.Component and not self.Build:
            raise ValueError("Build is required when Component is provided")

        if self.Build and not self.Branch:
            raise ValueError("Branch is required when Build is provided")

        if self.Branch and not self.App:
            raise ValueError("App is required when Branch is provided")

        if not self.Scope:
            self.Scope = self.get_scope()

        return self

    def get_scope(self) -> str:
        return DeploymentDetails._get_standard_scope(
            self.Portfolio, self.App, self.Branch, self.Build
        )

    @staticmethod
    def _get_standard_scope(
        portfolio: str | None, app: str | None, branch: str | None, build: str | None
    ) -> str:
        if ENV_SCOPE in os.environ:
            return os.getenv(ENV_SCOPE, SCOPE_BUILD)
        if build:
            return SCOPE_BUILD
        if branch:
            return SCOPE_BRANCH
        if app:
            return SCOPE_APP
        if portfolio:
            return SCOPE_PORTFOLIO
        return SCOPE_BUILD

    def get_identity(self) -> str:

        portfolio = self.Portfolio or "*"
        app = self.App or "*"
        branch_short_name = self.BranchShortName or "*"
        build = self.Build or "*"

        return f"prn:{portfolio}:{app}:{branch_short_name}:{build}".lower()

    @staticmethod
    def from_arguments(**kwargs):

        client = kwargs.get("client", util.get_client())
        if not client:
            raise ValueError("Client is required")

        prn = kwargs.get("prn", None)
        if prn is not None:
            portfolio, app, branch, build, component = util.split_prn(prn)
        else:
            portfolio = kwargs.get("portfolio", os.getenv(ENV_PORTFOLIO, None))
            app = kwargs.get("app", os.getenv(ENV_APP, None))
            branch = kwargs.get("branch", os.getenv(ENV_BRANCH, None))
            if branch:
                branch_short_name = kwargs.get(
                    "branch_short_name", util.branch_short_name(branch)
                )
            else:
                branch_short_name = None
            build = kwargs.get("build", os.getenv(ENV_BUILD, None))
            component = kwargs.get("component", None)

        scope = kwargs.get(
            "scope",
            DeploymentDetails._get_standard_scope(portfolio, app, branch, build),
        )

        return DeploymentDetails(
            Client=client,
            Portfolio=portfolio,
            App=app,
            Branch=branch,
            BranchShortName=branch_short_name,
            Build=build,
            Component=component,
            Scope=scope,
            Environment=kwargs.get("environment", None),
            DataCenter=kwargs.get("data_center", None),
            Tags=kwargs.get("tags", None),
            StackFile=kwargs.get("stack_file", None),
            DeliveredBy=kwargs.get("delivered_by", None),
        )

    # Override
    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def get_object_key(
        self,
        object_type: str,
        name: str | None = None,
        s3: bool = False,
    ) -> str:
        """
        Get the object path from the payload's deployment details. This will use os delimiters '/' for linux or SR
        or '\\' for Windows.  And if you need s3 keys, make sure that s3 parameter is set to True to for / delimiter.

        Args:
            object_type (str): The type of object to get the path for.  (files, packages, artefacts)
            name (str, optional): The name of the object to get the path for. (default: None)
            s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

        Return:
            str: The path to the object in the core automation s3 bucket
        """
        portfolio = self.Portfolio or V_EMPTY
        portfolio = portfolio.lower()

        app = self.App or V_EMPTY
        app = app.lower()

        branch = self.BranchShortName or V_EMPTY
        branch = branch.lower()

        build = self.Build or V_EMPTY
        build = build.lower()

        separator = "/" if s3 else os.path.sep

        if self.Scope == SCOPE_PORTFOLIO and portfolio:
            key = separator.join([object_type, portfolio])
        elif self.Scope == SCOPE_APP and portfolio and app:
            key = separator.join([object_type, portfolio, app])
        elif self.Scope == SCOPE_BRANCH and portfolio and app and branch:
            key = separator.join([object_type, portfolio, app, branch])
        elif self.Scope == SCOPE_BUILD and portfolio and app and branch and build:
            key = separator.join([object_type, portfolio, app, branch, build])
        else:
            key = object_type

        return key if name is None else f"{key}{separator}{name}"
