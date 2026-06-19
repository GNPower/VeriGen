"""Smoke tests for the verigen package surface."""

import verigen


def test_version_present():
    assert isinstance(verigen.__version__, str)
    assert verigen.__version__


def test_public_api_exports():
    for name in ("generate", "render", "load_definition", "VeriGenError"):
        assert hasattr(verigen, name)
