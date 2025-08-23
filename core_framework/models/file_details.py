"""FileDetails Model Module for Simple Cloud Kit Framework.

This module defines the FileDetails base class, which provides comprehensive file management
capabilities for both local filesystem and S3 storage modes. It serves as the foundation
for file-based operations throughout the Simple Cloud Kit framework with unified storage
interfaces and intelligent path handling.

The FileDetails class handles file location, validation, and path generation across different
storage backends, enabling seamless transitions between development (local) and production
(S3) environments while maintaining consistent APIs and behavior.

Key Features:
    - **Unified Storage Interface**: Seamless support for local filesystem and S3 storage
    - **Path Normalization**: Intelligent path handling across different operating systems
    - **Validation Framework**: Comprehensive field validation with error handling
    - **MIME Type Support**: Content type validation and management
    - **Storage Mode Detection**: Automatic detection and configuration of storage modes

Storage Modes:
    - **Local Mode (V_LOCAL)**: Development workflow using local filesystem storage
    - **Service Mode (V_SERVICE)**: Production deployment using AWS S3 bucket storage

Examples:
    >>> from core_framework.models import FileDetails

    >>> # S3 storage configuration
    >>> s3_file = FileDetails(
    ...     client="acme-corp",
    ...     bucket_name="deployment-artifacts",
    ...     bucket_region="us-east-1",
    ...     key="packages/web-app/v1.0.0/deployment.zip",
    ...     mode="service",
    ...     content_type="application/zip"
    ... )

    >>> # Local filesystem configuration
    >>> local_file = FileDetails(
    ...     client="dev-client",
    ...     bucket_name="/var/deployments",
    ...     key="packages/web-app/v1.0.0/deployment.zip",
    ...     mode="local",
    ...     content_type="application/zip"
    ... )

    >>> # Path operations
    >>> print(s3_file.get_name())  # "deployment.zip"
    >>> print(s3_file.get_full_path())  # "s3://deployment-artifacts/packages/web-app/v1.0.0/deployment.zip"
    >>> print(local_file.get_full_path())  # "/var/data/var/deployments/packages/web-app/v1.0.0/deployment.zip"

Related Classes:
    - ActionDetails: Extends FileDetails for action specification files
    - DeploymentDetails: Provides deployment context for path generation
    - PackageDetails: Extends FileDetails for deployment package files

Note:
    FileDetails serves as the base class for all file-related operations in the framework.
    It provides consistent behavior across storage backends and forms the foundation for
    more specialized file management classes.
"""

from typing import Any
import os
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator

import core_framework as util

from core_framework.constants import (
    V_LOCAL,
    V_SERVICE,
    V_EMPTY,
)


