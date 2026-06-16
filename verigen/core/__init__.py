"""
VeriGen Core Module

Contains the core data models, schema parsing, validation, and template engine.
"""

from .models import (
    AttributeDefinition,
    TableDefinition,
    ValidationRule,
    Row,
    Table,
    ParameterDefinition,
    Schema,
)
from .schema import SchemaParser, DataParser, SchemaParseError
from .validator import Validator, ValidationResult, ValidationError
from .engine import TemplateEngine, TemplateError, generate_templates

__all__ = [
    # Models
    'AttributeDefinition',
    'TableDefinition',
    'ValidationRule',
    'Row',
    'Table',
    'ParameterDefinition',
    'Schema',
    # Schema parsing
    'SchemaParser',
    'DataParser',
    'SchemaParseError',
    # Validation
    'Validator',
    'ValidationResult',
    'ValidationError',
    # Template engine
    'TemplateEngine',
    'TemplateError',
    'generate_templates',
]
