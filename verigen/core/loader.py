"""Load and validate generator-definition files from disk."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import yaml
from pydantic import ValidationError as PydanticValidationError

from verigen.core.definition import GeneratorDefinition
from verigen.core.errors import DefinitionError


def _format_pydantic_errors(exc: PydanticValidationError) -> str:
    lines = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", ())) or "<root>"
        lines.append(f"  - {loc}: {err.get('msg', 'invalid')}")
    return "\n".join(lines)


def load_definition(path: Union[str, Path]) -> GeneratorDefinition:
    """Read, parse, and validate a generator-definition file.

    Args:
        path: Path to the definition YAML file.

    Returns:
        A validated :class:`GeneratorDefinition` with its source path attached.

    Raises:
        DefinitionError: The file is missing, is not valid YAML, is not a mapping,
            or violates the definition schema.
    """
    source = Path(path)
    try:
        raw_text = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DefinitionError("definition file not found", str(source)) from exc
    except OSError as exc:
        raise DefinitionError(f"could not read definition file: {exc}", str(source)) from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise DefinitionError(f"invalid YAML: {exc}", str(source)) from exc

    if not isinstance(data, dict):
        raise DefinitionError("definition must be a YAML mapping at the top level", str(source))

    try:
        definition = GeneratorDefinition.model_validate(data)
    except PydanticValidationError as exc:
        raise DefinitionError(
            "definition does not match the expected format:\n"
            + _format_pydantic_errors(exc),
            str(source),
        ) from exc

    definition._set_source(source)
    return definition
