"""Lint generated SystemVerilog with an external linter when one is available.

Skips cleanly if neither ``verible-verilog-lint`` nor ``verilator`` is on PATH,
so contributors and CI without the tools still pass.
"""

import shutil
import subprocess

import pytest

from conftest import EXAMPLES_DIR, example_names, load_example_values

from verigen.core.pipeline import generate


def _linter():
    verible = shutil.which("verible-verilog-lint")
    if verible:
        return [verible]
    verilator = shutil.which("verilator")
    if verilator:
        return [verilator, "--lint-only", "-sv"]
    return None


LINTER = _linter()


def _golden_examples():
    return [n for n in example_names() if (EXAMPLES_DIR / n / "expected").is_dir()]


@pytest.mark.skipif(LINTER is None, reason="no SystemVerilog linter on PATH")
@pytest.mark.parametrize("name", _golden_examples())
def test_generated_sv_lints_clean(name, tmp_path):
    written = generate(
        EXAMPLES_DIR / name / "definition.yaml",
        load_example_values(name),
        tmp_path,
    )
    sv_files = [p for p in written if p.suffix == ".sv"]
    assert sv_files, f"{name} produced no .sv files"
    for sv in sv_files:
        result = subprocess.run(
            [*LINTER, str(sv)], capture_output=True, text=True
        )
        assert result.returncode == 0, (
            f"{name}: {sv.name} failed lint:\n{result.stdout}\n{result.stderr}"
        )
