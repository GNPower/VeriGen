#!/usr/bin/env python
"""Tests for `verigen` package - basic imports and version."""

import pytest


def test_version():
    """Test that version is accessible."""
    from verigen import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_core_imports():
    """Test that core modules can be imported."""
    from verigen import (
        AttributeDefinition,
        TableDefinition,
        Row,
        Table,
        ParameterDefinition,
        Schema,
        SchemaParser,
        Validator,
        TemplateEngine,
    )
    # All imports should succeed
    assert AttributeDefinition is not None
    assert TableDefinition is not None
    assert Row is not None
    assert Table is not None


def test_gui_imports():
    """Test that GUI modules can be imported (may fail without display)."""
    try:
        from verigen.gui import VeriGenApp, run_gui
        assert VeriGenApp is not None
    except ImportError:
        # GUI imports may fail in headless environments
        pytest.skip("GUI imports not available in this environment")
