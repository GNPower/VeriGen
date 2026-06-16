#!/usr/bin/env python
"""Tests for verigen.core.validator module."""

import pytest

from verigen.core.validator import Validator, ValidationResult, ValidationError
from verigen.core.models import (
    Schema,
    ParameterDefinition,
    TableDefinition,
    AttributeDefinition,
    ValidationRule,
    Table,
    Row,
)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_create_error(self):
        """Test creating a validation error."""
        error = ValidationError(
            path="registers[0].name",
            message="Name is required"
        )
        assert error.path == "registers[0].name"
        assert error.severity == "error"

    def test_str_representation(self):
        """Test string representation."""
        error = ValidationError(path="test.field", message="Invalid value")
        assert "test.field" in str(error)
        assert "Invalid value" in str(error)


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_is_valid_with_no_errors(self):
        """Test is_valid returns True when no errors."""
        result = ValidationResult(errors=[])
        assert result.is_valid is True

    def test_is_valid_with_errors(self):
        """Test is_valid returns False when errors exist."""
        result = ValidationResult(errors=[
            ValidationError(path="test", message="error")
        ])
        assert result.is_valid is False

    def test_warnings_dont_affect_validity(self):
        """Test that warnings alone don't make result invalid."""
        result = ValidationResult(errors=[
            ValidationError(path="test", message="warning", severity="warning")
        ])
        assert result.is_valid is True

    def test_error_count(self):
        """Test error counting."""
        result = ValidationResult(errors=[
            ValidationError(path="a", message="error1"),
            ValidationError(path="b", message="error2"),
            ValidationError(path="c", message="warning", severity="warning"),
        ])
        assert result.error_count == 2
        assert result.warning_count == 1

    def test_get_errors(self):
        """Test filtering errors only."""
        result = ValidationResult(errors=[
            ValidationError(path="a", message="error"),
            ValidationError(path="b", message="warning", severity="warning"),
        ])
        errors = result.get_errors()
        assert len(errors) == 1
        assert errors[0].path == "a"

    def test_format_errors(self):
        """Test error formatting."""
        result = ValidationResult(errors=[
            ValidationError(path="test", message="Something went wrong")
        ])
        formatted = result.format_errors()
        assert "ERROR" in formatted
        assert "test" in formatted
        assert "Something went wrong" in formatted


