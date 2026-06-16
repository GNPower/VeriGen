"""
VeriGen Core Data Models

This module contains the generic data models that allow users to define
their own hierarchical structures (registers/fields, FSM states, etc.)
through schema files rather than hardcoding domain-specific concepts.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator
import re


@dataclass
class ValidationRule:
    """
    Defines a custom validation rule for a table.

    Rules can reference row attributes and parameters using simple expressions.
    """
    expression: str  # Python-like expression to evaluate
    message: str  # Error message if validation fails
    scope: str = "row"  # "row" for per-row validation, "table" for cross-row


@dataclass
class AttributeDefinition:
    """
    Defines a user-specified attribute for table rows.

    Attributes are the properties that each row in a table can have,
    such as 'name', 'address_offset', 'bit_width', etc. The user defines
    these in their schema file.
    """
    name: str
    type: str  # string, integer, boolean, choice
    required: bool = True
    default: Any = None
    options: Optional[List[Any]] = None  # For choice type
    min_value: Optional[int] = None  # For integer type
    max_value: Optional[int] = None  # For integer type
    pattern: Optional[str] = None  # Regex for string validation
    description: str = ""
    display_name: str = ""  # Human-readable name for UI
    is_summary: bool = False  # If True, show this attribute in collapsed view
    unique: bool = False  # If True, values must be unique across all rows

    def validate_value(self, value: Any) -> List[str]:
        """
        Validate a value against this attribute definition.

        Returns a list of error messages (empty if valid).
        """
        errors = []

        # Required check
        if value is None:
            if self.required and self.default is None:
                errors.append(f"'{self.name}' is required")
            return errors

        # Type-specific validation
        if self.type == 'string':
            if not isinstance(value, str):
                errors.append(f"'{self.name}' must be a string")
            elif self.pattern:
                if not re.match(self.pattern, value):
                    errors.append(f"'{self.name}' does not match pattern '{self.pattern}'")

        elif self.type == 'integer':
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"'{self.name}' must be an integer")
            else:
                if self.min_value is not None and value < self.min_value:
                    errors.append(f"'{self.name}' must be >= {self.min_value}")
                if self.max_value is not None and value > self.max_value:
                    errors.append(f"'{self.name}' must be <= {self.max_value}")

        elif self.type == 'boolean':
            if not isinstance(value, bool):
                errors.append(f"'{self.name}' must be a boolean")

        elif self.type == 'choice':
            if self.options and value not in self.options:
                errors.append(f"'{self.name}' must be one of {self.options}")

        return errors

    def get_default(self) -> Any:
        """Get the default value for this attribute."""
        return self.default


@dataclass
class ParameterDefinition:
    """
    Defines a simple (non-hierarchical) parameter.

    Parameters are standalone values like 'module_name', 'data_width', etc.
    that don't belong to a table structure.
    """
    name: str
    type: str  # string, integer, boolean, choice
    default: Any = None
    options: Optional[List[Any]] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    pattern: Optional[str] = None
    description: str = ""
    display_name: str = ""  # Human-readable name for UI
    category: str = ""  # Optional grouping for UI

    def validate_value(self, value: Any) -> List[str]:
        """Validate a value against this parameter definition."""
        # Reuse AttributeDefinition validation logic
        attr = AttributeDefinition(
            name=self.name,
            type=self.type,
            required=True,
            default=self.default,
            options=self.options,
            min_value=self.min_value,
            max_value=self.max_value,
            pattern=self.pattern,
        )
        return attr.validate_value(value)

    def get_default(self) -> Any:
        """Get the default value for this parameter."""
        return self.default


@dataclass
class TableDefinition:
    """
    Defines a user-specified table structure.

    Tables are collections of rows where each row has the same set of
    attributes. Tables can be nested (e.g., registers containing fields).
    """
    name: str
    display_name: str = ""
    attributes: List[AttributeDefinition] = field(default_factory=list)
    nested_table: Optional[str] = None  # Name of child TableDefinition
    summary_attribute: Optional[str] = None  # Which attribute to show in collapsed view
    description: str = ""
    validation_rules: List[ValidationRule] = field(default_factory=list)  # Custom validation

    def get_attribute(self, name: str) -> Optional[AttributeDefinition]:
        """Get an attribute definition by name."""
        for attr in self.attributes:
            if attr.name == name:
                return attr
        return None

    def get_summary_attribute(self) -> Optional[AttributeDefinition]:
        """Get the attribute to use as the summary/display name."""
        if self.summary_attribute:
            return self.get_attribute(self.summary_attribute)
        # Look for is_summary flag
        for attr in self.attributes:
            if attr.is_summary:
                return attr
        # Fall back to first string attribute
        for attr in self.attributes:
            if attr.type == 'string':
                return attr
        return None


@dataclass
class Row:
    """
    A single row in a table, with user-defined attributes.

    Rows store attribute values in a dictionary and can have nested
    child rows if the parent table defines a nested_table.

    The __getattr__ method enables dot-notation access in Jinja2 templates:
        {{ field.bit_width }} instead of {{ field.attributes['bit_width'] }}
    """
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List['Row'] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Get an attribute value with optional default."""
        return self.attributes.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """
        Enable dot notation in templates: {{ row.bit_width }}

        This is called when the attribute is not found through normal lookup.
        """
        # Avoid recursion for special attributes
        if name.startswith('_') or name in ('attributes', 'children', 'get'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

        attributes = object.__getattribute__(self, 'attributes')
        if name in attributes:
            return attributes[name]

        # Return None for missing attributes (allows safe access in templates)
        return None

    def __iter__(self) -> Iterator['Row']:
        """Allow iteration over children: {% for field in reg %}"""
        return iter(self.children)

    def __len__(self) -> int:
        """Allow length check: {{ reg | length }} or {{ reg.children | length }}"""
        return len(self.children)

    def __bool__(self) -> bool:
        """Allow truthiness check based on whether row has any attributes."""
        return bool(self.attributes)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert row to dictionary for serialization.

        Recursively converts children as well.
        """
        result = dict(self.attributes)
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Row':
        """
        Create a Row from a dictionary.

        Recursively creates child rows from 'children' key.
        """
        children_data = data.pop('children', [])
        children = [cls.from_dict(child) for child in children_data]
        return cls(attributes=data, children=children)


@dataclass
class Table:
    """
    A collection of rows following a TableDefinition.

    Tables hold the actual data (rows) and reference their definition
    for validation and structure information.
    """
    definition: TableDefinition
    rows: List[Row] = field(default_factory=list)

    def validate(
        self,
        table_definitions: Optional[Dict[str, 'TableDefinition']] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Validate all rows against the table definition.

        Args:
            table_definitions: Dict mapping table names to definitions,
                             needed for validating nested tables.
            parameters: Dict of parameter values for custom validation rules.

        Returns:
            List of error messages (empty if valid).
        """
        errors = []
        parameters = parameters or {}

        # Validate individual rows
        for i, row in enumerate(self.rows):
            row_errors = self._validate_row(row, i, table_definitions, parameters)
            errors.extend(row_errors)

        # Validate uniqueness constraints
        unique_errors = self._validate_uniqueness()
        errors.extend(unique_errors)

        # Validate table-level custom rules
        rule_errors = self._validate_custom_rules(parameters)
        errors.extend(rule_errors)

        return errors

    def _validate_uniqueness(self) -> List[str]:
        """Check uniqueness constraints for attributes."""
        errors = []

        for attr_def in self.definition.attributes:
            if not attr_def.unique:
                continue

            # Collect all values for this attribute
            seen_values: Dict[Any, List[int]] = {}
            for i, row in enumerate(self.rows):
                value = row.attributes.get(attr_def.name)
                if value is not None:
                    if value not in seen_values:
                        seen_values[value] = []
                    seen_values[value].append(i)

            # Report duplicates
            for value, indices in seen_values.items():
                if len(indices) > 1:
                    row_names = [f"Row {i}" for i in indices]
                    errors.append(
                        f"Duplicate '{attr_def.name}' value '{value}' in rows: {', '.join(row_names)}"
                    )

        return errors

    def _validate_custom_rules(self, parameters: Dict[str, Any]) -> List[str]:
        """Evaluate custom validation rules."""
        errors = []

        for rule in self.definition.validation_rules:
            if rule.scope == "row":
                # Per-row validation
                for i, row in enumerate(self.rows):
                    if not self._evaluate_rule(rule.expression, row, i, parameters):
                        summary_attr = self.definition.get_summary_attribute()
                        row_name = row.get(summary_attr.name) if summary_attr else f"Row {i}"
                        errors.append(f"{row_name}: {rule.message}")
            elif rule.scope == "table":
                # Table-level validation (e.g., cross-row checks)
                if not self._evaluate_table_rule(rule.expression, parameters):
                    errors.append(rule.message)

        return errors

    def _evaluate_rule(
        self,
        expression: str,
        row: 'Row',
        index: int,
        parameters: Dict[str, Any]
    ) -> bool:
        """Evaluate a validation rule expression for a row."""
        try:
            # Build evaluation context
            context = dict(parameters)
            context.update(row.attributes)
            context['row_index'] = index

            # Safe evaluation of simple expressions
            return bool(eval(expression, {"__builtins__": {}}, context))
        except Exception:
            # If expression fails, consider it invalid
            return False

    def _evaluate_table_rule(
        self,
        expression: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Evaluate a table-level validation rule."""
        try:
            context = dict(parameters)
            context['rows'] = self.rows
            context['row_count'] = len(self.rows)

            return bool(eval(expression, {"__builtins__": {}}, context))
        except Exception:
            return False

    def _validate_row(
        self,
        row: Row,
        index: int,
        table_definitions: Optional[Dict[str, TableDefinition]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Validate a single row and its children."""
        errors = []
        prefix = f"Row {index}"
        parameters = parameters or {}

        # Validate each attribute
        for attr_def in self.definition.attributes:
            value = row.attributes.get(attr_def.name)

            # Use default if value not provided
            if value is None and attr_def.default is not None:
                value = attr_def.default

            attr_errors = attr_def.validate_value(value)
            for error in attr_errors:
                errors.append(f"{prefix}: {error}")

        # Validate children if this table has nested tables
        if self.definition.nested_table and row.children:
            if table_definitions and self.definition.nested_table in table_definitions:
                child_def = table_definitions[self.definition.nested_table]
                child_table = Table(definition=child_def, rows=row.children)
                child_errors = child_table.validate(table_definitions, parameters)
                for error in child_errors:
                    # Prefix with parent row info
                    summary_attr = self.definition.get_summary_attribute()
                    row_name = row.get(summary_attr.name) if summary_attr else f"Row {index}"
                    errors.append(f"{row_name} > {error}")

        return errors

    def __iter__(self) -> Iterator[Row]:
        """Allow iteration: {% for reg in registers %}"""
        return iter(self.rows)

    def __len__(self) -> int:
        """Allow length check: {{ registers | length }}"""
        return len(self.rows)


@dataclass
class Schema:
    """
    Complete schema definition containing parameters and tables.

    The schema defines the structure of user data - what parameters
    are available and what tables (with their attributes) can be used.
    """
    version: str = "1.0"
    parameters: Dict[str, ParameterDefinition] = field(default_factory=dict)
    tables: Dict[str, TableDefinition] = field(default_factory=dict)

    def get_parameter(self, name: str) -> Optional[ParameterDefinition]:
        """Get a parameter definition by name."""
        return self.parameters.get(name)

    def get_table(self, name: str) -> Optional[TableDefinition]:
        """Get a table definition by name."""
        return self.tables.get(name)

    def get_all_parameter_defaults(self) -> Dict[str, Any]:
        """Get a dictionary of all parameter default values."""
        return {
            name: param.get_default()
            for name, param in self.parameters.items()
        }

    def validate_parameters(self, values: Dict[str, Any]) -> List[str]:
        """Validate a dictionary of parameter values against the schema."""
        errors = []

        for name, param_def in self.parameters.items():
            value = values.get(name, param_def.get_default())
            param_errors = param_def.validate_value(value)
            errors.extend(param_errors)

        return errors
