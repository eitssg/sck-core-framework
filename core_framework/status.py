"""Build status tracking for the Core Automation framework.

Provides comprehensive status management for build lifecycle operations including
deployment, release, teardown, and compilation processes. Status values track
the current state and control workflow progression with validation rules.

Status Categories:
    - **INIT**: Initial state before any operations
    - **DEPLOY**: Deployment lifecycle states (requested, in progress, complete, failed)
    - **COMPILE**: Compilation process states (in progress, complete, failed)
    - **RELEASE**: Release lifecycle states (requested, in progress, complete, failed)
    - **TEARDOWN**: Teardown lifecycle states (requested, in progress, complete, failed)

Workflow Control:
    Status values determine which operations are permitted at each stage,
    preventing invalid state transitions and ensuring proper build lifecycle management.
"""

RELEASE_IN_PROGRESS = "RELEASE_IN_PROGRESS"
"""Release process is currently executing."""

RELEASE_COMPLETE = "RELEASE_COMPLETE"
"""Release process completed successfully."""

RELEASE_FAILED = "RELEASE_FAILED"
"""Release process failed with errors."""

RELEASE_REQUESTED = "RELEASE_REQUESTED"
"""Release operation has been requested."""

TEARDOWN_COMPLETE = "TEARDOWN_COMPLETE"
"""Teardown process completed successfully."""

TEARDOWN_FAILED = "TEARDOWN_FAILED"
"""Teardown process failed with errors."""

TEARDOWN_IN_PROGRESS = "TEARDOWN_IN_PROGRESS"
"""Teardown process is currently executing."""

TEARDOWN_REQUESTED = "TEARDOWN_REQUESTED"
"""Teardown operation has been requested."""

COMPILE_COMPLETE = "COMPILE_COMPLETE"
"""Compilation process completed successfully."""

COMPILE_FAILED = "COMPILE_FAILED"
"""Compilation process failed with errors."""

COMPILE_IN_PROGRESS = "COMPILE_IN_PROGRESS"
"""Compilation process is currently executing."""

DEPLOY_COMPLETE = "DEPLOY_COMPLETE"
"""Deployment process completed successfully."""

DEPLOY_FAILED = "DEPLOY_FAILED"
"""Deployment process failed with errors."""

DEPLOY_IN_PROGRESS = "DEPLOY_IN_PROGRESS"
"""Deployment process is currently executing."""

DEPLOY_REQUESTED = "DEPLOY_REQUESTED"
"""Deployment operation has been requested."""

INIT = "INIT"
"""Initial state before any operations have been performed."""


STATUS_LIST = [
    INIT,
    DEPLOY_REQUESTED,
    DEPLOY_IN_PROGRESS,
    DEPLOY_COMPLETE,
    DEPLOY_FAILED,
    COMPILE_IN_PROGRESS,
    COMPILE_COMPLETE,
    COMPILE_FAILED,
    RELEASE_REQUESTED,
    RELEASE_IN_PROGRESS,
    RELEASE_COMPLETE,
    RELEASE_FAILED,
    TEARDOWN_REQUESTED,
    TEARDOWN_IN_PROGRESS,
    TEARDOWN_COMPLETE,
    TEARDOWN_FAILED,
]
"""Complete list of valid build status values."""


