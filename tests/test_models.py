#!/usr/bin/env python
"""Tests for verigen.core.models module."""

import pytest

from verigen.core.models import (
    AttributeDefinition,
    ParameterDefinition,
    TableDefinition,
    ValidationRule,
    Row,
    Table,
    Schema,
)


class TestAttributeDefinition:
    """Tests for AttributeDefinition class."""

    def test_create_string_attribute(self):
        """Test creating a basic string attribute."""
        attr = AttributeDefinition(
            name="test_name",
            type="string",
            required=True,
            description="A test attribute"
        )
        assert attr.name == "test_name"
        assert attr.type == "string"
        assert attr.required is True

    def test_validate_required_missing(self):
        """Test validation fails for missing required value."""
        attr = AttributeDefinition(name="test", type="string", required=True)
        errors = attr.validate_value(None)
        assert len(errors) == 1
        assert "required" in errors[0].lower()

    def test_validate_optional_missing(self):
        """Test validation passes for missing optional value."""
        attr = AttributeDefinition(name="test", type="string", required=False)
        errors = attr.validate_value(None)
        assert len(errors) == 0

    def test_validate_integer_range(self):
        """Test integer validation with min/max."""
        attr = AttributeDefinition(
            name="count",
            type="integer",
            min_value=0,
            max_value=100
        )
        # Valid value
        assert attr.validate_value(50) == []
        # Below minimum
        errors = attr.validate_value(-1)
        assert len(errors) == 1
        # Above maximum
        errors = attr.validate_value(101)
        assert len(errors) == 1

    def test_validate_choice(self):
        """Test choice validation."""
        attr = AttributeDefinition(
            name="access",
            type="choice",
            options=["RW", "RO", "WO"]
        )
        # Valid choice
        assert attr.validate_value("RW") == []
        # Invalid choice
        errors = attr.validate_value("INVALID")
        assert len(errors) == 1

    def test_validate_pattern(self):
        """Test string pattern validation."""
        attr = AttributeDefinition(
            name="name",
            type="string",
            pattern="^[A-Z_][A-Z0-9_]*$"
        )
        # Valid pattern
        assert attr.validate_value("VALID_NAME") == []
        # Invalid pattern
        errors = attr.validate_value("invalid")
        assert len(errors) == 1

    def test_unique_flag(self):
        """Test unique flag is set correctly."""
        attr = AttributeDefinition(name="id", type="integer", unique=True)
        assert attr.unique is True


class TestParameterDefinition:
    """Tests for ParameterDefinition class."""

    def test_create_parameter(self):
        """Test creating a parameter definition."""
        param = ParameterDefinition(
            name="module_name",
            type="string",
            default="my_module",
            description="The module name"
        )
        assert param.name == "module_name"
        assert param.default == "my_module"

    def test_get_default(self):
        """Test getting default value."""
        param = ParameterDefinition(name="count", type="integer", default=42)
        assert param.get_default() == 42

    def test_validate_value(self):
        """Test parameter value validation."""
        param = ParameterDefinition(
            name="width",
            type="choice",
            options=[32, 64, 128]
        )
        assert param.validate_value(32) == []
        errors = param.validate_value(16)
        assert len(errors) == 1


class TestRow:
    """Tests for Row class."""

    def test_create_row(self):
        """Test creating a row with attributes."""
        row = Row(attributes={"name": "TEST", "value": 42})
        assert row.attributes["name"] == "TEST"
        assert row.attributes["value"] == 42

    def test_dot_notation_access(self):
        """Test accessing attributes via dot notation."""
        row = Row(attributes={"name": "TEST", "value": 42})
        assert row.name == "TEST"
        assert row.value == 42

    def test_get_method(self):
        """Test get method with default."""
        row = Row(attributes={"name": "TEST"})
        assert row.get("name") == "TEST"
        assert row.get("missing", "default") == "default"

    def test_missing_attribute_returns_none(self):
        """Test that missing attributes return None."""
        row = Row(attributes={"name": "TEST"})
        assert row.missing_attr is None

    def test_children(self):
        """Test row with children."""
        child1 = Row(attributes={"field": "A"})
        child2 = Row(attributes={"field": "B"})
        parent = Row(attributes={"name": "PARENT"}, children=[child1, child2])

        assert len(parent.children) == 2
        assert parent.children[0].field == "A"

    def test_iteration(self):
        """Test iterating over children."""
        children = [Row(attributes={"i": i}) for i in range(3)]
        parent = Row(attributes={}, children=children)

        collected = [child.i for child in parent]
        assert collected == [0, 1, 2]

    def test_to_dict(self):
        """Test converting row to dictionary."""
        child = Row(attributes={"field": "child_field"})
        parent = Row(attributes={"name": "PARENT"}, children=[child])

        d = parent.to_dict()
        assert d["name"] == "PARENT"
        assert len(d["children"]) == 1
        assert d["children"][0]["field"] == "child_field"

    def test_from_dict(self):
        """Test creating row from dictionary."""
        data = {
            "name": "TEST",
            "value": 42,
            "children": [{"field": "A"}, {"field": "B"}]
        }
        row = Row.from_dict(data.copy())

        assert row.name == "TEST"
        assert row.value == 42
        assert len(row.children) == 2


