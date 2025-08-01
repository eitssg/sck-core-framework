"""StateDetails Model Module
=========================

This module contains the StateDetails class which provides information about the current state
of the deployment, including the location of state files in either S3 or local storage.

The StateDetails class tracks state files that contain deployment execution information,
typically stored as {task}.state files in the artefacts folder structure.

Classes
-------
StateDetails : BaseModel
    Model for state file details with storage location and metadata.

Examples
--------
Creating a StateDetails for S3 storage::

    >>> state = StateDetails(
    ...     client="my-client",
    ...     bucket_name="my-deployment-bucket",
    ...     bucket_region="us-east-1",
    ...     key="artefacts/ecommerce/web-app/main/1.0.0/deploy.state",
    ...     mode="service"
    ... )

Creating a StateDetails for local storage::

    >>> state = StateDetails(
    ...     client="my-client",
    ...     bucket_name="/local/storage/root",
    ...     key="artefacts/ecommerce/web-app/main/1.0.0/deploy.state",
    ...     mode="local"
    ... )

Creating from arguments with automatic defaults::

    >>> from core_framework.models.deployment_details import DeploymentDetails
    >>> dd = DeploymentDetails(portfolio="ecommerce", app="web-app", build="1.0.0")
    >>> state = StateDetails.from_arguments(deployment_details=dd, task="deploy")
"""

from pydantic import model_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails
from .file_details import FileDetails


