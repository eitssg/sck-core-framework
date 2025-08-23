"""
Jinja2 Template Renderer for Core Automation Framework.

This module provides the Jinja2Renderer class for rendering Jinja2 templates within
the Core Automation context. It supports rendering CloudFormation templates, configuration
files, and other text-based resources with Core Automation's custom filters and
deployment context.

Key Features:
    - **Multiple Input Sources**: File system and dictionary-based template loading
    - **Context-Aware Rendering**: Integration with Core Automation deployment context
    - **Custom Filters**: Automatic loading of Core Automation Jinja2 filters
    - **Flexible Output**: String, object, file, and batch rendering capabilities
    - **Error Handling**: Strict undefined variable handling for reliable templates
    - **Cross-Platform**: Proper path handling for Windows and Unix systems

The renderer is optimized for AWS CloudFormation template generation but can be used
for any text-based template rendering within the Core Automation framework.
"""

from typing import Any
import jinja2
import core_logging as log
import os
import pathlib
import json

from .filters import load_filters


class Jinja2Renderer:
    """Jinja2 template renderer with Core Automation integration.

    Provides comprehensive template rendering capabilities for CloudFormation templates,
    configuration files, and other text-based resources. Integrates seamlessly with
    Core Automation's deployment context and custom filters.

    The renderer supports multiple template sources and output formats:
    - File system-based templates for development and structured projects
    - Dictionary-based templates for dynamic or embedded scenarios
    - String rendering for simple template operations
    - Object rendering for complex data structure templating
    - Batch file rendering for entire template directories

    All rendering operations include Core Automation's custom Jinja2 filters for
    AWS resource management, security rules, networking, and deployment context.
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
        """Initialize the Jinja2 renderer with template source configuration.

        Creates a Jinja2 environment with Core Automation filters and strict
        undefined variable handling. Templates can be loaded from either a
        file system directory or a dictionary of template strings.

        Args:
            template_path: Path to directory containing template files. If provided,
                          templates are loaded from the file system using relative paths.
            dictionary: Dictionary mapping template names to template strings. Used
                       when templates are embedded or generated dynamically.

        Note:
            Exactly one of template_path or dictionary must be provided. The renderer
            cannot be initialized with both or neither source types.
        """
        self.template_path = template_path
        self.dictionary = dictionary

        loader: jinja2.BaseLoader
        if template_path is not None:
            loader = jinja2.FileSystemLoader(template_path)
        else:
            loader = jinja2.DictLoader(dictionary)

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
        """Render a Jinja2 template string using the provided context.

        Processes a template string directly without loading from file system
        or dictionary sources. Useful for dynamic template generation and
        simple string templating operations.

        Args:
            string: Jinja2 template string containing variables and expressions
                   to be rendered.
            context: Dictionary of variables and values to substitute in the
                    template during rendering.

        Returns:
            Rendered string with all template variables and expressions resolved.
        """
        return self.env.from_string(string).render(context)

    def render_object(
        self, data: list[Any] | dict[str, Any] | str, context: dict[str, Any]
    ) -> list[Any] | dict[str, Any] | str:
        """Render a Python object (list, dict, or string) using the provided context.

        Recursively processes complex data structures to render embedded template
        strings while preserving the overall structure. Handles nested dictionaries,
        lists, and string values that may contain Jinja2 template syntax.

        Args:
            data: Python object to render. Can be:
                 - str: Rendered directly as template string
                 - list: Each element rendered recursively
                 - dict: Converted to JSON, rendered, then parsed back
            context: Dictionary of variables for template rendering.

        Returns:
            Rendered object with same structure as input but with all template
            strings resolved using the provided context.

        Raises:
            TypeError: If data type is not supported for rendering.
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
        """Render a JSON string using the Jinja2 environment.

        Processes JSON strings that may contain Jinja2 template syntax by
        rendering the JSON as a template string and then parsing the result
        back to a Python dictionary.

        Args:
            json_data: JSON string that may contain Jinja2 template variables
                      and expressions.
            context: Dictionary of variables for template rendering.

        Returns:
            Parsed dictionary from rendered JSON, or None if JSON parsing fails
            after template rendering.
        """
        try:
            return json.loads(self.render_string(json.dumps(json_data), context))
        except json.JSONDecodeError:
            return None

    def render_file(self, filename: str, context: dict[str, Any]) -> str:
        """Render a template file using the Jinja2 environment.

        Loads and renders a single template file using the configured template
        source (file system or dictionary). The filename interpretation depends
        on the renderer initialization method.

        Args:
            filename: Template identifier for rendering:
                     - File system mode: Relative path from template_path
                     - Dictionary mode: Key in the template dictionary
            context: Dictionary of variables and values for template rendering.

        Returns:
            Rendered template content as a string with all variables and
            expressions resolved.

        Raises:
            jinja2.TemplateNotFound: If the specified template cannot be found.
        """
        template = self.env.get_template(filename)
        return template.render(context)

    def render_files(self, path: str, context: dict[str, Any]) -> dict[str, str]:
        """Render all Jinja2 templates in the specified path using the provided context.

        Recursively processes all files in a directory tree, rendering each file
        as a Jinja2 template. Only works with file system-based template loading.
        Handles cross-platform path separators for consistent operation.

        Args:
            path: Relative path from template_path to the directory containing
                 templates to render. Use empty string for template_path root.
            context: Dictionary of variables for template rendering across all files.

        Returns:
            Dictionary mapping relative file paths to rendered content strings.
            Paths use forward slashes regardless of platform for consistency.

        Note:
            Only regular files are processed; directories and special files are
            skipped. Files are processed recursively through subdirectories.
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
