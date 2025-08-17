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

Examples:
    >>> from core_framework.models import DeploymentDetails

    >>> # Create basic deployment details
    >>> dd = DeploymentDetails(
    ...     client="acme-corp",
    ...     portfolio="ecommerce",
    ...     app="web-frontend",
    ...     branch="main",
    ...     build="v1.2.3"
    ... )

    >>> # Generate resource identifiers
    >>> print(dd.get_build_prn())  # "prn:ecommerce:web-frontend:main:v1.2.3"

    >>> # Generate S3 object keys
    >>> key = dd.get_object_key("artefacts", "deploy.yaml")
    >>> print(key)  # "artefacts/ecommerce/web-frontend/main/v1.2.3/deploy.yaml"

    >>> # Create from flexible arguments
    >>> dd = DeploymentDetails.from_arguments(
    ...     portfolio="mobile-apps",
    ...     app="ios-client"
    ... )

Related Classes:
    - ActionDetails: Uses DeploymentDetails for action file path generation
    - FileDetails: Base class for file storage and retrieval operations
    - ActionSpec: Uses deployment context for action specification loading

Note:
    DeploymentDetails enforces hierarchical dependencies where each level requires
    all parent levels to be present. This ensures consistent resource organization
    and prevents invalid deployment configurations.
"""

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

    Examples:
        >>> # Complete deployment hierarchy
        >>> dd = DeploymentDetails(
        ...     client="acme-corp",
        ...     portfolio="ecommerce",
        ...     app="web-frontend",
        ...     branch="feature/new-checkout",
        ...     build="v2.1.0-beta.3+f9a8b7c",
        ...     component="load-balancer",
        ...     environment="staging",
        ...     data_center="us-east-1"
        ... )

        >>> # Portfolio-level deployment
        >>> dd = DeploymentDetails(
        ...     client="acme-corp",
        ...     portfolio="data-analytics"
        ... )

        >>> # App-level deployment
        >>> dd = DeploymentDetails(
        ...     client="acme-corp",
        ...     portfolio="mobile-apps",
        ...     app="ios-client"
        ... )

        >>> # With custom tags and metadata
        >>> dd = DeploymentDetails(
        ...     client="acme-corp",
        ...     portfolio="ecommerce",
        ...     app="payment-service",
        ...     tags={"Team": "payments", "CostCenter": "engineering"},
        ...     delivered_by="jenkins-ci"
        ... )

    Validation Rules:
        - **Component requires Build**: Cannot specify component without build
        - **Build requires Branch**: Cannot specify build without branch
        - **Branch requires App**: Cannot specify branch without app
        - **Portfolio always required**: Portfolio must always be provided

    Scope Determination:
        Scope is automatically determined by the deepest level provided:
        - "build": When build is specified
        - "branch": When branch is specified but not build
        - "app": When app is specified but not branch
        - "portfolio": When only portfolio is specified

    Resource Identifier Format:
        PRNs (Portfolio Resource Names) follow this hierarchical format:
        - Portfolio: "prn:portfolio"
        - App: "prn:portfolio:app"
        - Branch: "prn:portfolio:app:branch"
        - Build: "prn:portfolio:app:branch:build"
        - Component: "prn:portfolio:app:branch:build:component"
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="Client identifier for multi-tenant deployments and billing isolation",
        default_factory=lambda: util.get_client(),
    )

    portfolio: str = Field(
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

    scope: str | None = Field(
        alias="Scope",
        description="Deployment scope determining storage hierarchy level",
        default=None,
    )

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

    def get_portfolio_prn(self) -> str:
        """Get the Portfolio Resource Name (PRN) for the deployment.

        Generates a PRN identifying the portfolio level of the deployment hierarchy.
        This is the most basic resource identifier in the system.

        Returns:
            str: Portfolio PRN in format 'prn:portfolio' (lowercase).

        Examples:
            >>> dd = DeploymentDetails(portfolio="ecommerce-platform")
            >>> print(dd.get_portfolio_prn())
            "prn:ecommerce-platform"

            >>> dd = DeploymentDetails(portfolio="Mobile-Apps")
            >>> print(dd.get_portfolio_prn())
            "prn:mobile-apps"
        """
        return f"prn:{self.portfolio}".lower()

    def get_app_prn(self) -> str:
        """Get the App Resource Name (PRN) for the deployment.

        Generates a PRN identifying the app level of the deployment hierarchy.
        If app is not specified, the app portion will be empty.

        Returns:
            str: App PRN in format 'prn:portfolio:app' (lowercase).

        Examples:
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web-frontend")
            >>> print(dd.get_app_prn())
            "prn:ecommerce:web-frontend"

            >>> dd = DeploymentDetails(portfolio="ecommerce", app=None)
            >>> print(dd.get_app_prn())
            "prn:ecommerce:"
        """
        return f"prn:{self.portfolio}:{self.app or ''}".lower()

    def get_branch_prn(self) -> str:
        """Get the Branch Resource Name (PRN) for the deployment.

        Generates a PRN identifying the branch level of the deployment hierarchy.
        Uses branch_short_name for AWS compatibility. If branch_short_name is not
        specified, the branch portion will be empty.

        Returns:
            str: Branch PRN in format 'prn:portfolio:app:branch' (lowercase).

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web-frontend",
            ...     branch_short_name="main"
            ... )
            >>> print(dd.get_branch_prn())
            "prn:ecommerce:web-frontend:main"

            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web-frontend",
            ...     branch="feature/user-auth",
            ...     branch_short_name="feature-user-auth"
            ... )
            >>> print(dd.get_branch_prn())
            "prn:ecommerce:web-frontend:feature-user-auth"
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}".lower()

    def get_build_prn(self) -> str:
        """Get the Build Resource Name (PRN) for the deployment.

        Generates a PRN identifying the build level of the deployment hierarchy.
        This is the most commonly used PRN for deployment operations.

        Returns:
            str: Build PRN in format 'prn:portfolio:app:branch:build' (lowercase).

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="api-gateway",
            ...     branch_short_name="main",
            ...     build="v1.2.3"
            ... )
            >>> print(dd.get_build_prn())
            "prn:ecommerce:api-gateway:main:v1.2.3"

            >>> dd = DeploymentDetails(
            ...     portfolio="mobile-apps",
            ...     app="ios-client",
            ...     branch_short_name="release-2.0",
            ...     build="2.0.1-beta.4+abc123"
            ... )
            >>> print(dd.get_build_prn())
            "prn:mobile-apps:ios-client:release-2.0:2.0.1-beta.4+abc123"
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}:{self.build or ''}".lower()

    def get_component_prn(self) -> str:
        """Get the Component Resource Name (PRN) for the deployment.

        Generates a PRN identifying the component level of the deployment hierarchy.
        This is the most specific resource identifier in the system.

        Returns:
            str: Component PRN in format 'prn:portfolio:app:branch:build:component' (lowercase).

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web-frontend",
            ...     branch_short_name="main",
            ...     build="v1.2.3",
            ...     component="load-balancer"
            ... )
            >>> print(dd.get_component_prn())
            "prn:ecommerce:web-frontend:main:v1.2.3:load-balancer"

            >>> dd = DeploymentDetails(
            ...     portfolio="data-platform",
            ...     app="etl-pipeline",
            ...     branch_short_name="main",
            ...     build="v3.1.0",
            ...     component="postgres-db"
            ... )
            >>> print(dd.get_component_prn())
            "prn:data-platform:etl-pipeline:main:v3.1.0:postgres-db"
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

        Examples:
            >>> # Called automatically during instance creation
            >>> values = {"portfolio": "test", "branch": "feature/user-login"}
            >>> processed = DeploymentDetails.validate_model_before(values)
            >>> print(processed["branch_short_name"])  # "feature-user-login"

        Side Effects:
            Modifies the provided values dictionary by adding missing defaults
            and normalizing field names.
        """
        if isinstance(values, dict):
            # Set client if not provided
            client = values.pop("client", None) or values.pop("Client", None)
            if not client:
                client = util.get_client()
            values["client"] = client

            # Generate branch_short_name from branch
            branch = values.get("Branch", None) or values.get("branch", None)
            branch_short_name = values.get("BranchShortName", None) or values.get("branch_short_name", None)
            if not branch_short_name:
                values["branch_short_name"] = util.branch_short_name(branch)

            # Set delivered_by if not provided
            delivered_by = values.get("DeliveredBy", None) or values.get("delivered_by", None)
            if not delivered_by:
                values["delivered_by"] = util.get_delivered_by()
            values["delivered_by"] = delivered_by

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

        Examples:
            >>> # Valid hierarchy
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     branch="main",
            ...     build="v1.0",
            ...     component="lb"
            ... )  # Success

            >>> # Invalid: component without build
            >>> try:
            ...     dd = DeploymentDetails(
            ...         portfolio="ecommerce",
            ...         app="web",
            ...         component="lb"
            ...     )
            ... except ValueError as e:
            ...     print(e)  # "Build is required when Component is provided"

        Validation Rules:
            - **Component → Build**: Component requires build to be specified
            - **Build → Branch**: Build requires branch to be specified
            - **Branch → App**: Branch requires app to be specified
            - **App → Portfolio**: App requires portfolio (enforced by field definition)

        Side Effects:
            Sets the scope attribute if not already provided based on the deepest
            level of the hierarchy that is populated.
        """
        if self.component and not self.build:
            raise ValueError("Build is required when Component is provided")

        if self.build and not self.branch:
            raise ValueError("Branch is required when Build is provided")

        if self.branch and not self.app:
            raise ValueError("App is required when Branch is provided")

        # Set scope if not provided
        if not self.scope:
            self.scope = self.get_scope()

        return self

    def get_scope(self) -> str:
        """Get the deployment scope based on available fields.

        Determines the deployment scope by examining the hierarchy depth and
        returning the most specific level available. Can be overridden by
        the ENV_SCOPE environment variable.

        Returns:
            str: Deployment scope - one of:
                - "build": Most specific, when build is provided
                - "branch": When branch provided but not build
                - "app": When app provided but not branch
                - "portfolio": When only portfolio provided

        Examples:
            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     branch="main",
            ...     build="v1.0"
            ... )
            >>> print(dd.get_scope())  # "build"

            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web")
            >>> print(dd.get_scope())  # "app"

            >>> dd = DeploymentDetails(portfolio="ecommerce")
            >>> print(dd.get_scope())  # "portfolio"

        Environment Override:
            The ENV_SCOPE environment variable can override automatic determination:
            ```bash
            export SCOPE=branch
            ```
        """
        return DeploymentDetails.get_scope_from(self.portfolio, self.app, self.branch, self.build)

    @staticmethod
    def get_scope_from(portfolio: str | None, app: str | None, branch: str | None, build: str | None) -> str:
        """Determine deployment scope from individual hierarchy components.

        Static method for determining scope without requiring a DeploymentDetails instance.
        Useful for scope calculation during instance creation or validation.

        Args:
            portfolio (str, optional): Portfolio name.
            app (str, optional): Application name.
            branch (str, optional): Branch name.
            build (str, optional): Build identifier.

        Returns:
            str: Determined scope based on deepest level provided.

        Examples:
            >>> scope = DeploymentDetails.get_scope_from("ecom", "web", "main", "v1.0")
            >>> print(scope)  # "build"

            >>> scope = DeploymentDetails.get_scope_from("ecom", "web", None, None)
            >>> print(scope)  # "app"

            >>> scope = DeploymentDetails.get_scope_from("ecom", None, None, None)
            >>> print(scope)  # "portfolio"

        Environment Override:
            The ENV_SCOPE environment variable takes precedence over automatic determination.
        """
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
        """Get deployment identity as a PRN with wildcards for missing fields.

        Generates a complete PRN representation using wildcards (*) for missing
        hierarchy levels. Useful for pattern matching and resource queries.

        Returns:
            str: Complete PRN with wildcards for missing fields.

        Examples:
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web")
            >>> print(dd.get_identity())
            "prn:ecommerce:web:*:*"

            >>> dd = DeploymentDetails(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     branch_short_name="main",
            ...     build="v1.0"
            ... )
            >>> print(dd.get_identity())
            "prn:ecommerce:web:main:v1.0"

            >>> dd = DeploymentDetails(portfolio="mobile-apps")
            >>> print(dd.get_identity())
            "prn:mobile-apps:*:*:*"

        Usage Patterns:
            Identity PRNs are commonly used for:
            - Resource query patterns
            - Access control policy matching
            - Deployment target specification
            - Audit trail generation
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
            **kwargs: Flexible keyword arguments supporting multiple naming conventions:

                     **Core Hierarchy Parameters:**
                     - client/Client (str): Client identifier
                     - portfolio/Portfolio (str): Portfolio name (required)
                     - app/App (str): Application name
                     - branch/Branch (str): Branch name
                     - branch_short_name/BranchShortName (str): AWS-compatible branch name
                     - build/Build (str): Build identifier
                     - component/Component (str): Component name

                     **Context Parameters:**
                     - environment/Environment (str): Deployment environment
                     - data_center/DataCenter (str): Data center location
                     - scope/Scope (str): Deployment scope override

                     **Special Parameters:**
                     - prn (str): Complete PRN to parse instead of individual fields
                     - tags/Tags (dict): Resource tags
                     - stack_file/StackFile (str): CloudFormation stack file
                     - delivered_by/DeliveredBy (str): Delivery person/system

        Returns:
            DeploymentDetails: Fully configured instance with all fields populated.

        Raises:
            ValueError: If required client parameter cannot be determined or if
                       PRN parsing fails.

        Examples:
            >>> # Create from individual parameters
            >>> dd = DeploymentDetails.from_arguments(
            ...     client="acme-corp",
            ...     portfolio="ecommerce",
            ...     app="web-frontend"
            ... )

            >>> # Create from PRN string
            >>> dd = DeploymentDetails.from_arguments(
            ...     client="acme-corp",
            ...     prn="prn:ecommerce:web-frontend:main:v1.0.0:load-balancer"
            ... )

            >>> # Create with framework defaults
            >>> dd = DeploymentDetails.from_arguments(
            ...     portfolio="mobile-apps"
            ...     # client, app, branch, build from framework defaults
            ... )

            >>> # Create with mixed case parameters (API compatibility)
            >>> dd = DeploymentDetails.from_arguments(
            ...     Client="AcmeCorp",
            ...     Portfolio="Ecommerce",
            ...     App="WebFrontend",
            ...     Branch="feature/checkout",
            ...     Build="v2.1.0"
            ... )

            >>> # Create with environment context
            >>> dd = DeploymentDetails.from_arguments(
            ...     portfolio="data-platform",
            ...     app="etl-pipeline",
            ...     environment="production",
            ...     data_center="us-east-1",
            ...     tags={"Team": "data-engineering", "Environment": "prod"}
            ... )

        Parameter Resolution Priority:
            1. **PRN Parsing**: If prn parameter provided, parse hierarchy from it
            2. **Explicit Parameters**: Use provided portfolio, app, branch, build, component
            3. **Framework Defaults**: Apply defaults from framework configuration
            4. **Intelligent Defaults**: Generate missing values (e.g., branch_short_name)

        Factory Patterns:
            ```python
            # Pattern 1: Minimal creation with defaults
            dd = DeploymentDetails.from_arguments(portfolio="web-services")

            # Pattern 2: Complete hierarchy specification
            dd = DeploymentDetails.from_arguments(
                client="acme", portfolio="ecom", app="web",
                branch="main", build="v1.0", component="db"
            )

            # Pattern 3: PRN-based creation
            dd = DeploymentDetails.from_arguments(
                client="acme", prn="prn:ecom:web:main:v1.0:db"
            )

            # Pattern 4: CLI integration with PascalCase
            dd = DeploymentDetails.from_arguments(**cli_args)
            ```
        """

        def _get(key1: str, key2: str, default: str | None, can_be_empty: bool = False) -> str:
            """Extract parameter with fallback and default handling."""
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else default

        client = _get("client", "Client", util.get_client())

        prn = kwargs.get("prn", None)
        if prn is not None:
            portfolio, app, branch, build, component = util.split_prn(prn)

        else:
            # You cannot set portfolio to None or empty string.  It must be provided.
            portfolio = _get("portfolio", "Portfolio", util.get_portfolio())

            # You are allowed to set app to None or empty string.  Only call for default if not provided.
            app = _get("app", "App", util.get_app(), True)

            # You are allowed to set branch to None or empty string.  Only call for default if not provided.
            branch = _get("branch", "Branch", util.get_branch(), True)

            # If supplied a branch short name, use it.  Otherwise, generate from branch.
            branch_short_name = _get("branch_short_name", "BranchShortName", util.branch_short_name(branch))

            # You are allow to set build to None or empty string.  Only call for default if not provided.
            build = _get("build", "Build", util.get_build(), True)

            component = _get("component", "Component", None)

        scope = _get("scope", "Scope", cls.get_scope_from(portfolio, app, branch, build))

        return cls(
            client=client,
            portfolio=portfolio,
            app=app,
            branch=branch,
            branch_short_name=branch_short_name,
            build=build,
            component=component,
            scope=scope,
            environment=_get("environment", "Environment", None),
            data_center=_get("data_center", "DataCenter", None),
            tags=_get("tags", "Tags", None),
            stack_file=_get("stack_file", "StackFile", None),
            delivered_by=_get("delivered_by", "DeliveredBy", None),
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
            - Local mode: Uses OS-appropriate separators (\ on Windows, / on Unix)
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

    def get_client_portfolio_key(self) -> str:
        """Generate client-portfolio composite key for database operations.

        Creates a composite key used for AppFactsModel retrieval and other
        database operations that require client-portfolio identification.

        Returns:
            str: Composite key in format "client:portfolio".

        Examples:
            >>> dd = DeploymentDetails(
            ...     client="acme-corp",
            ...     portfolio="ecommerce"
            ... )
            >>> key = dd.get_client_portfolio_key()
            >>> print(key)  # "acme-corp:ecommerce"

            >>> # Use for database lookup
            >>> app_facts = AppFactsModel.get(key, app_name)

        Usage:
            This key format is used throughout the Simple Cloud Kit for:
            - Database record identification
            - Multi-tenant data isolation
            - Resource access control
            - Billing and cost tracking
        """
        return f"{self.client}:{self.portfolio}"