class TestValidator:
    """Tests for Validator class."""

    @pytest.fixture
    def simple_schema(self):
        """Create a simple schema for testing."""
        return Schema(
            version="2.0",
            parameters={
                "name": ParameterDefinition(
                    name="name",
                    type="string",
                    default="default_name"
                ),
                "width": ParameterDefinition(
                    name="width",
                    type="choice",
                    options=[32, 64, 128]
                ),
            },
            tables={
                "items": TableDefinition(
                    name="items",
                    attributes=[
                        AttributeDefinition(name="id", type="integer", required=True),
                        AttributeDefinition(name="label", type="string", required=False),
                    ]
                )
            }
        )

    def test_validate_valid_parameters(self, simple_schema):
        """Test validating valid parameters."""
        validator = Validator(simple_schema)
        params = {"name": "test", "width": 32}

        errors = validator.validate_parameters(params)

        # Should have no actual errors
        error_only = [e for e in errors if e.severity == "error"]
        assert len(error_only) == 0

    def test_validate_invalid_parameter_choice(self, simple_schema):
        """Test validating invalid choice parameter."""
        validator = Validator(simple_schema)
        params = {"name": "test", "width": 16}  # 16 is not a valid option

        errors = validator.validate_parameters(params)

        error_only = [e for e in errors if e.severity == "error"]
        assert len(error_only) == 1

    def test_validate_unknown_parameter_warning(self, simple_schema):
        """Test that unknown parameters generate warnings."""
        validator = Validator(simple_schema)
        params = {"name": "test", "unknown_param": "value"}

        errors = validator.validate_parameters(params)

        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) == 1
        assert "unknown" in warnings[0].message.lower()

    def test_validate_valid_table(self, simple_schema):
        """Test validating a valid table."""
        validator = Validator(simple_schema)
        table = Table(
            definition=simple_schema.tables["items"],
            rows=[
                Row(attributes={"id": 1, "label": "A"}),
                Row(attributes={"id": 2, "label": "B"}),
            ]
        )

        errors = validator.validate_table("items", table)

        error_only = [e for e in errors if e.severity == "error"]
        assert len(error_only) == 0

    def test_validate_missing_required_attribute(self, simple_schema):
        """Test validating table with missing required attribute."""
        validator = Validator(simple_schema)
        table = Table(
            definition=simple_schema.tables["items"],
            rows=[
                Row(attributes={"label": "Missing ID"}),  # Missing required 'id'
            ]
        )

        errors = validator.validate_table("items", table)

        error_only = [e for e in errors if e.severity == "error"]
        assert len(error_only) >= 1

    def test_validate_all(self, simple_schema):
        """Test validating everything at once."""
        validator = Validator(simple_schema)
        params = {"name": "test", "width": 64}
        tables = {
            "items": Table(
                definition=simple_schema.tables["items"],
                rows=[Row(attributes={"id": 1})]
            )
        }

        result = validator.validate_all(params, tables)

        assert result.is_valid

    def test_validate_nested_tables(self):
        """Test validating tables with nested children."""
        schema = Schema(
            tables={
                "registers": TableDefinition(
                    name="registers",
                    attributes=[
                        AttributeDefinition(name="name", type="string", required=True)
                    ],
                    nested_table="fields"
                ),
                "fields": TableDefinition(
                    name="fields",
                    attributes=[
                        AttributeDefinition(name="bit", type="integer", required=True)
                    ]
                )
            }
        )

        validator = Validator(schema)
        table = Table(
            definition=schema.tables["registers"],
            rows=[
                Row(
                    attributes={"name": "CTRL"},
                    children=[
                        Row(attributes={"bit": 0}),
                        Row(attributes={}),  # Missing required 'bit'
                    ]
                )
            ]
        )

        errors = validator.validate_table("registers", table)

        # Should have error for missing 'bit' in child
        error_only = [e for e in errors if e.severity == "error"]
        assert len(error_only) >= 1

    def test_validate_uniqueness(self):
        """Test uniqueness validation."""
        schema = Schema(
            tables={
                "items": TableDefinition(
                    name="items",
                    attributes=[
                        AttributeDefinition(name="id", type="integer", unique=True)
                    ]
                )
            }
        )

        validator = Validator(schema)
        table = Table(
            definition=schema.tables["items"],
            rows=[
                Row(attributes={"id": 1}),
                Row(attributes={"id": 2}),
                Row(attributes={"id": 1}),  # Duplicate
            ]
        )

        errors = validator.validate_table("items", table)

        error_only = [e for e in errors if e.severity == "error"]
        assert any("Duplicate" in e.message for e in error_only)

    def test_validate_custom_rule(self):
        """Test custom validation rule."""
        schema = Schema(
            parameters={
                "max_value": ParameterDefinition(
                    name="max_value",
                    type="integer",
                    default=100
                )
            },
            tables={
                "items": TableDefinition(
                    name="items",
                    attributes=[
                        AttributeDefinition(name="value", type="integer")
                    ],
                    validation_rules=[
                        ValidationRule(
                            expression="value <= max_value",
                            message="Value exceeds maximum"
                        )
                    ]
                )
            }
        )

        validator = Validator(schema)
        params = {"max_value": 100}
        table = Table(
            definition=schema.tables["items"],
            rows=[
                Row(attributes={"value": 50}),   # Valid
                Row(attributes={"value": 150}),  # Exceeds max
            ]
        )

        errors = validator.validate_table("items", table, params)

        error_only = [e for e in errors if e.severity == "error"]
        assert any("exceeds" in e.message.lower() for e in error_only)

    def test_validate_schema_consistency(self):
        """Test schema self-validation."""
        # Schema with invalid nested_table reference
        schema = Schema(
            tables={
                "items": TableDefinition(
                    name="items",
                    attributes=[],
                    nested_table="nonexistent"  # References non-existent table
                )
            }
        )

        validator = Validator(schema)
        result = validator.validate_schema()

        assert not result.is_valid
        assert any("nonexistent" in e.message for e in result.errors)

    def test_validate_schema_duplicate_attributes(self):
        """Test detecting duplicate attribute names in schema."""
        # Create schema with duplicate attribute names
        schema = Schema(
            tables={
                "items": TableDefinition(
                    name="items",
                    attributes=[
                        AttributeDefinition(name="id", type="integer"),
                        AttributeDefinition(name="id", type="string"),  # Duplicate
                    ]
                )
            }
        )

        validator = Validator(schema)
        result = validator.validate_schema()

        assert any("Duplicate" in e.message for e in result.errors)
