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

from typing import Any, List, Dict, Set

import jinja2
from jinja2 import meta
import os
import pathlib
import json

from jinja2.utils import internalcode

import core_logging as log

from .filters import load_filters

from jinja2 import UndefinedError, StrictUndefined, Undefined, TemplateError, ChainableUndefined


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

    errors: List[Dict[str, str]] = []

    current_template = ""

    def collect_error(self, message: str) -> None:
        """Whether to collect undefined variable errors during rendering."""
        self.errors.append({"template": self.current_template, "message": message})

    def get_collector(self) -> Type[Undefined]:
        """Retrieve collected errors and reset the collector."""

        def collect_message(message: str):
            """
            Collects an undefined variable error message using the parent renderer's collect_error method.
            """
            # Attempt to get the variable name and context for error reporting
            message = f"Undefined variable: {message}"
            # Try to call the parent renderer's collect_error if available
            renderer = getattr(self, "_renderer", None)
            if renderer is not None and hasattr(renderer, "collect_error"):
                renderer.collect_error(message)

        class CollectingUndefined(Undefined):  # type: ignore
            __slots__ = ("errors",)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.errors = []

            def _fail_with_undefined_error(self, *args: Any, **kwargs: Any) -> "NoReturn":  # type: ignore
                try:
                    super()._fail_with_undefined_error(*args, **kwargs)
                except self._undefined_exception as e:
                    collect_message("Template variable error: %s", e)  # type: ignore
                    raise e

            def __getattr__(self, name):
                self.errors.append(f"Undefined variable: {name}")
                return super().__getattr__(name)

            def __str__(self):
                return "{{ UNDEFINED }}"

            def __iter__(self) -> Iterator[Any]:
                collect_message("<iter>")
                return super().__iter__()  # type: ignore

            def __bool__(self) -> bool:
                collect_message("<bool>")
                return super().__bool__()  # type: ignore

        return CollectingUndefined

    def __init__(
        self,
        template_path: str | None = None,
        dictionary: Dict[str, str] | None = None,
        collect_errors: Dict[str, List[str]] | None = None,
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
        self.collect_errors = collect_errors
        self.template_path = template_path or ''
        self.dictionary = dictionary or {}

        if collect_errors is not None:
            self.errors = []

        loader: jinja2.BaseLoader | None = None
        if template_path is not None:
            loader = jinja2.FileSystemLoader(self.template_path)
        else:
            loader = jinja2.DictLoader(self.dictionary)

        self.env = jinja2.Environment(
            loader=loader,
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=True,
            undefined=ChainableUndefined,
        )

        load_filters(self.env)

    # --- Analysis helpers -------------------------------------------------

    def _make_tracking_undefined(self, collector: List[Dict[str, Any]]):
        """Create a ChainableUndefined subclass that records undefined usage.

        The returned class does not raise on access; it records a path of
        attribute/item lookups and operations into the provided collector.
        """

        class TrackingUndefined(ChainableUndefined):  # type: ignore
            __slots__ = ("_path",)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._path: List[Any] = []
                # Record the initial undefined creation (root variable or missing attr/item)
                self._record(
                    kind="name",
                    segment=getattr(self, "_undefined_name", None),
                    obj=getattr(self, "_undefined_obj", None),
                    hint=getattr(self, "_undefined_hint", None),
                )

            def _record(self, kind: str, segment: Any, obj: Any, hint: Any) -> None:
                base = getattr(self, "_undefined_name", None) or segment or "<unknown>"
                parts = [str(base)] + [str(p) for p in self._path]
                path = ".".join(parts)
                entry: Dict[str, Any] = {
                    "path": path,
                    "kind": kind,
                    "object_type": type(obj).__name__ if obj is not None else None,
                    "hint": hint,
                }
                collector.append(entry)

            def __getattr__(self, name: str):  # type: ignore[override]
                if name[:2] == "__" and name[-2:] == "__":
                    raise AttributeError(name)
                self._path.append(name)
                self._record("attr", name, getattr(self, "_undefined_obj", None), None)
                return self

            def __getitem__(self, key: Any):  # type: ignore[override]
                self._path.append(key)
                self._record("item", key, getattr(self, "_undefined_obj", None), None)
                return self

            def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
                self._record("call", "()", getattr(self, "_undefined_obj", None), None)
                return self

            # Be permissive to avoid aborting analysis
            def __str__(self) -> str:  # type: ignore[override]
                return ""

            def __iter__(self):  # type: ignore[override]
                return iter(())

            def __bool__(self) -> bool:  # type: ignore[override]
                return False

            def __int__(self) -> int:  # type: ignore[override]
                return 0

            def __float__(self) -> float:  # type: ignore[override]
                return 0.0

            # Swallow operations that would otherwise raise
            def _fail_with_undefined_error(self, *args, **kwargs):  # type: ignore[override]
                # Record that an operation was attempted, then keep flowing
                self._record("op", "<op>", getattr(self, "_undefined_obj", None), getattr(self, "_undefined_hint", None))
                return self

        return TrackingUndefined

    def analyze_string(self, string: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze a template string for undefined usage without raising.

        Returns a dict with: rendered, undefined (list of dicts), undeclared (list).
        """
        # Static pass: find undeclared variable roots
        ast = self.env.parse(string)
        undeclared: Set[str] = set(meta.find_undeclared_variables(ast))

        # Dynamic pass: track nested misses via a tracking undefined
        collector: List[Dict[str, Any]] = []
        Tracking = self._make_tracking_undefined(collector)
        env2 = self.env.overlay(undefined=Tracking)
        tmpl = env2.from_string(string)
        tmpl.name = "<string>"
        rendered = tmpl.render(context)

        # Deduplicate by path while preserving order
        seen: Set[str] = set()
        uniq: List[Dict[str, Any]] = []
        for e in collector:
            p = e.get("path")
            if p in seen:
                continue
            seen.add(p)
            uniq.append(e)

        return {"rendered": rendered, "undefined": uniq, "undeclared": sorted(undeclared)}

    def analyze_file(self, filename: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze a template file for undefined usage without raising.

        Returns a dict with: rendered, undefined (list of dicts), undeclared (list).
        """
        # Load raw source for static analysis
        if self.env.loader is None:
            raise ValueError("Environment has no loader; cannot analyze file.")
        src, _, _ = self.env.loader.get_source(self.env, filename)
        ast = self.env.parse(src)
        undeclared: Set[str] = set(meta.find_undeclared_variables(ast))

        # Dynamic pass
        collector: List[Dict[str, Any]] = []
        Tracking = self._make_tracking_undefined(collector)
        env2 = self.env.overlay(undefined=Tracking)
        template = env2.get_template(filename)
        rendered = template.render(context)

        seen: Set[str] = set()
        uniq: List[Dict[str, Any]] = []
        for e in collector:
            p = e.get("path")
            if p in seen:
                continue
            seen.add(p)
            uniq.append(e)

        return {"rendered": rendered, "undefined": uniq, "undeclared": sorted(undeclared)}

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
        try:
            tmpl = self.env.from_string(string)
            # Help Jinja include a name in tracebacks for string templates
            tmpl.name = "<string>"
            return tmpl.render(context)
        except UndefinedError:
            # Preserve custom VerboseUndefined message
            raise
        except TemplateError:
            # Other template-related errors already include location
            raise
        except Exception:
            # Non-template errors: let Jinja format traceback
            raise self.env.handle_exception()

    def render_object(self, data: list[Any] | dict[str, Any] | str, context: dict[str, Any]) -> Any:
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
            rendered_json: dict | None = self.render_json(data, context)
            if rendered_json is not None:
                return rendered_json
            return {}

        else:
            raise TypeError("Unsupported data type for rendering: {}".format(type(data)))

    def render_json(self, json_data: str | dict, context: dict[str, Any]) -> dict | None:
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
            if json_data is None:
                return None
            if isinstance(json_data, dict):
                json_data = json.dumps(json_data, indent=2)
            return json.loads(self.render_string(json_data, context))
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
        try:
            template = self.env.get_template(filename)
            return template.render(context)
        except UndefinedError:
            # Preserve custom VerboseUndefined message
            raise
        except TemplateError:
            # Jinja provides file/line info for template errors
            raise
        except Exception:
            # Non-template errors: let Jinja format traceback
            raise self.env.handle_exception()

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
            log.debug("Rendering file '{}' with short_path '{}'", renderer_path, short_path)

            rendered_template = self.render_file(renderer_path, context)

            # Save the rendered file into our dictionary
            files[short_path] = rendered_template

        return files
