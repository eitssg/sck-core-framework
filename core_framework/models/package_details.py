"""
PackageDetails Model Module
===========================

This module contains the PackageDetails class used to track where package.zip is located
in storage (S3 or local filesystem) for a deployment.

The PackageDetails class provides a comprehensive model for package information including
storage location, metadata, and deployment specifications. It supports both local filesystem
and S3 storage modes with automatic path resolution.

Classes
-------
PackageDetails : BaseModel
    Model for package details with storage location and metadata.

Examples
--------
Creating a PackageDetails for S3 storage::

    >>> package = PackageDetails(
    ...     client="my-client",
    ...     bucket_name="my-deployment-bucket",
    ...     bucket_region="us-east-1",
    ...     key="packages/ecommerce/web-app/main/1.0.0/package.zip",
    ...     mode="service"
    ... )

Creating a PackageDetails for local storage::

    >>> package = PackageDetails(
    ...     client="my-client",
    ...     bucket_name="/local/storage/root",
    ...     key="packages/ecommerce/web-app/main/1.0.0/package.zip",
    ...     mode="local"
    ... )

Creating from arguments with automatic defaults::

    >>> from core_framework.models.deployment_details import DeploymentDetails
    >>> dd = DeploymentDetails(portfolio="ecommerce", app="web-app", build="1.0.0")
    >>> package = PackageDetails.from_arguments(deployment_details=dd)
"""

from typing import Any, Self
import os
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator

import core_framework as util

from .deployment_details import DeploymentDetails as DeploymentDetailsClass
from .deploy_spec import DeploySpec as DeploySpecClass

from core_framework.constants import (
    V_FULL,
    V_INCREMENTAL,
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
    V_PACKAGE_ZIP,
    OBJ_PACKAGES,
)


