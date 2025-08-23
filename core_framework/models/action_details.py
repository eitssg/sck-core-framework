"""ActionDetails Model Module for Simple Cloud Kit Framework.

This module defines the ActionDetails class, which serves as a file descriptor for action files
stored in either S3 buckets or local filesystem locations. It provides a unified interface for
accessing action specification files regardless of storage backend, enabling flexible deployment
automation across different environments.

The ActionDetails class extends FileDetails to provide specialized functionality for action files,
including intelligent key generation, deployment context integration, and support for both
cloud and local development workflows.

Key Features:
    - **Unified Storage Interface**: Seamless support for S3 and local filesystem storage
    - **Intelligent Key Generation**: Automatic key construction from deployment context
    - **Flexible Factory Methods**: Multiple ways to create instances from various parameter sources
    - **Deployment Integration**: Native integration with deployment details and contexts
    - **Content Type Detection**: Automatic MIME type handling for YAML and JSON action files

Storage Modes:
    - **S3 Mode (V_SERVICE)**: Production deployment using AWS S3 bucket storage
    - **Local Mode (V_LOCAL)**: Development workflow using local filesystem storage

Examples:
    >>> from core_framework.models import ActionDetails, DeploymentDetails

    >>> # Create from task name (most common pattern)
    >>> details = ActionDetails.from_arguments(
    ...     task="deploy",
    ...     client="acme",
    ...     bucket_name="acme-deployments",
    ...     bucket_region="us-east-1"
    ... )
    >>> print(details.key)  # "acme/artefacts/deploy.actions"

    >>> # Create with explicit key
    >>> details = ActionDetails.from_arguments(
    ...     client="acme",
    ...     key="custom/deployment/special.actions",
    ...     bucket_name="acme-deployments"
    ... )

    >>> # Create for local development
    >>> details = ActionDetails.from_arguments(
    ...     task="test",
    ...     client="dev-client",
    ...     bucket_name="/var/local/deployments",
    ...     mode="local"
    ... )

    >>> # Set key from deployment context
    >>> deployment_details = DeploymentDetails(client="acme", environment="prod")
    >>> details = ActionDetails(client="acme", bucket_name="acme-bucket")
    >>> details.set_key(deployment_details, "rollback.actions")

Related Classes:
    - FileDetails: Base class providing common file descriptor functionality
    - DeploymentDetails: Deployment context for key generation and environment configuration
    - ActionSpec: Action specification content loaded from ActionDetails locations

Note:
    The storage mode (S3 vs local) is typically determined by the application's configuration
    and environment settings, not by the ActionDetails instance itself. Use the mode parameter
    to override default behavior when needed.
"""

from pydantic import model_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails
from .file_details import FileDetails


