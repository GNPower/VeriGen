"""Tests for the UI's pure helpers (no NiceGUI required)."""

import io
import zipfile

import yaml

from verigen.core.rendering import OutputFile
from verigen.ui import forms


def test_zip_outputs_roundtrip():
    outputs = [
        OutputFile("a.sv", "module a; endmodule\n"),
        OutputFile("sub/b.sv", "content b"),
    ]
    data = forms.zip_outputs(outputs)
    archive = zipfile.ZipFile(io.BytesIO(data))
    assert set(archive.namelist()) == {"a.sv", "sub/b.sv"}
    assert archive.read("a.sv").decode() == "module a; endmodule\n"


def test_aggrid_column_defs():
    config = {
        "sub_elements": [
            {"id": "name", "label": "Signal", "type": "string"},
            {"id": "w", "type": "integer"},
        ]
    }
    cols = forms.aggrid_column_defs(config)
    assert cols[0]["field"] == "name"
    assert cols[0]["headerName"] == "Signal"
    assert cols[0]["checkboxSelection"] is True
    assert cols[1]["field"] == "w"
    assert "checkboxSelection" not in cols[1]


def test_table_row_default():
    config = {
        "sub_elements": [
            {"id": "name", "type": "string"},
            {"id": "w", "type": "integer", "min": 1},
            {"id": "on", "type": "boolean", "default": True},
        ]
    }
    assert forms.table_row_default(config) == {"name": "", "w": 1, "on": True}


def test_values_yaml_roundtrip():
    text = forms.values_yaml({"a": 1, "b": "x"})
    assert yaml.safe_load(text) == {"a": 1, "b": "x"}


def test_merge_values():
    assert forms.merge_values({"a": 1}, {"t": [{"x": 1}]}) == {"a": 1, "t": [{"x": 1}]}
