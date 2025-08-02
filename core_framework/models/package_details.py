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

from pydantic import Field, field_validator, model_validator

import core_framework as util

from .deployment_details import DeploymentDetails
from .deploy_spec import DeploySpec
from .file_details import FileDetails

from core_framework.constants import (
    V_FULL,
    V_INCREMENTAL,
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
    V_PACKAGE_ZIP,
    OBJ_PACKAGES,
)


class PackageDetails(FileDetails):
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

    Methods
    -------
    set_key(deployment_details, filename)
        Set the key path based on deployment details and filename.
    from_arguments(**kwargs)
        Create a PackageDetails instance from keyword arguments with intelligent defaults.
    get_full_path()
        Get the full path to the package file (inherited from FileDetails).
    get_name()
        Get the filename from the key path (inherited from FileDetails).
    is_local_mode()
        Check if the package is in local storage mode (inherited from FileDetails).
    is_service_mode()
        Check if the package is in service (S3) storage mode (inherited from FileDetails).
    model_dump(**kwargs)
        Override to exclude None values by default in serialization (inherited from FileDetails).

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

    Create with factory method and auto-generated key::

        >>> from core_framework.models.deployment_details import DeploymentDetails
        >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> package = PackageDetails.from_arguments(deployment_details=dd)
        >>> print(package.key)  # "packages/ecommerce/web/main/1.0.0/package.zip"

    With deployment specification::

        >>> from core_framework.models.deploy_spec import DeploySpec
        >>> from core_framework.models.action_spec import ActionSpec
        >>> action = ActionSpec(label="deploy", type="create_stack", params={"stack_name": "web"})
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

        Examples
        --------
        ::

            >>> PackageDetails.validate_compile_mode("full")
            'full'

            >>> PackageDetails.validate_compile_mode("incremental")
            'incremental'

            >>> PackageDetails.validate_compile_mode("invalid")
            ValueError: Compile mode must be 'full' or 'incremental', got 'invalid'
        """
        if value not in [V_FULL, V_INCREMENTAL, V_EMPTY]:
            raise ValueError(f"Compile mode must be '{V_FULL}' or '{V_INCREMENTAL}', got '{value}'")
        return value

    deployspec: DeploySpec | None = Field(
        ..., alias="DeploySpec", description="Deployment specification containing actions", default_factory=lambda: list()
    )

    def set_key(self, deployment_details: DeploymentDetails, filename: str) -> None:
        """
        Set the key path based on deployment details and filename.

        Generates the key path using the deployment details hierarchy and the specified filename.
        The path format will be: packages/{portfolio}/{app}/{branch}/{build}/{filename}

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
            >>> package = PackageDetails(client="test", bucket_name="test-bucket")
            >>> package.set_key(dd, "package.zip")
            >>> print(package.key)  # packages/ecommerce/web/main/1.0.0/package.zip
        """
        super().set_key(deployment_details.get_object_key(OBJ_PACKAGES, filename))

    @classmethod
    def from_arguments(cls, **kwargs) -> "PackageDetails":
        """
        Create a PackageDetails instance from keyword arguments.

        This factory method provides a flexible way to create PackageDetails instances
        by accepting various parameter combinations and applying intelligent defaults.
        It can generate package keys automatically from deployment details and supports
        both CamelCase and snake_case parameter names for compatibility.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments that can include any of the following:

            Core Parameters:
                client/Client (str): Client identifier. Defaults to util.get_client().
                key/Key (str): Package key path. If not provided, will be generated.
                package_file/PackageFile (str): Package filename. Defaults to "package.zip".
                mode/Mode (str): Storage mode ('local' or 'service').
                               Defaults to 'local' if util.is_local_mode() else 'service'.

            Storage Parameters:
                bucket_name/BucketName (str): Bucket name or root directory path.
                                            Defaults to util.get_bucket_name().
                bucket_region/BucketRegion (str): Bucket region (S3 only).
                                                Defaults to util.get_bucket_region().
                content_type/ContentType (str): MIME type. Defaults to 'application/zip'.
                version_id/VersionId (str): S3 version ID (service mode only).

            Package Parameters:
                compile_mode/CompileMode (str): Compile mode ('full' or 'incremental').
                                              Defaults to 'full'.
                deployspec/DeploySpec (DeploySpec | dict | list): Deployment specification.
                                     Can be a DeploySpec instance, dict, or list of actions.
                                     Defaults to empty DeploySpec if not provided.

            Key Generation Parameters (used when key is not provided):
                deployment_details/DeploymentDetails (DeploymentDetails | dict):
                    Deployment context for generating key path. Can be a DeploymentDetails
                    instance or dict. If not provided, will attempt to create from other kwargs.

            DeploymentDetails Parameters (used when deployment_details is not provided):
                portfolio/Portfolio (str): Portfolio name.
                app/App (str): Application name.
                build/Build (str): Build version.
                branch/Branch (str): Branch name (defaults to 'main').

        Returns
        -------
        PackageDetails
            A new PackageDetails instance with populated fields and intelligent defaults.

        Raises
        ------
        ValueError
            If required parameters are missing or invalid for key generation.

        Examples
        --------
        Create with explicit key::

            >>> package = PackageDetails.from_arguments(
            ...     client="my-client",
            ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
            ...     mode="service"
            ... )
            >>> print(package.key)  # packages/ecommerce/web/main/1.0.0/package.zip

        Create from deployment details::

            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> package = PackageDetails.from_arguments(deployment_details=dd)
            >>> print(package.key)  # packages/ecommerce/web/main/1.0.0/package.zip

        Create with minimal arguments (auto-generates DeploymentDetails)::

            >>> package = PackageDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0"
            ... )
            >>> print(package.key)  # packages/ecommerce/web/main/1.0.0/package.zip

        Create with deployment specification::

            >>> from core_framework.models.deploy_spec import DeploySpec
            >>> actions = [{"label": "deploy", "type": "create_stack", "params": {}}]
            >>> package = PackageDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0",
            ...     deployspec=actions
            ... )
            >>> print(len(package.deployspec.actions))  # 1

        Create with command line arguments::

            >>> # Assuming command_line_args contains portfolio, app, build
            >>> package = PackageDetails.from_arguments(**command_line_args)
            >>> print(package.key)  # packages/{portfolio}/{app}/main/{build}/package.zip

        Notes
        -----
        Key Generation Logic:
            1. If 'key' is provided, it's used directly
            2. If deployment_details is provided, key is generated from it + package_file
            3. If deployment_details is not provided, it's created from kwargs
            4. Final key format: packages/{portfolio}/{app}/{branch}/{build}/{package_file}

        Parameter Aliases:
            This method accepts both CamelCase and snake_case parameter names for
            compatibility (e.g., both 'bucket_name' and 'BucketName' are accepted).

        DeploySpec Handling:
            The deployspec parameter can be:
            - DeploySpec instance: used directly
            - dict: converted to DeploySpec
            - list: treated as actions list and wrapped in DeploySpec
            - None: creates empty DeploySpec with no actions
        """

        def _get(key1: str, key2: str, default: str | None, can_be_empty: bool = False) -> str:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else default

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

        bucket_name = _get(
            "bucket_name",
            "BucketName",
            util.get_bucket_name(client, bucket_region),
        )

        mode = _get("mode", "Mode", V_LOCAL if util.is_local_mode() else V_SERVICE)

        content_type = _get("content_type", "ContentType", "application/zip")

        version_id = _get("version_id", "VersionId", None)

        # Ensure compile_mode is set, default to full if not provided
        compile_mode = _get("compile_mode", "CompileMode", V_FULL)

        # Handle deployspec parameter
        deployspec = _get("deployspec", "DeploySpec", None)
        if deployspec is None:
            deployspec = DeploySpec(Actions=[])

        return cls(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            version_id=version_id,
            content_type=content_type,
            mode=mode,
            compile_mode=compile_mode,
            deployspec=deployspec,
        )

    def __str__(self) -> str:
        """
        Return a human-readable string representation.

        Returns
        -------
        str
            String showing the package filename, storage mode, and location.

        Examples
        --------
        ::

            >>> package = PackageDetails(
            ...     bucket_name="my-bucket",
            ...     key="packages/app/main/1.0.0/package.zip",
            ...     mode="service"
            ... )
            >>> str(package)
            'PackageDetails(service: my-bucket/packages/app/main/1.0.0/package.zip)'
        """
        return f"PackageDetails({self.mode}: {self.bucket_name}/{self.key})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            Detailed representation showing key attributes for debugging.

        Examples
        --------
        ::

            >>> package = PackageDetails(bucket_name="my-bucket", key="packages/app/package.zip")
            >>> repr(package)
            "PackageDetails(bucket_name='my-bucket', key='packages/app/package.zip')"
        """
        return f"PackageDetails(bucket_name='{self.bucket_name}', key='{self.key}')"
