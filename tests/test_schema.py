#!/usr/bin/env python
"""Tests for verigen.core.schema module."""

import pytest
import tempfile
import os

from verigen.core.schema import SchemaParser, DataParser, SchemaParseError
from verigen.core.models import Schema


class TestSchemaParser:
    """Tests for SchemaParser class."""

    def test_parse_v2_schema(self):
        """Test parsing a v2 format schema."""
        parser = SchemaParser()
        data = {
            "version": "2.0",
            "parameters": {
                "module_name": {
                    "type": "string",
                    "default": "test_module",
                    "description": "Module name"
                },
                "data_width": {
                    "type": "choice",
                    "options": [32, 64],
                    "default": 32
                }
            },
            "tables": {
                "registers": {
                    "display_name": "Registers",
                    "attributes": [
                        {"name": "name", "type": "string", "required": True},
                        {"name": "offset", "type": "integer", "min": 0}
                    ]
                }
            }
        }

        schema = parser.parse_dict(data)

        assert schema.version == "2.0"
        assert "module_name" in schema.parameters
        assert schema.parameters["module_name"].default == "test_module"
        assert "registers" in schema.tables
        assert len(schema.tables["registers"].attributes) == 2

    def test_parse_nested_tables(self):
        """Test parsing schema with nested tables."""
        parser = SchemaParser()
        data = {
            "version": "2.0",
            "tables": {
                "registers": {
                    "attributes": [
                        {"name": "name", "type": "string"}
                    ],
                    "nested_table": "fields"
                },
                "fields": {
                    "attributes": [
                        {"name": "bit_offset", "type": "integer"}
                    ]
                }
            }
        }

        schema = parser.parse_dict(data)

        assert schema.tables["registers"].nested_table == "fields"
        assert "fields" in schema.tables

    def test_parse_validation_rules(self):
        """Test parsing custom validation rules."""
        parser = SchemaParser()
        data = {
            "version": "2.0",
            "tables": {
                "items": {
                    "attributes": [
                        {"name": "value", "type": "integer"}
                    ],
                    "validation": [
                        {
                            "rule": "value > 0",
                            "message": "Value must be positive"
                        }
                    ]
                }
            }
        }

        schema = parser.parse_dict(data)

        rules = schema.tables["items"].validation_rules
        assert len(rules) == 1
        assert rules[0].expression == "value > 0"

    def test_parse_unique_constraint(self):
        """Test parsing unique constraint on attributes."""
        parser = SchemaParser()
        data = {
            "version": "2.0",
            "tables": {
                "items": {
                    "attributes": [
                        {"name": "id", "type": "integer", "unique": True}
                    ]
                }
            }
        }

        schema = parser.parse_dict(data)

        attr = schema.tables["items"].attributes[0]
        assert attr.unique is True

    def test_parse_file(self):
        """Test parsing schema from a YAML file."""
        parser = SchemaParser()

        yaml_content = """
version: "2.0"
parameters:
  name:
    type: string
    default: test
tables:
  items:
    attributes:
      - name: id
        type: integer
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            temp_path = f.name

        try:
            schema = parser.parse_file(temp_path)
            assert schema.version == "2.0"
            assert "name" in schema.parameters
            assert "items" in schema.tables
        finally:
            os.unlink(temp_path)

    def test_parse_file_not_found(self):
        """Test that parsing non-existent file raises error."""
        parser = SchemaParser()
        with pytest.raises(SchemaParseError):
            parser.parse_file("/nonexistent/path/schema.yaml")

    def test_parse_v1_ui_spec(self):
        """Test parsing legacy v1 UI spec format."""
        parser = SchemaParser()
        data = {
            "pages": [
                {
                    "title": "Settings",
                    "elements": [
                        {
                            "id": "module_name",
                            "type": "string",
                            "label": "Module Name",
                            "default": "test"
                        },
                        {
                            "id": "width",
                            "type": "choice",
                            "options": [32, 64],
                            "default": 32
                        }
                    ]
                }
            ]
        }

        schema = parser.parse_dict(data)

        assert "module_name" in schema.parameters
        assert "width" in schema.parameters
        assert schema.parameters["width"].options == [32, 64]

    def test_parse_summary_attribute(self):
        """Test parsing summary_attribute field."""
        parser = SchemaParser()
        data = {
            "version": "2.0",
            "tables": {
                "items": {
                    "summary_attribute": "name",
                    "attributes": [
                        {"name": "name", "type": "string"},
                        {"name": "value", "type": "integer"}
                    ]
                }
            }
        }

        schema = parser.parse_dict(data)
        assert schema.tables["items"].summary_attribute == "name"

    def test_parse_is_summary_flag(self):
        """Test parsing is_summary flag on attributes."""
        parser = SchemaParser()
        data = {
            "version": "2.0",
            "tables": {
                "items": {
                    "attributes": [
                        {"name": "name", "type": "string", "is_summary": True},
                        {"name": "value", "type": "integer"}
                    ]
                }
            }
        }

        schema = parser.parse_dict(data)
        # Should auto-detect summary_attribute from is_summary flag
        assert schema.tables["items"].summary_attribute == "name"


class TestDataParser:
    """Tests for DataParser class."""

    @pytest.fixture
    def sample_schema(self):
        """Create a sample schema for testing."""
        parser = SchemaParser()
        return parser.parse_dict({
            "version": "2.0",
            "parameters": {
                "name": {"type": "string", "default": "test"}
            },
            "tables": {
                "items": {
                    "attributes": [
                        {"name": "id", "type": "integer"},
                        {"name": "label", "type": "string"}
                    ]
                }
            }
        })

    def test_parse_parameters(self, sample_schema):
        """Test parsing parameter values."""
        data_parser = DataParser(sample_schema)
        data = {
            "name": "my_module"
        }

        params, tables = data_parser.parse_dict(data)

        assert params["name"] == "my_module"

    def test_parse_table_data(self, sample_schema):
        """Test parsing table data."""
        data_parser = DataParser(sample_schema)
        data = {
            "items": [
                {"id": 1, "label": "First"},
                {"id": 2, "label": "Second"}
            ]
        }

        params, tables = data_parser.parse_dict(data)

        assert "items" in tables
        assert len(tables["items"].rows) == 2
        assert tables["items"].rows[0].id == 1

    def test_parse_nested_data(self):
        """Test parsing nested table data."""
        parser = SchemaParser()
        schema = parser.parse_dict({
            "version": "2.0",
            "tables": {
                "registers": {
                    "attributes": [{"name": "name", "type": "string"}],
                    "nested_table": "fields"
                },
                "fields": {
                    "attributes": [{"name": "bit", "type": "integer"}]
                }
            }
        })

        data_parser = DataParser(schema)
        data = {
            "registers": [
                {
                    "name": "CTRL",
                    "children": [
                        {"bit": 0},
                        {"bit": 1}
                    ]
                }
            ]
        }

        params, tables = data_parser.parse_dict(data)

        assert len(tables["registers"].rows) == 1
        assert len(tables["registers"].rows[0].children) == 2

    def test_parse_file(self, sample_schema):
        """Test parsing data from a YAML file."""
        yaml_content = """
name: file_module
items:
  - id: 1
    label: A
  - id: 2
    label: B
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            temp_path = f.name

        try:
            data_parser = DataParser(sample_schema)
            params, tables = data_parser.parse_file(temp_path)

            assert params["name"] == "file_module"
            assert len(tables["items"].rows) == 2
        finally:
            os.unlink(temp_path)
