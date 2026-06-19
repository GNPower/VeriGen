"""Built-in Jinja2 filters and globals shipped with VeriGen.

These are generic code-generation helpers (string casing, number formatting,
bit math). Nothing here is specific to any IP. A generator definition can add
more via an optional Python extension module; see :mod:`verigen.core.extensions`.
"""

from __future__ import annotations

from typing import Callable, Dict

from verigen.filters import hdl, text


def builtin_filters() -> Dict[str, Callable]:
    """Return the mapping of filter name to callable for the Jinja2 environment."""
    merged: Dict[str, Callable] = {}
    merged.update(text.FILTERS)
    merged.update(hdl.FILTERS)
    return merged


def builtin_globals() -> Dict[str, Callable]:
    """Return the mapping of global name to callable for the Jinja2 environment."""
    merged: Dict[str, Callable] = {}
    merged.update(getattr(text, "GLOBALS", {}))
    merged.update(getattr(hdl, "GLOBALS", {}))
    return merged


__all__ = ["builtin_filters", "builtin_globals"]
