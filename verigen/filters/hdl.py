"""Generic HDL-flavored number and bit-math filters for templates.

None of these encode any specific IP. They are the arithmetic helpers any
Verilog/SystemVerilog generator reaches for (widths, masks, literals).
"""

from __future__ import annotations

from typing import Callable, Dict


def _as_int(value) -> int:
    """Coerce ints and common string forms (``"0x1F"``, ``"42"``) to ``int``."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text, 0) if text.lower().startswith(("0x", "0b", "0o")) else int(text)


def clog2(value) -> int:
    """Ceiling of log2: the number of address bits needed to index ``value`` items.

    ``clog2(1) == 0``, ``clog2(2) == 1``, ``clog2(4) == 2``, ``clog2(5) == 3``.
    """
    n = _as_int(value)
    if n <= 1:
        return 0
    return (n - 1).bit_length()


def mask(width) -> int:
    """All-ones value ``(1 << width) - 1`` for a field of ``width`` bits."""
    w = _as_int(width)
    return (1 << w) - 1 if w > 0 else 0


def to_hex(value, digits=None) -> str:
    """Hex digits (no ``0x``), uppercase, zero-padded to ``digits`` if given."""
    n = _as_int(value)
    text = format(n, "X")
    if digits is not None:
        text = text.rjust(int(digits), "0")
    return text


def to_bin(value, width=None) -> str:
    """Binary digits (no ``0b``), zero-padded to ``width`` bits if given."""
    n = _as_int(value)
    text = format(n, "b")
    if width is not None:
        text = text.rjust(int(width), "0")
    return text


def sv_hex(value, width) -> str:
    """A sized SystemVerilog hex literal, e.g. ``sv_hex(15, 8)`` -> ``8'h0F``."""
    w = _as_int(width)
    digits = (w + 3) // 4
    return f"{w}'h{to_hex(value, digits)}"


def bits(hi, lo=None) -> str:
    """A bit-range string: ``bits(7)`` -> ``[7]``; ``bits(7, 0)`` -> ``[7:0]``."""
    if lo is None:
        return f"[{_as_int(hi)}]"
    return f"[{_as_int(hi)}:{_as_int(lo)}]"


FILTERS: Dict[str, Callable] = {
    "clog2": clog2,
    "mask": mask,
    "to_hex": to_hex,
    "to_bin": to_bin,
    "sv_hex": sv_hex,
    "bits": bits,
}

# Also expose clog2/mask as callable globals so templates can write clog2(x).
GLOBALS: Dict[str, Callable] = {
    "clog2": clog2,
    "mask": mask,
}
