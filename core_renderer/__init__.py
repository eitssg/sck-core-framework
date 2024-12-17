"""
General compiler framework for Jinja2.  Should be hable to handle CloudFormation or Terraform

"""

from .renderer import Jinja2Renderer
from .monkeypatch import patch_the_monkeys

__all__ = ["Jinja2Renderer", "patch_the_monkeys"]