class TestTableDefinition:
    """Tests for TableDefinition class."""

    def test_create_table_definition(self):
        """Test creating a table definition."""
        attrs = [
            AttributeDefinition(name="name", type="string"),
            AttributeDefinition(name="value", type="integer"),
        ]
        table_def = TableDefinition(
            name="registers",
            display_name="Registers",
            attributes=attrs
        )
        assert table_def.name == "registers"
        assert len(table_def.attributes) == 2

    def test_get_attribute(self):
        """Test getting attribute by name."""
        attrs = [
            AttributeDefinition(name="name", type="string"),
            AttributeDefinition(name="value", type="integer"),
        ]
        table_def = TableDefinition(name="test", attributes=attrs)

        assert table_def.get_attribute("name") is not None
        assert table_def.get_attribute("missing") is None

    def test_nested_table(self):
        """Test nested table reference."""
        table_def = TableDefinition(
            name="registers",
            nested_table="fields"
        )
        assert table_def.nested_table == "fields"


class TestValidationRule:
    """Tests for ValidationRule class."""

    def test_create_rule(self):
        """Test creating a validation rule."""
        rule = ValidationRule(
            expression="value > 0",
            message="Value must be positive",
            scope="row"
        )
        assert rule.expression == "value > 0"
        assert rule.scope == "row"


class TestTable:
    """Tests for Table class."""

    def test_create_table(self):
        """Test creating a table with rows."""
        table_def = TableDefinition(
            name="test",
            attributes=[AttributeDefinition(name="name", type="string")]
        )
        rows = [
            Row(attributes={"name": "A"}),
            Row(attributes={"name": "B"}),
        ]
        table = Table(definition=table_def, rows=rows)

        assert len(table) == 2

    def test_iteration(self):
        """Test iterating over table rows."""
        table_def = TableDefinition(
            name="test",
            attributes=[AttributeDefinition(name="name", type="string")]
        )
        rows = [Row(attributes={"name": f"Item{i}"}) for i in range(3)]
        table = Table(definition=table_def, rows=rows)

        names = [row.name for row in table]
        assert names == ["Item0", "Item1", "Item2"]

    def test_validate_uniqueness(self):
        """Test uniqueness constraint validation."""
        table_def = TableDefinition(
            name="test",
            attributes=[
                AttributeDefinition(name="id", type="integer", unique=True)
            ]
        )
        # Duplicate values
        rows = [
            Row(attributes={"id": 1}),
            Row(attributes={"id": 2}),
            Row(attributes={"id": 1}),  # Duplicate
        ]
        table = Table(definition=table_def, rows=rows)

        errors = table.validate()
        assert any("Duplicate" in e for e in errors)

    def test_validate_custom_rule(self):
        """Test custom validation rule."""
        rule = ValidationRule(
            expression="value > 0",
            message="Value must be positive"
        )
        table_def = TableDefinition(
            name="test",
            attributes=[AttributeDefinition(name="value", type="integer")],
            validation_rules=[rule]
        )
        rows = [
            Row(attributes={"value": 10}),  # Valid
            Row(attributes={"value": -5}),  # Invalid
        ]
        table = Table(definition=table_def, rows=rows)

        errors = table.validate(parameters={})
        assert any("positive" in e for e in errors)


class TestSchema:
    """Tests for Schema class."""

    def test_create_schema(self):
        """Test creating a schema."""
        schema = Schema(
            version="2.0",
            parameters={
                "name": ParameterDefinition(name="name", type="string", default="test")
            },
            tables={
                "items": TableDefinition(
                    name="items",
                    attributes=[AttributeDefinition(name="id", type="integer")]
                )
            }
        )
        assert schema.version == "2.0"
        assert "name" in schema.parameters
        assert "items" in schema.tables

    def test_get_all_parameter_defaults(self):
        """Test getting all parameter defaults."""
        schema = Schema(
            parameters={
                "a": ParameterDefinition(name="a", type="integer", default=1),
                "b": ParameterDefinition(name="b", type="string", default="test"),
            }
        )
        defaults = schema.get_all_parameter_defaults()
        assert defaults == {"a": 1, "b": "test"}
