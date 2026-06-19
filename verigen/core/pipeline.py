"""The VeriGen generation pipeline: the public API shared by the CLI and the UI.

    load_definition -> normalize values -> validate (incl. hooks)
        -> build context (incl. derived) -> render -> write

Neither the CLI nor any UI imports the other; both call into here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from verigen.core.context import build_context
from verigen.core.definition import GeneratorDefinition
from verigen.core.errors import ValidationError
from verigen.core.extensions import ExtensionRegistry, load_extension
from verigen.core.loader import load_definition
from verigen.core.rendering import OutputFile, make_environment, render_outputs

__all__ = ["load_definition", "render", "generate", "OutputFile"]


def _coerce_definition(definition: Union[str, Path, GeneratorDefinition]) -> GeneratorDefinition:
    if isinstance(definition, GeneratorDefinition):
        return definition
    return load_definition(definition)


def _meta(definition: GeneratorDefinition) -> Dict[str, Any]:
    return {
        "name": definition.name,
        "id": definition.id,
        "version": definition.version,
        "description": definition.description,
    }


def _load_registry(definition: GeneratorDefinition) -> Optional[ExtensionRegistry]:
    if not definition.extension:
        return None
    return load_extension(definition.extension, definition.base_dir)


def render(
    definition: Union[str, Path, GeneratorDefinition],
    values: Dict[str, Any],
) -> Tuple[List[OutputFile], Dict[str, Any]]:
    """Validate and render a definition in memory, writing nothing.

    Returns:
        A tuple ``(outputs, normalized_values)``. ``outputs`` are the rendered
        files; ``normalized_values`` is the cleaned values mapping (handy for
        saving a reproducible values config).

    Raises:
        DefinitionError, ValidationError, ExtensionError, GenerationError.
    """
    from verigen.core.values import normalize_values  # local import avoids a cycle

    defn = _coerce_definition(definition)
    registry = _load_registry(defn)

    normalized = normalize_values(defn, values)
    if registry is not None:
        hook_errors = registry.run_validators(normalized, defn)
        if hook_errors:
            raise ValidationError(hook_errors, source=str(defn.source_path or defn.id))

    context = build_context(defn, normalized, registry)
    base_dir = defn.base_dir or Path.cwd()
    env = make_environment(base_dir, registry, meta=_meta(defn))
    outputs = render_outputs(defn, context, env)
    return outputs, normalized


def generate(
    definition: Union[str, Path, GeneratorDefinition],
    values: Dict[str, Any],
    output_dir: Union[str, Path],
    *,
    save_values: bool = False,
    values_filename: Optional[str] = None,
) -> List[Path]:
    """Render a definition and write the results under ``output_dir``.

    Args:
        definition: A definition object or a path to a definition file.
        values: The user's values config.
        output_dir: Directory to write into (created if absent).
        save_values: Also write the normalized values config alongside the output.
        values_filename: Override the saved values filename
            (default ``<id>.values.yaml``).

    Returns:
        The list of written file paths.
    """
    defn = _coerce_definition(definition)
    outputs, normalized = render(defn, values)

    out_root = Path(output_dir)
    written: List[Path] = []
    for output in outputs:
        dest = out_root / output.relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(output.content, encoding="utf-8")
        written.append(dest)

    if save_values:
        name = values_filename or f"{defn.id}.values.yaml"
        values_path = out_root / name
        values_path.parent.mkdir(parents=True, exist_ok=True)
        values_path.write_text(
            yaml.safe_dump(normalized, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        written.append(values_path)

    return written
