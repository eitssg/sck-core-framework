"""DeploymentDetails Model Module for Simple Cloud Kit Framework.

This module contains the DeploymentDetails class which provides a comprehensive model for
deployment details used throughout the core-execute library and deployment automation system.
It serves as the central data structure for identifying deployment context and generating
resource identifiers across the Simple Cloud Kit ecosystem.

The DeploymentDetails class identifies the Client, Portfolio, App, Branch, Build, Component,
Environment, DataCenter, Scope, Tags, and StackFile for a deployment. It provides methods
for generating resource identifiers, S3 object keys, and deployment paths with support for
hierarchical deployment structures and multi-tenant environments.

Key Features:
    - **Hierarchical Deployment Model**: Client → Portfolio → App → Branch → Build → Component
    - **Resource Identifier Generation**: PRN (Portfolio Resource Name) generation at all levels
    - **S3 Object Key Generation**: Intelligent path generation for storage and retrieval
    - **Scope Management**: Automatic scope determination based on deployment depth
    - **Multi-Tenant Support**: Client-based isolation and resource organization
    - **Flexible Factory Methods**: Multiple ways to create instances from various sources

Deployment Hierarchy:
    ```
    Client (acme-corp)
    └── Portfolio (ecommerce)
        └── App (web-frontend)
            └── Branch (feature/checkout)
                └── Build (v1.2.3-beta.5+abc123)
                    └── Component (load-balancer)
    ```

Examples::

    from core_framework.models import DeploymentDetails

    # Create basic deployment details
    dd = DeploymentDetails(
    client="acme-corp",
    portfolio="ecommerce",
    app="web-frontend",
    branch="main",
    build="v1.2.3"
    )

    # Generate resource identifiers
    print(dd.get_build_prn())  # "prn:ecommerce:web-frontend:main:v1.2.3"

    # Generate S3 object keys
    key = dd.get_object_key("artefacts", "deploy.yaml")
    print(key)  # "artefacts/ecommerce/web-frontend/main/v1.2.3/deploy.yaml"

    # Create from flexible arguments
    dd = DeploymentDetails.from_arguments(
    portfolio="mobile-apps",
    app="ios-client"
    )

Related Classes:
    - ActionDetails: Uses DeploymentDetails for action file path generation
    - FileDetails: Base class for file storage and retrieval operations
    - ActionResource: Uses deployment context for action specification loading

Note:
    DeploymentDetails enforces hierarchical dependencies where each level requires
    all parent levels to be present. This ensures consistent resource organization
    and prevents invalid deployment configurations.
"""

from turtle import st
from typing import Any, Self
import os

from pydantic import BaseModel, ConfigDict, Field, model_validator, computed_field

import core_framework as util

from core_framework.constants import (
    ENV_SCOPE,
    SCOPE_BUILD,
    SCOPE_BRANCH,
    SCOPE_APP,
    SCOPE_COMPONENT,
    SCOPE_PORTFOLIO,
    OBJ_ARTEFACTS,
    OBJ_FILES,
    V_EMPTY,
)


