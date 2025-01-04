"""
This module contains the Jinja2Renderer class which is used to render Jinja2 CloudFormation templates within the Core Automation context.
"""

from typing import Any
from collections.abc import Mapping

import jinja2
import core_logging as log
import os
import pathlib
import json

from .filters import load_filters


class Jinja2Renderer:
    """
    This renderer class is used to read/write files from the filesystem.  We want to change the compiler
    so that it can be run in lambda.

    Therefore, we will deprecate this class and use the Jinja2Renderer instead inside the compiler.

    .. deprecated: 1.0
        Use core compiler renderer class instead

    """

    env: jinja2.Environment
    dictionary: Mapping[str, str]

    # If loading from filesystem
    template_path: str | None = None

    def __init__(
        self,
        template_path: str | None = None,
        dictionary: Mapping[str, str] | None = None,
    ):
        loader: jinja2.BaseLoader
        if template_path is not None:
            self.template_path = template_path
            loader = jinja2.FileSystemLoader(template_path)
        elif dictionary is not None:
            self.dictionary = dictionary
            loader = jinja2.DictLoader(dictionary)
        else:
            loader = jinja2.DictLoader({})

        self.env = jinja2.Environment(
            autoescape=False,
            loader=loader,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )

        load_filters(self.env)

    def render_string(self, string: str, context: dict[str, Any]) -> str:
        return self.env.from_string(string).render(context)

    def render_object(self, data: str, context: dict[str, Any]) -> dict | None:
        try:
            return json.loads(self.render_string(json.dumps(data), context))
        except json.JSONDecodeError:
            return None

    def render_file(self, path: str, context: dict[str, Any]) -> str:
        template = self.env.get_template(path)
        return template.render(context)

    def render_files(self, path: str, context: dict[str, Any]) -> dict[str, str]:

        files: dict = {}

        if self.template_path is None:
            log.warning("No template path set.  Cannot render files.")
            return files

        files_path = pathlib.Path(os.path.join(self.template_path, path))
        for file_path in files_path.glob("**/*"):

            # Skip non-files (directories, etc)
            if not file_path.is_file():
                continue

            # Retrieve file path relative to the files path and the base path
            short_path = str(file_path.relative_to(files_path))
            renderer_path = str(file_path.relative_to(self.template_path))

            # Jinja2 expects forward slash. See split_template_path.
            # Update short_path as well, to ensure we upload correctly to s3.
            short_path = short_path.replace("\\", "/")
            renderer_path = renderer_path.replace("\\", "/")

            # Load and render the files
            log.debug(
                "Rendering file '{}' with short_path '{}'", renderer_path, short_path
            )

            rendered_template = self.render_file(renderer_path, context)

            # Save the rendered file into our dictionary
            files[short_path] = rendered_template

        return files
