"""
VeriGen - A generic code generation tool using Jinja2 templates.

VeriGen allows you to define hierarchical data structures (like registers
with fields) through schema files, and generate code from Jinja2 templates.
"""

__author__ = """GNPower"""
__email__ = "gnpowergithub@gmail.com"
__version__ = "2.0.0"

# Core exports for programmatic use
from .core import (
    # Models
    AttributeDefinition,
    TableDefinition,
    ValidationRule,
    Row,
    Table,
    ParameterDefinition,
    Schema,
    # Schema parsing
    SchemaParser,
    DataParser,
    SchemaParseError,
    # Validation
    Validator,
    ValidationResult,
    ValidationError,
    # Template engine
    TemplateEngine,
    TemplateError,
    generate_templates,
)

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__email__',
    # Models
    'AttributeDefinition',
    'TableDefinition',
    'Row',
    'Table',
    'ParameterDefinition',
    'Schema',
    # Schema
    'SchemaParser',
    'DataParser',
    'SchemaParseError',
    # Validation
    'Validator',
    'ValidationResult',
    'ValidationError',
    # Engine
    'TemplateEngine',
    'TemplateError',
    'generate_templates',
]
