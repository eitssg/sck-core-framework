"""
Actions are commands or instructions that tell Core Automation exactly what to do when
deploying infrastructure to your Cloud.  There are one or more Action objects within a Task and
are defined in the task.actions file for the deployment.

The action defintiions are stored on S3 in the artefacts file: **s3://client-bucket/artefacts/portfolio/app/branch/build/{task}.actions**
where {task} is the action to be performed as defined in the core-execute/actionlib.

"""

from .action import Action, LABEL, TYPE, DEPENDS_ON, PARAMS, SCOPE
from .action_params import *  # noqa F403


__all__ = ["Action", "LABEL", "TYPE", "DEPENDS_ON", "PARAMS", "SCOPE"]
