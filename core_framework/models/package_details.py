"""PackageDetails model for Core Automation package management.

The PackageDetails class manages package artifacts (typically package.zip files) that contain
deployment templates and resources. Supports both S3 and local filesystem storage with
automatic path generation based on deployment context and compile mode tracking.

Key Features:
    - **Package artifact tracking** for deployment templates and resources
    - **Storage flexibility** with S3 and local filesystem support
    - **Automatic key generation** from deployment context and filenames
    - **Compile mode management** for full and incremental deployments
    - **DeploySpec integration** for deployment action specifications
    - **Version management** with S3 object versioning support

Storage Organization:
    Packages follow a consistent folder structure:
    **bucket_name/packages/portfolio/app/branch/build/package.zip**

Common Use Cases:
    - Deployment package storage and retrieval
    - Template versioning and distribution
    - Multi-environment deployment coordination
    - Build artifact management
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
    """Manages deployment package location, metadata, and compile configuration.

    PackageDetails tracks package artifacts containing deployment templates and resources,
    typically stored as package.zip files in a hierarchical folder structure. Supports
    both local filesystem and S3 storage with automatic path resolution and compile
    mode tracking for deployment optimization.

    The package system enables distributed deployment coordination by storing versioned
    artifacts with deployment specifications and metadata for consistent deployments
    across environments.

    Attributes:
        client: Client identifier for multi-tenant operations.
        bucket_name: S3 bucket name or local directory root path.
        bucket_region: AWS region for S3 bucket (S3 mode only).
        key: Full path to package file relative to bucket_name.
        mode: Storage mode ('local' for filesystem, 'service' for S3).
        version_id: S3 object version ID for versioned packages.
        content_type: MIME type of package file (defaults to 'application/zip').
        compile_mode: Compilation strategy ('full' or 'incremental').
        deployspec: Optional deployment specification with action definitions.

    Properties:
        data_path: Storage volume path for the application (local mode only).
        temp_dir: Temporary directory for package processing operations.

    Examples:
        >>> # S3 storage mode with full compilation
        >>> package = PackageDetails(
        ...     client="my-client",
        ...     bucket_name="deployment-bucket",
        ...     bucket_region="us-east-1",
        ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
        ...     mode="service",
        ...     compile_mode="full"
        ... )
        >>> print(package.is_service_mode())
        True

        >>> # Local storage mode with incremental compilation
        >>> package = PackageDetails(
        ...     client="my-client",
        ...     bucket_name="/var/deployments",
        ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
        ...     mode="local",
        ...     compile_mode="incremental"
        ... )
        >>> print(package.get_full_path())
        '/var/deployments/packages/ecommerce/web/main/1.0.0/package.zip'

        >>> # Automatic creation from deployment context
        >>> from core_framework.models.deployment_details import DeploymentDetails
        >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> package = PackageDetails.from_arguments(deployment_details=dd)
        >>> print(package.key)
        'packages/ecommerce/web/main/1.0.0/package.zip'

        >>> # With deployment specification
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
        >>> print(len(package.deployspec.actions))
        1

    Storage Patterns:
        Packages follow a consistent hierarchical organization:

        >>> # Different builds for same app
        >>> dd_v1 = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> dd_v2 = DeploymentDetails(portfolio="ecommerce", app="web", build="1.1.0")
        >>> pkg_v1 = PackageDetails.from_arguments(deployment_details=dd_v1)
        >>> pkg_v2 = PackageDetails.from_arguments(deployment_details=dd_v2)
        >>> print(pkg_v1.key)
        'packages/ecommerce/web/main/1.0.0/package.zip'
        >>> print(pkg_v2.key)
        'packages/ecommerce/web/main/1.1.0/package.zip'
    """

    compile_mode: str = Field(
        alias="CompileMode",
        description="Compilation strategy: 'full' for complete rebuild or 'incremental' for optimized",
        default=V_FULL,
    )

    deployspec: DeploySpec | None = Field(
        alias="DeploySpec",
        description="Deployment specification containing action definitions and metadata",
        default=None,
    )

    @field_validator("compile_mode")
    @classmethod
    def validate_compile_mode(cls, value: str) -> str:
        """Validate compile mode value against allowed options.

        Args:
            value: The compile mode to validate.

        Returns:
            The validated compile mode value.

        Raises:
            ValueError: If compile mode is not 'full' or 'incremental'.

        Examples:
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

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: dict) -> dict:
        """Validate and normalize values before model creation.

        Sets default content type for package files if not provided. Package files
        are typically ZIP archives containing deployment templates and resources.

        Args:
            values: Input values for model creation.

        Returns:
            Normalized values with default content type set.

        Examples:
            >>> values = {"client": "test", "bucket_name": "bucket"}
            >>> normalized = PackageDetails.validate_model_before(values)
            >>> print(normalized["content_type"])
            'application/zip'
        """
        if isinstance(values, dict):
            content_type = values.pop("content_type", None) or values.pop("ContentType", None)
            if not content_type:
                content_type = "application/zip"
            values["content_type"] = content_type
        return values

    def set_key(self, deployment_details: DeploymentDetails, filename: str) -> None:
        """Set the key path based on deployment details and filename.

        Generates the key path using the deployment details hierarchy and the
        specified filename. The path format follows the standard pattern:
        packages/{portfolio}/{app}/{branch}/{build}/{filename}

        Args:
            deployment_details: Deployment context containing portfolio, app, build info.
            filename: Package filename (e.g., "package.zip").

        Examples:
            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> package = PackageDetails(client="test", bucket_name="test-bucket")
            >>> package.set_key(dd, "package.zip")
            >>> print(package.key)
            'packages/ecommerce/web/main/1.0.0/package.zip'

            >>> # Different package types
            >>> package.set_key(dd, "templates.zip")
            >>> print(package.key)
            'packages/ecommerce/web/main/1.0.0/templates.zip'

        Path Generation:
            The generated path uses the deployment hierarchy:
            - **Portfolio**: Top-level organization
            - **App**: Application within portfolio
            - **Branch**: Source branch (defaults to 'main')
            - **Build**: Version or build identifier
            - **Filename**: Package file name
        """
        super().set_key(deployment_details.get_object_key(OBJ_PACKAGES, filename))

    @classmethod
    def from_arguments(cls, **kwargs) -> "PackageDetails":
        """Create PackageDetails from keyword arguments with intelligent defaults.

        Flexible factory method that accepts various parameter combinations and
        applies intelligent defaults. Can generate package keys automatically
        from deployment details and supports both CamelCase and snake_case
        parameter names for compatibility.

        Args:
            **kwargs: Keyword arguments including:
                - **Core Parameters**:
                    - client/Client (str): Client identifier
                    - key/Key (str): Package key path
                    - package_file/PackageFile (str): Package filename
                    - mode/Mode (str): Storage mode ('local' or 'service')
                - **Storage Parameters**:
                    - bucket_name/BucketName (str): Bucket name or root directory
                    - bucket_region/BucketRegion (str): S3 bucket region
                    - content_type/ContentType (str): MIME type
                    - version_id/VersionId (str): S3 version ID
                - **Package Parameters**:
                    - compile_mode/CompileMode (str): Compile mode
                    - deployspec/DeploySpec: Deployment specification
                - **Key Generation Parameters**:
                    - deployment_details/DeploymentDetails: Deployment context
                - **DeploymentDetails Parameters**:
                    - portfolio/Portfolio (str): Portfolio name
                    - app/App (str): Application name
                    - build/Build (str): Build version
                    - branch/Branch (str): Branch name

        Returns:
            PackageDetails instance with populated fields and intelligent defaults.

        Raises:
            ValueError: If required parameters are missing or invalid for key generation.

        Examples:
            >>> # Explicit key specification
            >>> package = PackageDetails.from_arguments(
            ...     client="my-client",
            ...     key="packages/ecommerce/web/main/1.0.0/package.zip",
            ...     mode="service"
            ... )
            >>> print(package.key)
            'packages/ecommerce/web/main/1.0.0/package.zip'

            >>> # Auto-generation from deployment details
            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> package = PackageDetails.from_arguments(deployment_details=dd)
            >>> print(package.key)
            'packages/ecommerce/web/main/1.0.0/package.zip'

            >>> # Minimal arguments with auto-generation
            >>> package = PackageDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0"
            ... )
            >>> print(package.key)
            'packages/ecommerce/web/main/1.0.0/package.zip'

            >>> # With deployment specification
            >>> from core_framework.models.deploy_spec import DeploySpec
            >>> actions = [{"label": "deploy", "type": "create_stack", "params": {}}]
            >>> package = PackageDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0",
            ...     deployspec=actions
            ... )
            >>> print(len(package.deployspec.actions))
            1

            >>> # Command line integration
            >>> cli_args = {
            ...     "portfolio": "ecommerce",
            ...     "app": "web",
            ...     "build": "1.0.0",
            ...     "compile_mode": "incremental",
            ...     "mode": "local"
            ... }
            >>> package = PackageDetails.from_arguments(**cli_args)

        Key Generation Logic:
            1. **Explicit key**: If 'key' parameter provided, use directly
            2. **Deployment context**: Generate from deployment_details + package_file
            3. **Auto-deployment**: Create DeploymentDetails from kwargs if not provided
            4. **Path normalization**: Apply storage-appropriate separators

        Parameter Aliases:
            Accepts both CamelCase and snake_case parameter names:
            - bucket_name/BucketName
            - bucket_region/BucketRegion
            - content_type/ContentType
            - version_id/VersionId
            - deployment_details/DeploymentDetails
            - compile_mode/CompileMode

        Default Behavior:
            - **Client**: Defaults to util.get_client()
            - **Mode**: 'local' if util.is_local_mode() else 'service'
            - **Bucket name**: util.get_bucket_name()
            - **Bucket region**: util.get_bucket_region()
            - **Content type**: 'application/zip'
            - **Package file**: 'package.zip'
            - **Compile mode**: 'full'

        DeploySpec Handling:
            The deployspec parameter accepts multiple formats:
            - **DeploySpec instance**: Used directly
            - **Dictionary**: Converted to DeploySpec
            - **List**: Treated as actions list and wrapped in DeploySpec
            - **None**: Creates empty DeploySpec with no actions
        """

        def _get(key1: str, key2: str, default: str | None, can_be_empty: bool = False) -> str:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else default

        # Get core parameters with fallbacks
        client = _get("client", "Client", util.get_client())
        package_file = _get("package_file", "PackageFile", V_PACKAGE_ZIP)
        key = _get("key", "Key", V_EMPTY)

        # Generate key from deployment details if not provided
        if not key:
            dd = _get("deployment_details", "DeploymentDetails", None)
            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails.from_arguments(**kwargs)

            if dd:
                key = dd.get_object_key(OBJ_PACKAGES, package_file)

        # Get storage parameters
        bucket_region = _get("bucket_region", "BucketRegion", util.get_bucket_region())
        bucket_name = _get(
            "bucket_name",
            "BucketName",
            util.get_bucket_name(client, bucket_region),
        )
        mode = _get("mode", "Mode", V_LOCAL if util.is_local_mode() else V_SERVICE)
        content_type = _get("content_type", "ContentType", "application/zip")
        version_id = _get("version_id", "VersionId", None)

        # Get package-specific parameters
        compile_mode = _get("compile_mode", "CompileMode", V_FULL)
        deployspec = _get("deployspec", "DeploySpec", None)

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
        """Return a human-readable string representation.

        Returns:
            String showing the storage mode and package location.

        Examples:
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
        """Return a detailed string representation for debugging.

        Returns:
            Detailed representation showing key attributes for debugging.

        Examples:
            >>> package = PackageDetails(bucket_name="my-bucket", key="packages/app/package.zip")
            >>> repr(package)
            "PackageDetails(bucket_name='my-bucket', key='packages/app/package.zip')"
        """
        return f"PackageDetails(bucket_name='{self.bucket_name}', key='{self.key}')"
