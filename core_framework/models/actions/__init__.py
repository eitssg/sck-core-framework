from .actions import Action
from .params import *  # noqa F403

# Give constants for the keys in the definition
LABEL = "Label"
TYPE = "Type"
DEPENDS_ON = "DependsOn"
PARAMS = "Params"
SCOPE = "Scope"


__all__ = ["Action", "LABEL", "TYPE", "DEPENDS_ON", "PARAMS", "SCOPE"]