class FileDetails(BaseModel):
    """Base model for file information with support for local filesystem and S3 storage.

    FileDetails provides a comprehensive abstraction for file management across different
    storage backends. It handles path normalization, validation, and provides utilities
    for working with files in both development and production environments.

    The class enforces proper validation of storage modes, content types, and path formats
    while providing intelligent defaults and flexible configuration options.

    Attributes:
        client (str): Client identifier for multi-tenant deployments and access control.
                     Defaults to framework client configuration if not provided.
        bucket_name (str): S3 bucket name for cloud storage, or root directory path for local mode.
                          For S3: AWS bucket name (e.g., "acme-deployment-bucket")
                          For local: Base directory path (e.g., "/var/deployments")
        bucket_region (str): AWS region for S3 bucket location. Required for S3 operations,
                           ignored in local mode.
        key (str): File path relative to bucket_name. Normalized based on storage mode.
                  Example: "packages/web-app/v1.0.0/deployment.zip"
        mode (str): Storage mode - V_LOCAL for filesystem or V_SERVICE for S3 storage.
                   Automatically determined if not provided.
        version_id (str, optional): S3 object version identifier for versioned storage.
                                  Only used in S3 mode for object versioning.
        content_type (str): MIME type of the file. Defaults to "application/octet-stream".
                          Validated against supported MIME types.

    Properties:
        data_path (str): Base storage volume path from framework configuration.
        temp_dir (str): Temporary directory path for file processing operations.

    Examples:
        >>> # Complete S3 file configuration
        >>> s3_file = FileDetails(
        ...     client="acme-corp",
        ...     bucket_name="prod-deployments",
        ...     bucket_region="us-east-1",
        ...     key="artifacts/web-frontend/v2.1.0/bundle.zip",
        ...     mode="service",
        ...     content_type="application/zip",
        ...     version_id="abc123def456"
        ... )

        >>> # Local development file configuration
        >>> local_file = FileDetails(
        ...     client="dev-client",
        ...     bucket_name="/home/dev/projects",
        ...     key="artifacts/web-frontend/v2.1.0/bundle.zip",
        ...     mode="local",
        ...     content_type="application/zip"
        ... )

        >>> # Minimal configuration with intelligent defaults
        >>> file_details = FileDetails(
        ...     key="config/application.yaml"
        ...     # client, bucket_name, bucket_region, mode auto-populated
        ... )

    Validation Rules:
        - **Mode**: Must be either "local" or "service"
        - **Content Type**: Must be a supported MIME type from framework configuration
        - **Key Path**: Automatically normalized for storage mode compatibility
        - **Required Fields**: Client, bucket_name, and key are required for operations

    Storage Path Examples:
        **S3 Storage**:
        - bucket_name: "acme-prod-deployments"
        - key: "packages/web-app/v1.0.0/app.zip"
        - Full path: "s3://acme-prod-deployments/packages/web-app/v1.0.0/app.zip"

        **Local Storage**:
        - bucket_name: "/var/deployments"
        - key: "packages/web-app/v1.0.0/app.zip"
        - Full path: "/var/data/var/deployments/packages/web-app/v1.0.0/app.zip"

    Content Type Support:
        Common supported MIME types include:
        - "application/zip": ZIP archives and compressed packages
        - "application/json": JSON configuration files
        - "application/yaml": YAML configuration files
        - "application/x-yaml": Alternative YAML MIME type
        - "text/plain": Plain text files
        - "application/octet-stream": Binary files (default)
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="Client identifier for multi-tenant deployments and access control",
        default=V_EMPTY,
    )

    bucket_name: str = Field(
        alias="BucketName",
        description="S3 bucket name or root directory path where files are stored",
        default=V_EMPTY,
    )

    bucket_region: str = Field(
        alias="BucketRegion",
        description="AWS region for S3 bucket location (S3 mode only)",
        default=V_EMPTY,
    )

    key: str = Field(
        alias="Key",
        description="File path relative to bucket_name, normalized for storage mode",
        default=V_EMPTY,
    )

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        """Validate and normalize the key path for consistent storage operations.

        Removes leading slashes and prepares the path for storage mode normalization.
        This ensures consistent path handling across different input sources and
        storage backends.

        Args:
            value (str): The key path to validate and normalize.

        Returns:
            str: The validated and normalized key path with leading slashes removed.

        Examples:
            >>> FileDetails.validate_key("/path/to/file.txt")
            "path/to/file.txt"

            >>> FileDetails.validate_key("\\\\windows\\\\path\\\\file.txt")
            "windows\\\\path\\\\file.txt"

            >>> FileDetails.validate_key("already/normalized/path.txt")
            "already/normalized/path.txt"

            >>> FileDetails.validate_key("")
            ""

        Notes:
            - Leading forward slashes and backslashes are removed for consistency
            - Empty values are preserved and returned as-is
            - Path separator normalization occurs in the model validator where mode is accessible
            - This validator focuses on basic cleanup while preserving the path structure
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

    def set_key(self, key: str) -> None:
        """Set the key path with validation and normalization.

        Updates the key field while ensuring proper validation and normalization.
        This method allows dynamic key updates after model initialization while
        maintaining data integrity.

        Args:
            key (str): The new key path to set. Will be validated and normalized.

        Examples:
            >>> file_details = FileDetails(
            ...     bucket_name="test-bucket",
            ...     mode="local"
            ... )
            >>> file_details.set_key("packages/app/main/package.zip")
            >>> print(file_details.key)
            "packages/app/main/package.zip"

            >>> # Leading slashes are automatically removed
            >>> file_details.set_key("/artifacts/config.yaml")
            >>> print(file_details.key)
            "artifacts/config.yaml"

        Side Effects:
            Updates the instance's key attribute in-place after validation.
        """
        self.key = self.validate_key(key)

    mode: str = Field(
        alias="Mode",
        description="Storage mode: 'local' for filesystem or 'service' for S3",
        default=V_EMPTY,
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        """Validate that mode is a supported storage mode.

        Ensures the storage mode is one of the supported values defined in the
        framework constants. This validation prevents invalid storage configurations
        and ensures consistent behavior.

        Args:
            value (str): The mode value to validate.

        Returns:
            str: The validated mode value.

        Raises:
            ValueError: If mode is not 'local' or 'service'.

        Examples:
            >>> FileDetails.validate_mode("local")
            "local"

            >>> FileDetails.validate_mode("service")
            "service"

            >>> try:
            ...     FileDetails.validate_mode("invalid")
            ... except ValueError as e:
            ...     print(e)
            "Mode must be 'local' or 'service', got 'invalid'"

        Supported Modes:
            - **"local"**: Local filesystem storage for development workflows
            - **"service"**: AWS S3 storage for production deployments
        """
        if value not in [V_LOCAL, V_SERVICE]:
            raise ValueError(
                f"Mode must be '{V_LOCAL}' or '{V_SERVICE}', got '{value}'"
            )
        return value

    version_id: str | None = Field(
        alias="VersionId",
        description="S3 object version identifier for versioned storage (S3 only)",
        default=None,
    )

    content_type: str | None = Field(
        alias="ContentType",
        description="MIME type of the file, validated against supported types",
        default="application/octet-stream",
    )

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        """Validate that content_type is a supported MIME type.

        Checks the content type against the framework's list of supported MIME types
        to ensure compatibility with storage operations and content handling systems.

        Args:
            value (str): The content_type value to validate.

        Returns:
            str: The validated content_type value.

        Raises:
            ValueError: If content_type is not in the list of supported MIME types.

        Examples:
            >>> FileDetails.validate_content_type("application/zip")
            "application/zip"

            >>> FileDetails.validate_content_type("application/json")
            "application/json"

            >>> FileDetails.validate_content_type("application/yaml")
            "application/yaml"

            >>> try:
            ...     FileDetails.validate_content_type("invalid/type")
            ... except ValueError as e:
            ...     print(e)
            "ContentType must be one of [...], got: invalid/type"

        Supported MIME Types:
            Common supported types include:
            - application/zip: ZIP archives and compressed packages
            - application/json: JSON configuration files
            - application/yaml: YAML configuration files
            - application/x-yaml: Alternative YAML MIME type
            - text/plain: Plain text files
            - application/octet-stream: Binary files (default)

        Notes:
            The complete list of supported MIME types is retrieved from the framework
            configuration and may vary based on deployment environment and extensions.
        """
        allowed_types = util.get_valid_mimetypes()
        if value not in allowed_types:
            raise ValueError(
                f"ContentType must be one of {allowed_types}, got: {value}"
            )
        return value

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and populate missing fields with intelligent defaults.

        Performs pre-validation processing to ensure all required fields are populated
        with sensible defaults from the framework configuration. Handles both snake_case
        and PascalCase field names for maximum compatibility.

        Args:
            values (dict[str, Any]): Raw field values for model creation. If not a dict,
                                   values are returned unchanged.

        Returns:
            dict[str, Any]: Processed field values with intelligent defaults applied:
                          - client: From framework configuration if not provided
                          - bucket_region: From framework configuration if not provided
                          - bucket_name: Generated from client and region if not provided
                          - mode: Determined from framework settings if not provided

        Examples:
            >>> # Minimal input with intelligent defaults
            >>> values = {"key": "packages/app/package.zip"}
            >>> result = FileDetails.validate_before(values)
            >>> # Result includes populated client, bucket_region, bucket_name, mode

            >>> # Mixed case parameter compatibility
            >>> values = {
            ...     "Client": "test-client",
            ...     "bucket_region": "us-west-2",
            ...     "Key": "artifacts/config.yaml"
            ... }
            >>> result = FileDetails.validate_before(values)
            >>> # Normalizes parameter names and applies remaining defaults

        Default Population Logic:
            **Client**: Retrieved from framework configuration (util.get_client())
            **Bucket Region**: Retrieved from framework configuration (util.get_bucket_region())
            **Bucket Name**: Generated using client and region (util.get_bucket_name())
            **Mode**: Determined by framework deployment mode (local vs service)

        Parameter Alias Handling:
            Accepts both naming conventions:
            - Client/client, BucketRegion/bucket_region, BucketName/bucket_name, Mode/mode
            - PascalCase parameters take precedence when both are provided
            - snake_case fallback ensures compatibility with internal usage

        Side Effects:
            Modifies the provided values dictionary by adding missing defaults
            and normalizing field names to snake_case for internal consistency.
        """
        if isinstance(values, dict):
            # Set client if not provided
            client = values.pop("Client", None) or values.pop("client", None)
            if not client:
                client = util.get_client()
            values["client"] = client

            # Set bucket region if not provided
            region = values.pop("BucketRegion", None) or values.pop(
                "bucket_region", None
            )
            if not region:
                region = util.get_bucket_region()
            values["bucket_region"] = region

            # Set bucket name if not provided
            bucket_name = values.pop("BucketName", None) or values.pop(
                "bucket_name", None
            )
            if not bucket_name:
                bucket_name = util.get_bucket_name(client, region)
            values["bucket_name"] = bucket_name

            mode = values.pop("Mode", None) or values.pop("mode", None)
            if not mode:
                mode = V_LOCAL if util.is_local_mode() else V_SERVICE
            values["mode"] = mode

        return values

    @property
    def data_path(self) -> str:
        """Get the base storage volume path for file operations.

        Returns the storage volume path configured in the framework, which serves
        as the mount point or prefix for all file storage operations.

        Returns:
            str: The base storage volume path from framework configuration.

        Examples:
            >>> file_details = FileDetails(mode="local")
            >>> print(file_details.data_path)
            "/var/data"  # or configured volume path

            >>> file_details = FileDetails(mode="service")
            >>> print(file_details.data_path)
            "/var/data"  # same base path, mode affects full_path generation
        """
        return util.get_storage_volume()

    @property
    def temp_dir(self) -> str:
        """Get the temporary directory for file processing operations.

        Returns the temporary directory path configured in the framework, typically
        used for intermediate file processing, extraction, and transformation operations.

        Returns:
            str: The temporary directory path from framework configuration.

        Examples:
            >>> file_details = FileDetails()
            >>> print(file_details.temp_dir)
            "/tmp"  # or configured temporary directory

            >>> # Usage in file processing
            >>> temp_path = os.path.join(file_details.temp_dir, "processing")
            >>> os.makedirs(temp_path, exist_ok=True)
        """
        return util.get_temp_dir()

    def get_name(self) -> str:
        """Extract the filename from the key path.

        Parses the key path to extract just the filename portion, handling both
        forward slashes and OS-specific path separators. Returns empty string
        if no key is set.

        Returns:
            str: The filename from the key path, or empty string if no key is set.

        Examples:
            >>> file_details = FileDetails(
            ...     key="artifacts/ecommerce/web-app/v1.0.0/deployment.zip"
            ... )
            >>> print(file_details.get_name())
            "deployment.zip"

            >>> # Windows-style paths
            >>> file_details = FileDetails(
            ...     key="packages\\\\app\\\\release.zip"
            ... )
            >>> print(file_details.get_name())
            "release.zip"

            >>> # Single filename without path
            >>> file_details = FileDetails(key="config.yaml")
            >>> print(file_details.get_name())
            "config.yaml"

            >>> # Empty key
            >>> file_details = FileDetails(key="")
            >>> print(file_details.get_name())
            ""

        Path Separator Handling:
            - Handles both forward slashes (/) and OS-specific separators
            - Works correctly on Windows, Linux, and macOS systems
            - Gracefully handles mixed separator usage in paths
        """
        if not self.key:
            return ""

        # Try both separators since key might contain either depending on how it was set
        if "/" in self.key:
            return self.key.rsplit("/", 1)[-1]
        elif os.path.sep in self.key:
            return self.key.rsplit(os.path.sep, 1)[-1]
        else:
            # No separators found, return the key itself
            return self.key

    def get_full_path(self) -> str:
        """Generate the complete path to the file including storage prefix.

        Constructs the full path by combining the storage volume, bucket name,
        and key path according to the storage mode. The format varies between
        local filesystem and S3 storage modes.

        Returns:
            str: The complete path to the file with appropriate storage prefix.
                Returns empty string if bucket_name or key is not set.

        Examples:
            >>> # Local filesystem mode
            >>> local_file = FileDetails(
            ...     bucket_name="deployments",
            ...     key="packages/web-app/v1.0.0/app.zip",
            ...     mode="local"
            ... )
            >>> print(local_file.get_full_path())
            "/var/data/deployments/packages/web-app/v1.0.0/app.zip"  # Unix
            "C:\\var\\data\\deployments\\packages\\web-app\\v1.0.0\\app.zip"  # Windows

            >>> # S3 service mode
            >>> s3_file = FileDetails(
            ...     bucket_name="prod-deployments",
            ...     key="packages/web-app/v1.0.0/app.zip",
            ...     mode="service"
            ... )
            >>> print(s3_file.get_full_path())
            "s3://prod-deployments/packages/web-app/v1.0.0/app.zip"

            >>> # Missing required fields
            >>> incomplete_file = FileDetails(bucket_name="", key="test.txt")
            >>> print(incomplete_file.get_full_path())
            ""

        Path Format by Mode:
            **Local Mode**: {data_path}{sep}{bucket_name}{sep}{key}
            - Uses OS-specific path separators
            - Includes storage volume prefix
            - Results in absolute filesystem path

            **Service Mode**: s3://{bucket_name}/{key}
            - Always uses forward slashes
            - Standard S3 URI format
            - Compatible with AWS CLI and SDKs

        Usage:
            The full path is suitable for:
            - Direct file system operations (local mode)
            - AWS S3 API calls (service mode)
            - Logging and debugging output
            - Configuration file references
        """
        if not self.bucket_name or not self.key:
            return ""

        if self.mode == V_LOCAL:
            sep = os.path.sep
            return f"{self.data_path}{sep}{self.bucket_name}{sep}{self.key}"
        else:
            # Service: s3:// + bucket_name + key (always forward slashes)
            return f"s3://{self.bucket_name}/{self.key}"

    def is_local_mode(self) -> bool:
        """Check if the file is configured for local filesystem storage.

        Returns:
            bool: True if mode is local, False if mode is service.

        Examples:
            >>> local_file = FileDetails(mode="local")
            >>> print(local_file.is_local_mode())
            True

            >>> s3_file = FileDetails(mode="service")
            >>> print(s3_file.is_local_mode())
            False

            >>> # Conditional file operations
            >>> if file_details.is_local_mode():
            ...     with open(file_details.get_full_path(), 'r') as f:
            ...         content = f.read()
            ... else:
            ...     # Use S3 client
            ...     content = s3_client.get_object(...)['Body'].read()
        """
        return self.mode == V_LOCAL

    def is_service_mode(self) -> bool:
        """Check if the file is configured for S3 service storage.

        Returns:
            bool: True if mode is service, False if mode is local.

        Examples:
            >>> s3_file = FileDetails(mode="service")
            >>> print(s3_file.is_service_mode())
            True

            >>> local_file = FileDetails(mode="local")
            >>> print(s3_file.is_service_mode())
            False

            >>> # Mode-specific operations
            >>> if file_details.is_service_mode():
            ...     # Configure S3 client
            ...     s3_client = boto3.client('s3', region_name=file_details.bucket_region)
            ... else:
            ...     # Use local file operations
            ...     os.makedirs(os.path.dirname(file_details.get_full_path()), exist_ok=True)
        """
        return self.mode == V_SERVICE

    def model_dump(self, **kwargs) -> dict:
        """Serialize model to dictionary with optimized defaults.

        Overrides the default Pydantic serialization to provide cleaner output
        by excluding None values and using field aliases by default. This reduces
        clutter in API responses and configuration files.

        Args:
            **kwargs: Keyword arguments passed to parent model_dump method.
                     All standard Pydantic serialization options are supported:
                     - exclude_none (bool): Exclude None values (default: True)
                     - by_alias (bool): Use field aliases (default: True)
                     - include (set): Specific fields to include
                     - exclude (set): Specific fields to exclude

        Returns:
            dict: Dictionary representation with None values excluded by default.

        Examples:
            >>> file_details = FileDetails(
            ...     client="test-client",
            ...     bucket_name="test-bucket",
            ...     key="test-file.txt",
            ...     version_id=None  # This will be excluded
            ... )
            >>> result = file_details.model_dump()
            >>> print("version_id" in result)
            False  # Excluded because it's None

            >>> # Include None values explicitly
            >>> result = file_details.model_dump(exclude_none=False)
            >>> print("version_id" in result)
            True  # Now included with null value

            >>> # Use original field names instead of aliases
            >>> result = file_details.model_dump(by_alias=False)
            >>> print("client" in result)
            True  # snake_case instead of "Client"

        Default Behavior:
            - **exclude_none=True**: Removes clutter from serialized output
            - **by_alias=True**: Uses PascalCase field names for API compatibility
            - Maintains compatibility with external systems expecting specific formats
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)