class BuildStatus:
    """Manages build lifecycle status with workflow validation.

    Tracks the current state of build operations and provides validation methods
    to ensure proper workflow progression. Invalid status values are automatically
    normalized to INIT state for safety.

    The status system enforces proper build lifecycle management by controlling
    which operations are permitted based on the current state.

    Attributes:
        value: The current status string, guaranteed to be a valid status value.

    Examples:
        >>> status = BuildStatus("DEPLOY_COMPLETE")
        >>> print(status.value)
        'DEPLOY_COMPLETE'
        >>> print(status.is_allowed_to_release())
        True

        >>> # Invalid status normalized to INIT
        >>> status = BuildStatus("INVALID_STATUS")
        >>> print(status.value)
        'INIT'

        >>> # Status validation
        >>> status = BuildStatus.from_str("DEPLOY_FAILED")
        >>> print(status.is_deploy())
        True
        >>> print(status.is_failed())
        True
    """

    def __init__(self, value: str) -> None:
        """Initialize BuildStatus with automatic validation.

        Args:
            value: Status string to set. If invalid, defaults to INIT.

        Examples:
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.value)
            'DEPLOY_COMPLETE'

            >>> # Invalid values default to INIT
            >>> status = BuildStatus("invalid")
            >>> print(status.value)
            'INIT'
        """
        self.value = value.upper() if value in STATUS_LIST else INIT

    def __str__(self) -> str:
        """Return string representation of the status value.

        Returns:
            The current status value as a string.
        """
        return self.value

    def __repr__(self) -> str:
        """Return developer-friendly representation.

        Returns:
            Formatted string showing the BuildStatus object and its value.
        """
        return f"<BuildStatus value={self.value}>"

    @classmethod
    def from_str(cls, value: str) -> "BuildStatus":
        """Create BuildStatus with strict validation.

        Args:
            value: Status string that must be valid.

        Returns:
            New BuildStatus instance with the specified value.

        Raises:
            ValueError: If the value is not a valid status string.

        Examples:
            >>> status = BuildStatus.from_str("DEPLOY_COMPLETE")
            >>> print(status.value)
            'DEPLOY_COMPLETE'

            >>> # This raises ValueError
            >>> status = BuildStatus.from_str("INVALID")
            ValueError: 'INVALID' is not a valid status
        """
        status = cls(value)
        if status.value != INIT or value.upper() == INIT:
            return status
        raise ValueError(f"'{value}' is not a valid status")

    def is_init(self) -> bool:
        """Check if status is in initial state.

        Returns:
            True if the status is INIT.

        Examples:
            >>> status = BuildStatus("INIT")
            >>> print(status.is_init())
            True
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_init())
            False
        """
        return self.value == INIT

    def is_deploy(self) -> bool:
        """Check if status is in any deployment state.

        Returns:
            True if status is one of the 4 deployment states.

        Examples:
            >>> status = BuildStatus("DEPLOY_IN_PROGRESS")
            >>> print(status.is_deploy())
            True
            >>> status = BuildStatus("RELEASE_COMPLETE")
            >>> print(status.is_deploy())
            False
        """
        return self.value in [
            DEPLOY_REQUESTED,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
        ]

    def is_release(self) -> bool:
        """Check if status is in any release state.

        Returns:
            True if status is one of the 4 release states.

        Examples:
            >>> status = BuildStatus("RELEASE_IN_PROGRESS")
            >>> print(status.is_release())
            True
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_release())
            False
        """
        return self.value in [
            RELEASE_REQUESTED,
            RELEASE_IN_PROGRESS,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]

    def is_teardown(self) -> bool:
        """Check if status is in any teardown state.

        Returns:
            True if status is one of the 4 teardown states.

        Examples:
            >>> status = BuildStatus("TEARDOWN_IN_PROGRESS")
            >>> print(status.is_teardown())
            True
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_teardown())
            False
        """
        return self.value in [
            TEARDOWN_REQUESTED,
            TEARDOWN_IN_PROGRESS,
            TEARDOWN_COMPLETE,
            TEARDOWN_FAILED,
        ]

    def is_in_progress(self) -> bool:
        """Check if any operation is currently active.

        Returns:
            True if status indicates an operation is requested or in progress.

        Examples:
            >>> status = BuildStatus("DEPLOY_IN_PROGRESS")
            >>> print(status.is_in_progress())
            True
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_in_progress())
            False
        """
        return self.value in [
            DEPLOY_REQUESTED,
            RELEASE_REQUESTED,
            TEARDOWN_REQUESTED,
            COMPILE_IN_PROGRESS,
            DEPLOY_IN_PROGRESS,
            RELEASE_IN_PROGRESS,
            TEARDOWN_IN_PROGRESS,
        ]

    def is_complete(self) -> bool:
        """Check if any operation has completed successfully.

        Returns:
            True if status indicates successful completion of any operation.

        Examples:
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_complete())
            True
            >>> status = BuildStatus("DEPLOY_FAILED")
            >>> print(status.is_complete())
            False
        """
        return self.value in [
            COMPILE_COMPLETE,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            TEARDOWN_COMPLETE,
        ]

    def is_failed(self) -> bool:
        """Check if any operation has failed.

        Returns:
            True if status indicates failure of any operation.

        Examples:
            >>> status = BuildStatus("DEPLOY_FAILED")
            >>> print(status.is_failed())
            True
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_failed())
            False
        """
        return self.value in [
            COMPILE_FAILED,
            DEPLOY_FAILED,
            RELEASE_FAILED,
            TEARDOWN_FAILED,
        ]

    def is_allowed_to_teardown(self) -> bool:
        """Check if teardown operation is permitted.

        Teardown is allowed from most states except when another operation
        is actively in progress or has completed successfully.

        Returns:
            True if teardown operation can proceed safely.

        Examples:
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_allowed_to_teardown())
            True
            >>> status = BuildStatus("RELEASE_IN_PROGRESS")
            >>> print(status.is_allowed_to_teardown())
            False

        Workflow Rules:
            - ✅ **INIT**: Fresh state, teardown allowed
            - ✅ **DEPLOY_IN_PROGRESS**: Can interrupt deployment
            - ✅ **DEPLOY_COMPLETE**: Can teardown successful deployment
            - ✅ **DEPLOY_FAILED**: Can cleanup failed deployment
            - ✅ **RELEASE_REQUESTED**: Can teardown before release starts
            - ✅ **RELEASE_COMPLETE**: Can teardown released resources
            - ✅ **RELEASE_FAILED**: Can cleanup failed release
            - ✅ **TEARDOWN_REQUESTED**: Can retry teardown
            - ✅ **TEARDOWN_FAILED**: Can retry failed teardown
            - ❌ **RELEASE_IN_PROGRESS**: Cannot interrupt active release
            - ❌ **TEARDOWN_IN_PROGRESS**: Already tearing down
        """
        return self.value in [
            INIT,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
            RELEASE_REQUESTED,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
            TEARDOWN_REQUESTED,
            TEARDOWN_FAILED,
        ]

    def is_allowed_to_release(self) -> bool:
        """Check if release operation is permitted.

        Release requires successful deployment or can retry from certain states.
        Cannot release while other operations are in progress.

        Returns:
            True if release operation can proceed safely.

        Examples:
            >>> status = BuildStatus("DEPLOY_COMPLETE")
            >>> print(status.is_allowed_to_release())
            True
            >>> status = BuildStatus("DEPLOY_IN_PROGRESS")
            >>> print(status.is_allowed_to_release())
            False

        Workflow Rules:
            - ✅ **INIT**: Fresh state, release allowed
            - ✅ **DEPLOY_COMPLETE**: Normal path after successful deployment
            - ✅ **RELEASE_REQUESTED**: Can retry release
            - ✅ **RELEASE_COMPLETE**: Can re-release if needed
            - ✅ **RELEASE_FAILED**: Can retry failed release
            - ✅ **TEARDOWN_REQUESTED**: Can release before teardown
            - ❌ **DEPLOY_IN_PROGRESS**: Must wait for deployment completion
            - ❌ **DEPLOY_FAILED**: Cannot release failed deployment
            - ❌ **RELEASE_IN_PROGRESS**: Already releasing
            - ❌ **TEARDOWN_IN_PROGRESS**: Cannot release during teardown
        """
        return self.value in [
            INIT,
            DEPLOY_COMPLETE,
            RELEASE_REQUESTED,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
            TEARDOWN_REQUESTED,
        ]
