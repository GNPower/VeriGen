"""Shared pytest fixtures and helpers for the VeriGen test suite."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Resolve examples from the source tree (which includes the expected/ goldens),
# independent of where the package is installed.
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "verigen" / "examples"


@pytest.fixture
def examples_dir() -> Path:
    return EXAMPLES_DIR


def example_names() -> list[str]:
    return sorted(p.name for p in EXAMPLES_DIR.iterdir() if (p / "definition.yaml").is_file())


def load_example_values(name: str) -> dict:
    path = EXAMPLES_DIR / name / "values.example.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
