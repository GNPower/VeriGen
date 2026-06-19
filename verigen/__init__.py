"""VeriGen: a general, config-driven Verilog/SystemVerilog code generator.

VeriGen renders Jinja2 templates from a *generator definition* (which also
declares the wizard UI and the variable contract) and a *values config*. It
contains no logic specific to any IP; authors supply their own templates,
config, and optional Python extension hooks.
"""

__author__ = "GNPower"
__email__ = "powerg@mcmaster.ca"
__version__ = "0.1.0"

from verigen.core.errors import (
    DefinitionError,
    ExtensionError,
    GenerationError,
    ValidationError,
    VeriGenError,
)
from verigen.core.pipeline import generate, load_definition, render

__all__ = [
    "__version__",
    "generate",
    "render",
    "load_definition",
    "VeriGenError",
    "DefinitionError",
    "ValidationError",
    "ExtensionError",
    "GenerationError",
]
