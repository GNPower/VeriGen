"""Pure helpers for the web UI, kept free of NiceGUI so they are unit-testable."""

from __future__ import annotations

import io
import zipfile
from typing import Any, Dict, List

import yaml


def zip_outputs(outputs) -> bytes:
    """Pack rendered :class:`OutputFile` objects into a zip archive (bytes)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for output in outputs:
            archive.writestr(output.relative_path, output.content)
    return buffer.getvalue()


def values_yaml(values: Dict[str, Any]) -> str:
    """Serialize a values mapping to YAML for download."""
    return yaml.safe_dump(values, default_flow_style=False, sort_keys=False)


def aggrid_column_defs(table_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build AG Grid column definitions from a ``dynamic_table`` element config."""
    columns: List[Dict[str, Any]] = []
    for index, sub in enumerate(table_config.get("sub_elements", [])):
        column = {
            "headerName": sub.get("label") or sub["id"],
            "field": sub["id"],
            "editable": True,
            "flex": 1,
        }
        if index == 0:
            column["checkboxSelection"] = True
            column["headerCheckboxSelection"] = True
        columns.append(column)
    return columns


def table_row_default(table_config: Dict[str, Any]) -> Dict[str, Any]:
    """A blank row for a ``dynamic_table``, using each column's default."""
    row: Dict[str, Any] = {}
    for sub in table_config.get("sub_elements", []):
        stype = sub.get("type")
        if stype == "boolean":
            row[sub["id"]] = bool(sub.get("default") or False)
        elif sub.get("default") is not None:
            row[sub["id"]] = sub["default"]
        elif stype in ("integer", "float"):
            row[sub["id"]] = sub.get("min", 0)
        elif stype == "choice":
            row[sub["id"]] = sub.get("options", [""])[0]
        else:
            row[sub["id"]] = ""
    return row


def merge_values(scalar_values: Dict[str, Any], table_values: Dict[str, Any]) -> Dict[str, Any]:
    """Combine scalar inputs and table rows into one values mapping."""
    return {**scalar_values, **table_values}
