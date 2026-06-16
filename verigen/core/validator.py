"""
VeriGen Validator

Provides schema-driven validation for user data.
All validation rules come from the schema - nothing is hardcoded.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .models import Schema, Table, Row, ParameterDefinition, TableDefinition


@dataclass
class ValidationError:
    """Represents a single validation error."""
    path: str  # e.g., "registers[0].fields[2].bit_width"
    message: str
    severity: str = "error"  # error, warning, info

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validation containing all errors and warnings."""
    errors: List[ValidationError]

    @property
    def is_valid(self) -> bool:
        """Returns True if there are no errors."""
        return not any(e.severity == "error" for e in self.errors)

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for e in self.errors if e.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for e in self.errors if e.severity == "warning")

    def get_errors(self) -> List[ValidationError]:
        """Get only error-level issues."""
        return [e for e in self.errors if e.severity == "error"]

    def get_warnings(self) -> List[ValidationError]:
        """Get only warning-level issues."""
        return [e for e in self.errors if e.severity == "warning"]

    def format_errors(self) -> str:
        """Format all errors as a human-readable string."""
        if not self.errors:
            return "No validation errors."

        lines = []
        for error in self.errors:
            prefix = "ERROR" if error.severity == "error" else "WARNING"
            lines.append(f"[{prefix}] {error.path}: {error.message}")

        return "\n".join(lines)


class Validator:
    """
    Schema-driven validator for VeriGen data.

    Validates parameter values and table data against the schema definitions.
    All validation rules come from the schema - the validator itself has
    no domain-specific knowledge.
    """

    def __init__(self, schema: Schema):
        self.schema = schema

    def validate_all(
        self,
        parameters: Dict[str, Any],
        tables: Dict[str, Table]
    ) -> ValidationResult:
        """
        Validate all parameters and tables.

        Args:
            parameters: Dictionary of parameter values.
            tables: Dictionary of Table objects.

        Returns:
            ValidationResult with all errors and warnings.
        """
        errors: List[ValidationError] = []

        # Validate parameters
        param_errors = self.validate_parameters(parameters)
        errors.extend(param_errors)

        # Validate tables (pass parameters for custom validation rules)
        for table_name, table in tables.items():
            table_errors = self.validate_table(table_name, table, parameters)
            errors.extend(table_errors)

        return ValidationResult(errors=errors)

    def validate_parameters(self, parameters: Dict[str, Any]) -> List[ValidationError]:
        """Validate parameter values against schema definitions."""
        errors: List[ValidationError] = []

        # Check for required parameters
        for name, param_def in self.schema.parameters.items():
            value = parameters.get(name)

            if value is None:
                if param_def.default is None:
                    errors.append(ValidationError(
                        path=f"parameters.{name}",
                        message=f"Required parameter '{name}' is missing"
                    ))
                continue

            # Validate the value
            value_errors = param_def.validate_value(value)
            for msg in value_errors:
                errors.append(ValidationError(
                    path=f"parameters.{name}",
                    message=msg
                ))

        # Check for unknown parameters (warning only)
        for name in parameters:
            if name not in self.schema.parameters and name not in self.schema.tables:
                errors.append(ValidationError(
                    path=f"parameters.{name}",
                    message=f"Unknown parameter '{name}' (not in schema)",
                    severity="warning"
                ))

        return errors

    def validate_table(
        self,
        table_name: str,
        table: Table,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[ValidationError]:
        """Validate a table and all its rows."""
        errors: List[ValidationError] = []

        # Use Table's built-in validation (includes uniqueness and custom rules)
        table_errors = table.validate(self.schema.tables, parameters)
        for msg in table_errors:
            errors.append(ValidationError(
                path=f"{table_name}",
                message=msg
            ))

        # Additional per-row validation with full path info
        for i, row in enumerate(table.rows):
            row_errors = self._validate_row(
                table.definition,
                row,
                path=f"{table_name}[{i}]"
            )
            errors.extend(row_errors)

        return errors

    def _validate_row(
        self,
        table_def: TableDefinition,
        row: Row,
        path: str
    ) -> List[ValidationError]:
        """Validate a single row and its children."""
        errors: List[ValidationError] = []

        # Validate each attribute
        for attr_def in table_def.attributes:
            value = row.attributes.get(attr_def.name)

            # Use default if value is None
            if value is None:
                value = attr_def.default

            attr_errors = attr_def.validate_value(value)
            for msg in attr_errors:
                errors.append(ValidationError(
                    path=f"{path}.{attr_def.name}",
                    message=msg
                ))

        # Check for unknown attributes (warning only)
        known_attrs = {attr.name for attr in table_def.attributes}
        for attr_name in row.attributes:
            if attr_name not in known_attrs and attr_name != 'children':
                errors.append(ValidationError(
                    path=f"{path}.{attr_name}",
                    message=f"Unknown attribute '{attr_name}'",
                    severity="warning"
                ))

        # Validate children if this table has nested tables
        if table_def.nested_table and row.children:
            nested_def = self.schema.tables.get(table_def.nested_table)
            if nested_def:
                for j, child in enumerate(row.children):
                    child_errors = self._validate_row(
                        nested_def,
                        child,
                        path=f"{path}.{table_def.nested_table}[{j}]"
                    )
                    errors.extend(child_errors)
            else:
                errors.append(ValidationError(
                    path=path,
                    message=f"Nested table '{table_def.nested_table}' not found in schema",
                    severity="warning"
                ))

        return errors

    def validate_schema(self) -> ValidationResult:
        """
        Validate the schema itself for internal consistency.

        Checks things like:
        - Nested table references exist
        - Summary attributes exist
        - No duplicate attribute names
        """
        errors: List[ValidationError] = []

        for table_name, table_def in self.schema.tables.items():
            # Check nested table exists
            if table_def.nested_table:
                if table_def.nested_table not in self.schema.tables:
                    errors.append(ValidationError(
                        path=f"tables.{table_name}.nested_table",
                        message=f"Nested table '{table_def.nested_table}' not defined"
                    ))

            # Check summary attribute exists
            if table_def.summary_attribute:
                if not table_def.get_attribute(table_def.summary_attribute):
                    errors.append(ValidationError(
                        path=f"tables.{table_name}.summary_attribute",
                        message=f"Summary attribute '{table_def.summary_attribute}' not defined"
                    ))

            # Check for duplicate attribute names
            attr_names = [attr.name for attr in table_def.attributes]
            seen = set()
            for name in attr_names:
                if name in seen:
                    errors.append(ValidationError(
                        path=f"tables.{table_name}.attributes",
                        message=f"Duplicate attribute name '{name}'"
                    ))
                seen.add(name)

        return ValidationResult(errors=errors)
