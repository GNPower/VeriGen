"""Discover generator definitions on disk so VeriGen can present a catalog.

A definition is recognized by filename: ``definition.yaml`` or ``*.verigen.yaml``.
Search paths may be individual files or directories (searched recursively).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Union

from verigen.core.errors import DefinitionError
from verigen.core.loader import load_definition

_GLOBS = ("definition.yaml", "*.verigen.yaml")


def builtin_examples_dir() -> Path:
    """Return the directory of examples shipped inside the package."""
    return Path(__file__).resolve().parent.parent / "examples"


@dataclass
class CatalogEntry:
    """One discovered definition (valid or not)."""

    path: Path
    id: Optional[str] = None
    name: Optional[str] = None
    description: str = ""
    category: str = "General"
    error: Optional[str] = None

    @property
    def valid(self) -> bool:
        return self.error is None


def _candidate_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    found: List[Path] = []
    for pattern in _GLOBS:
        try:
            found.extend(sorted(path.rglob(pattern)))
        except OSError:
            # Skip directory trees we cannot read rather than aborting discovery.
            continue
    # De-duplicate while preserving order.
    seen = set()
    unique = []
    for f in found:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def discover(paths: Iterable[Union[str, Path]]) -> List[CatalogEntry]:
    """Return a catalog entry for every definition found under ``paths``.

    Invalid definitions are included with their ``error`` set rather than dropped,
    so a UI/CLI can show them and explain why.
    """
    entries: List[CatalogEntry] = []
    for raw in paths:
        for candidate in _candidate_files(Path(raw)):
            try:
                defn = load_definition(candidate)
                entries.append(
                    CatalogEntry(
                        path=candidate,
                        id=defn.id,
                        name=defn.name,
                        description=defn.description,
                        category=defn.category,
                    )
                )
            except DefinitionError as exc:
                entries.append(CatalogEntry(path=candidate, error=str(exc)))
    return entries
