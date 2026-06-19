"""Validate and normalize a values config against a generator definition.

A *values config* is a plain ``{variable_id: value}`` mapping (from a YAML file
in CLI mode, or collected from widgets in the UI). This module checks it against
the variable contract the definition declares and returns a cleaned, type-coerced
mapping ready for rendering. The same path is used by the CLI and the UI.
"""

from __future__ import annotations

from typing import Any, Dict, List

from verigen.core.errors import ValidationError

_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    return None  # signal failure to caller


def _coerce_int(value: Any) -> Any:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return int(text, 0) if text.lower().startswith(("0x", "0b", "0o")) else int(text)
    except (ValueError, TypeError):
        pass
    # Accept integral float strings such as "8.0" (e.g. from a web number input).
    try:
        as_float = float(text)
    except (ValueError, TypeError):
        return None
    return int(as_float) if as_float.is_integer() else None


def _coerce_float(value: Any) -> Any:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def _coerce_scalar(elem, value: Any, label: str, errors: List[str]) -> Any:
    """Coerce/validate one scalar value; append a message to ``errors`` on failure."""
    etype = elem.type
    if etype in ("string", "text"):
        return str(value)
    if etype == "float":
        coerced = _coerce_float(value)
        if coerced is None:
            errors.append(f"{label}: expected a number, got {value!r}")
            return elem.default
        if not (elem.min <= coerced <= elem.max):
            errors.append(
                f"{label}: value {coerced} is outside [{elem.min}, {elem.max}]"
            )
        return coerced
    if etype == "boolean":
        coerced = _coerce_bool(value)
        if coerced is None:
            errors.append(f"{label}: expected a boolean, got {value!r}")
            return elem.default
        return coerced
    if etype == "integer":
        coerced = _coerce_int(value)
        if coerced is None:
            errors.append(f"{label}: expected an integer, got {value!r}")
            return elem.default
        if not (elem.min <= coerced <= elem.max):
            errors.append(
                f"{label}: value {coerced} is outside [{elem.min}, {elem.max}]"
            )
        return coerced
    if etype == "choice":
        if value in elem.options:
            return value
        if all(isinstance(o, int) for o in elem.options):
            coerced = _coerce_int(value)
            if coerced in elem.options:
                return coerced
        errors.append(
            f"{label}: value {value!r} is not one of {elem.options}"
        )
        return elem.default
    errors.append(f"{label}: unsupported element type {etype!r}")
    return value


def _scalar_default(elem):
    if elem.type == "boolean":
        return bool(elem.default)
    return elem.default


def normalize_values(definition, values: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ``values`` against ``definition`` and return a clean mapping.

    Missing variables fall back to their declared default; a variable with no
    default is required. Unknown keys (other than directory selectors) are an
    error. Every problem found is reported together.

    Raises:
        ValidationError: One or more variables are missing, out of range, of the
            wrong type, or not declared.
    """
    if not isinstance(values, dict):
        raise ValidationError(["values config must be a mapping of variable to value"])

    errors: List[str] = []
    result: Dict[str, Any] = {}

    value_elems = {e.id: e for e in definition.value_elements()}
    ignore_ids = set()
    selector_id = definition.directory_selector_id()
    if selector_id:
        ignore_ids.add(selector_id)

    # Unknown keys.
    for key in values:
        if key not in value_elems and key not in ignore_ids:
            errors.append(f"{key!r} is not a variable declared by this generator")

    for vid, elem in value_elems.items():
        present = vid in values
        label = elem.label or vid if hasattr(elem, "label") else vid

        if elem.type == "dynamic_table":
            rows = values.get(vid, [])
            if not present:
                result[vid] = []
                continue
            if not isinstance(rows, list):
                errors.append(f"{label}: expected a list of rows, got {type(rows).__name__}")
                result[vid] = []
                continue
            sub_by_id = {s.id: s for s in elem.sub_elements}
            norm_rows = []
            for i, row in enumerate(rows):
                if not isinstance(row, dict):
                    errors.append(f"{label}[{i}]: each row must be a mapping")
                    continue
                norm_row = {}
                for unknown in set(row) - set(sub_by_id):
                    errors.append(f"{label}[{i}]: {unknown!r} is not a column of this table")
                for sid, sub in sub_by_id.items():
                    rlabel = f"{label}[{i}].{sid}"
                    if sid in row:
                        norm_row[sid] = _coerce_scalar(sub, row[sid], rlabel, errors)
                    elif _scalar_default(sub) is not None or sub.type == "boolean":
                        norm_row[sid] = _scalar_default(sub)
                    else:
                        errors.append(f"{rlabel}: required value is missing")
                norm_rows.append(norm_row)
            result[vid] = norm_rows
            continue

        # Scalar element.
        if present:
            result[vid] = _coerce_scalar(elem, values[vid], label, errors)
        elif _scalar_default(elem) is not None or elem.type == "boolean":
            result[vid] = _scalar_default(elem)
        else:
            errors.append(f"{label}: required value is missing")

    if errors:
        raise ValidationError(errors, source=str(definition.source_path or definition.id))
    return result


def default_values(definition) -> Dict[str, Any]:
    """Return a values mapping using every variable's declared default.

    Variables without a default get a neutral placeholder (empty string / zero /
    first option / empty list) so a partially-specified config can still render.
    """
    out: Dict[str, Any] = {}
    for elem in definition.value_elements():
        if elem.type == "dynamic_table":
            out[elem.id] = []
        elif elem.type == "boolean":
            out[elem.id] = bool(elem.default)
        elif elem.default is not None:
            out[elem.id] = elem.default
        elif elem.type in ("integer", "float"):
            out[elem.id] = elem.min
        elif elem.type == "choice":
            out[elem.id] = elem.options[0]
        else:
            out[elem.id] = ""
    return out
