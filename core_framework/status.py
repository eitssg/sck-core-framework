"""
Let's begin to put common status strings in this file rather than "constants"
Attempting to orginize these into Build Status and create more
consistency across the codebase
"""

RELEASE_IN_PROGRESS = "RELEASE_IN_PROGRESS"
""" \\- RELASE_IN_PROGRESS """
RELEASE_COMPLETE = "RELEASE_COMPLETE"
""" \\- RELEASE_COMPLETE """
RELEASE_FAILED = "RELEASE_FAILED"
""" \\- RELEASE_FAILED """
RELEASE_REQUESTED = "RELEASE_REQUESTED"
""" \\- RELEASE_REQUESTED """
TEARDOWN_COMPLETE = "TEARDOWN_COMPLETE"
""" \\- TEARDOWN_COMPLETE """
TEARDOWN_FAILED = "TEARDOWN_FAILED"
""" \\- TEARDOWN_FAILED """
TEARDOWN_IN_PROGRESS = "TEARDOWN_IN_PROGRESS"
""" \\- TEARDOWN_IN_PROGRESS """
TEARDOWN_REQUESTED = "TEARDOWN_REQUESTED"
""" \\- TEARDOWN_REQUESTED """
COMPILE_COMPLETE = "COMPILE_COMPLETE"
""" \\- COMPILE_COMPLETE """
COMPILE_FAILED = "COMPILE_FAILED"
""" \\- COMPILE_FAILED """
COMPILE_IN_PROGRESS = "COMPILE_IN_PROGRESS"
""" \\- COMPILE_IN_PROGRESS """
DEPLOY_COMPLETE = "DEPLOY_COMPLETE"
""" \\- DEPLOY_COMPLETE """
DEPLOY_FAILED = "DEPLOY_FAILED"
""" \\- DEPLOY_FAILED """
DEPLOY_IN_PROGRESS = "DEPLOY_IN_PROGRESS"
""" \\- DEPLOY_IN_PROGRESS """
DEPLOY_REQUESTED = "DEPLOY_REQUESTED"
""" \\- DEPLOY_REQUESTED """
INIT = "INIT"
""" \\- INIT """


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

    def __init__(self, value):
        self.value = value.upper() if value in STATUS_LIST else None

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"<BuildStatus value={self.value}>"

    @classmethod
    def from_str(cls, value) -> "BuildStatus":
        status = cls(value)
        if status:
            return status
        raise ValueError(f"{value} is not a valid status")

    def is_init(self):
        return self.value == INIT

    def is_deploy(self):
        return self.value in [
            DEPLOY_REQUESTED,
            DEPLOY_IN_PROGRESS,
            DEPLOY_COMPLETE,
            DEPLOY_FAILED,
        ]

    def is_release(self):
        return self in [
            RELEASE_REQUESTED,
            RELEASE_IN_PROGRESS,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]

    def is_teardown(self):
        return self.value in [
            TEARDOWN_REQUESTED,
            TEARDOWN_IN_PROGRESS,
            TEARDOWN_COMPLETE,
            TEARDOWN_FAILED,
        ]

    def is_in_progress(self):
        return self.value in [
            TEARDOWN_REQUESTED,
            RELEASE_REQUESTED,
            COMPILE_IN_PROGRESS,
            DEPLOY_IN_PROGRESS,
            RELEASE_IN_PROGRESS,
            TEARDOWN_IN_PROGRESS,
        ]

    def is_complete(self):
        return self in [
            COMPILE_COMPLETE,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            TEARDOWN_COMPLETE,
        ]

    def is_failed(self):
        return self.value in [
            COMPILE_FAILED,
            DEPLOY_FAILED,
            RELEASE_FAILED,
            TEARDOWN_FAILED,
        ]

    def is_allowed_to_teardown(self):

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

    def is_allowed_to_release(self):
        return self.value in [
            INIT,
            TEARDOWN_REQUESTED,
            RELEASE_REQUESTED,
            DEPLOY_COMPLETE,
            RELEASE_COMPLETE,
            RELEASE_FAILED,
        ]
