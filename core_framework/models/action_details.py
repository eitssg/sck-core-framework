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

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails
from .file_details import FileDetails


class ActionDetails(FileDetails):
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

        def _get(key1: str, key2: str, defualt: str | None, can_be_empty: bool = False) -> str:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else defualt

        # Extract all parameters with defaults
        client = _get("client", "Client", util.get_client())

        # Handle key generation from task/action_file
        key = _get("key", "Key", None)

        if not key:

            action_file = _get("action_file", "ActionFile", None)

            if not action_file:
                task = _get("task", "Task", "deploy")
                action_file = f"{task}.actions"

            dd = _get("deployment_details", "DeploymentDetails", None)
            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails.from_arguments(**kwargs)

            dd.client = client  # Ensure client is set to the correct value
            key = dd.get_object_key(OBJ_ARTEFACTS, action_file)

        # Bucket region must be populated before bucket_name
        bucket_region = _get("bucket_region", "BucketRegion", util.get_artefact_bucket_region())

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

    def __str__(self) -> str:
        """
        Return a human-readable string representation.

        Returns
        -------
        str
            String showing the storage mode and key information.
        """
        return f"ActionDetails({self.mode}: {self.bucket_name}/{self.key})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            Detailed representation showing all key attributes.
        """
        return f"ActionDetails(bucket_name='{self.bucket_name}', key='{self.key}')"
