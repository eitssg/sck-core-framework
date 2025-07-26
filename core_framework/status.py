"""This module provides the BuildStatus class which is used to track the status of a build."""

RELEASE_IN_PROGRESS = "RELEASE_IN_PROGRESS"
""":const RELEASE_IN_PROGRESS: The release process is currently in progress."""
RELEASE_COMPLETE = "RELEASE_COMPLETE"
""":const RELEASE_COMPLETE: The release process has completed successfully."""
RELEASE_FAILED = "RELEASE_FAILED"
""":const RELEASE_FAILED: The release process has failed."""
RELEASE_REQUESTED = "RELEASE_REQUESTED"
""":const RELEASE_REQUESTED: A release has been requested."""
TEARDOWN_COMPLETE = "TEARDOWN_COMPLETE"
""":const TEARDOWN_COMPLETE: The teardown process has completed successfully."""
TEARDOWN_FAILED = "TEARDOWN_FAILED"
""":const TEARDOWN_FAILED: The teardown process has failed."""
TEARDOWN_IN_PROGRESS = "TEARDOWN_IN_PROGRESS"
""":const TEARDOWN_IN_PROGRESS: The teardown process is currently in progress."""
TEARDOWN_REQUESTED = "TEARDOWN_REQUESTED"
""":const TEARDOWN_REQUESTED: A teardown has been requested."""
COMPILE_COMPLETE = "COMPILE_COMPLETE"
""":const COMPILE_COMPLETE: The compile process has completed successfully."""
COMPILE_FAILED = "COMPILE_FAILED"
""":const COMPILE_FAILED: The compile process has failed."""
COMPILE_IN_PROGRESS = "COMPILE_IN_PROGRESS"
""":const COMPILE_IN_PROGRESS: The compile process is currently in progress."""
DEPLOY_COMPLETE = "DEPLOY_COMPLETE"
""":const DEPLOY_COMPLETE: The deployment process has completed successfully."""
DEPLOY_FAILED = "DEPLOY_FAILED"
""":const DEPLOY_FAILED: The deployment process has failed."""
DEPLOY_IN_PROGRESS = "DEPLOY_IN_PROGRESS"
""":const DEPLOY_IN_PROGRESS: The deployment process is currently in progress."""
DEPLOY_REQUESTED = "DEPLOY_REQUESTED"
""":const DEPLOY_REQUESTED: A deployment has been requested."""
INIT = "INIT"
""":const INIT: The initial state before any action has been taken."""


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
""":const STATUS_LIST: A list of all valid status strings."""


class BuildStatus(object):
    """Provides a class to manage the status of a build.

    The status is used to track the current state of the build process and
    ensure that each step is completed successfully before moving on to the
    next step. If the status is not one of the valid status strings, it will
    be set to INIT by default.

    :ivar value: The status of the build. This is a string that is one of the valid status values.
    :vartype value: str
    """

    def __init__(self, value: str):
        """Initializes a BuildStatus object.

        The value must be one of the valid status strings, otherwise it will be set to INIT.

        :param value: A string representing the status of the build.
        :type value: str
        """
        self.value = value.upper() if value in STATUS_LIST else INIT

    def __str__(self) -> str:
        """Returns the string representation of the status value."""
        return self.value

    def __repr__(self) -> str:
        """Returns the developer-friendly representation of the BuildStatus object."""
        return f"<BuildStatus value={self.value}>"

    @classmethod
    def from_str(cls, value: str) -> "BuildStatus":
        """Creates a BuildStatus object from a string.

        This is the same as ``__init__()`` but raises an exception if the value is not valid.

        :param value: A valid BuildStatus string.
        :type value: str
        :raises ValueError: If the build status is not valid.
        :return: The :class:`BuildStatus` object.
        :rtype: BuildStatus
        """
        status = cls(value)
        if status.value != INIT or value.upper() == INIT:
            return status
        raise ValueError(f"'{value}' is not a valid status")

    def is_init(self) -> bool:
        """Checks if the build is in the INIT state.

        :return: True if the value is INIT.
        :rtype: bool
        """
        return self.value == INIT

    def is_deploy(self) -> bool:
        """Checks if the build is in any of the DEPLOY states.

        :return: True if in one of the 4 DEPLOY states.
        :rtype: bool
        """
        return self.value in [
            DEPLOY_REQUESTED,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
        ]

    def is_release(self) -> bool:
        """Checks if the build is in any of the RELEASE states.

        :return: True if in one of the 4 RELEASE states.
        :rtype: bool
        """
        return self.value in [
            RELEASE_REQUESTED,
            RELEASE_IN_PROGRESS,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]

    def is_teardown(self) -> bool:
        """Checks if the build is in any of the TEARDOWN states.

        :return: True if in one of the 4 TEARDOWN states.
        :rtype: bool
        """
        return self.value in [
            TEARDOWN_REQUESTED,
            TEARDOWN_IN_PROGRESS,
            TEARDOWN_COMPLETE,
            TEARDOWN_FAILED,
        ]

    def is_in_progress(self) -> bool:
        """Checks if the build is in any of the IN_PROGRESS or REQUESTED states.

        :return: True if in one of the 6 IN_PROGRESS or REQUESTED states.
        :rtype: bool
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
        """Checks if the build is in any of the COMPLETE states.

        :return: True if in one of the 4 COMPLETE states.
        :rtype: bool
        """
        return self.value in [
            COMPILE_COMPLETE,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            TEARDOWN_COMPLETE,
        ]

    def is_failed(self) -> bool:
        """Checks if the build is in any of the FAILED states.

        :return: True if in one of the 4 FAILED states.
        :rtype: bool
        """
        return self.value in [
            COMPILE_FAILED,
            DEPLOY_FAILED,
            RELEASE_FAILED,
            TEARDOWN_FAILED,
        ]

    def is_allowed_to_teardown(self) -> bool:
        """Checks if the current status allows a teardown to proceed.

        :return: True if it's ok to proceed with a teardown.
        :rtype: bool
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
        """Checks if the current status allows a release to proceed.

        :return: True if it's ok to proceed with a release.
        :rtype: bool
        """
        return self.value in [
            INIT,
            DEPLOY_COMPLETE,
            RELEASE_REQUESTED,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
            TEARDOWN_REQUESTED,
        ]
