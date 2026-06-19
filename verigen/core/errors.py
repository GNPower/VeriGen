"""Error hierarchy for VeriGen.

Every failure the engine raises derives from :class:`VeriGenError`, so a host
(CLI or UI) can catch one type and print a clean message instead of a traceback.
"""

from __future__ import annotations

from typing import List, Optional


class VeriGenError(Exception):
    """Base class for all errors raised by VeriGen."""


class DefinitionError(VeriGenError):
    """A generator definition file is missing, malformed, or self-inconsistent.

    Args:
        message: Human-readable description of the problem.
        source: Path to the definition file the problem was found in, if known.
    """

    def __init__(self, message: str, source: Optional[str] = None) -> None:
        self.source = source
        if source:
            message = f"{source}: {message}"
        super().__init__(message)


class ValidationError(VeriGenError):
    """A values config does not satisfy a definition's variable contract.

    Aggregates every problem found so the user sees them all at once rather than
    one per run.
    """

    def __init__(self, errors: List[str], source: Optional[str] = None) -> None:
        self.errors = list(errors)
        self.source = source
        header = "Configuration is invalid. The following issues were found:"
        if source:
            header = f"{source}: {header}"
        body = "\n".join(f"  - {e}" for e in self.errors)
        super().__init__(f"{header}\n{body}")


class ExtensionError(VeriGenError):
    """An optional Python extension module failed to load or register."""


class GenerationError(VeriGenError):
    """Rendering or writing an output file failed."""
