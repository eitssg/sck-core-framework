"""
ActionDetails Model Module
===========================

This module defines the ActionDetails class, which serves as a file descriptor for action files
stored in either S3 buckets or local filesystem locations. It provides a unified interface for
accessing action specification files regardless of storage backend.

Classes
-------
ActionDetails : BaseModel
    File descriptor for action files with S3 and local filesystem support

Examples
--------
Creating an ActionDetails instance for S3 storage::

    >>> details = ActionDetails(
    ...     client="my-client",
    ...     bucket_name="core-bucket",
    ...     bucket_region="us-east-1",
    ...     key="artefacts/deploy.actions"
    ... )

Creating an ActionDetails instance for local storage::

    >>> details = ActionDetails(
    ...     client="my-client",
    ...     bucket_name="/var/data/core",
    ...     key="artefacts/deploy.actions"
    ...     mode=local
    ... )

Note
----
The storage mode (S3 vs local) is determined by the application's configuration,
not by the ActionDetails instance itself.
"""

"""Defines the class ActionDetails that provide information about where ActionSpec files are stored in S3 (or local filesystem)."""

from typing import Any, Self
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails


class ActionDetails(BaseModel):
    """
    ActionDetails: The details of the action location in S3 or local filesystem.

    This class serves as a file descriptor for action files, providing a unified interface
    for accessing action specification files regardless of storage backend (S3 or local filesystem).

    Attributes
    ----------
    client : str
        The client to use for the action
    bucket_name : str
        The name of the S3 bucket where the action file is stored, or base directory path for local mode
    bucket_region : str
        The region of the S3 bucket where the action file is stored (unused in local mode)
    key : str
        The key prefix where the action file is stored in s3, or relative path for local mode. Usually in the artefacts folder
    version_id : str | None
        The version of the action file (S3 only)
    content_type : str
        The content type of the action file such as 'application/json' or 'application/x-yaml'
    mode : str
        The storage mode - either V_LOCAL for local filesystem or V_SERVICE for S3 storage

    Notes
    -----
    Storage Modes:
        - S3 Mode (V_SERVICE): Uses S3 bucket storage with bucket_name as S3 bucket name
        - Local Mode (V_LOCAL): Uses local filesystem with bucket_name as base directory path

    Examples
    --------
    Create from task name::

        >>> details = ActionDetails.from_arguments(task="deploy", client="my-client")

    Create with explicit key::

        >>> details = ActionDetails.from_arguments(key="custom/path/file.actions")

    Set key using deployment details::

        >>> details.set_key(deployment_details, "custom.actions")
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="The client to use for the action",
        default=V_EMPTY,
    )
    bucket_name: str = Field(
        alias="BucketName",
        description="The name of the S3 bucket where the action file is stored, or base directory path for local mode",
        default=V_EMPTY,
    )
    bucket_region: str = Field(
        alias="BucketRegion",
        description="The region of the S3 bucket where the action file is stored (unused in local mode)",
        default=V_EMPTY,
    )
    key: str = Field(
        alias="Key",
        description="The key prefix where the action file is stored in s3, or relative path for local mode. Usually in the artefacts folder",
        default=V_EMPTY,
    )
    version_id: str | None = Field(
        alias="VersionId",
        description="The version of the action file (S3 only)",
        default=None,
    )
    content_type: str = Field(
        alias="ContentType",
        description="The content type of the action file such as 'application/json' or 'application/x-yaml'",
        default="application/x-yaml",
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
            raise ValueError(
                f"ContentType must be one of {allowed_types}, got: {value}"
            )
        return value

    mode: str = Field(
        alias="Mode",
        description="The storage mode - either V_LOCAL for local filesystem or V_SERVICE for S3 storage",
        default=V_EMPTY,
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        """
        Validate that mode is one of the allowed values.

        Parameters
        ----------
        value : str
            The mode value to validate

        Returns
        -------
        str
            The validated mode value

        Raises
        ------
        ValueError
            If mode is not V_LOCAL or V_SERVICE
        """
        valid_modes = [V_LOCAL, V_SERVICE]
        if value not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}, got: {value}")
        return value

    @property
    def data_path(self) -> str:
        """
        Get the storage volume path for local mode.

        Returns
        -------
        str
            The base storage directory path. Only used in local mode.
            Returns empty string or current directory in S3 mode.
        """
        return util.get_storage_volume()

    @property
    def temp_dir(self) -> str:
        """
        Get the temporary directory for the application.

        Returns
        -------
        str
            Path to the temporary directory used for file operations.
        """
        return util.get_temp_dir()

    @property
    def s3_uri(self) -> str:
        """
        Generate the complete S3 URI for the action file.

        Returns
        -------
        str
            Complete S3 URI in format 's3://bucket/key' or
            's3://bucket/key?versionId=version' if version_id is present.

        Examples
        --------
        ::

            >>> details = ActionDetails(bucket_name="my-bucket", key="path/file.actions")
            >>> print(details.s3_uri)
            's3://my-bucket/path/file.actions?versionId=1234567890abcdef'
        """
        base_uri = f"s3://{self.bucket_name}/{self.key}"
        if self.version_id:
            base_uri += f"?versionId={self.version_id}"
        return base_uri

    def is_s3_mode(self) -> bool:
        """
        Check if the instance is configured for S3 storage mode.

        Returns
        -------
        bool
            True if using S3 storage (V_SERVICE), False if using local filesystem.
        """
        return self.mode == V_SERVICE

    def is_local_mode(self) -> bool:
        """
        Check if the instance is configured for local filesystem mode.

        Returns
        -------
        bool
            True if using local filesystem (V_LOCAL), False if using S3 storage.
        """
        return self.mode == V_LOCAL

    @model_validator(mode="before")
    @classmethod
    def validate_mode_before(cls, values: dict) -> dict:
        """
        Validate that the mode is consistent with other field requirements.

        This validator ensures that S3-specific fields are properly set when
        using S3 mode, and provides warnings for inconsistent configurations.
        It also sets the default bucket_name if not provided, as it depends
        on other fields (client, region) that must be resolved first.

        Parameters
        ----------
        value : dict
            The raw input values for the ActionDetails instance

        Returns
        -------
        dict
            The validated values

        Raises
        ------
        ValueError
            If mode-specific requirements are not met
        """
        if isinstance(values, dict):
            # Set default bucket_name if not provided, using resolved client and region
            client = values.get("client") or values.get("Client")
            if not client:
                client = util.get_client()
                values["client"] = client

            region = values.get("bucket_region") or values.get("BucketRegion")
            if not region:
                region = util.get_artefact_bucket_region()
                values["bucket_region"] = region

            bucket_name = values.get("bucket_name") or values.get("BucketName")
            if not bucket_name:
                bucket_name = util.get_artefact_bucket_name(client, region)
                values["bucket_name"] = bucket_name

            if not values.get("Mode") and not values.get("mode"):
                values["mode"] = V_LOCAL if util.is_local_mode() else V_SERVICE

        return values

    def set_key(self, dd: DeploymentDetails, filename: str) -> None:
        """
        Set the key based on deployment details and filename.

        This method constructs the appropriate object key by combining the
        deployment details with the specified filename in the artefacts folder.

        Parameters
        ----------
        dd : DeploymentDetails
            Deployment details instance containing the context for key generation.
        filename : str
            The name of the action file (e.g., "deploy.actions").

        Returns
        -------
        None
            This method modifies the instance's key attribute in-place.

        Examples
        --------
        ::

            >>> details = ActionDetails(client="test", bucket_name="my-bucket")
            >>> details.set_key(deployment_details, "deploy.actions")
            >>> print(details.key)  # Will be something like "client/env/deploy.actions"
        """
        self.key = dd.get_object_key(OBJ_ARTEFACTS, filename)

    @classmethod
    def from_arguments(cls, **kwargs) -> "ActionDetails":
        """
        Create ActionDetails instance from keyword arguments.

        This factory method provides a flexible way to create ActionDetails instances
        by accepting various parameter combinations and applying intelligent defaults.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments that can include:
                - key/Key (str): Direct key specification
                - task/Task (str): Task name to generate key from
                - action_file/ActionFile (str): Action file name
                - client/Client (str): Client identifier
                - bucket_name/BucketName (str): S3 bucket name or local base path
                - bucket_region/BucketRegion (str): AWS region
                - version_id/VersionId (str): S3 object version
                - content_type/ContentType (str): MIME type
                - mode/Mode (str): Storage mode (V_LOCAL or V_SERVICE)
                - deployment_details/DeploymentDetails: Deployment context

        Returns
        -------
        ActionDetails
            A new ActionDetails instance with populated fields.

        Raises
        ------
        ValueError
            If the instance cannot be created due to missing required
            parameters or other validation errors.

        Examples
        --------
        Create from task name::

            >>> details = ActionDetails.from_arguments(**command_line_args)

        """

        def _get(
            key1: str, key2: str, defualt: str | None, can_be_empty: bool = False
        ) -> str:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else defualt

        # Extract all parameters with defaults
        client = _get("client", "Client", util.get_client())

        # Handle key generation from task/action_file
        key = _get("key", "Key", None)
        if not key:
            task = _get("task", "Task", "deploy")

            action_file = _get("action_file", "ActionFile", f"{task.lower()}.actions")

            dd = _get("deployment_details", "DeploymentDetails", None)
            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails.from_arguments(**kwargs)

            dd.client = client  # Ensure client is set to the correct value
            key = dd.get_object_key(OBJ_ARTEFACTS, action_file)

        # Bucket region must be populated before bucket_name
        bucket_region = _get(
            "bucket_region", "BucketRegion", util.get_artefact_bucket_region()
        )

        # Bucket name must alos be populated before creating ActionDetails
        bucket_name = _get(
            "bucket_name",
            "BucketName",
            util.get_artefact_bucket_name(client, bucket_region),
        )

        mode = _get("mode", "Mode", V_LOCAL if util.is_local_mode() else V_SERVICE)

        content_type = _get("content_type", "ContentType", "application/x-yaml")

        version_id = _get("version_id", "VersionId", None)

        return cls(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            version_id=version_id,
            content_type=content_type,
            mode=mode,
        )

    def model_dump(self, **kwargs) -> dict:
        """
        Override to exclude None values by default.

        This method customizes the default serialization behavior to exclude
        None values unless explicitly requested.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments that are passed to the parent model_dump method.
            All standard Pydantic model_dump parameters are supported.

        Returns
        -------
        dict
            Dictionary representation of the model with None values excluded by default.

        Examples
        --------
        ::

            >>> details = ActionDetails(client="test", version_id=None)
            >>> result = details.model_dump()
            >>> # version_id will not be in the result dict
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
            String showing the storage mode and key information.
        """
        mode_str = "S3" if self.is_s3_mode() else "Local"
        return f"ActionDetails({mode_str}: {self.bucket_name}/{self.key})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            Detailed representation showing all key attributes.
        """
        return (
            f"ActionDetails(client='{self.client}', "
            f"bucket_name='{self.bucket_name}', "
            f"bucket_region='{self.bucket_region}', "
            f"key='{self.key}', "
            f"mode='{self.mode}')"
        )
