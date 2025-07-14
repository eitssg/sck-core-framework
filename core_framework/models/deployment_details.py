"""
DeploymentDetails Model Module
==============================

This module contains the DeploymentDetails class which provides a model for how deployment
details are to be provided to the core-execute library.

The DeploymentDetails class identifies the Client, Portfolio, App, Branch, Build, Component,
Environment, DataCenter, Scope, Tags, and StackFile for a deployment. It provides methods
for generating resource identifiers and S3 object keys.

Classes
-------
DeploymentDetails : BaseModel
    Model for deployment details with validation and utility methods.

Examples
--------
Creating a DeploymentDetails instance::

    >>> dd = DeploymentDetails(
    ...     client="my-client",
    ...     portfolio="my-portfolio",
    ...     app="my-app",
    ...     branch="feature/new-feature",
    ...     build="1.0.0"
    ... )

Creating from arguments with automatic defaults::

    >>> dd = DeploymentDetails.from_arguments(
    ...     portfolio="my-portfolio",
    ...     app="my-app"
    ... )

Generating S3 keys::

    >>> key = dd.get_object_key("artefacts", "deploy.yaml")
    >>> print(key)  # artefacts/my-portfolio/my-app/feature-new-feature/1.0.0/deploy.yaml
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
    """
    DeploymentDetails identifies deployment context and generates resource identifiers.

    This class provides a comprehensive model for deployment details including client
    information, application hierarchy (portfolio/app/branch/build), deployment context,
    and utility methods for generating S3 keys and resource identifiers.

    Attributes
    ----------
    client : str
        The name of the client or customer (installation or AWS Organization)
    portfolio : str
        Portfolio name is the BizApp name
    app : str | None
        The name of the part of the BizApp. The deployment unit.
    branch : str | None
        The name of the branch of the deployment unit being deployed
    branch_short_name : str | None
        The short name of the branch suitable for AWS resource names
    build : str | None
        The build number, version number, or repo tag
    component : str | None
        The item deployed (EC2, Volume, ResourceGroup, etc)
    environment : str | None
        Related to the Zone (Prod, Dev, Non-Prod, UAT, PEN, PERF, PT, etc)
    data_center : str | None
        The physical location, similar to AWS region (us-east-1, us-west-2, etc)
    scope : str | None
        The deployment scope (portfolio, app, branch, build)
    tags : dict[str, str] | None
        Key-value pairs that can be applied to resources
    stack_file : str | None
        The name of the CloudFormation stack file used in deployment
    delivered_by : str | None
        The name of the person or system that delivered the deployment

    Notes
    -----
    Hierarchical Dependencies:
        - Component requires Build
        - Build requires Branch
        - Branch requires App
        - App requires Portfolio

    Scope Determination:
        The scope is automatically determined based on the most specific level provided,
        unless explicitly overridden via environment variable or parameter.

    Examples
    --------
    Basic deployment details::

        >>> dd = DeploymentDetails(
        ...     client="acme-corp",
        ...     portfolio="ecommerce",
        ...     app="web-frontend",
        ...     branch="main",
        ...     build="v1.2.3"
        ... )

    Component-level deployment::

        >>> dd = DeploymentDetails(
        ...     client="acme-corp",
        ...     portfolio="ecommerce",
        ...     app="web-frontend",
        ...     branch="main",
        ...     build="v1.2.3",
        ...     component="load-balancer"
        ... )

    Generating resource identifiers::

        >>> prn = dd.get_build_prn()
        >>> print(prn)  # prn:ecommerce:web-frontend:main:v1.2.3

    Generating S3 keys::

        >>> key = dd.get_artefacts_key("deploy.yaml")
        >>> print(key)  # artefacts/ecommerce/web-frontend/main/v1.2.3/deploy.yaml
    """
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",  # Alias for PascalCase compatibility
        description="Client is the name of the client or customer (installation or AWS Organizatoion)",
        default=lambda: util.get_client(),  # Default to util.get_client()
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
        """
        Get the Portfolio Resource Name (PRN) for the deployment.
        
        Returns
        -------
        str
            The portfolio PRN in format 'prn:portfolio'.
            
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="my-portfolio")
            >>> print(dd.get_portfolio_prn())
            prn:my-portfolio
        """
        return f"prn:{self.portfolio}".lower()

    def get_app_prn(self) -> str:
        """
        Get the App Resource Name (PRN) for the deployment.
        
        Returns
        -------
        str
            The app PRN in format 'prn:portfolio:app'.
            
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="my-portfolio", app="my-app")
            >>> print(dd.get_app_prn())
            prn:my-portfolio:my-app
        """
        return f"prn:{self.portfolio}:{self.app or ''}".lower()

    def get_branch_prn(self) -> str:
        """
        Get the Branch Resource Name (PRN) for the deployment.
        
        Returns
        -------
        str
            The branch PRN in format 'prn:portfolio:app:branch'.
            
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="my-portfolio", app="my-app", branch_short_name="main")
            >>> print(dd.get_branch_prn())
            prn:my-portfolio:my-app:main
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}".lower()

    def get_build_prn(self) -> str:
        """
        Get the Build Resource Name (PRN) for the deployment.
        
        Returns
        -------
        str
            The build PRN in format 'prn:portfolio:app:branch:build'.
            
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="my-portfolio", app="my-app", 
            ...                       branch_short_name="main", build="1.0.0")
            >>> print(dd.get_build_prn())
            prn:my-portfolio:my-app:main:1.0.0
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}:{self.build or ''}".lower()

    def get_component_prn(self) -> str:
        """
        Get the Component Resource Name (PRN) for the deployment.
        
        Returns
        -------
        str
            The component PRN in format 'prn:portfolio:app:branch:build:component'.
            
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="my-portfolio", app="my-app", 
            ...                       branch_short_name="main", build="1.0.0", component="web")
            >>> print(dd.get_component_prn())
            prn:my-portfolio:my-app:main:1.0.0:web
        """
        return f"prn:{self.portfolio}:{self.app or ''}:{self.branch_short_name or ''}:{self.build or ''}:{self.component or ''}".lower()

    @model_validator(mode="before")
    @classmethod
    def validate_incoming(cls, values: dict) -> dict:
        """
        Validate and populate missing fields before model creation.
        
        This validator ensures that required fields are properly populated by applying
        intelligent defaults when values are missing.
        
        Parameters
        ----------
        values : dict
            The input values for model creation.
            
        Returns
        -------
        dict
            The validated and potentially modified values.
            
        Notes
        -----
        Side Effects:
            - Populates missing client with util.get_client()
            - Generates branch_short_name from branch if branch is provided
            - Populates missing delivered_by with util.get_delivered_by()
        """
        if isinstance(values, dict):
            # Set client if not provided
            if not values.get("Client") and not values.get("client"):
                values["client"] = util.get_client()
            
            # Generate branch_short_name from branch
            branch = values.get("Branch", values.get("branch", None))
            if branch:
                values["branch_short_name"] = util.branch_short_name(branch)
            else:
                values["branch_short_name"] = branch  # branch might be V_EMPTY
            
            # Set delivered_by if not provided
            if not values.get("DeliveredBy") and not values.get("delivered_by"):
                values["delivered_by"] = util.get_delivered_by()
        
        return values

    @model_validator(mode="after")
    def check_conditional_fields(self) -> Self:
        """
        Validate hierarchical dependencies between fields.
        
        This validator ensures that the deployment hierarchy is maintained:
        Component -> Build -> Branch -> App -> Portfolio
        
        Returns
        -------
        Self
            The validated DeploymentDetails instance.
            
        Raises
        ------
        ValueError
            If hierarchical dependencies are not satisfied.
            
        Notes
        -----
        Validation Rules:
            - Component requires Build
            - Build requires Branch  
            - Branch requires App
            - App requires Portfolio (implicitly required by field definition)
            
        Side Effects:
            - Sets scope if not provided based on available fields
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
        """
        Get the deployment scope based on available fields.
    
        Returns
        -------
        str
            The deployment scope (portfolio, app, branch, or build).
        
        Notes
        -----
        Scope is determined by the most specific level available:
            - build: if build is provided
            - branch: if branch is provided but not build
            - app: if app is provided but not branch
            - portfolio: if only portfolio is provided
        
        Environment variable ENV_SCOPE can override this logic.
        """
        return DeploymentDetails._get_standard_scope(
            self.portfolio, self.app, self.branch, self.build
        )

    @staticmethod
    def _get_standard_scope(
        portfolio: str | None, app: str | None, branch: str | None, build: str | None
    ) -> str:
        """
        Determine the standard scope based on provided deployment fields.
    
        Parameters
        ----------
        portfolio : str | None
            The portfolio name.
        app : str | None
            The app name.
        branch : str | None
            The branch name.
        build : str | None
            The build identifier.
        
        Returns
        -------
        str
            The determined scope (portfolio, app, branch, or build).
        
        Notes
        -----
        The ENV_SCOPE environment variable can override the automatic determination.
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
        """
        Get the deployment identity as a PRN with wildcards for missing fields.
    
        Returns
        -------
        str
            The deployment identity in PRN format with '*' for missing fields.
        
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web")
            >>> print(dd.get_identity())
            prn:ecommerce:web:*:*
        """
        portfolio = self.portfolio or "*"
        app = self.app or "*"
        branch_short_name = self.branch_short_name or "*"
        build = self.build or "*"

        return f"prn:{portfolio}:{app}:{branch_short_name}:{build}".lower()

    @staticmethod
    def from_arguments(**kwargs) -> "DeploymentDetails":
        """
        Create a DeploymentDetails instance from keyword arguments.
        
        This factory method provides a flexible way to create DeploymentDetails instances
        by accepting various parameter combinations and applying intelligent defaults.
        
        Parameters
        ----------
        **kwargs : dict
            Keyword arguments that can include:
                - client/Client (str): Client identifier
                - prn (str): Complete PRN to parse
                - portfolio/Portfolio (str): Portfolio name
                - app/App (str): Application name
                - branch/Branch (str): Branch name
                - branch_short_name/BranchShortName (str): Short branch name
                - build/Build (str): Build identifier
                - component/Component (str): Component name
                - scope/Scope (str): Deployment scope
                - environment/Environment (str): Environment name
                - data_center/DataCenter (str): Data center location
                - tags/Tags (dict): Resource tags
                - stack_file/StackFile (str): Stack file name
                - delivered_by/DeliveredBy (str): Delivery person/system
                
        Returns
        -------
        DeploymentDetails
            A new DeploymentDetails instance with populated fields.
            
        Raises
        ------
        ValueError
            If required client parameter is missing or invalid.
            
        Examples
        --------
        Create from individual parameters::

            >>> dd = DeploymentDetails.from_arguments(
            ...     client="my-client",
            ...     portfolio="my-portfolio",
            ...     app="my-app"
            ... )
            
        Create from PRN::

            >>> dd = DeploymentDetails.from_arguments(
            ...     client="my-client",
            ...     prn="prn:portfolio:app:branch:build:component"
            ... )
        """
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
            branch_short_name=branch_short_name,  # Fixed: was branchShortName
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
    def model_dump(self, **kwargs) -> dict:
        """
        Override to exclude None values by default.
    
        This method customizes the default serialization behavior to exclude
        None values unless explicitly requested.
    
        Parameters
        ----------
        **kwargs : dict
            Keyword arguments passed to the parent model_dump method.
            All standard Pydantic model_dump parameters are supported.
            
        Returns
        -------
        dict
            Dictionary representation of the model with None values excluded by default.
            
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="ecom", app="web", component=None)
            >>> result = dd.model_dump()
            >>> # component will not be in the result dict
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "exclude_unset" not in kwargs:
            kwargs["exclude_unset"] = True
        return super().model_dump(**kwargs)

    def get_object_key(
        self,
        object_type: str,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """
        Get the object path from the deployment details.
        
        This method generates paths suitable for S3 keys or local filesystem paths
        based on the deployment hierarchy and scope.
        
        Parameters
        ----------
        object_type : str
            The type of object to get the path for (files, packages, artefacts).
        name : str | None, optional
            The name of the object to get the path for. If None, returns the directory path.
        scope : str | None, optional
            The scope override. If None, uses the deployment's scope.
            Valid values: portfolio, app, branch, build.
        s3 : bool | None, optional
            Forces forward slashes for S3 instead of OS-dependent separators.
            If None, determined by util.is_use_s3().
        
        Returns
        -------
        str
            The path to the object in the specified format.
        
        Examples
        --------
        Get artefacts directory path::

            >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
            >>> path = dd.get_object_key("artefacts")
            >>> print(path)  # artefacts/ecom/web/main/1.0
            
        Get specific file path::

            >>> path = dd.get_object_key("artefacts", "deploy.yaml")
            >>> print(path)  # artefacts/ecom/web/main/1.0/deploy.yaml
            
        Override scope::

            >>> path = dd.get_object_key("artefacts", "app-config.yaml", scope="app")
            >>> print(path)  # artefacts/ecom/web/app-config.yaml
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
        Get the artefacts path in the core automation storage.
        
        This is a convenience method that calls get_object_key with object_type="artefacts".
        
        Parameters
        ----------
        name : str | None, optional
            The name of the artefacts file or directory.
        scope : str | None, optional
            The scope override. If None, uses the deployment's scope.
        s3 : bool | None, optional
            Forces forward slashes for S3 instead of OS-dependent separators.
        
        Returns
        -------
        str
            The path to the artefacts location.
        
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
            >>> path = dd.get_artefacts_key("deploy.yaml")
            >>> print(path)  # artefacts/ecom/web/main/1.0/deploy.yaml
        """
        return self.get_object_key(OBJ_ARTEFACTS, name, scope, s3)

    def get_files_key(
        self,
        name: str | None = None,
        scope: str | None = None,
        s3: bool | None = None,
    ) -> str:
        """
        Get the files path in the core automation storage.
        
        This is a convenience method that calls get_object_key with object_type="files".
        
        Parameters
        ----------
        name : str | None, optional
            The name of the file or directory.
        scope : str | None, optional
            The scope override. If None, uses the deployment's scope.
        s3 : bool | None, optional
            Forces forward slashes for S3 instead of OS-dependent separators.
        
        Returns
        -------
        str
            The path to the files location.
        
        Examples
        --------
        ::

            >>> dd = DeploymentDetails(portfolio="ecom", app="web", branch="main", build="1.0")
            >>> path = dd.get_files_key("config.json")
            >>> print(path)  # files/ecom/web/main/1.0/config.json
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