class ActionDetails(FileDetails):
    """File descriptor for action specification files with S3 and local filesystem support.

    ActionDetails serves as a comprehensive file descriptor for action files, providing a unified
    interface for accessing action specification files regardless of storage backend. It extends
    FileDetails with specialized functionality for deployment automation workflows.

    The class handles both S3 bucket storage for production deployments and local filesystem
    storage for development workflows, with intelligent key generation and deployment context
    integration.

    Attributes:
        client (str): Client identifier for multi-tenant deployments and access control.
        bucket_name (str): S3 bucket name for cloud storage, or base directory path for local mode.
        bucket_region (str): AWS region for S3 bucket location (unused in local mode).
        key (str): S3 object key or relative file path for the action specification file.
        version_id (str, optional): S3 object version identifier for versioned deployments.
        content_type (str): MIME type such as 'application/yaml' or 'application/json'.
        mode (str): Storage mode - V_LOCAL for filesystem or V_SERVICE for S3 storage.

    Examples:
        >>> # Basic S3 action details
        >>> details = ActionDetails(
        ...     client="acme",
        ...     bucket_name="acme-deployments",
        ...     bucket_region="us-east-1",
        ...     key="artefacts/deploy.actions",
        ...     content_type="application/yaml"
        ... )

        >>> # Local filesystem action details
        >>> details = ActionDetails(
        ...     client="dev-client",
        ...     bucket_name="/var/deployments",
        ...     key="artefacts/test.actions",
        ...     mode="local"
        ... )

        >>> # Check storage mode and construct paths
        >>> if details.mode == "service":
        ...     s3_url = f"s3://{details.bucket_name}/{details.key}"
        ... else:
        ...     local_path = f"{details.bucket_name}/{details.key}"

    Storage Patterns:
        **S3 Storage (Production)**:
        - bucket_name: AWS S3 bucket name (e.g., "acme-prod-deployments")
        - bucket_region: AWS region (e.g., "us-east-1")
        - key: Object key path (e.g., "client/env/artefacts/deploy.actions")
        - mode: "service"

        **Local Storage (Development)**:
        - bucket_name: Base directory path (e.g., "/var/local/deployments")
        - bucket_region: Ignored in local mode
        - key: Relative file path (e.g., "client/env/artefacts/test.actions")
        - mode: "local"

    Key Generation:
        Action file keys follow a hierarchical pattern:
        ```
        {client}/{environment}/artefacts/{action_file}
        ```

        Example keys:
        - "acme/production/artefacts/deploy.actions"
        - "testcorp/staging/artefacts/rollback.actions"
        - "dev-client/local/artefacts/test.actions"

    Content Types:
        Supported MIME types for action specification files:
        - "application/yaml": YAML format action specifications
        - "application/json": JSON format action specifications
        - "application/x-yaml": Alternative YAML MIME type
        - "text/yaml": Text-based YAML format
    """

    @model_validator(mode="before")
    def validate_model_before(cls, values: dict) -> dict:
        """Validate and normalize model values before instance creation.

        Performs pre-validation processing to normalize content type values from various
        sources and apply default values where needed. Handles both direct field names
        and capitalized variants commonly found in AWS responses.

        Args:
            values (dict): Raw field values for model creation, which may include:
                          - content_type or ContentType: MIME type specification
                          - Other ActionDetails fields in various formats

        Returns:
            dict: Processed and normalized field values with:
                 - content_type: Normalized MIME type (defaults to "application/yaml")
                 - All other fields preserved and normalized

        Examples:
            >>> # Called automatically during instance creation
            >>> details = ActionDetails(
            ...     client="test",
            ...     bucket_name="test-bucket",
            ...     ContentType="application/json"  # Gets normalized to content_type
            ... )
            >>> print(details.content_type)  # "application/json"

            >>> # Default content type applied
            >>> details = ActionDetails(
            ...     client="test",
            ...     bucket_name="test-bucket"
            ... )
            >>> print(details.content_type)  # "application/yaml"

        Note:
            This validator runs before field validation and handles the common pattern
            of AWS services returning capitalized field names that need normalization.
        """
        if isinstance(values, dict):
            content_type = values.pop("content_type", None) or values.pop(
                "ContentType", None
            )
            if not content_type:
                content_type = "application/yaml"
            values["content_type"] = content_type
        return values

    def set_key(self, dd: DeploymentDetails, filename: str) -> None:
        """Set the object key based on deployment details and filename.

        Constructs the appropriate object key by combining deployment context with the
        specified filename in the artefacts folder. The key follows the hierarchical
        pattern used throughout the deployment system for consistent organization.

        Args:
            dd (DeploymentDetails): Deployment details providing the context for key generation.
                                   Must include client, environment, and other contextual information.
            filename (str): Name of the action file including extension (e.g., "deploy.actions").

        Examples:
            >>> from core_framework.models import ActionDetails, DeploymentDetails

            >>> # Set key for production deployment
            >>> details = ActionDetails(client="acme", bucket_name="acme-deployments")
            >>> deployment = DeploymentDetails(client="acme", environment="production")
            >>> details.set_key(deployment, "deploy.actions")
            >>> print(details.key)  # "acme/production/artefacts/deploy.actions"

            >>> # Set key for staging rollback
            >>> details.set_key(deployment, "rollback.actions")
            >>> print(details.key)  # "acme/production/artefacts/rollback.actions"

            >>> # Custom action file
            >>> details.set_key(deployment, "custom-migration.actions")
            >>> print(details.key)  # "acme/production/artefacts/custom-migration.actions"

        Key Structure:
            The generated key follows this pattern:
            ```
            {client}/{environment}/artefacts/{filename}
            ```

            Where:
            - client: From deployment details client field
            - environment: From deployment details environment context
            - artefacts: Fixed folder name for action specifications
            - filename: Provided filename parameter

        Side Effects:
            Modifies the instance's key attribute in-place. No return value.
        """
        super().set_key(dd.get_object_key(OBJ_ARTEFACTS, filename))

    @classmethod
    def from_arguments(cls, **kwargs) -> "ActionDetails":
        """Create ActionDetails instance from flexible keyword arguments.

        Factory method that provides intelligent ActionDetails creation by accepting various
        parameter combinations and applying defaults. Handles multiple parameter naming
        conventions and automatically generates missing values from context.

        Args:
            **kwargs: Flexible keyword arguments supporting multiple naming conventions:

                     **Core Parameters:**
                     - client/Client (str): Client identifier
                     - bucket_name/BucketName (str): S3 bucket or local base path
                     - bucket_region/BucketRegion (str): AWS region
                     - mode/Mode (str): Storage mode (V_LOCAL or V_SERVICE)

                     **Key Generation Parameters:**
                     - key/Key (str): Direct key specification (overrides generation)
                     - task/Task (str): Task name for automatic key generation
                     - action_file/ActionFile (str): Action filename for key generation
                     - deployment_details/DeploymentDetails: Deployment context object

                     **Optional Parameters:**
                     - version_id/VersionId (str): S3 object version
                     - content_type/ContentType (str): MIME type

        Returns:
            ActionDetails: Fully configured ActionDetails instance with all required fields populated.

        Raises:
            ValueError: If required parameters cannot be determined or if there are
                       validation errors in the provided arguments.

        Examples:
            >>> # Create from task name (common pattern)
            >>> details = ActionDetails.from_arguments(
            ...     task="deploy",
            ...     client="acme",
            ...     bucket_region="us-east-1"
            ... )
            >>> print(details.key)  # Auto-generated from task and context

            >>> # Create with explicit key
            >>> details = ActionDetails.from_arguments(
            ...     client="acme",
            ...     key="custom/path/special.actions",
            ...     bucket_name="acme-bucket"
            ... )

            >>> # Create for local development
            >>> details = ActionDetails.from_arguments(
            ...     task="test",
            ...     client="dev",
            ...     mode="local",
            ...     bucket_name="/tmp/actions"
            ... )

            >>> # Create from command line arguments
            >>> cli_args = {
            ...     "Task": "deploy",
            ...     "Client": "production-client",
            ...     "BucketRegion": "eu-west-1"
            ... }
            >>> details = ActionDetails.from_arguments(**cli_args)

            >>> # Create with deployment context
            >>> deployment = DeploymentDetails(client="acme", environment="staging")
            >>> details = ActionDetails.from_arguments(
            ...     action_file="rollback.actions",
            ...     deployment_details=deployment
            ... )

        Parameter Resolution:
            The method uses intelligent defaults and context-aware resolution:

            **Client Resolution:**
            1. Explicit client/Client parameter
            2. Framework default client from configuration

            **Key Generation:**
            1. Direct key/Key parameter (highest priority)
            2. Generated from action_file + deployment_details
            3. Generated from task name (defaults to "deploy")

            **Storage Configuration:**
            1. Explicit bucket_name or auto-generated from client + region
            2. Explicit bucket_region or framework default region
            3. Mode determined by framework configuration (local vs service)

        Factory Patterns:
            ```python
            # Pattern 1: Task-based creation
            details = ActionDetails.from_arguments(task="deploy", client="acme")

            # Pattern 2: Explicit key creation
            details = ActionDetails.from_arguments(key="path/file.actions")

            # Pattern 3: Deployment context creation
            details = ActionDetails.from_arguments(
                deployment_details=deployment_context,
                action_file="custom.actions"
            )

            # Pattern 4: Command line integration
            details = ActionDetails.from_arguments(**parsed_cli_args)
            ```
        """

        def _get(
            key1: str, key2: str, default: str | None, can_be_empty: bool = False
        ) -> str:
            """Extract parameter with fallback and default handling."""
            value = kwargs.get(key1, None) or kwargs.get(key2, None)
            return value if value or can_be_empty else default

        # Extract all parameters with intelligent defaults
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
        bucket_region = _get(
            "bucket_region", "BucketRegion", util.get_artefact_bucket_region()
        )

        # Bucket name must also be populated before creating ActionDetails
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
        """Return a human-readable string representation.

        Provides a concise, user-friendly representation showing the storage mode
        and location information for quick identification and debugging.

        Returns:
            str: Human-readable string in format "ActionDetails(mode: location/key)".

        Examples:
            >>> details = ActionDetails.from_arguments(task="deploy", client="acme")
            >>> print(str(details))
            "ActionDetails(service: acme-bucket/acme/prod/artefacts/deploy.actions)"

            >>> local_details = ActionDetails.from_arguments(
            ...     task="test",
            ...     mode="local",
            ...     bucket_name="/tmp"
            ... )
            >>> print(str(local_details))
            "ActionDetails(local: /tmp/client/env/artefacts/test.actions)"
        """
        return f"ActionDetails({self.mode}: {self.bucket_name}/{self.key})"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Provides a detailed representation suitable for debugging and development,
        showing the key attributes needed to reconstruct or understand the instance.

        Returns:
            str: Detailed string representation showing bucket_name and key.

        Examples:
            >>> details = ActionDetails.from_arguments(task="deploy", client="acme")
            >>> print(repr(details))
            "ActionDetails(bucket_name='acme-deployments', key='acme/prod/artefacts/deploy.actions')"

            >>> # Useful in debugging and logging
            >>> import logging
            >>> logging.debug(f"Processing action: {repr(details)}")
        """
        return f"ActionDetails(bucket_name='{self.bucket_name}', key='{self.key}')"
