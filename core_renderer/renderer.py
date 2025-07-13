"""
This module contains the Jinja2Renderer class which is used to render Jinja2 CloudFormation templates within the Core Automation context.
"""

from typing import Any
import core_framework as util
import jinja2
import core_logging as log
import os
import pathlib
import json

from .filters import load_filters


class Jinja2Renderer:
    """
    Jinja2Renderer is a class that provides methods to render Jinja2 templates.
    It can render strings, objects, and files using a Jinja2 environment.
    """

    # Jinja2 environment for rendering templates
    env: jinja2.Environment

    # Dictionary of templates to render
    dictionary: dict[str, str] | None = None

    # If loading from filesystem
    template_path: str | None = None

    def __init__(
        self,
        template_path: str | None = None,
        dictionary: dict[str, str] | None = None,
    ):
        loader: jinja2.BaseLoader

        if template_path is not None:
            self.template_path = template_path
            loader = jinja2.FileSystemLoader(template_path)
        elif dictionary is not None:
            self.dictionary = dictionary
            loader = jinja2.DictLoader(dictionary)
        else:
            raise jinja2.exceptions.TemplateNotFound(
                "You must provide either a template path or a dictionary of templates."
            )

        self.env = jinja2.Environment(
            loader=loader,
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )

        load_filters(self.env)

    def render_string(self, string: str, context: dict[str, Any]) -> str:
        """
        Render a Jinja2 template string using the provided context.

        :param string: The Jinja2 template string to render.
        :param context: The context to use for rendering the template string.
        :return: The rendered string.
        """
        return self.env.from_string(string).render(context)

    def render_object(
        self, data: list[Any] | dict[str, Any] | str, context: dict[str, Any]
    ) -> list[Any] | dict[str, Any] | str:
        """
        Render a dictionary using the provided context.

        :param data: The data to render, which can be a list, dictionary, or string.
        :param context: The context to use for rendering the data.
        :return: A dictionary with the rendered data.

        This method is used to render a Python object (list, dict, or string) into a Jinja2 template format.
        It converts the object to YAML format and then renders it using the provided context.

        """
        if isinstance(data, str):
            # If data is a string, render it directly
            rendered_string = self.render_string(data, context)
            return rendered_string

        # BUG - If the resulting data is invalid yaml, it will raise an error.
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, str):
                    result.append(self.render_string(item, context))
                elif isinstance(item, dict):
                    result.append(self.render_object(item, context))
            return result
        elif isinstance(data, dict):
            json_data = json.dumps(data, indent=2)
            rendered_json = self.render_json(json_data, context)
            return json.loads(rendered_json)
        else:
            raise TypeError(
                "Unsupported data type for rendering: {}".format(type(data))
            )

    def render_json(self, json_data: str, context: dict[str, Any]) -> dict | None:
        """
        Render a JSON string using the Jinja2 environment.

        :param json_data: The JSON string to render.
        :param context: The context to use for rendering the JSON string.
        :return: The rendered JSON converted to a dictionary, or None if parsing fails.
        """
        try:
            return json.loads(self.render_string(json.dumps(json_data), context))
        except json.JSONDecodeError:
            return None

    def render_file(self, filename: str, context: dict[str, Any]) -> str:
        """
        Render a tempalte file using the Jinja2 environment.  If you have initaialize the Jinja2Renderer
        with a dictionary, this will be the dictionary key (a.k.a filename) for the template.

        :param filename: The name of the template to render (a filename or a dictionary key depending on how this class was initialized).
        :param context: The context (variables) to use for rendering the file.
        :return: The rendered content of the template.
        """
        template = self.env.get_template(filename)
        return template.render(context)

    def render_files(self, path: str, context: dict[str, Any]) -> dict[str, str]:
        """
        Render all the jinja2 templates in the spacified path using the context provided.

        The ouptuput is a dictionary of each template name and its rendered content.

        :param path: The path to the directory containing the templates.
        :param context: The context to use for rendering the files.
        :return: A dictionary of rendered files.
        """
        log.debug("Rendering files in path: {}", path)

        # Dictionary to hold rendered files
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
