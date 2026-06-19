"""Tests for the optional Python extension hook API."""

import pytest

from conftest import EXAMPLES_DIR, load_example_values

from verigen.core.errors import ValidationError
from verigen.core.pipeline import render

EXT_DEF = EXAMPLES_DIR / "extension_demo" / "definition.yaml"


def test_extension_filter_and_context_render():
    outputs, values = render(EXT_DEF, load_example_values("extension_demo"))
    content = outputs[0].content
    # Custom filter applied: "depth" | shout -> "DEPTH!"
    assert "DEPTH!" in content
    # Derived context: addr_width = clog2(64) = 6
    assert "ADDR_WIDTH = 6" in content


def test_extension_validator_rejects_bad_value():
    bad = dict(load_example_values("extension_demo"))
    bad["depth"] = 63  # not a power of two
    with pytest.raises(ValidationError) as exc:
        render(EXT_DEF, bad)
    assert any("power of two" in e for e in exc.value.errors)
