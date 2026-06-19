"""Tests for catalog discovery."""

from conftest import EXAMPLES_DIR, example_names

from verigen.core import catalog


def test_discovers_all_examples():
    entries = catalog.discover([EXAMPLES_DIR])
    found_ids = {e.id for e in entries if e.valid}
    for name in example_names():
        assert name in found_ids


def test_all_discovered_examples_are_valid():
    entries = catalog.discover([EXAMPLES_DIR])
    assert entries
    assert all(e.valid for e in entries), [e.error for e in entries if not e.valid]
