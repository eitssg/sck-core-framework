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
    """
    FileDetails is a model that contains file information within the context of the core framework.

    This base class provides common functionality for managing files in both local filesystem
    and S3 storage modes. It handles path normalization, validation, and provides utilities
    for working with file paths across different storage backends.

    Attributes
    ----------
    client : str
        The client identifier for the deployment.
    bucket_name : str
        The S3 bucket name or root directory path where files are stored.
        For S3 mode: bucket name (e.g., "my-deployment-bucket")
        For local mode: root directory path (e.g., "/local/storage/root")
    bucket_region : str
        The region of the S3 bucket where files are stored (S3 mode only).
    key : str
        The full path to the file relative to bucket_name.
        Example: "artefacts/ecommerce/web-app/main/1.0.0/deploy.state"
    mode : str
        The storage mode. Either "local" for local filesystem or "service" for S3 storage.
        Defaults to "local" if util.is_local_mode() else "service".
    version_id : str | None
        The version ID of the file (S3 only). Used for S3 object versioning.
    content_type : str | None
        The MIME type of the file. Defaults to "application/zip".

    Properties
    ----------
    data_path : str
        The storage volume path for the application.
    temp_dir : str
        The temporary directory to use for processing files.

    Methods
    -------
    set_key(key)
        Set the key path for the file with validation and normalization.
    get_name()
        Get the filename from the key path.
    get_full_path()
        Get the full path to the file including storage prefix.
    is_local_mode()
        Check if the file is in local storage mode.
    is_service_mode()
        Check if the file is in service (S3) storage mode.
    model_dump(**kwargs)
        Override to exclude None values by default in serialization.

    Class Methods
    --------------
    validate_key(value)
        Validate and normalize the key path based on storage mode.
    validate_mode(value)
        Validate that mode is either 'local' or 'service'.
    validate_content_type(value)
        Validate that content_type is a valid MIME type.
    validate_before(values)
        Validate and populate missing fields before model creation.

    Examples
    --------
    S3 storage mode::

        >>> file_details = FileDetails(
        ...     client="my-client",
        ...     bucket_name="deployment-bucket",
        ...     bucket_region="us-east-1",
        ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
        ...     mode="service"
        ... )

    Local storage mode::

        >>> file_details = FileDetails(
        ...     client="my-client",
        ...     bucket_name="/var/deployments",
        ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
        ...     mode="local"
        ... )

    Working with file paths::

        >>> file_details = FileDetails(
        ...     bucket_name="my-bucket",
        ...     key="packages/app/main/1.0.0/package.zip"
        ... )
        >>> print(file_details.get_name())  # package.zip
        >>> print(file_details.get_full_path())  # s3://my-bucket/packages/app/main/1.0.0/package.zip
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="The client identifier for the deployment",
        default=V_EMPTY,
    )

    bucket_name: str = Field(
        alias="BucketName",
        description="The S3 bucket name or root directory path where packages are stored",
        default=V_EMPTY,
    )

    bucket_region: str = Field(
        alias="BucketRegion",
        description="The region of the bucket where packages are stored (S3 mode only)",
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

        Removes leading slashes and prepares the path for normalization.
        Path separators are normalized later in the model validator since
        the mode field is not accessible during field validation.

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
        - Removes leading forward slashes and backslashes for consistency
        - Empty values are preserved and returned as-is
        - Full path separator normalization occurs in the model validator

        Examples
        --------
        ::

            >>> FileDetails.validate_key("/path/to/file.txt")
            'path/to/file.txt'

            >>> FileDetails.validate_key("\\\\path\\\\to\\\\file.txt")
            'path\\\\to\\\\file.txt'

            >>> FileDetails.validate_key("")
            ''
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
        """
        Set the key path for the file with validation and normalization.

        This method allows setting the key path after model initialization,
        ensuring it is validated and normalized according to the current storage mode.

        Parameters
        ----------
        key : str
            The new key path to set.

        Examples
        --------
        ::

            >>> file_details = FileDetails(bucket_name="test-bucket", mode="local")
            >>> file_details.set_key("packages/app/main/package.zip")
            >>> print(file_details.key)  # packages/app/main/package.zip
        """
        self.key = self.validate_key(key)

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

        Examples
        --------
        ::

            >>> FileDetails.validate_mode("local")
            'local'

            >>> FileDetails.validate_mode("service")
            'service'

            >>> FileDetails.validate_mode("invalid")
            ValueError: Mode must be 'local' or 'service', got 'invalid'
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
        Validate that content_type is a valid MIME type.

        Checks against the list of supported MIME types defined in the framework.
        Common supported types include application/zip, application/json,
        application/yaml, and text/plain.

        Parameters
        ----------
        value : str
            The content_type value to validate.

        Returns
        -------
        str
            The validated content_type value.

        Raises
        ------
        ValueError
            If content_type is not a supported MIME type.

        Examples
        --------
        ::

            >>> FileDetails.validate_content_type("application/zip")
            'application/zip'

            >>> FileDetails.validate_content_type("application/json")
            'application/json'

            >>> FileDetails.validate_content_type("invalid/type")
            ValueError: ContentType must be one of [...], got: invalid/type
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
        intelligent defaults when values are missing. It handles both CamelCase and
        snake_case parameter names for compatibility.

        Parameters
        ----------
        values : dict[str, Any]
            The input values for model creation. If not a dict, values are returned unchanged.

        Returns
        -------
        dict[str, Any]
            The validated and potentially modified values with populated defaults.

        Notes
        -----
        Default Population Logic:
            - client: populated with util.get_client() if missing
            - bucket_region: populated with util.get_bucket_region() if missing
            - bucket_name: populated with util.get_bucket_name(client, region) if missing
            - mode: populated with 'local' or 'service' based on util.is_local_mode() if missing

        Parameter Aliases:
            Accepts both CamelCase and snake_case versions of parameter names:
            - Client/client, BucketRegion/bucket_region, BucketName/bucket_name, Mode/mode

        Examples
        --------
        ::

            >>> # Minimal input with intelligent defaults
            >>> values = {"key": "packages/app/package.zip"}
            >>> result = FileDetails.validate_before(values)
            >>> # result will include populated client, bucket_region, bucket_name, mode

            >>> # Mixed case parameter names
            >>> values = {"Client": "test", "bucket_region": "us-east-1"}
            >>> result = FileDetails.validate_before(values)
            >>> # Normalizes to consistent parameter names
        """
        if isinstance(values, dict):
            # Set client if not provided
            client = values.pop("Client", None) or values.pop("client", None)
            if not client:
                client = util.get_client()
            values["client"] = client

            # Set bucket region if not provided
            region = values.pop("BucketRegion", None) or values.pop("bucket_region", None)
            if not region:
                region = util.get_bucket_region()
            values["bucket_region"] = region

            # Set bucket name if not provided
            bucket_name = values.pop("BucketName", None) or values.pop("bucket_name", None)
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
        """
        Get the storage volume path for the application.

        Returns the base storage path used by the framework for file operations.
        This path represents the mount point or prefix where files are stored.

        Returns
        -------
        str
            The storage volume path for the application.

        Examples
        --------
        ::

            >>> file_details = FileDetails(mode="local")
            >>> print(file_details.data_path)  # /var/data (or configured volume path)

            >>> file_details = FileDetails(mode="service")
            >>> print(file_details.data_path)  # s3:// (or configured service prefix)
        """
        return util.get_storage_volume()

    @property
    def temp_dir(self) -> str:
        """
        Get the temporary directory for processing files.

        Returns the temporary directory path configured in the framework,
        typically used for intermediate file processing operations.

        Returns
        -------
        str
            The temporary directory path.

        Examples
        --------
        ::

            >>> file_details = FileDetails()
            >>> print(file_details.temp_dir)  # /tmp (or configured temp directory)
        """
        return util.get_temp_dir()

    def get_name(self) -> str:
        """
        Get the filename from the key path.

        Extracts the filename from the full key path, handling both forward slashes
        and OS-specific path separators. Returns empty string if no key is set.

        Returns
        -------
        str
            The filename from the key path, or empty string if no key is set.

        Examples
        --------
        ::

            >>> file_details = FileDetails(key="artefacts/ecommerce/web/main/1.0.0/deploy.state")
            >>> print(file_details.get_name())  # deploy.state

            >>> file_details = FileDetails(key="packages\\\\app\\\\package.zip")  # Windows path
            >>> print(file_details.get_name())  # package.zip

            >>> file_details = FileDetails(key="")
            >>> print(file_details.get_name())  # ""

            >>> file_details = FileDetails(key="single-file.txt")
            >>> print(file_details.get_name())  # single-file.txt
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
        """
        Get the full path to the file including storage prefix.

        Constructs the complete path to the file by combining the storage volume,
        bucket name, and key path. The format depends on the storage mode.

        Returns
        -------
        str
            The full path to the file with appropriate storage prefix.
            Returns empty string if bucket_name or key is not set.

        Examples
        --------
        Local mode::

            >>> file_details = FileDetails(
            ...     bucket_name="my-bucket",
            ...     key="packages/app/package.zip",
            ...     mode="local"
            ... )
            >>> print(file_details.get_full_path())
            # /var/data/my-bucket/packages/app/package.zip (Unix)
            # C:\\var\\data\\my-bucket\\packages\\app\\package.zip (Windows)

        Service mode::

            >>> file_details = FileDetails(
            ...     bucket_name="my-bucket",
            ...     key="packages/app/package.zip",
            ...     mode="service"
            ... )
            >>> print(file_details.get_full_path())
            # s3://my-bucket/packages/app/package.zip

        Missing required fields::

            >>> file_details = FileDetails(bucket_name="", key="")
            >>> print(file_details.get_full_path())  # ""
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
        """
        Check if the file is in local storage mode.

        Returns
        -------
        bool
            True if mode is local, False if mode is service.

        Examples
        --------
        ::

            >>> file_details = FileDetails(mode="local")
            >>> print(file_details.is_local_mode())  # True

            >>> file_details = FileDetails(mode="service")
            >>> print(file_details.is_local_mode())  # False
        """
        return self.mode == V_LOCAL

    def is_service_mode(self) -> bool:
        """
        Check if the file is in service (S3) storage mode.

        Returns
        -------
        bool
            True if mode is service, False if mode is local.

        Examples
        --------
        ::

            >>> file_details = FileDetails(mode="service")
            >>> print(file_details.is_service_mode())  # True

            >>> file_details = FileDetails(mode="local")
            >>> print(file_details.is_service_mode())  # False
        """
        return self.mode == V_SERVICE

    def model_dump(self, **kwargs) -> dict:
        """
        Override to exclude None values by default in model serialization.

        Provides convenient defaults for model serialization by excluding None values
        and using field aliases by default, reducing clutter in serialized output.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments passed to the parent model_dump method.
            All standard Pydantic model_dump parameters are supported.

            Common parameters:
                exclude_none (bool): Exclude fields with None values. Defaults to True.
                by_alias (bool): Use field aliases in output. Defaults to True.
                include (set): Fields to include in output.
                exclude (set): Fields to exclude from output.

        Returns
        -------
        dict
            Dictionary representation of the model with None values excluded by default.

        Examples
        --------
        ::

            >>> file_details = FileDetails(
            ...     client="test",
            ...     bucket_name="bucket",
            ...     key="file.txt",
            ...     version_id=None
            ... )
            >>> result = file_details.model_dump()
            >>> # version_id is excluded because it's None
            >>> print("version_id" in result)  # False

            >>> # Include None values explicitly
            >>> result = file_details.model_dump(exclude_none=False)
            >>> print("version_id" in result)  # True

            >>> # Use original field names instead of aliases
            >>> result = file_details.model_dump(by_alias=False)
            >>> print("client" in result)  # True (vs "Client" with aliases)
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)
