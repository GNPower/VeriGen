"""Tests for loading and validating generator definitions."""

import pytest

from conftest import EXAMPLES_DIR, example_names

from verigen.core.errors import DefinitionError
from verigen.core.loader import load_definition


@pytest.mark.parametrize("name", example_names())
def test_examples_load(name):
    defn = load_definition(EXAMPLES_DIR / name / "definition.yaml")
    assert defn.id == name
    assert defn.base_dir == (EXAMPLES_DIR / name)
    assert defn.outputs


def test_missing_file_raises(tmp_path):
    with pytest.raises(DefinitionError):
        load_definition(tmp_path / "nope.yaml")


def test_top_level_not_mapping(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(DefinitionError):
        load_definition(p)


def test_invalid_yaml(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text("foo: [unclosed\n", encoding="utf-8")
    with pytest.raises(DefinitionError):
        load_definition(p)


def test_unknown_key_rejected(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text(
        "id: t\nname: T\nbogus_key: 1\n"
        "pages:\n  - elements:\n      - {type: string, id: a}\n"
        "outputs:\n  - {template: t.j2, destination: x}\n",
        encoding="utf-8",
    )
    with pytest.raises(DefinitionError):
        load_definition(p)


def test_duplicate_variable_ids_rejected(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text(
        "id: t\nname: T\n"
        "pages:\n  - elements:\n"
        "      - {type: string, id: dup}\n"
        "      - {type: integer, id: dup}\n"
        "outputs:\n  - {template: t.j2, destination: x}\n",
        encoding="utf-8",
    )
    with pytest.raises(DefinitionError):
        load_definition(p)


def test_no_outputs_rejected(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text(
        "id: t\nname: T\n"
        "pages:\n  - elements:\n      - {type: string, id: a}\n"
        "outputs: []\n",
        encoding="utf-8",
    )
    with pytest.raises(DefinitionError):
        load_definition(p)