class PackageDetails(BaseModel):
    """
    PackageDetails is a model that contains all information needed to locate and process a package.
    
    A package is the artefact called "package.zip" that is uploaded and contains all of the templates
    and resources necessary to perform a deployment. Packages are typically stored in the packages
    folder structure: **bucket_name/packages/portfolio/app/branch/build/package.zip**.

    Attributes
    ----------
    client : str
        The client identifier for the deployment.
    bucket_region : str
        The region of the bucket where packages are stored (S3 mode) or empty for local mode.
    bucket_name : str
        The name of the S3 bucket or root folder path where packages are stored.
        For S3 mode: bucket name (e.g., "my-deployment-bucket")
        For local mode: root directory path (e.g., "/local/storage/root")
    key : str
        The full path to the package file relative to bucket_name.
        Example: "packages/ecommerce/web-app/main/1.0.0/package.zip"
    mode : str
        The storage mode. Either "local" for local filesystem or "service" for S3 storage.
        Defaults to "local" if util.is_local_mode() else "service".
    compile_mode : str
        The compile mode of the package. Either "full" or "incremental". Defaults to "full".
    deployspec : DeploySpecClass | None
        Optional DeploySpec object containing deployment actions. Added later by lambda handlers.
    version_id : str | None
        The version ID of the package file (S3 only). Used for S3 object versioning.
    content_type : str | None
        The MIME type of the package file. Defaults to "application/zip".

    Properties
    ----------
    data_path : str
        The storage volume path for the application. Used for local mode only.
    temp_dir : str
        The temporary directory to use for processing the package.

    Examples
    --------
    S3 storage mode::

        >>> package = PackageDetails(
        ...     client="my-client",
        ...     bucket_name="deployment-bucket",
        ...     bucket_region="us-east-1",
        ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
        ...     mode="service"
        ... )

    Local storage mode::

        >>> package = PackageDetails(
        ...     client="my-client",
        ...     bucket_name="/var/deployments",
        ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
        ...     mode="local"
        ... )

    With deployment specification::

        >>> from core_framework.models.deploy_spec import DeploySpec
        >>> from core_framework.models.action_spec import ActionSpec
        >>> action = ActionSpec(name="deploy", kind="create_stack", params={"stack_name": "web"})
        >>> deploy_spec = DeploySpec(actions=[action])
        >>> package = PackageDetails(
        ...     client="my-client",
        ...     bucket_name="deployment-bucket",
        ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
        ...     deployspec=deploy_spec
        ... )
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="The client identifier for the deployment",
        default="",
    )

    bucket_region: str = Field(
        alias="BucketRegion",
        description="The region of the bucket where packages are stored (S3 mode only)",
        default=V_EMPTY,
    )

    bucket_name: str = Field(
        alias="BucketName",
        description="The S3 bucket name or root directory path where packages are stored",
        default=V_EMPTY,
    )

    key: str = Field(
        alias="Key",
        description="The full path to the package file relative to bucket_name",
        default=V_EMPTY,
    )

    mode: str = Field(
        alias="Mode",
        description="The storage mode: 'local' for filesystem or 'service' for S3",
        default_factory=lambda: V_LOCAL if util.is_local_mode() else V_SERVICE,
    )

    compile_mode: str = Field(
        alias="CompileMode",
        description="The compile mode: 'full' or 'incremental'",
        default=V_FULL,
    )

    deployspec: DeploySpecClass | None = Field(
        alias="DeploySpec",
        description="Optional DeploySpec object containing deployment actions",
        default=None,
    )

    version_id: str | None = Field(
        alias="VersionId",
        description="The version ID of the package file (S3 only)",
        default=None,
    )

    content_type: str | None = Field(
        alias="ContentType",
        description="The MIME type of the package file",
        default="application/zip",
    )

    @property
    def data_path(self) -> str:
        """
        Get the storage volume path for the application.
        
        Used for local mode only. Returns the storage volume path from utility functions.
        For service mode, this returns an empty string.
        
        Returns
        -------
        str
            The storage volume path for local mode, empty string for service mode.
            
        Examples
        --------
        ::

            >>> package = PackageDetails(mode="local")
            >>> path = package.data_path
            >>> print(path)  # /var/local/storage (example)
        """
        return util.get_storage_volume() if self.mode == V_LOCAL else ""

    @property
    def temp_dir(self) -> str:
        """
        Get the temporary directory for processing the package.
        
        Returns the system temporary directory path from utility functions.
        
        Returns
        -------
        str
            The temporary directory path.
            
        Examples
        --------
        ::

            >>> package = PackageDetails()
            >>> temp_path = package.temp_dir
            >>> print(temp_path)  # /tmp (example)
        """
        return util.get_temp_dir()

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        """
        Validate that mode is either 'local' or 'service'.
        
        Parameters
        ----------
        value : str
            The mode value to validate.
            
        Returns
        -------
        str
            The validated mode value.
            
        Raises
        ------
        ValueError
            If mode is not 'local' or 'service'.
        """
        if value not in [V_LOCAL, V_SERVICE]:
            raise ValueError(f"Mode must be '{V_LOCAL}' or '{V_SERVICE}', got '{value}'")
        return value

    @field_validator("compile_mode")
    @classmethod
    def validate_compile_mode(cls, value: str) -> str:
        """
        Validate that compile_mode is either 'full' or 'incremental'.
        
        Parameters
        ----------
        value : str
            The compile_mode value to validate.
            
        Returns
        -------
        str
            The validated compile_mode value.
            
        Raises
        ------
        ValueError
            If compile_mode is not 'full' or 'incremental'.
        """
        if value not in [V_FULL, V_INCREMENTAL, V_EMPTY]:
            raise ValueError(f"Compile mode must be '{V_FULL}' or 'incremental', got '{value}'")
        return value

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        """
        Validate and normalize the key path based on storage mode.
        
        Parameters
        ----------
        value : str
            The key path to validate.
            
        Returns
        -------
        str
            The validated and normalized key path.
            
        Notes
        -----
        - For S3 mode: removes leading slashes and normalizes to forward slashes
        - For local mode: normalizes to OS-appropriate path separators
        - Validates that the path is not empty when provided
        """
        if not value:
            return value
        
        # Remove leading slashes for consistency
        if value.startswith("/"):
            value = value.lstrip("/")
        if value.startswith("\\"):
            value = value.lstrip("\\")
        
        # Note: We can't access self.mode here in a field validator
        # So we'll normalize the path separators in the model_validator instead
        return value

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, values: Any) -> Any:
        """
        Validate and populate missing fields before model creation.
        
        This validator ensures that required fields are properly populated by applying
        intelligent defaults when values are missing.
        
        Parameters
        ----------
        values : Any
            The input values for model creation. Expected to be a dict for processing,
            but other types are passed through unchanged.
            
        Returns
        -------
        Any
            The validated and potentially modified values.
            
        Notes
        -----
        Side Effects:
            - Populates missing client with util.get_client()
            - Populates missing bucket_region with util.get_bucket_region()
            - Populates missing bucket_name with util.get_bucket_name()
        """
        if isinstance(values, dict):
            # Set client if not provided
            if not values.get("Client") and not values.get("client"):
                values["client"] = util.get_client()
            
            client = values.get("Client", values.get("client", util.get_client()))

            # Set bucket region if not provided
            if not values.get("BucketRegion") and not values.get("bucket_region"):
                values["bucket_region"] = util.get_bucket_region()
            
            region = values.get("BucketRegion", values.get("bucket_region"))

            # Set bucket name if not provided
            if not values.get("BucketName") and not values.get("bucket_name"):
                values["bucket_name"] = util.get_bucket_name(client, region)

        return values

    @model_validator(mode="after")
    def validate_after(self) -> Self:
        """
        Validate the complete model after creation.
        
        This validator performs cross-field validation to ensure the model is in a
        consistent state and normalizes paths based on storage mode.
        
        Returns
        -------
        Self
            The validated PackageDetails instance.
            
        Raises
        ------
        ValueError
            If version_id is provided for local mode (not supported).
            If bucket_region is provided for local mode (not needed).
            
        Notes
        -----
        Validation Rules:
            - version_id is only valid for service mode (S3)
            - bucket_region is only needed for service mode (S3)
        """
        if self.mode == V_LOCAL:
            if self.version_id:
                raise ValueError("version_id is not supported in local mode")
            if self.bucket_region and self.bucket_region != V_EMPTY:
                # Warning: bucket_region is not needed for local mode
                pass  # Allow but ignore for backward compatibility
        else:
            # Normalize key path for service mode (S3)
            self.key = self.key.replace("\\", "/")  # Normalize backslashes to forward slashes

        return self

    def get_name(self) -> str:
        """
        Get the filename from the key path.
        
        Extracts the filename from the full key path, handling both local and S3 paths.
        
        Returns
        -------
        str
            The filename from the key path, or default package name if no key is set.
            
        Examples
        --------
        ::

            >>> package = PackageDetails(key="packages/ecommerce/web/main/1.0.0/package.zip")
            >>> print(package.get_name())  # package.zip
            
            >>> package = PackageDetails(key="")
            >>> print(package.get_name())  # package.zip (default)
        """
        if not self.key:
            return V_PACKAGE_ZIP
        
        # Use appropriate separator based on mode
        separator = os.path.sep if self.mode == V_LOCAL else "/"
        return self.key.rsplit(separator, 1)[-1]

    def get_full_path(self) -> str:
        """
        Get the full path to the package file.
        
        Combines bucket_name and key to create the complete path to the package file.
        
        Returns
        -------
        str
            The full path to the package file.
            
        Examples
        --------
        S3 mode::

            >>> package = PackageDetails(
            ...     bucket_name="my-bucket",
            ...     key="packages/ecommerce/web/package.zip",
            ...     mode="service"
            ... )
            >>> print(package.get_full_path())  # my-bucket/packages/ecommerce/web/package.zip
            
        Local mode::

            >>> package = PackageDetails(
            ...     bucket_name="/var/storage",
            ...     key="packages/ecommerce/web/package.zip",
            ...     mode="local"
            ... )
            >>> print(package.get_full_path())  # /var/storage/packages/ecommerce/web/package.zip
        """
        if not self.bucket_name or not self.key:
            return ""
        
        # Use appropriate separator based on mode
        separator = os.path.sep if self.mode == V_LOCAL else "/"
        return f"{self.bucket_name}{separator}{self.key}"

    def set_key(self, deployment_details: DeploymentDetailsClass, filename: str) -> None:
        """
        Set the key path based on deployment details and filename.
        
        Generates the key path using the deployment details hierarchy and the specified filename.
        
        Parameters
        ----------
        deployment_details : DeploymentDetailsClass
            The deployment details object containing the deployment context.
        filename : str
            The filename for the package (e.g., "package.zip").
            
        Examples
        --------
        ::

            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> package = PackageDetails()
            >>> package.set_key(dd, "package.zip")
            >>> print(package.key)  # packages/ecommerce/web/main/1.0.0/package.zip
        """
        self.key = deployment_details.get_object_key(OBJ_PACKAGES, filename)

    def is_local_mode(self) -> bool:
        """
        Check if the package is in local storage mode.
        
        Returns
        -------
        bool
            True if mode is local, False if mode is service.
            
        Examples
        --------
        ::

            >>> package = PackageDetails(mode="local")
            >>> print(package.is_local_mode())  # True
            
            >>> package = PackageDetails(mode="service")
            >>> print(package.is_local_mode())  # False
        """
        return self.mode == V_LOCAL

    def is_service_mode(self) -> bool:
        """
        Check if the package is in service (S3) storage mode.
        
        Returns
        -------
        bool
            True if mode is service, False if mode is local.
            
        Examples
        --------
        ::

            >>> package = PackageDetails(mode="service")
            >>> print(package.is_service_mode())  # True
            
            >>> package = PackageDetails(mode="local")
            >>> print(package.is_service_mode())  # False
        """
        return self.mode == V_SERVICE

    @classmethod
    def from_arguments(cls, **kwargs) -> "PackageDetails":
        """
        Create a PackageDetails instance from keyword arguments.
        
        This factory method provides a flexible way to create PackageDetails instances
        by accepting various parameter combinations and applying intelligent defaults.
        
        Parameters
        ----------
        **kwargs : dict
            Keyword arguments that can include:
                - client/Client (str): Client identifier
                - key/Key/package_key/PackageKey (str): Package key path
                - package_file/PackageFile (str): Package filename (default: package.zip)
                - deployment_details/DeploymentDetails (DeploymentDetailsClass): Deployment context
                - bucket_name/BucketName (str): Bucket name or root path
                - bucket_region/BucketRegion (str): Bucket region (S3 only)
                - mode/Mode (str): Storage mode (local/service)
                - content_type/ContentType (str): MIME type
                - version_id/VersionId (str): S3 version ID
                - deployspec/DeploySpec (DeploySpecClass|dict|list): Deployment specification
                - compile_mode/CompileMode (str): Compile mode (full/incremental)
                
        Returns
        -------
        PackageDetails
            A new PackageDetails instance with populated fields.
            
        Raises
        ------
        ValueError
            If deployment_details cannot be created from provided arguments.
            
        Examples
        --------
        Create with explicit key::

            >>> package = PackageDetails.from_arguments(
            ...     client="my-client",
            ...     key="packages/ecommerce/web/main/1.0.0/package.zip"
            ... )
            
        Create from deployment details::

            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> package = PackageDetails.from_arguments(deployment_details=dd)
            
        Create with custom package file::

            >>> package = PackageDetails.from_arguments(
            ...     client="my-client",
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     package_file="custom-package.zip"
            ... )
        """
        # Get key from various possible parameter names
        key = kwargs.get(
            "key",
            kwargs.get(
                "Key", kwargs.get("package_key", kwargs.get("PackageKey", V_EMPTY))
            ),
        )
        
        # Get package filename
        package_file = kwargs.get(
            "package_file", kwargs.get("PackageFile", V_PACKAGE_ZIP)
        )
        
        # Generate key from deployment details if not provided
        if not key:
            dd = kwargs.get(
                "deployment_details", kwargs.get("DeploymentDetails", None)
            )
            if dd is None:
                # Try to create deployment details from kwargs
                dd = DeploymentDetailsClass.from_arguments(**kwargs)
            elif not isinstance(dd, DeploymentDetailsClass):
                # Convert dict to DeploymentDetails if needed
                dd = DeploymentDetailsClass.from_arguments(**dd)
            
            if dd:
                key = dd.get_object_key(OBJ_PACKAGES, package_file)

        # Get other parameters with fallbacks
        client = kwargs.get("client", kwargs.get("Client", util.get_client()))
        bucket_name = kwargs.get(
            "bucket_name", kwargs.get("BucketName", util.get_bucket_name(client))
        )
        bucket_region = kwargs.get(
            "bucket_region", kwargs.get("BucketRegion", util.get_bucket_region())
        )
        mode = kwargs.get(
            "mode", kwargs.get("Mode", V_LOCAL if util.is_local_mode() else V_SERVICE)
        )
        content_type = kwargs.get(
            "content_type", kwargs.get("ContentType", "application/zip")
        )
        version_id = kwargs.get("version_id", kwargs.get("VersionId", None))
        compile_mode = kwargs.get("compile_mode", kwargs.get("CompileMode", V_FULL))

        # Handle deployspec parameter
        deployspec = kwargs.get("deployspec", kwargs.get("DeploySpec", None))
        if isinstance(deployspec, dict):
            # Convert single ActionSpec dict to DeploySpec
            deployspec = DeploySpecClass(actions=[deployspec])
        elif isinstance(deployspec, list):
            # Convert list of ActionSpec dicts to DeploySpec
            deployspec = DeploySpecClass(actions=deployspec)
        elif deployspec is not None and not isinstance(deployspec, DeploySpecClass):
            # Invalid deployspec type
            deployspec = None

        return cls(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            mode=mode,
            compile_mode=compile_mode,
            deployspec=deployspec,
            content_type=content_type,
            version_id=version_id,
        )

    def model_dump(self, **kwargs) -> dict:
        """
        Override to exclude None values by default.
        
        Parameters
        ----------
        **kwargs : dict
            Keyword arguments passed to the parent model_dump method.
            All standard Pydantic model_dump parameters are supported.
            
        Returns
        -------
        dict
            Dictionary representation of the model with None values excluded by default.
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def __str__(self) -> str:
        """
        Return a human-readable string representation.
        
        Returns
        -------
        str
            String showing the package location and mode.
        """
        name = self.get_name()
        return f"PackageDetails({name}, mode={self.mode})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.
        
        Returns
        -------
        str
            Detailed representation showing key attributes.
        """
        return (
            f"PackageDetails(client='{self.client}', bucket_name='{self.bucket_name}', "
            f"key='{self.key}', mode='{self.mode}')"
        )
