"""module contains the DeploymentDetails class which provides a model for how deployment details are to be provided to the core-execute library."""

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
    OBJ_ARTEFACTS,
    OBJ_FILES,
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

    client: str = Field(
        alias="Client",  # Alias for PascalCase compatibility
        description="Client is the name of the client or customer (installation or AWS Organizatoion)",
        default="",
    )

    portfolio: str = Field(
        alias="Portfolio",  # Alias for PascalCase compatibility
        description="Portfolio name is the BizApp name",
    )

    app: str | None = Field(
        alias="App",  # Alias for PascalCase compatibility
        description="App is the name of the part of the BizApp.  The deployment unit.",
        default=None,
    )

    branch: str | None = Field(
        alias="Branch",  # Alias for PascalCase compatibility
        description="Branch is the name of the branch of the deployment unit being deployed",
        default=None,
    )

    branch_short_name: str | None = Field(
        alias="BranchShortName",  # Alias for PascalCase compatibility
        description="BranchShortName is the short name of the branch of the deployment unit being deployed.  "
        "Done because of special characters that cannot be used as AWS resource names",
        default=None,
    )

    build: str | None = Field(
        alias="Build",  # Alias for PascalCase compatibility
        description="Build is the build number, version number.  Or repo tag.  May even have the repository "
        "commit ID in the name.  (Ex. 0.0.6-pre.204+f9908cc6)",
        default=None,
    )

    component: str | None = Field(
        alias="Component",  # Alias for PascalCase compatibility
        description="Component is the item deployed (EC2, Volumne, ResourceGrooup, etc).  "
        "These are parts of the deploment unit.",
        default=None,
    )

    environment: str | None = Field(
        alias="Environment",  # Alias for PascalCase compatibility
        description="Environment is related to the Zone.  Examples are Prod, Dev, Non-Prod, UAT, PEN, PERF, PT, etc",
        default=None,
    )

    data_center: str | None = Field(
        alias="DataCenter",  # Alias for PascalCase compatibility
        description="DataCenter is the physical location.  This is almost identical to an AWS region, but different.  "
        "Examples are us-east-1, us-west-2, etc",
        default=None,
    )

    scope: str | None = Field(
        alias="Scope",  # Alias for PascalCase compatibility
        description="Scope is the deployment scope from the values: portfolio, app, branch, build.  It does not "
        "include the component or environment. It's primarily used to determine the location in S3 folder hierarchy "
        "to store packages, artefacts, and files for the deployment.",
        default=None,
    )

    tags: dict[str, str] | None = Field(
        alias="Tags",  # Alias for PascalCase compatibility
        description="Tags are key value pairs that can be applied to resources.  These values can come from the "
        "FACTS database from Apps or Zone defaults.  Your deployment may specify additional tags.",
        default=None,
    )

    stack_file: str | None = Field(
        alias="StackFile",  # Alias for PascalCase compatibility
        description="StackFile is the name of the CloudFormation stack file that was used in the deployment.",
        default=None,
    )

    delivered_by: str | None = Field(
        alias="DeliveredBy",  # Alias for PascalCase compatibility
        description="DeliveredBy is the name of the person or system that delivered the deployment.",
        default=None,
    )

    def get_portfolio_prn(self) -> str:
        return f"prn:{self.portfolio}".lower()

    def get_app_prn(self) -> str:
        return f"prn:{self.portfolio}:{self.app or ""}".lower()

    def get_branch_prn(self) -> str:
        return f"prn:{self.portfolio}:{self.app or ""}:{self.branch_short_name or ""}".lower()

    def get_build_prn(self) -> str:
        return f"prn:{self.portfolio}:{self.app or ""}:{self.branch_short_name or ""}:{self.build or ""}".lower()

    def get_component_prn(self) -> str:
        return f"prn:{self.portfolio}:{self.app or ""}:{self.branch_short_name or ""}:{self.build or ""}:{self.component or ""}".lower()

    @model_validator(mode="before")
    @classmethod
    def validate_incoming(cls, values):
        if isinstance(values, dict):
            if not values.get("Client") and not values.get("client"):
                values["client"] = os.getenv(
                    ENV_CLIENT, os.getenv(ENV_AWS_PROFILE, "default")
                )
            branch = values.get("Branch", values.get("branch", None))
            if branch:
                values["branch_short_name"] = util.branch_short_name(branch)
            else:
                values["branch_short_name"] = branch  # branch might by V_EMPTY
            if not values.get("DeliveredBy") and not values.get("delivered_by"):
                values["delivered_by"] = util.get_delivered_by()
        return values

    @model_validator(mode="after")
    def check_conditional_fields(self) -> Self:

        if self.component and not self.build:
            raise ValueError("Build is required when Component is provided")

        if self.build and not self.branch:
            raise ValueError("Branch is required when Build is provided")

        if self.branch and not self.app:
            raise ValueError("App is required when Branch is provided")

        if not self.scope:
            self.scope = self.get_scope()

        return self

    def get_scope(self) -> str:
        return DeploymentDetails._get_standard_scope(
            self.portfolio, self.app, self.branch, self.build
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

        portfolio = self.portfolio or "*"
        app = self.app or "*"
        branch_short_name = self.branch_short_name or "*"
        build = self.build or "*"

        return f"prn:{portfolio}:{app}:{branch_short_name}:{build}".lower()

    @staticmethod
    def from_arguments(**kwargs):

        client = kwargs.get("client", kwargs.get("Client", util.get_client()))
        if not client:
            raise ValueError("Client is required")

        prn = kwargs.get("prn", None)
        if prn is not None:
            portfolio, app, branch, build, component = util.split_prn(prn)
        else:
            portfolio = kwargs.get(
                "portfolio", kwargs.get("Portfolio", util.get_portfolio())
            )
            app = kwargs.get("app", kwargs.get("App", util.get_app()))
            branch = kwargs.get("branch", kwargs.get("Branch", util.get_branch()))
            if branch:
                branch_short_name = kwargs.get(
                    "branch_short_name",
                    kwargs.get("BranchShortName", util.branch_short_name(branch)),
                )
            else:
                branch_short_name = None
            build = kwargs.get("build", kwargs.get("Build", util.get_build()))
            component = kwargs.get("component", kwargs.get("Component", None))

        scope = kwargs.get(
            "scope",
            kwargs.get(
                "Scope",
                DeploymentDetails._get_standard_scope(portfolio, app, branch, build),
            ),
        )

        return DeploymentDetails(
            client=client,
            portfolio=portfolio,
            app=app,
            branch=branch,
            branchShortName=branch_short_name,
            build=build,
            component=component,
            scope=scope,
            environment=kwargs.get("environment", kwargs.get("Environment", None)),
            data_center=kwargs.get("data_center", kwargs.get("DataCenter", None)),
            tags=kwargs.get("tags", kwargs.get("Tags", None)),
            stack_file=kwargs.get("stack_file", kwargs.get("StackFile", None)),
            delivered_by=kwargs.get("delivered_by", kwargs.get("DeliveredBy", None)),
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
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """
        Get the object path from the payload's deployment details. This will use os delimiters '/' for linux or SR
        or '\\' for Windows.  And if you need s3 keys, make sure that s3 parameter is set to True to for / delimiter.

        If you specify the **scope** then it will override the scope in the deployment details.

        Args:
            object_type (str): The type of object to get the path for.  (files, packages, artefacts)
            name (str, optional): The name of the object to get the path for. (default: None)
            scope (str, optional): The scope of the artefacts (default: None).  Allowed values are: portfolio, app, branch, build.
            s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

        Return:
            str: The path to the object in the core automation s3 bucket
        """
        portfolio = self.portfolio or V_EMPTY
        portfolio = portfolio.lower()

        app = self.app or V_EMPTY
        app = app.lower()

        branch = self.branch_short_name or V_EMPTY
        branch = branch.lower()

        build = self.build or V_EMPTY
        build = build.lower()

        if s3 is None:
            s3 = util.is_use_s3()

        separator = "/" if s3 else os.path.sep

        if not scope:
            scope = self.scope or SCOPE_BUILD

        if scope == SCOPE_PORTFOLIO and portfolio:
            key = separator.join([object_type, portfolio])
        elif scope == SCOPE_APP and portfolio and app:
            key = separator.join([object_type, portfolio, app])
        elif scope == SCOPE_BRANCH and portfolio and app and branch:
            key = separator.join([object_type, portfolio, app, branch])
        elif scope == SCOPE_BUILD and portfolio and app and branch and build:
            key = separator.join([object_type, portfolio, app, branch, build])
        else:
            key = object_type

        return key if name is None else f"{key}{separator}{name}"

    def get_artefacts_key(
        self,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """
        Helper function to get the artefacts path in the core automation s3 bucket for the task payload.

        Example: artefacts/portfolio/app/branch/build-213/<name>

        If you specify the **scope** then it will override the scope in the deployment details.

        Args:
            deployment_details (DeploymentDetails): The deployment details describing the deployment
            name (str, optional): The name of the artefacts folder
            scope (str, optional): The scope of the artefacts (default: None).  Allowed values are: portfolio, app, branch, build.
            s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

        Return:
            str | None: The path to the artefacts in the core automation s3 bucket
        """
        return self.get_object_key(OBJ_ARTEFACTS, name, scope, s3)

    def get_files_key(
        self,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """
        Helper function to get the artefacts path in the core automation s3 bucket for the task payload.

        Example: artefacts/portfolio/app/branch/build-213/<name>

        If you specify the **scope** then it will override the scope in the deployment details.

        Args:
            deployment_details (DeploymentDetails): The deployment details describing the deployment
            name (str, optional): The name of the artefacts folder
            scope (str, optional): The scope of the artefacts (default: None).  Allowed values are: portfolio, app, branch, build.
            s3 (bool, optional): Forces slashes to '/' instead of os dependent (default: False)

        Return:
            str | None: The path to the artefacts in the core automation s3 bucket
        """
        return self.get_object_key(OBJ_FILES, name, scope, s3)

    def get_client_portfolio_key(self) -> str:
        """
        Return the client portfolio key for the deployment details `AppFacts`

        The key is in the format: key = {client}:{portfolio}

        Example: client:portfolio

        Returns:
            str: The key for AppFacts retrieval
        """
        return f"{self.client}:{self.portfolio}"
