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

from typing import Any, Self, Optional, Union, Dict
import os
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
import logging

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails

logger = logging.getLogger(__name__)


class StateDetails(BaseModel):
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
    temp_dir : str
        The temporary directory to use for processing state files.

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

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    client: str = Field(
        alias="Client",
        description="The client identifier for the deployment",
        default=V_EMPTY,
    )

    bucket_name: str = Field(
        alias="BucketName",
        description="The S3 bucket name or root directory path where state files are stored",
        default=V_EMPTY,
    )

    bucket_region: str = Field(
        alias="BucketRegion",
        description="The region of the S3 bucket where state files are stored (S3 mode only)",
        default=V_EMPTY,
    )

    key: str = Field(
        alias="Key",
        description="The full path to the state file relative to bucket_name",
        default=V_EMPTY,
    )

    mode: str = Field(
        alias="Mode",
        description="The storage mode: 'local' for filesystem or 'service' for S3",
        default_factory=lambda: V_LOCAL if util.is_local_mode() else V_SERVICE,
    )

    version_id: str | None = Field(
        alias="VersionId",
        description="The version ID of the state file (S3 only)",
        default=None,
    )

    content_type: str = Field(
        alias="ContentType",
        description="The MIME type of the state file",
        default="application/x-yaml",
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

            >>> state = StateDetails(mode="local")
            >>> path = state.data_path
            >>> print(path)  # /var/local/storage (example)
        """
        return util.get_storage_volume() if self.mode == V_LOCAL else V_EMPTY

    @property
    def temp_dir(self) -> str:
        """
        Get the temporary directory for processing state files.
        
        Returns the system temporary directory path from utility functions.
        
        Returns
        -------
        str
            The temporary directory path.
            
        Examples
        --------
        ::

            >>> state = StateDetails()
            >>> temp_path = state.temp_dir
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

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        """
        Validate and normalize the key path.
        
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
        - Removes leading slashes for consistency
        - Path separator normalization is handled in the model validator
          after mode is available
        """
        if not value:
            return value
        
        # Remove leading slashes for consistency
        if value.startswith("/"):
            value = value.lstrip("/")
        if value.startswith("\\"):
            value = value.lstrip("\\")
            
        return value

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        """
        Validate the content type for state files.
        
        Parameters
        ----------
        value : str
            The content type to validate.
            
        Returns
        -------
        str
            The validated content type.
            
        Notes
        -----
        Common valid content types for state files:
        - application/json
        - application/x-yaml
        - application/yaml
        - text/yaml
        """
        valid_types = [
            "application/json",
            "application/x-yaml", 
            "application/yaml",
            "text/yaml",
            "text/plain"
        ]
        
        if value not in valid_types:
            # Log warning but don't fail - allow custom content types
            pass
        
        return value

    def _normalize_key_for_mode(self, key: str, mode: str) -> str:
        """
        Normalize key path separators based on storage mode.
        
        Parameters
        ----------
        key : str
            The key path to normalize.
        mode : str
            The storage mode (V_LOCAL or V_SERVICE).
            
        Returns
        -------
        str
            The normalized key path.
            
        Notes
        -----
        - Local mode: converts to OS-appropriate separators (os.sep)
        - Service mode: converts to forward slashes for S3 compatibility
        - Handles double separator normalization
        """
        if not key:
            return key
        
        if mode == V_LOCAL:
            # Convert to OS-appropriate separators for local mode
            normalized_key = key.replace("/", os.path.sep)
            # Normalize any double separators
            while (os.path.sep + os.path.sep) in normalized_key:
                normalized_key = normalized_key.replace(os.path.sep + os.path.sep, os.path.sep)
        else:  # V_SERVICE
            # Convert to forward slashes for S3 mode
            normalized_key = key.replace(os.path.sep, "/")
            # Normalize any double slashes
            while "//" in normalized_key:
                normalized_key = normalized_key.replace("//", "/")
        
        return normalized_key

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
            - Populates missing bucket_region with util.get_artefact_bucket_region()
            - Populates missing bucket_name with util.get_artefact_bucket_name()
        """
        if isinstance(values, dict):
            # Set client if not provided
            client = values.get("Client", values.get("client", V_EMPTY))
            if not client:
                client = util.get_client()
                values["client"] = client

            # Set bucket region if not provided
            region = values.get("BucketRegion", values.get("bucket_region", V_EMPTY))
            if not region:
                region = util.get_artefact_bucket_region()
                values["bucket_region"] = region

            # Set bucket name if not provided
            if not (values.get("BucketName") or values.get("bucket_name")):
                values["bucket_name"] = util.get_artefact_bucket_name(client, region)

        return values

    @model_validator(mode="after")
    def validate_after(self) -> Self:
        """
        Validate the complete model after creation and normalize key path separators.
        
        This validator performs cross-field validation to ensure the model is in a
        consistent state and updates key path separators when mode changes.
        
        Returns
        -------
        Self
            The validated StateDetails instance.
            
        Raises
        ------
        ValueError
            If version_id is provided for local mode (not supported).
            
        Notes
        -----
        Validation Rules:
            - version_id is only valid for service mode (S3)
            - bucket_region is only needed for service mode (S3)
            - key path separators are normalized based on mode
        """
        if self.mode == V_LOCAL:
            if self.version_id:
                raise ValueError("version_id is not supported in local mode")
            if self.bucket_region and self.bucket_region != V_EMPTY:
                # Warning: bucket_region is not needed for local mode
                pass  # Allow but ignore for backward compatibility
        
        # Normalize key path separators
        if self.key:
            self.key = self._normalize_key_for_mode(self.key, self.mode)
        
        return self

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
            >>> state = StateDetails(mode="local")
            >>> state.set_key(dd, "deploy.state")
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state (Unix)
            >>> # or artefacts\ecommerce\web\main\1.0.0\deploy.state (Windows)
        """
        # Get the key from deployment details with appropriate separator for mode
        s3_mode = self.mode == V_SERVICE
        key = deployment_details.get_object_key(OBJ_ARTEFACTS, filename, s3=s3_mode)
        
        # Set the key and normalize it for the current mode
        self.key = self._normalize_key_for_mode(key, self.mode)

    def get_name(self) -> str:
        """
        Get the filename from the key path.
        
        Extracts the filename from the full key path, handling both local and S3 paths.
        
        Returns
        -------
        str
            The filename from the key path, or empty string if no key is set.
            
        Examples
        --------
        ::

            >>> state = StateDetails(key="artefacts/ecommerce/web/main/1.0.0/deploy.state")
            >>> print(state.get_name())  # deploy.state
            
            >>> state = StateDetails(key="")
            >>> print(state.get_name())  # ""
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
        Get the full path to the state file.
        
        Combines bucket_name and key to create the complete path to the state file.
        
        Returns
        -------
        str
            The full path to the state file.
            
        Examples
        --------
        S3 mode::

            >>> state = StateDetails(
            ...     bucket_name="my-bucket",
            ...     key="artefacts/ecommerce/web/deploy.state",
            ...     mode="service"
            ... )
            >>> print(state.get_full_path())  # my-bucket/artefacts/ecommerce/web/deploy.state
            
        Local mode::

            >>> state = StateDetails(
            ...     bucket_name="/var/storage",
            ...     key="artefacts/ecommerce/web/deploy.state",
            ...     mode="local"
            ... )
            >>> print(state.get_full_path())  # /var/storage/artefacts/ecommerce/web/deploy.state (Unix)
            >>> # or /var/storage\artefacts\ecommerce\web\deploy.state (Windows)
        """
        if not self.bucket_name or not self.key:
            return ""
        
        # Use appropriate separator based on mode
        separator = os.path.sep if self.mode == V_LOCAL else "/"
        
        # Ensure bucket_name doesn't end with separator to avoid double separators
        bucket_name = self.bucket_name.rstrip(separator)
        
        return f"{bucket_name}{separator}{self.key}"

    def is_local_mode(self) -> bool:
        """
        Check if the state file is in local storage mode.
        
        Returns
        -------
        bool
            True if mode is local, False if mode is service.
            
        Examples
        --------
        ::

            >>> state = StateDetails(mode="local")
            >>> print(state.is_local_mode())  # True
            
            >>> state = StateDetails(mode="service")
            >>> print(state.is_local_mode())  # False
        """
        return self.mode == V_LOCAL

    def is_service_mode(self) -> bool:
        """
        Check if the state file is in service (S3) storage mode.
        
        Returns
        -------
        bool
            True if mode is service, False if mode is local.
            
        Examples
        --------
        ::

            >>> state = StateDetails(mode="service")
            >>> print(state.is_service_mode())  # True
            
            >>> state = StateDetails(mode="local")
            >>> print(state.is_service_mode())  # False
        """
        return self.mode == V_SERVICE

    @classmethod
    def from_arguments(cls, **kwargs: Any) -> "StateDetails":
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

            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> state = StateDetails.from_arguments(
            ...     deployment_details=dd, 
            ...     task="deploy"
            ... )
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state
                
        Create with minimal arguments (auto-generates DeploymentDetails)::

            >>> state = StateDetails.from_arguments(
            ...     client="my-client",
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0",
            ...     task="deploy"
            ... )
            >>> print(state.key)  # artefacts/ecommerce/web/main/1.0.0/deploy.state
            
        Create for local mode::

            >>> state = StateDetails.from_arguments(
            ...     mode="local",
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     task="deploy"
            ... )
            >>> print(state.mode)  # local
            >>> print(state.key)  # artefacts/ecommerce/web/main/latest/deploy.state (with os.sep)
            
        Create with custom state file name::

            >>> state = StateDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     state_file="custom.state"
            ... )
            >>> print(state.get_name())  # custom.state
            
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
        
        def _normalize_empty_values(value: Any) -> str:
            """Normalize empty values to empty string."""
            if value is None or value == V_EMPTY:
                return ""
            return str(value)
        
        # Get key from various possible parameter names
        key = _normalize_empty_values(kwargs.get("key", kwargs.get("Key", "")))
        
        # Generate key from task and deployment details if not provided
        if not key:
            state_file = kwargs.get("state_file", kwargs.get("StateFile", None))
            task = kwargs.get("task", kwargs.get("Task", None))
            
            if task and state_file is None:
                state_file = f"{task}.state"
            
            dd = kwargs.get("deployment_details", kwargs.get("DeploymentDetails", None))
            
            if dd is None:
                # Try to create deployment details from kwargs
                try:
                    dd = DeploymentDetails.from_arguments(**kwargs)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not create DeploymentDetails from kwargs: {e}")
                    dd = None
            elif not isinstance(dd, DeploymentDetails):
                # Convert dict to DeploymentDetails if needed
                try:
                    if isinstance(dd, dict):
                        dd = DeploymentDetails.from_arguments(**dd)
                    else:
                        logger.warning(f"Unexpected type for deployment_details: {type(dd)}")
                        dd = None
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not convert deployment_details to DeploymentDetails: {e}")
                    dd = None
            
            if dd and state_file:
                # Determine mode first to set S3 flag correctly
                mode = kwargs.get("mode", kwargs.get("Mode", V_LOCAL if util.is_local_mode() else V_SERVICE))
                s3_mode = mode == V_SERVICE
                key = dd.get_object_key(OBJ_ARTEFACTS, state_file, s3=s3_mode)

        # Get other parameters with fallbacks
        client = _normalize_empty_values(kwargs.get("client", kwargs.get("Client", "")))
        if not client:
            client = util.get_client()
        
        bucket_region = kwargs.get(
            "bucket_region",
            kwargs.get("BucketRegion", util.get_artefact_bucket_region()),
        )
        
        bucket_name = kwargs.get("bucket_name", kwargs.get("BucketName", None))
        if not bucket_name:
            bucket_name = util.get_artefact_bucket_name(client, bucket_region)
        
        mode = kwargs.get(
            "mode", kwargs.get("Mode", V_LOCAL if util.is_local_mode() else V_SERVICE)
        )
        content_type = kwargs.get(
            "content_type", kwargs.get("ContentType", "application/x-yaml")
        )
        version_id = kwargs.get("version_id", kwargs.get("VersionId", None))

        return cls(
            client=client,
            bucket_name=bucket_name,
            bucket_region=bucket_region,
            key=key,
            mode=mode,
            version_id=version_id,
            content_type=content_type,
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
            String showing the state file name and mode.
        """
        name = self.get_name() or "state"
        return f"StateDetails({name}, mode={self.mode})"

    def __repr__(self) -> str:
        """
        Return a detailed string representation for debugging.
        
        Returns
        -------
        str
            Detailed representation showing key attributes.
        """
        return (
            f"StateDetails(client='{self.client}', bucket_name='{self.bucket_name}', "
            f"key='{self.key}', mode='{self.mode}')"
        )
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Custom setter to handle mode changes and update key path separators.
        
        Parameters
        ----------
        name : str
            The attribute name being set.
        value : Any
            The value being assigned to the attribute.
            
        Notes
        -----
        When mode is changed after instantiation, the key path separators
        are automatically updated to match the new mode.
        """
        # Call the parent setter first
        super().__setattr__(name, value)
        
        # If mode was changed, update key path separators
        if name == "mode" and hasattr(self, "key") and self.key:
            # Use the centralized normalization method
            super().__setattr__("key", self._normalize_key_for_mode(self.key, value))