class DeploymentDetails(BaseModel):
    """Comprehensive model for deployment details with validation and utility methods.

    DeploymentDetails serves as the central data structure for deployment context throughout
    the Simple Cloud Kit framework. It provides a hierarchical model for organizing
    deployments from client-level down to individual components, with automatic validation
    and intelligent resource identifier generation.

    The class enforces a strict hierarchy: Client → Portfolio → App → Branch → Build → Component,
    ensuring consistent organization and preventing invalid deployment configurations.

    Attributes:
        client (str): Client identifier for multi-tenant deployments and billing isolation.
                     Defaults to framework client configuration if not provided.
        portfolio (str): Portfolio name representing the business application or project group.
                        Required field that serves as the primary organizational unit.
        app (str, optional): Application name within the portfolio representing a deployment unit.
                            Can be None for portfolio-level operations.
        branch (str, optional): Source code branch name for version control integration.
                               Can be None for app-level operations.
        branch_short_name (str, optional): AWS-compatible short branch name without special characters.
                                          Auto-generated from branch if not provided.
        build (str, optional): Build number, version, or repository tag for release tracking.
                              Can be None for branch-level operations.
        component (str, optional): Specific component within a build (EC2, Volume, ResourceGroup).
                                  Represents the finest granularity of deployment.
        environment (str, optional): Deployment environment (Prod, Dev, Staging, UAT, etc.).
                                    Related to zone configuration.
        data_center (str, optional): Physical location or AWS region (us-east-1, eu-west-1).
                                    Used for geographic deployment distribution.
        scope (str, optional): Deployment scope determining storage hierarchy level.
                              Auto-determined if not provided.
        tags (dict[str, str], optional): Key-value pairs for resource tagging and metadata.
        stack_file (str, optional): CloudFormation stack file name for infrastructure deployment.
        delivered_by (str, optional): Person or system responsible for the deployment.

    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client_id: str = Field(
        alias="ClientId",
        description="Client ID for multi-tenant deployments and billing isolation",
        default="cid-1",
    )

    client: str = Field(
        alias="Client",
        description="Client identifier for multi-tenant deployments and billing isolation",
        default="core",
    )

    portfolio: str = Field(
        ...,
        alias="Portfolio",
        description="Portfolio name representing the business application or project group",
    )

    app: str | None = Field(
        alias="App",
        description="Application name within the portfolio representing a deployment unit",
        default=None,
    )

    branch: str | None = Field(
        alias="Branch",
        description="Source code branch name for version control integration",
        default=None,
    )

    branch_short_name: str | None = Field(
        alias="BranchShortName",
        description="AWS-compatible short branch name without special characters",
        default=None,
    )

    build: str | None = Field(
        alias="Build",
        description="Build number, version, or repository tag for release tracking",
        default=None,
    )

    component: str | None = Field(
        alias="Component",
        description="Specific component within a build (EC2, Volume, ResourceGroup)",
        default=None,
    )

    environment: str | None = Field(
        alias="Environment",
        description="Deployment environment (Prod, Dev, Staging, UAT, etc.)",
        default=None,
    )

    data_center: str | None = Field(
        alias="DataCenter",
        description="Physical location or AWS region (us-east-1, eu-west-1)",
        default=None,
    )

    @computed_field(alias="Scope", return_type=str | None)
    def scope(self) -> str | None:
        if not self.portfolio:
            return None
        if not self.app:
            return SCOPE_PORTFOLIO
        if not self.branch:
            return SCOPE_APP
        if not self.build:
            return SCOPE_BRANCH
        if not self.component:
            return SCOPE_BUILD
        return SCOPE_COMPONENT

    tags: dict[str, str] | None = Field(
        alias="Tags",
        description="Key-value pairs for resource tagging and metadata",
        default=None,
    )

    stack_file: str | None = Field(
        alias="StackFile",
        description="CloudFormation stack file name for infrastructure deployment",
        default=None,
    )

    delivered_by: str | None = Field(
        alias="DeliveredBy",
        description="Person or system responsible for the deployment",
        default=None,
    )

    def get_prn(self) -> str:
        if self.scope == SCOPE_PORTFOLIO:
            return self.get_portfolio_prn()

        if self.scope == SCOPE_APP:
            return self.get_app_prn()

        if self.scope == SCOPE_BRANCH:
            return self.get_branch_prn()

        if self.scope == SCOPE_BUILD:
            return self.get_build_prn()

        if self.scope == SCOPE_COMPONENT:
            return self.get_component_prn()

        return V_EMPTY

    def get_portfolio_prn(self) -> str:
        """Get the Portfolio Resource Name (PRN) for the deployment.

        Generates a PRN identifying the portfolio level of the deployment hierarchy.
        This is the most basic resource identifier in the system.

        Returns:
            str: Portfolio PRN in format 'prn:portfolio' (lowercase).

        Examples::

            dd = DeploymentDetails(portfolio="ecommerce-platform")
            print(dd.get_portfolio_prn())
            # Returns: "prn:ecommerce-platform"

            dd = DeploymentDetails(portfolio="Mobile-Apps")
            print(dd.get_portfolio_prn())
            # Returns: "prn:mobile-apps"
        """
        return f"prn:{self.portfolio}".lower()

    def get_app_prn(self) -> str:
        """Get the App Resource Name (PRN) for the deployment.

        Generates a PRN identifying the app level of the deployment hierarchy.
        If app is not specified, the app portion will be empty.

        Returns:
            str: App PRN in format 'prn:portfolio:app' (lowercase).

        Examples::

            dd = DeploymentDetails(portfolio="ecommerce", app="web-frontend")
            print(dd.get_app_prn())
            # Returns: "prn:ecommerce:web-frontend"

            dd = DeploymentDetails(portfolio="ecommerce", app=None)
            print(dd.get_app_prn())
            # Returns: "prn:ecommerce:"
        """
        return f"prn:{self.portfolio}:{self.app or ''}".lower()

    def get_branch_prn(self) -> str:
        """Get the Branch Resource Name (PRN) for the deployment.

        Generates a PRN identifying the branch level of the deployment hierarchy.
        Uses branch_short_name for AWS compatibility. If branch_short_name is not
        specified, the branch portion will be empty.

        Returns:
            str: Branch PRN in format 'prn:portfolio:app:branch' (lowercase).

        Examples::

            dd = DeploymentDetails(
            portfolio="ecommerce",
            app="web-frontend",
            branch_short_name="main"
            )
            print(dd.get_branch_prn())
            # Returns: "prn:ecommerce:web-frontend:main"

            dd = DeploymentDetails(
            portfolio="ecommerce",
            app="web-frontend",
            branch="feature/user-auth",
            branch_short_name="feature-user-auth"
            )
            print(dd.get_branch_prn())
            # Returns: "prn:ecommerce:web-frontend:feature-user-auth"
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}".lower()

    def get_build_prn(self) -> str:
        """Get the Build Resource Name (PRN) for the deployment.

        Generates a PRN identifying the build level of the deployment hierarchy.
        This is the most commonly used PRN for deployment operations.

        Returns:
            str: Build PRN in format 'prn:portfolio:app:branch:build' (lowercase).

        Examples::

            dd = DeploymentDetails(
            portfolio="ecommerce",
            app="api-gateway",
            branch_short_name="main",
            build="v1.2.3"
            )
            print(dd.get_build_prn())
            # Returns: "prn:ecommerce:api-gateway:main:v1.2.3"

            dd = DeploymentDetails(
            portfolio="mobile-apps",
            app="ios-client",
            branch_short_name="release-2.0",
            build="2.0.1-beta.4+abc123"
            )
            print(dd.get_build_prn())
            # Returns: "prn:mobile-apps:ios-client:release-2.0:2.0.1-beta.4+abc123"
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}:{self.build or ''}".lower()

    def get_component_prn(self) -> str:
        """Get the Component Resource Name (PRN) for the deployment.

        Generates a PRN identifying the component level of the deployment hierarchy.
        This is the most specific resource identifier in the system.

        Returns:
            str: Component PRN in format 'prn:portfolio:app:branch:build:component' (lowercase).

        Examples::

            dd = DeploymentDetails(
            portfolio="ecommerce",
            app="web-frontend",
            branch_short_name="main",
            build="v1.2.3",
            component="load-balancer"
            )
            print(dd.get_component_prn())
            # Returns: "prn:ecommerce:web-frontend:main:v1.2.3:load-balancer"

            dd = DeploymentDetails(
            portfolio="data-platform",
            app="etl-pipeline",
            branch_short_name="main",
            build="v3.1.0",
            component="postgres-db"
            )
            print(dd.get_component_prn())
            # Returns: "prn:data-platform:etl-pipeline:main:v3.1.0:postgres-db"
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}:{self.build or ''}:{self.component or ''}".lower()

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: dict) -> dict:
        """Validate and populate missing fields before model creation.

        Performs pre-validation processing to apply intelligent defaults and normalize
        field values. Handles both snake_case and PascalCase field names for compatibility
        with various input sources.

        Args:
            values (dict): Raw field values for model creation, which may include:
                          - client/Client: Client identifier
                          - branch/Branch: Source branch name
                          - branch_short_name/BranchShortName: AWS-compatible branch name
                          - delivered_by/DeliveredBy: Delivery person/system

        Returns:
            dict: Processed and normalized field values with:
                 - client: Populated from framework default if missing
                 - branch_short_name: Generated from branch if not provided
                 - delivered_by: Populated from framework default if missing

        Examples::

            # Called automatically during instance creation
            values = {"portfolio": "test", "branch": "feature/user-login"}
            processed = DeploymentDetails.validate_model_before(values)
            print(processed["branch_short_name"])  # "feature-user-login"

        Side Effects:
            Modifies the provided values dictionary by adding missing defaults
            and normalizing field names.
        """
        if isinstance(values, dict):
            # Set client if not provided
            client = values.pop("client", values.pop("Client", None))
            if not client:
                client = util.get_client() or "core"
            values["client"] = client

            delivered_by = values.get("DeliveredBy", None) or values.get("delivered_by", None)
            if not delivered_by:
                values["delivered_by"] = util.get_delivered_by()
            values["delivered_by"] = delivered_by

            # Portfolio
            portfolio = values.pop("portfolio", values.pop("Portfolio", None))

            # App
            app = values.pop("app", values.pop("App", None))

            # Branch
            branch = values.get("Branch", None) or values.get("branch", None)
            branch_short_name = values.get("BranchShortName", None) or values.get("branch_short_name", None)
            if not branch:
                branch_short_name = branch
            elif not branch_short_name:
                branch_short_name = util.branch_short_name(branch)

            # Build
            build = values.pop("build", values.pop("Build", None))

            # Component
            component = values.pop("component", values.pop("Component", None))

            # Scope
            scope = values.pop("scope", values.pop("Scope", SCOPE_COMPONENT))
            if scope == SCOPE_PORTFOLIO:
                values["portfolio"] = portfolio
            elif scope == SCOPE_APP:
                values["portfolio"] = portfolio
                values["app"] = app
            elif scope == SCOPE_BRANCH:
                values["portfolio"] = portfolio
                values["app"] = app
                values["branch"] = branch
                values["branch_short_name"] = branch_short_name
            elif scope == SCOPE_BUILD:
                values["portfolio"] = portfolio
                values["app"] = app
                values["branch"] = branch
                values["branch_short_name"] = branch_short_name
                values["build"] = build
            elif scope == SCOPE_COMPONENT:
                values["portfolio"] = portfolio
                values["app"] = app
                values["branch"] = branch
                values["branch_short_name"] = branch_short_name
                values["build"] = build
                values["component"] = component

        return values

    @model_validator(mode="after")
    def check_conditional_fields(self) -> Self:
        """Validate hierarchical dependencies between fields.

        Ensures that the deployment hierarchy is maintained and sets automatic
        scope determination based on the deepest level provided.

        Returns:
            Self: The validated DeploymentDetails instance.

        Raises:
            ValueError: If hierarchical dependencies are not satisfied:
                       - Component provided without Build
                       - Build provided without Branch
                       - Branch provided without App

        """
        if self.component and not self.build:
            raise ValueError("Build is required when Component is provided")

        if self.build and not self.branch:
            raise ValueError("Branch is required when Build is provided")

        if self.branch and not self.app:
            raise ValueError("App is required when Branch is provided")

        return self

    def get_identity(self) -> str:
        """Get deployment identity as a PRN with wildcards for missing fields.

        Generates a complete PRN representation using wildcards (*) for missing
        hierarchy levels. Useful for pattern matching and resource queries.

        Returns:
            str: Complete PRN with wildcards for missing fields.

        """
        portfolio = self.portfolio or "*"
        app = self.app or "*"
        branch_short_name = self.branch_short_name or "*"
        build = self.build or "*"

        return f"prn:{portfolio}:{app}:{branch_short_name}:{build}".lower()

    @classmethod
    def from_arguments(cls, **kwargs) -> "DeploymentDetails":
        """Create DeploymentDetails instance from flexible keyword arguments.

        Factory method providing intelligent DeploymentDetails creation by accepting
        various parameter combinations and applying defaults. Supports both direct
        parameter specification and PRN parsing for maximum flexibility.

        Args:
            - client_id/ClientId (str): Client identifier
            - client/Client (str): Client identifier
            - portfolio/Portfolio (str): Portfolio name (required)
            - app/App (str): Application name
            - branch/Branch (str): Branch name
            - branch_short_name/BranchShortName (str): AWS-compatible branch name
            - build/Build (str): Build identifier
            - component/Component (str): Component name

        Returns:
            DeploymentDetails: Fully configured instance with all fields populated.

        Raises:
            ValueError: If required client parameter cannot be determined or if
                       PRN parsing fails.

        """

        def _get(key1: str, key2: str, default: Any, can_be_empty: bool = False) -> Any:
            """Extract parameter with fallback and default handling."""
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else default

        client: str = _get("client", "Client", util.get_client() or "core")
        client_id: str = _get("client_id", "ClientId", "cid-1")

        prn = kwargs.get("prn", None)
        if prn is not None:
            portfolio, app, branch, build, component = util.split_prn(prn)

        else:
            # You cannot set portfolio to None or empty string.  It must be provided.
            portfolio: str | None = _get("portfolio", "Portfolio", util.get_portfolio())

            # You are allowed to set app to None or empty string.  Only call for default if not provided.
            app: str | None = _get("app", "App", util.get_app(), True)

            # You are allowed to set branch to None or empty string.  Only call for default if not provided.
            branch: str | None = _get("branch", "Branch", util.get_branch(), True)

            # If supplied a branch short name, use it.  Otherwise, generate from branch.
            branch_short_name: str | None = _get("branch_short_name", "BranchShortName", util.branch_short_name(branch))

            # You are allow to set build to None or empty string.  Only call for default if not provided.
            build: str | None = _get("build", "Build", util.get_build(), True)

            component: str | None = _get("component", "Component", None)

            scope = _get("scope", "Scope", None)
            if scope is not None:
                if scope == SCOPE_PORTFOLIO:
                    app = None
                    branch = None
                    branch_short_name = None
                    build = None
                    component = None
                elif scope == SCOPE_APP:
                    branch = None
                    branch_short_name = None
                    build = None
                    component = None
                elif scope == SCOPE_BRANCH:
                    build = None
                    component = None
                elif scope == SCOPE_BUILD:
                    component = None

        return cls(
            ClientId=client_id,
            Client=client,
            Portfolio=portfolio or "",
            App=app,
            Branch=branch,
            BranchShortName=branch_short_name,
            Build=build,
            Component=component,
            Environment=_get("environment", "Environment", None),
            DataCenter=_get("data_center", "DataCenter", None),
            Tags=_get("tags", "Tags", None),
            StackFile=_get("stack_file", "StackFile", None),
            DeliveredBy=_get("delivered_by", "DeliveredBy", None),
        )

    def model_dump(self, **kwargs) -> dict:
        """Serialize model to dictionary with customized defaults.

        Overrides the default Pydantic serialization to exclude None values by default
        and use field aliases, providing cleaner output for API responses and logging.

        Args:
            **kwargs: Keyword arguments passed to parent model_dump method.
                     Standard Pydantic serialization options are supported:
                     - exclude_none (bool): Exclude None values (default: True)
                     - by_alias (bool): Use field aliases (default: True)
                     - include (set): Fields to include
                     - exclude (set): Fields to exclude

        Returns:
            dict: Dictionary representation with None values excluded by default.

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     branch=None,
            ...     build=None
            ... )
            >>> result = dd.model_dump()
            >>> print(result)
            # Only portfolio and app included, branch/build excluded

            >>> # Include None values explicitly
            >>> result = dd.model_dump(exclude_none=False)
            >>> print(result)
            # All fields included, branch/build as null

            >>> # Use original field names
            >>> result = dd.model_dump(by_alias=False)
            >>> # Fields use snake_case names instead of PascalCase aliases
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)

    def get_object_key(
        self,
        object_type: str,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """Generate object path from deployment details for storage operations.

        Creates hierarchical paths suitable for S3 keys or local filesystem paths
        based on deployment context and scope. Supports flexible scope overrides
        for different storage patterns.

        Args:
            object_type (str): Type of object for path prefix (files, packages, artefacts).
            name (str, optional): Specific object name to append. If None, returns
                                 directory path only.
            scope (str, optional): Scope override for path depth. If None, uses
                                  deployment's scope. Valid values: portfolio, app, branch, build.
            s3 (bool, optional): Force forward slashes for S3 compatibility. If None,
                               determined by util.is_use_s3().

        Returns:
            str: Generated path suitable for storage operations.

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web-frontend",
            ...     branch_short_name="main",
            ...     build="v1.2.3"
            ... )

            >>> # Get artefacts directory path
            >>> path = dd.get_object_key("artefacts")
            >>> print(path)  # "artefacts/ecommerce/web-frontend/main/v1.2.3"

            >>> # Get specific file path
            >>> path = dd.get_object_key("artefacts", "deploy.yaml")
            >>> print(path)  # "artefacts/ecommerce/web-frontend/main/v1.2.3/deploy.yaml"

            >>> # Override scope for app-level storage
            >>> path = dd.get_object_key("config", "app.json", scope="app")
            >>> print(path)  # "config/ecommerce/web-frontend/app.json"

            >>> # Portfolio-level shared resources
            >>> path = dd.get_object_key("shared", "common.yaml", scope="portfolio")
            >>> print(path)  # "shared/ecommerce/common.yaml"

        Scope Behavior:
            - **portfolio**: object_type/portfolio[/name]
            - **app**: object_type/portfolio/app[/name]
            - **branch**: object_type/portfolio/app/branch[/name]
            - **build**: object_type/portfolio/app/branch/build[/name]

        Path Separators:
            - S3 mode: Always uses forward slashes (/)
            - Local mode: Uses OS-appropriate separators (\\ on Windows, / on Unix)
        """
        portfolio = self.portfolio or V_EMPTY
        portfolio = portfolio.lower()

        app = self.app or V_EMPTY
        app = app.lower()

        branch = self.branch_short_name or V_EMPTY
        branch = branch.lower()

        build = self.build or V_EMPTY
        build = build.lower()

        component = self.component or V_EMPTY
        component = component.lower()

        if s3 is None:
            s3 = util.is_use_s3()

        separator = "/" if s3 else os.path.sep

        if name and name.startswith(separator):
            return name

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
        elif scope == SCOPE_COMPONENT and portfolio and app and branch and build:
            key = separator.join([object_type, portfolio, app, branch, build, component])
        else:
            key = object_type

        return key if name is None else separator.join([key, name])

    def get_artefacts_key(
        self,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """Get artefacts path in the core automation storage.

        Convenience method for generating artefacts storage paths. Artefacts typically
        include deployment specifications, configuration files, and build outputs.

        Args:
            name (str, optional): Artefacts file or directory name.
            scope (str, optional): Scope override for path depth.
            s3 (bool, optional): Force S3-compatible path separators.

        Returns:
            str: Path to artefacts location.

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="api-gateway",
            ...     branch_short_name="main",
            ...     build="v2.1.0"
            ... )

            >>> # Artefacts directory
            >>> path = dd.get_artefacts_key()
            >>> print(path)  # "artefacts/ecommerce/api-gateway/main/v2.1.0"

            >>> # Deployment specification file
            >>> path = dd.get_artefacts_key("deploy.yaml")
            >>> print(path)  # "artefacts/ecommerce/api-gateway/main/v2.1.0/deploy.yaml"

            >>> # App-level configuration
            >>> path = dd.get_artefacts_key("app-config.yaml", scope="app")
            >>> print(path)  # "artefacts/ecommerce/api-gateway/app-config.yaml"
        """
        return self.get_object_key(OBJ_ARTEFACTS, name, scope, s3)

    def get_artefact_bucket_name(self) -> str:
        """Get the S3 bucket name for artefacts storage.

        Returns:
            str: S3 bucket name for artefacts.
        """
        return util.get_artefact_bucket_name()

    def get_artefact_bucket_region(self) -> str:
        """Get the AWS region for the artefacts S3 bucket.

        Returns:
            str: AWS region where the artefacts bucket is located.
        """
        return util.get_artefact_bucket_region()

    def get_packages_bucket_name(self) -> str:
        """Get the S3 bucket name for packages storage.

        Returns:
            str: S3 bucket name for packages.
        """
        return util.get_bucket_name()

    def get_packages_bucket_region(self) -> str:
        """Get the AWS region for the packages S3 bucket.

        Returns:
            str: AWS region where the packages bucket is located.
        """
        return util.get_bucket_region()

    def get_files_key(
        self,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """Get files path in the core automation storage.

        Convenience method for generating files storage paths. Files typically
        include documentation, logs, and supplementary resources.

        Args:
            name (str, optional): File or directory name.
            scope (str, optional): Scope override for path depth.
            s3 (bool, optional): Force S3-compatible path separators.

        Returns:
            str: Path to files location.

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="data-platform",
            ...     app="etl-pipeline",
            ...     branch_short_name="main",
            ...     build="v1.5.2"
            ... )

            >>> # Files directory
            >>> path = dd.get_files_key()
            >>> print(path)  # "files/data-platform/etl-pipeline/main/v1.5.2"

            >>> # Configuration file
            >>> path = dd.get_files_key("database.conf")
            >>> print(path)  # "files/data-platform/etl-pipeline/main/v1.5.2/database.conf"

            >>> # Deployment logs
            >>> path = dd.get_files_key("deployment.log")
            >>> print(path)  # "files/data-platform/etl-pipeline/main/v1.5.2/deployment.log"
        """
        return self.get_object_key(OBJ_FILES, name, scope, s3)
