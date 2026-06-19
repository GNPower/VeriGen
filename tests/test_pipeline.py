"""End-to-end pipeline tests, including golden-file comparison for examples."""

import pytest

from conftest import EXAMPLES_DIR, example_names, load_example_values

from verigen.core.pipeline import generate, render


def _golden_examples():
    return [n for n in example_names() if (EXAMPLES_DIR / n / "expected").is_dir()]


@pytest.mark.parametrize("name", _golden_examples())
def test_examples_match_golden(name):
    definition = EXAMPLES_DIR / name / "definition.yaml"
    values = load_example_values(name)
    outputs, _ = render(definition, values)
    assert outputs, f"{name} produced no output"
    for output in outputs:
        expected = (EXAMPLES_DIR / name / "expected" / output.relative_path).read_text(
            encoding="utf-8"
        )
        assert output.content == expected, f"{name}: {output.relative_path} drifted from golden"


def test_generate_writes_files(tmp_path):
    name = "synchronizer"
    written = generate(
        EXAMPLES_DIR / name / "definition.yaml",
        load_example_values(name),
        tmp_path,
    )
    assert written
    for path in written:
        assert path.is_file()


def test_generate_save_values(tmp_path):
    name = "synchronizer"
    written = generate(
        EXAMPLES_DIR / name / "definition.yaml",
        load_example_values(name),
        tmp_path,
        save_values=True,
    )
    values_files = [p for p in written if p.name.endswith(".values.yaml")]
    assert len(values_files) == 1
    assert values_files[0].is_file()


def test_destination_is_templated(tmp_path):
    name = "mux"
    written = generate(
        EXAMPLES_DIR / name / "definition.yaml",
        load_example_values(name),
        tmp_path,
    )
    # values.example sets module_name: mux4 -> mux4.sv
    assert any(p.name == "mux4.sv" for p in written)
