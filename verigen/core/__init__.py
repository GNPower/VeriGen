"""Headless core of the VeriGen code-generation engine.

The core knows nothing about the CLI or any UI. Its public surface is the
generation pipeline plus the definition models and error types.
"""

from verigen.core.errors import (
    DefinitionError,
    ExtensionError,
    GenerationError,
    ValidationError,
    VeriGenError,
)

__all__ = [
    "DefinitionError",
    "ExtensionError",
    "GenerationError",
    "ValidationError",
    "VeriGenError",
]
