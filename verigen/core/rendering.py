"""Jinja2 environment construction and output rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2 import TemplateError

from verigen.core.errors import GenerationError
from verigen.core.extensions import ExtensionRegistry
from verigen.filters import builtin_filters, builtin_globals


@dataclass
class OutputFile:
    """A rendered file: a destination path (relative to the output dir) and content."""

    relative_path: str
    content: str


def make_environment(
    base_dir: Path,
    registry: Optional[ExtensionRegistry] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Environment:
    """Build the Jinja2 environment used to render a definition's templates.

    Configured for code generation, not HTML: ``StrictUndefined`` (a typo'd
    variable fails loudly), ``autoescape=False``, and whitespace control on.
    Built-in filters/globals are always present; an extension can add more.
    """
    env = Environment(
        loader=FileSystemLoader(str(base_dir)),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters.update(builtin_filters())
    env.globals.update(builtin_globals())
    if meta is not None:
        env.globals["verigen"] = meta
    if registry is not None:
        env.filters.update(registry.filters)
        env.globals.update(registry.globals)
    return env


def render_outputs(
    definition, context: Dict[str, Any], env: Environment
) -> List[OutputFile]:
    """Render every output declared by ``definition`` into in-memory files.

    Both the destination path and the template body are rendered with ``context``,
    so destinations can be templated (e.g. ``{{ module_name }}.sv``).

    Raises:
        GenerationError: A template is missing or fails to render.
    """
    outputs: List[OutputFile] = []
    for spec in definition.outputs:
        try:
            relative_path = env.from_string(spec.destination).render(context)
        except TemplateError as exc:
            raise GenerationError(
                f"could not render destination {spec.destination!r}: {exc}"
            ) from exc
        try:
            template = env.get_template(spec.template)
            content = template.render(context)
        except TemplateError as exc:
            raise GenerationError(
                f"could not render template {spec.template!r}: {exc}"
            ) from exc
        outputs.append(OutputFile(relative_path=relative_path.strip(), content=content))
    return outputs