class StateDetails(FileDetails):
    """
    StateDetails provides information about the current state of the deployment.

    This class tracks state files that contain deployment execution information,
    typically stored as {task}.state files in the artefacts folder structure.
    The state files can be stored in either S3 or local filesystem depending on the mode.

    Attributes
    ----------
    client : str
        The client identifier for the deployment.
    bucket_name : str
        The name of the S3 bucket or root folder path where state files are stored.
        For S3 mode: bucket name (e.g., "my-deployment-bucket")
        For local mode: root directory path (e.g., "/local/storage/root")
    bucket_region : str
        The region of the S3 bucket where state files are stored (S3 mode only).
    key : str
        The full path to the state file relative to bucket_name.
        Example: "artefacts/ecommerce/web-app/main/1.0.0/deploy.state"
    mode : str
        The storage mode. Either "local" for local filesystem or "service" for S3 storage.
        Defaults to "local" if util.is_local_mode() else "service".
    version_id : str | None
        The version ID of the state file (S3 only). Used for S3 object versioning.
    content_type : str
        The MIME type of the state file. Defaults to "application/x-yaml".

    Properties
    ----------
    data_path : str
        The storage volume path for the application. Used for local mode only.
        (Inherited from FileDetails)
    temp_dir : str
        The temporary directory to use for processing state files.
        (Inherited from FileDetails)

    Methods
    -------
    set_key(deployment_details, filename)
        Set the key path based on deployment details and filename.
    from_arguments(**kwargs)
        Create a StateDetails instance from keyword arguments with intelligent defaults.
    get_full_path()
        Get the full path to the state file (inherited from FileDetails).
    get_name()
        Get the filename from the key path (inherited from FileDetails).
    is_local_mode()
        Check if the state is in local storage mode (inherited from FileDetails).
    is_service_mode()
        Check if the state is in service (S3) storage mode (inherited from FileDetails).

    Examples
    --------
    S3 storage mode::

        >>> state = StateDetails(
        ...     client="my-client",
        ...     bucket_name="deployment-bucket",
        ...     bucket_region="us-east-1",
        ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
        ...     mode="service"
        ... )

    Local storage mode::

        >>> state = StateDetails(
        ...     client="my-client",
        ...     bucket_name="/var/deployments",
        ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
        ...     mode="local"
        ... )

    Creating from task and deployment details::

        >>> from core_framework.models.deployment_details import DeploymentDetails
        >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> state = StateDetails.from_arguments(deployment_details=dd, task="deploy")
        >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state
    """

    def set_key(self, deployment_details: DeploymentDetails, filename: str) -> None:
        """
        Set the key path based on deployment details and filename.

        Generates the key path using the deployment details hierarchy and the specified filename.
        The path separators will use the OS-appropriate separator based on the current mode.

        Parameters
        ----------
        deployment_details : DeploymentDetails
            The deployment details object containing the deployment context.
        filename : str
            The filename for the state file (e.g., "deploy.state").

        Examples
        --------
        ::

            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> state = StateDetails(client="test", bucket_name="test-bucket", mode="local")
            >>> state.set_key(dd, "deploy.state")
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state (Unix)
            >>> # or artefacts\\ecommerce\\web\\main\\1.0.0\\deploy.state (Windows)
        """
        # Get the key from deployment details with appropriate separator for mode
        super().set_key(deployment_details.get_object_key(OBJ_ARTEFACTS, filename))

    @classmethod
    def from_arguments(cls, **kwargs) -> "StateDetails":
        """
        Create a StateDetails instance from keyword arguments.

        This factory method provides a flexible way to create StateDetails instances
        by accepting various parameter combinations and applying intelligent defaults.
        It can generate state file keys automatically from deployment details and task names.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments that can include any of the following:

            Core Parameters:
                client/Client (str): Client identifier. Defaults to util.get_client().
                key/Key (str): State file key path. If not provided, will be generated.
                mode/Mode (str): Storage mode ('local' or 'service').
                               Defaults to 'local' if util.is_local_mode() else 'service'.

            Storage Parameters:
                bucket_name/BucketName (str): Bucket name or root directory path.
                                            Defaults to util.get_artefact_bucket_name().
                bucket_region/BucketRegion (str): Bucket region (S3 only).
                                                Defaults to util.get_artefact_bucket_region().
                content_type/ContentType (str): MIME type. Defaults to 'application/x-yaml'.
                version_id/VersionId (str): S3 version ID (service mode only).

            Key Generation Parameters (used when key is not provided):
                state_file/StateFile (str): State filename. If not provided but task is given,
                                          defaults to '{task}.state'.
                task/Task (str): Task name used to generate state filename.
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
        StateDetails
            A new StateDetails instance with populated fields and intelligent defaults.

        Raises
        ------
        ValueError
            If required parameters are missing or invalid for the chosen mode.

        Examples
        --------
        Create with explicit key::

            >>> state = StateDetails.from_arguments(
            ...     client="my-client",
            ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
            ...     mode="service"
            ... )
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state

        Create from task and deployment details::

            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> state = StateDetails.from_arguments(
            ...     deployment_details=dd,
            ...     task="deploy"
            ... )
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state

        Create with minimal arguments (auto-generates DeploymentDetails)::

            >>> state = StateDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0",
            ...     task="deploy"
            ... )
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state

        Create with command line arguments::

            >>> # Assuming command_line_args contains portfolio, app, build, task
            >>> state = StateDetails.from_arguments(**command_line_args)
            >>> print(state.key)  # artefacts/{portfolio}/{app}/main/{build}/{task}.state

        Notes
        -----
        Key Generation Logic:
            1. If 'key' is provided, it's used directly
            2. If 'state_file' is provided, it's combined with deployment details
            3. If 'task' is provided but 'state_file' is not, state_file = f"{task}.state"
            4. DeploymentDetails are created from kwargs if not provided
            5. Final key is generated using deployment_details.get_object_key()

        Parameter Aliases:
            This method accepts both CamelCase and snake_case parameter names for
            compatibility (e.g., both 'bucket_name' and 'BucketName' are accepted).

        Default Behavior:
            - Missing parameters are populated with intelligent defaults from util functions
            - Mode defaults to local/service based on util.is_local_mode()
            - Key path separators are automatically normalized for the chosen mode
        """

        def _get(key1: str, key2: str, default: str | None, can_be_empty: bool = False) -> str:
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else default

        client = _get("client", "Client", util.get_client())

        # Get key from various possible parameter names
        key = _get("key", "Key", V_EMPTY)

        # Generate key from task and deployment details if not provided
        if not key:

            state_file = _get("state_file", "StateFile", None)

            if not state_file:
                task = _get("task", "Task", "deploy")
                state_file = f"{task}.state"

            dd = _get("deployment_details", "DeploymentDetails", None)
            if isinstance(dd, dict):
                dd = DeploymentDetails(**dd)
            elif not isinstance(dd, DeploymentDetails):
                dd = DeploymentDetails.from_arguments(**kwargs)

            if dd:
                key = dd.get_object_key(OBJ_ARTEFACTS, state_file)

        bucket_region = _get("bucket_region", "BucketRegion", util.get_artefact_bucket_region())

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
            String showing the state file name and mode.

        Examples
        --------
        ::

            >>> state = StateDetails(client="test", bucket_name="bucket", key="deploy.state")
            >>> str(state)
            'StateDetails(deploy.state, mode=local)'
        """
        return f"StateDetails({self.mode}: {self.bucket_name}/{self.key})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            Detailed representation showing key attributes.

        """
        return f"StateDetails(bucket_name='{self.bucket_name}', key='{self.key}')"
