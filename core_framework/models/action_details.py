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

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails as DeploymentDetailsClass


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
    mode: str = Field(
        alias="Mode",
        description="The storage mode - either V_LOCAL for local filesystem or V_SERVICE for S3 storage",
        default_factory=lambda: V_LOCAL if util.is_local_mode() else V_SERVICE,
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
            s3://my-bucket/path/file.actions
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
    def validate_artefacts_before(cls, values: Any) -> Any:
        """
        Validate and populate missing artefact-related fields before model creation.

        This validator ensures that required fields for artefact access are properly
        populated by applying intelligent defaults when values are missing. It also
        sets the mode if not explicitly provided.

        Parameters
        ----------
        values : Any
            The input values for model creation. Expected to be a dict
            for processing, but other types are passed through unchanged.

        Returns
        -------
        Any
            The validated and potentially modified values. If input was a dict,
            missing fields may be populated with defaults.

        Notes
        -----
        Side Effects:
            - Populates missing client with util.get_client()
            - Populates missing bucket_region with util.get_artefact_bucket_region()
            - Populates missing bucket_name with util.get_artefact_bucket_name()
            - Sets mode based on application configuration if not provided

        This validator only processes dict inputs. Other input types are returned
        unchanged to allow for flexible model creation patterns.
        """
        if isinstance(values, dict):
            # Set mode if not provided, based on application configuration
            if not (values.get("Mode") or values.get("mode")):
                mode = V_LOCAL if util.is_local_mode() else V_SERVICE
                values["mode"] = mode

            # Get or set client
            client = values.get("Client", values.get("client"))
            if not client:
                client = util.get_client()
                values["client"] = client

            # Get or set bucket region
            region = values.get("BucketRegion", values.get("bucket_region", None))
            if region is None:
                region = util.get_artefact_bucket_region()
                values["bucket_region"] = region

            # Get or set bucket name
            if not (values.get("BucketName") or values.get("bucket_name")):
                bucket_name = util.get_artefact_bucket_name(client, region)
                values["bucket_name"] = bucket_name

        return values

    @model_validator(mode="after")
    def validate_mode_consistency(self) -> "ActionDetails":
        """
        Validate that the mode is consistent with other field requirements.

        This validator ensures that S3-specific fields are properly set when
        using S3 mode, and provides warnings for inconsistent configurations.

        Returns
        -------
        ActionDetails
            The validated instance

        Raises
        ------
        ValueError
            If mode-specific requirements are not met
        """
        # For S3 mode, ensure bucket_region is set
        if self.is_s3_mode() and not self.bucket_region:
            raise ValueError("bucket_region is required when mode is V_SERVICE (S3)")

        # For local mode, version_id should not be used
        if self.is_local_mode() and self.version_id:
            import warnings

            warnings.warn(
                "version_id is not applicable in local mode and will be ignored",
                UserWarning,
            )

        return self

    def set_key(self, dd: DeploymentDetailsClass, filename: str) -> None:
        """
        Set the key based on deployment details and filename.

        This method constructs the appropriate object key by combining the
        deployment details with the specified filename in the artefacts folder.

        Parameters
        ----------
        dd : DeploymentDetailsClass
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

    @staticmethod
    def from_arguments(**kwargs) -> "ActionDetails":
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

            >>> details = ActionDetails.from_arguments(task="deploy", client="test")

        Create with explicit parameters::

            >>> details = ActionDetails.from_arguments(
            ...     key="custom/path/file.actions",
            ...     bucket_name="my-bucket",
            ...     bucket_region="us-east-1",
            ...     mode=V_SERVICE
            ... )

        Create from deployment details::

            >>> details = ActionDetails.from_arguments(
            ...     deployment_details=dd,
            ...     action_file="custom.actions"
            ... )
        """
        try:
            # Handle key generation from task/action_file
            key = kwargs.get("key", kwargs.get("Key", V_EMPTY))
            if not key:
                task = kwargs.get("task", kwargs.get("Task", None))
                action_file = kwargs.get("action_file", kwargs.get("ActionFile", None))
                if task and not action_file:
                    action_file = f"{task.lower()}.actions"
                dd = kwargs.get(
                    "deployment_details", kwargs.get("DeploymentDetails", kwargs)
                )
                if not isinstance(dd, DeploymentDetailsClass):
                    dd = DeploymentDetailsClass.from_arguments(**kwargs)
                if dd and action_file:
                    key = dd.get_object_key(OBJ_ARTEFACTS, action_file)

            # Extract all parameters with defaults
            client = kwargs.get("client", kwargs.get("Client", util.get_client()))
            bucket_region = kwargs.get(
                "bucket_region",
                kwargs.get("BucketRegion", util.get_artefact_bucket_region()),
            )
            bucket_name = kwargs.get(
                "bucket_name",
                kwargs.get(
                    "BucketName", util.get_artefact_bucket_name(client, bucket_region)
                ),
            )
            version_id = kwargs.get("version_id", kwargs.get("VersionId", None))
            content_type = kwargs.get(
                "content_type", kwargs.get("ContentType", "application/x-yaml")
            )
            # Allow mode to be explicitly set, otherwise use default factory
            mode = kwargs.get("mode", kwargs.get("Mode", None))

            # Create the instance
            instance_kwargs = {
                "client": client,
                "bucket_name": bucket_name,
                "bucket_region": bucket_region,
                "key": key,
                "version_id": version_id,
                "content_type": content_type,
            }

            # Only add mode if explicitly provided, otherwise let default factory handle it
            if mode is not None:
                instance_kwargs["mode"] = mode

            return ActionDetails(**instance_kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create ActionDetails from arguments: {e}")

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
