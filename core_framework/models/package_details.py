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

from typing import Any
import os
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator

import core_framework as util

from .deployment_details import DeploymentDetails
from .deploy_spec import DeploySpec

from core_framework.constants import (
    V_FULL,
    V_INCREMENTAL,
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
    V_PACKAGE_ZIP,
    OBJ_PACKAGES,
)


class FolderInfo(BaseModel):
    """FolderInfo is a model that contains information about a folder witin the context of the core model."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="The client identifier for the deployment",
        default=V_EMPTY,
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

    mode: str = Field(
        alias="Mode",
        description="The storage mode: 'local' for filesystem or 'service' for S3",
        default=V_EMPTY,
    )

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

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        """
        Validate that content_type is a valid YAML or JSON MIME type.

        Parameters
        ----------
        value : str
            The content_type value to validate

        Returns
        -------
        str
            The validated content_type value

        Raises
        ------
        ValueError
            If content_type is not a supported MIME type
        """
        allowed_types = util.get_valid_mimetypes()
        if value not in allowed_types:
            raise ValueError(f"ContentType must be one of {allowed_types}, got: {value}")
        return value

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, values: dict[str, Any]) -> dict[str, Any]:
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
            client = values.get("Client") or values.get("client")

            if not client:
                client = util.get_client()
                values["client"] = client

            # Set bucket region if not provided
            region = values.get("BucketRegion") or values.get("bucket_region")
            if not region:
                region = util.get_bucket_region()
                values["bucket_region"] = region

            # Set bucket name if not provided
            bucket_name = values.get("BucketName") or values.get("bucket_name")
            if not bucket_name:
                bucket_name = util.get_bucket_name(client, region)
                values["bucket_name"] = bucket_name

            if not values.get("Mode") and not values.get("mode"):
                values["mode"] = V_LOCAL if util.is_local_mode() else V_SERVICE

        return values

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
            >>> print(package.get_full_path())  # s3://my-bucket/packages/ecommerce/web/package.zip

        Local mode::

            >>> package = PackageDetails(
            ...     bucket_name="/var/storage",
            ...     key="packages/ecommerce/web/package.zip",
            ...     mode="local"
            ... )
            >>> print(package.get_full_path())  # file:///var/storage/packages/ecommerce/web/package.zip

            >>> package = PackageDetails(
            ...     bucket_name="N:\data\storage",
            ...     key="packages\ecommerce\web\package.zip",
            ...     mode="local"
            ... )
            >>> print(package.get_full_path())  # file://N:\data\storage\packages\ecommerce\web\package.zip
        """
        if not self.bucket_name or not self.key:
            return ""

        # Use appropriate separator based on mode
        if self.mode == V_LOCAL:
            separator = os.path.sep
            return f"file://{self.bucket_name}{separator}{self.key}"
        else:
            separator = "/"
            return f"s3://{self.bucket_name}/{self.key}"

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


class PackageDetails(FolderInfo):
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
    deployspec : DeploySpec | None
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

    compile_mode: str = Field(
        alias="CompileMode",
        description="The compile mode: 'full' or 'incremental'",
        default=V_FULL,
    )

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

    deployspec: DeploySpec | None = Field(
        alias="DeploySpec",
        description="Optional DeploySpec object containing deployment actions",
        default=None,
    )

    def set_key(self, deployment_details: DeploymentDetails, filename: str) -> None:
        """
        Set the key path based on deployment details and filename.

        Generates the key path using the deployment details hierarchy and the specified filename.

        Parameters
        ----------
        deployment_details : DeploymentDetails
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
                - deployment_details/DeploymentDetails (DeploymentDetails): Deployment context
                - bucket_name/BucketName (str): Bucket name or root path
                - bucket_region/BucketRegion (str): Bucket region (S3 only)
                - mode/Mode (str): Storage mode (local/service)
                - content_type/ContentType (str): MIME type
                - version_id/VersionId (str): S3 version ID
                - deployspec/DeploySpec (DeploySpec|dict|list): Deployment specification
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

            >>> package = PackageDetails.from_arguments(**command_line_args)

        """

        def _get(key1: str, key2: str, defualt: str | None, can_be_empty: bool = False) -> str:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else defualt

        # Get other parameters with fallbacks
        client = _get("client", "Client", util.get_client())

        # Get package filename
        package_file = _get("package_file", "PackageFile", V_PACKAGE_ZIP)

        # Get key from various possible parameter names
        key = _get("key", "Key", V_EMPTY)
        if not key:
            dd = _get("deployment_details", "DeploymentDetails", None)
            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails.from_arguments(**kwargs)

            if dd:
                key = dd.get_object_key(OBJ_PACKAGES, package_file)

        # Handle bucket_region
        bucket_region = _get("bucket_region", "BucketRegion", util.get_bucket_region())

        bucket_name = _get("bucket_name", "BucketName", util.get_bucket_name(client, bucket_region))

        mode = _get("mode", "Mode", V_LOCAL if util.is_local_mode() else V_SERVICE)

        # Ensure compile_mode is set, default to full if not provided
        compile_mode = _get("compile_mode", "CompileMode", V_FULL)

        content_type = _get("content_type", "ContentType", "application/zip")

        # Handle version_id
        version_id = _get("version_id", "VersionId", None)

        # Handle deployspec parameter
        deployspec = _get("deployspec", "DeploySpec", None)
        if deployspec is None:
            deployspec = DeploySpec(actions=[])

        return cls(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            mode=mode,
            version_id=version_id,
            content_type=content_type,
            compile_mode=compile_mode,
            deployspec=deployspec,
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
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
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
        return f"PackageDetails(client='{self.client}', bucket_name='{self.bucket_name}', " f"key='{self.key}', mode='{self.mode}')"
