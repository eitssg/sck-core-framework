"""
This module provides the BuildStatus class which is used to track the status of a build.
"""

RELEASE_IN_PROGRESS = "RELEASE_IN_PROGRESS"
""" \\-RELASE_IN_PROGRESS """
RELEASE_COMPLETE = "RELEASE_COMPLETE"
""" \\-RELEASE_COMPLETE """
RELEASE_FAILED = "RELEASE_FAILED"
""" \\-RELEASE_FAILED """
RELEASE_REQUESTED = "RELEASE_REQUESTED"
""" \\-RELEASE_REQUESTED """
TEARDOWN_COMPLETE = "TEARDOWN_COMPLETE"
""" \\-TEARDOWN_COMPLETE """
TEARDOWN_FAILED = "TEARDOWN_FAILED"
""" \\-TEARDOWN_FAILED """
TEARDOWN_IN_PROGRESS = "TEARDOWN_IN_PROGRESS"
""" \\-TEARDOWN_IN_PROGRESS """
TEARDOWN_REQUESTED = "TEARDOWN_REQUESTED"
""" \\-TEARDOWN_REQUESTED """
COMPILE_COMPLETE = "COMPILE_COMPLETE"
""" \\-COMPILE_COMPLETE """
COMPILE_FAILED = "COMPILE_FAILED"
""" \\-COMPILE_FAILED """
COMPILE_IN_PROGRESS = "COMPILE_IN_PROGRESS"
""" \\-COMPILE_IN_PROGRESS """
DEPLOY_COMPLETE = "DEPLOY_COMPLETE"
""" \\-DEPLOY_COMPLETE """
DEPLOY_FAILED = "DEPLOY_FAILED"
""" \\-DEPLOY_FAILED """
DEPLOY_IN_PROGRESS = "DEPLOY_IN_PROGRESS"
""" \\-DEPLOY_IN_PROGRESS """
DEPLOY_REQUESTED = "DEPLOY_REQUESTED"
""" \\-DEPLOY_REQUESTED """
INIT = "INIT"
""" \\-INIT """


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


class BuildStatus(object):
    """
    Provides a class to manage the status of a build.

    Attributes:
        value (str): The status of the build.  This is a string that is one of valid status values.

            The status is used to track the current state of the build process and
            ensure that each step is completed successfully before moving on to the
            next step. If the status is not one of the valid status strings, it will
            be set to INIT by default.

    """

    def __init__(self, value: str):
        """
        Initialize a BuildStatus object.  The value must be one of the valid status strings or else it will be set to INIT.

        Args:
            value (str): a string representing the status of the build.
        """
        self.value = value.upper() if value in STATUS_LIST else INIT

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"<BuildStatus value={self.value}>"

    @classmethod
    def from_str(cls, value: str) -> "BuildStatus":
        """
        Create a BuildStatus object from a string.  Same as __init__() but throws an exception if the value is not valid.

        Args:
            value (str): A valie BuildStatus string

        Raises:
            ValueError: If the build status is not valid

        Returns:
            BuildStatus: The :class:`BuildStatus` object
        """
        status = cls(value)
        if status:
            return status
        raise ValueError(f"{value} is not a valid status")

    def is_init(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is in the INIT state.

        Returns:
            bool: True if the value is INIT
        """
        return self.value == INIT

    def is_deploy(self) -> bool:
        """
        Retursn true if this is a BuildStatus indicating the build is in the DEPLOY state.

        Returns:
            bool: True if in one of the 4 DEPLOY states
        """
        return self.value in [
            DEPLOY_REQUESTED,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
        ]

    def is_release(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is in the RELEASE state.

        Returns:
            bool: True if in one of the 4 RELEASE states
        """
        return self in [
            RELEASE_REQUESTED,
            RELEASE_IN_PROGRESS,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]

    def is_teardown(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is in the TEARDOWN state.

        Returns:
            bool: True if in one of the 4 TEARDOWN states
        """
        return self.value in [
            TEARDOWN_REQUESTED,
            TEARDOWN_IN_PROGRESS,
            TEARDOWN_COMPLETE,
            TEARDOWN_FAILED,
        ]

    def is_in_progress(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is in progress.

        Returns:
            bool: True if in one of the 6 IN_PROGRESS states
        """
        return self.value in [
            TEARDOWN_REQUESTED,
            RELEASE_REQUESTED,
            COMPILE_IN_PROGRESS,
            DEPLOY_IN_PROGRESS,
            RELEASE_IN_PROGRESS,
            TEARDOWN_IN_PROGRESS,
        ]

    def is_complete(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is complete.

        Returns:
            bool: True if in one of the 4 COMPLETE states
        """
        return self in [
            COMPILE_COMPLETE,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            TEARDOWN_COMPLETE,
        ]

    def is_failed(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build has failed.

        Returns:
            bool: True if in one of the 4 FAILED states
        """
        return self.value in [
            COMPILE_FAILED,
            DEPLOY_FAILED,
            RELEASE_FAILED,
            TEARDOWN_FAILED,
        ]

    def is_allowed_to_teardown(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is allowed to teardown.

        Returns:
            bool: True if it's ok to proceed with a tearddown.
        """
        return self.value in [
            INIT,
            TEARDOWN_REQUESTED,
            RELEASE_REQUESTED,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
            TEARDOWN_FAILED,
            TEARDOWN_FAILED,
        ]

    def is_allowed_to_release(self) -> bool:
        """
        Return true if this is a BuildStatus indicating the build is allowed to release.

        Returns:
            bool: True if it's ok to proceed with a release.
        """
        return self.value in [
            INIT,
            TEARDOWN_REQUESTED,
            RELEASE_REQUESTED,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]
