"""Tests for the JSON Schema export and its CLI command."""

import json

from verigen.cli.main import main
from verigen.core.definition import GeneratorDefinition


def test_model_json_schema_shape():
    schema = GeneratorDefinition.model_json_schema()
    assert "$defs" in schema
    assert "pages" in schema["properties"]
    assert "outputs" in schema["properties"]
    # The new scalar types are part of the schema.
    assert "FloatVar" in schema["$defs"]
    assert "TextVar" in schema["$defs"]


def test_cli_schema_writes_file(tmp_path):
    out = tmp_path / "schema.json"
    assert main(["schema", "-o", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["properties"]["outputs"]
