"""StateDetails model for Core Automation deployment state tracking.

The StateDetails class manages deployment execution state files that contain information
about task progress, results, and metadata. State files are typically stored as
{task}.state files in the artefacts folder structure and can be managed in either
S3 or local filesystem depending on the deployment mode.

Key Features:
    - **State file tracking** for deployment execution history
    - **Storage flexibility** with S3 and local filesystem support
    - **Automatic key generation** from deployment context and task names
    - **Version management** with S3 object versioning support
    - **Cross-platform compatibility** with proper path handling

Common Use Cases:
    - Task execution state persistence
    - Deployment rollback information
    - Audit trail storage
    - Inter-task communication via state files
"""

from typing import Any
from pydantic import model_validator

import core_framework as util
from core_framework.constants import OBJ_ARTEFACTS, V_LOCAL, V_SERVICE, V_EMPTY
from .deployment_details import DeploymentDetails
from .file_details import FileDetails


class StateDetails(FileDetails):
    """Manages deployment state file location and metadata.

    StateDetails tracks state files that contain deployment execution information,
    typically stored as {task}.state files in the artefacts folder structure.
    Supports both S3 and local filesystem storage with automatic path generation
    based on deployment context.

    State files contain execution results, progress information, and metadata
    that enable task coordination and deployment rollback capabilities.

    Attributes:
        client: Client identifier for multi-tenant operations.
        bucket_name: S3 bucket name or local directory root path.
        bucket_region: AWS region for S3 bucket (S3 mode only).
        key: Full path to state file relative to bucket_name.
        mode: Storage mode ('local' for filesystem, 'service' for S3).
        version_id: S3 object version ID for versioned state files.
        content_type: MIME type of state file (defaults to 'application/x-yaml').

    Examples:
        >>> # S3 storage mode
        >>> state = StateDetails(
        ...     client="my-client",
        ...     bucket_name="deployment-bucket",
        ...     bucket_region="us-east-1",
        ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
        ...     mode="service"
        ... )
        >>> print(state.is_service_mode())
        True

        >>> # Local storage mode
        >>> state = StateDetails(
        ...     client="my-client",
        ...     bucket_name="/var/deployments",
        ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
        ...     mode="local"
        ... )
        >>> print(state.get_full_path())
        '/var/deployments/artefacts/ecommerce/web/main/1.0.0/deploy.state'

        >>> # Automatic creation from deployment context
        >>> from core_framework.models.deployment_details import DeploymentDetails
        >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
        >>> state = StateDetails.from_arguments(deployment_details=dd, task="deploy")
        >>> print(state.key)
        'artefacts/ecommerce/web/main/1.0.0/deploy.state'

    Storage Patterns:
        State files follow a consistent naming and organization pattern:

        >>> # Task-specific state files
        >>> deploy_state = StateDetails.from_arguments(dd=dd, task="deploy")
        >>> release_state = StateDetails.from_arguments(dd=dd, task="release")
        >>> teardown_state = StateDetails.from_arguments(dd=dd, task="teardown")

        >>> # Files stored under artefacts hierarchy
        >>> print(deploy_state.key)
        'artefacts/portfolio/app/branch/build/deploy.state'
        >>> print(release_state.key)
        'artefacts/portfolio/app/branch/build/release.state'
    """

    @model_validator(mode="before")
    @classmethod
    def validate_model_before(cls, values: dict) -> dict:
        """Validate and normalize values before model creation.

        Sets default content type for state files if not provided. State files
        typically use YAML format for human readability and structured data.

        Args:
            values: Input values for model creation.

        Returns:
            Normalized values with default content type set.

        Examples:
            >>> values = {"client": "test", "bucket_name": "bucket"}
            >>> normalized = StateDetails.validate_model_before(values)
            >>> print(normalized["content_type"])
            'application/yaml'
        """
        if isinstance(values, dict):
            content_type = values.pop("content_type", None) or values.pop(
                "ContentType", None
            )
            if not content_type:
                content_type = "application/yaml"
            values["content_type"] = content_type
        return values

    def set_key(self, deployment_details: DeploymentDetails, filename: str) -> None:
        """Set the key path based on deployment details and filename.

        Generates the key path using the deployment details hierarchy and the
        specified filename. The path separators are automatically normalized
        for the current storage mode (OS-appropriate for local, forward slashes for S3).

        Args:
            deployment_details: Deployment context containing portfolio, app, build info.
            filename: State filename (e.g., "deploy.state", "release.state").

        Examples:
            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> state = StateDetails(client="test", bucket_name="test-bucket", mode="local")
            >>> state.set_key(dd, "deploy.state")
            >>> print(state.key)
            'artefacts/ecommerce/web/main/1.0.0/deploy.state'

            >>> # Different tasks use same hierarchy
            >>> state.set_key(dd, "release.state")
            >>> print(state.key)
            'artefacts/ecommerce/web/main/1.0.0/release.state'

        Path Generation:
            The generated path follows the pattern:
            artefacts/{portfolio}/{app}/{branch}/{build}/{filename}

            Where branch defaults to 'main' if not specified in deployment_details.
        """
        # Get the key from deployment details with appropriate separator for mode
        super().set_key(deployment_details.get_object_key(OBJ_ARTEFACTS, filename))

    @classmethod
    def from_arguments(cls, **kwargs: Any) -> "StateDetails":
        """Create StateDetails from keyword arguments with intelligent defaults.

        Flexible factory method that accepts various parameter combinations and
        applies intelligent defaults. Can generate state file keys automatically
        from deployment details and task names, making it ideal for command-line
        tools and programmatic creation.

        Args:
            **kwargs: Keyword arguments including:
                - **Core Parameters**:
                    - client/Client (str): Client identifier
                    - key/Key (str): State file key path
                    - mode/Mode (str): Storage mode ('local' or 'service')
                - **Storage Parameters**:
                    - bucket_name/BucketName (str): Bucket name or root directory
                    - bucket_region/BucketRegion (str): S3 bucket region
                    - content_type/ContentType (str): MIME type
                    - version_id/VersionId (str): S3 version ID
                - **Key Generation Parameters**:
                    - state_file/StateFile (str): State filename
                    - task/Task (str): Task name for auto-generating filename
                    - deployment_details/DeploymentDetails: Deployment context
                - **DeploymentDetails Parameters**:
                    - portfolio/Portfolio (str): Portfolio name
                    - app/App (str): Application name
                    - build/Build (str): Build version
                    - branch/Branch (str): Branch name

        Returns:
            StateDetails instance with populated fields and intelligent defaults.

        Raises:
            ValueError: If required parameters are missing or invalid.

        Examples:
            >>> # Explicit key specification
            >>> state = StateDetails.from_arguments(
            ...     client="my-client",
            ...     key="artefacts/ecommerce/web/main/1.0.0/deploy.state",
            ...     mode="service"
            ... )
            >>> print(state.key)
            'artefacts/ecommerce/web/main/1.0.0/deploy.state'

            >>> # Auto-generation from task and deployment details
            >>> from core_framework.models.deployment_details import DeploymentDetails
            >>> dd = DeploymentDetails(portfolio="ecommerce", app="web", build="1.0.0")
            >>> state = StateDetails.from_arguments(
            ...     deployment_details=dd,
            ...     task="deploy"
            ... )
            >>> print(state.key)
            'artefacts/ecommerce/web/main/1.0.0/deploy.state'

            >>> # Minimal arguments with auto-generation
            >>> state = StateDetails.from_arguments(
            ...     portfolio="ecommerce",
            ...     app="web",
            ...     build="1.0.0",
            ...     task="release"
            ... )
            >>> print(state.key)
            'artefacts/ecommerce/web/main/1.0.0/release.state'

            >>> # Command line integration
            >>> cli_args = {
            ...     "portfolio": "ecommerce",
            ...     "app": "web",
            ...     "build": "1.0.0",
            ...     "task": "deploy",
            ...     "mode": "local"
            ... }
            >>> state = StateDetails.from_arguments(**cli_args)

        Key Generation Logic:
            1. **Explicit key**: If 'key' parameter provided, use directly
            2. **State file + deployment**: Combine 'state_file' with deployment context
            3. **Task-based**: Generate filename as '{task}.state' from task parameter
            4. **Auto-deployment**: Create DeploymentDetails from kwargs if not provided
            5. **Path normalization**: Apply OS-appropriate separators for storage mode

        Parameter Aliases:
            Accepts both CamelCase and snake_case parameter names:
            - bucket_name/BucketName
            - bucket_region/BucketRegion
            - content_type/ContentType
            - version_id/VersionId
            - deployment_details/DeploymentDetails

        Default Behavior:
            - **Client**: Defaults to util.get_client()
            - **Mode**: 'local' if util.is_local_mode() else 'service'
            - **Bucket name**: util.get_artefact_bucket_name()
            - **Bucket region**: util.get_artefact_bucket_region()
            - **Content type**: 'application/x-yaml'
            - **Task**: 'deploy' if not specified
        """

        def _get(
            key1: str, key2: str, default: str | None, can_be_empty: bool = False
        ) -> str:
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

        bucket_region = _get(
            "bucket_region", "BucketRegion", util.get_artefact_bucket_region()
        )

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

        Returns:
            String showing the storage mode and file location.

        Examples:
            >>> state = StateDetails(client="test", bucket_name="bucket", key="deploy.state")
            >>> str(state)
            'StateDetails(local: bucket/deploy.state)'
        """
        return f"StateDetails({self.mode}: {self.bucket_name}/{self.key})"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            Detailed representation showing key attributes.

        Examples:
            >>> state = StateDetails(bucket_name="bucket", key="deploy.state")
            >>> repr(state)
            "StateDetails(bucket_name='bucket', key='deploy.state')"
        """
        return f"StateDetails(bucket_name='{self.bucket_name}', key='{self.key}')"
