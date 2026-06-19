"""Generic text/identifier filters for templates."""

from __future__ import annotations

import re
from typing import Callable, Dict

_WORD_SPLIT = re.compile(r"[^0-9a-zA-Z]+")


def _words(value: str) -> list[str]:
    """Split an arbitrary string into lowercase word tokens.

    Handles snake_case, kebab-case, spaces, and camelCase/PascalCase boundaries.
    """
    text = str(value)
    # Insert a separator at lower->upper and acronym boundaries before splitting.
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    parts = [p for p in _WORD_SPLIT.split(text) if p]
    return [p.lower() for p in parts]


def snake_case(value: str) -> str:
    """``Some Value`` / ``someValue`` -> ``some_value``."""
    return "_".join(_words(value))


def kebab_case(value: str) -> str:
    """``Some Value`` -> ``some-value``."""
    return "-".join(_words(value))


def camel_case(value: str) -> str:
    """``some value`` -> ``someValue``."""
    parts = _words(value)
    if not parts:
        return ""
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def pascal_case(value: str) -> str:
    """``some value`` -> ``SomeValue``."""
    return "".join(p.capitalize() for p in _words(value))


def upper_case(value: str) -> str:
    """``Some Value`` -> ``SOME_VALUE`` (a SCREAMING_SNAKE constant name)."""
    return "_".join(_words(value)).upper()


def comment_block(value: str, prefix: str = "// ") -> str:
    """Prefix every line of ``value`` with ``prefix`` to form a comment block."""
    lines = str(value).splitlines() or [""]
    return "\n".join(f"{prefix}{line}".rstrip() for line in lines)


def pad(value, width: int, fill: str = " ") -> str:
    """Left-justify ``value`` to ``width`` columns using ``fill``."""
    return str(value).ljust(int(width), fill)


FILTERS: Dict[str, Callable] = {
    "snake_case": snake_case,
    "kebab_case": kebab_case,
    "camel_case": camel_case,
    "pascal_case": pascal_case,
    "upper_case": upper_case,
    "comment_block": comment_block,
    "pad": pad,
}
