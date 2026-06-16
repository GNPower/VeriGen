"""
VeriGen Schema Parser

Parses user-defined schema files (YAML) into the core data models.
Supports both v1 (legacy UI-tied) and v2 (separated schema) formats.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml

from .models import (
    AttributeDefinition,
    ParameterDefinition,
    TableDefinition,
    ValidationRule,
    Row,
    Table,
    Schema,
)


class SchemaParseError(Exception):
    """Raised when schema parsing fails."""
    pass


class SchemaParser:
    """
    Parses YAML schema files into Schema objects.

    Supports two formats:
    - v1 (legacy): UI spec directly defines parameters and tables
    - v2 (new): Separate schema file with explicit parameters and tables sections
    """

    def parse_file(self, filepath: str) -> Schema:
        """
        Parse a schema file and return a Schema object.

        Args:
            filepath: Path to the YAML schema file.

        Returns:
            Parsed Schema object.

        Raises:
            SchemaParseError: If the file cannot be parsed.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise SchemaParseError(f"Schema file not found: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SchemaParseError(f"Invalid YAML in schema file: {e}")

        if not isinstance(data, dict):
            raise SchemaParseError("Schema file must contain a YAML dictionary")

        return self.parse_dict(data)

    def parse_dict(self, data: Dict[str, Any]) -> Schema:
        """
        Parse a dictionary into a Schema object.

        Automatically detects format version and parses accordingly.
        """
        version = self._detect_version(data)

        if version == "1.0" or version is None:
            # Check if this is v1 (UI spec) or v2 format
            if 'pages' in data:
                # This is a v1 UI spec - extract schema from UI definition
                return self._parse_v1_ui_spec(data)
            elif 'parameters' in data or 'tables' in data:
                # This is v2 format
                return self._parse_v2_schema(data)
            else:
                # Empty or minimal schema
                return Schema(version="1.0")

        return self._parse_v2_schema(data)

    def _detect_version(self, data: Dict[str, Any]) -> Optional[str]:
        """Detect the schema version from the data."""
        return data.get('version')

    def _parse_v1_ui_spec(self, data: Dict[str, Any]) -> Schema:
        """
        Parse a v1 UI spec format where parameters are defined as UI elements.

        This provides backward compatibility with the original VeriGen format
        where the UI spec also served as the parameter definition.
        """
        parameters: Dict[str, ParameterDefinition] = {}
        tables: Dict[str, TableDefinition] = {}

        pages = data.get('pages', [])
        for page in pages:
            elements = page.get('elements', [])
            for elem in elements:
                elem_id = elem.get('id')
                elem_type = elem.get('type')

                if not elem_id or not elem_type:
                    continue

                # Skip UI-only elements
                if elem_type in ('summary', 'image', 'label', 'directory_selector'):
                    continue

                if elem_type == 'dynamic_table':
                    # Parse as table definition
                    table_def = self._parse_v1_dynamic_table(elem)
                    tables[elem_id] = table_def
                else:
                    # Parse as simple parameter
                    param_def = self._parse_v1_element_as_parameter(elem)
                    parameters[elem_id] = param_def

        return Schema(version="1.0", parameters=parameters, tables=tables)

    def _parse_v1_element_as_parameter(self, elem: Dict[str, Any]) -> ParameterDefinition:
        """Convert a v1 UI element to a ParameterDefinition."""
        elem_id = elem['id']
        elem_type = elem['type']

        # Map v1 types to schema types
        type_map = {
            'string': 'string',
            'integer': 'integer',
            'boolean': 'boolean',
            'choice': 'choice',
        }
        schema_type = type_map.get(elem_type, 'string')

        return ParameterDefinition(
            name=elem_id,
            type=schema_type,
            default=elem.get('default'),
            options=elem.get('options'),
            min_value=elem.get('min'),
            max_value=elem.get('max'),
            pattern=elem.get('pattern'),
            description=elem.get('tooltip', elem.get('description', '')),
            display_name=elem.get('label', elem.get('display_name', '')),
            category=elem.get('category', ''),
        )

    def _parse_v1_dynamic_table(self, elem: Dict[str, Any]) -> TableDefinition:
        """Convert a v1 dynamic_table element to a TableDefinition."""
        elem_id = elem['id']
        sub_elements = elem.get('sub_elements', [])

        attributes: list[AttributeDefinition] = []
        summary_attribute = None

        for sub_elem in sub_elements:
            sub_id = sub_elem.get('id')
            sub_type = sub_elem.get('type', 'string')

            # Map v1 types to schema types
            type_map = {
                'string': 'string',
                'integer': 'integer',
                'boolean': 'boolean',
                'choice': 'choice',
            }
            schema_type = type_map.get(sub_type, 'string')

            is_summary = sub_elem.get('is_summary', False)
            if is_summary:
                summary_attribute = sub_id

            attr = AttributeDefinition(
                name=sub_id,
                type=schema_type,
                required=sub_elem.get('required', True),
                default=sub_elem.get('default'),
                options=sub_elem.get('options'),
                min_value=sub_elem.get('min'),
                max_value=sub_elem.get('max'),
                pattern=sub_elem.get('pattern'),
                description=sub_elem.get('tooltip', ''),
                is_summary=is_summary,
            )
            attributes.append(attr)

        return TableDefinition(
            name=elem_id,
            display_name=elem.get('add_button_text', elem_id).replace('Add ', ''),
            attributes=attributes,
            summary_attribute=summary_attribute,
            description=elem.get('tooltip', ''),
        )

    def _parse_v2_schema(self, data: Dict[str, Any]) -> Schema:
        """Parse a v2 format schema with explicit parameters and tables."""
        version = data.get('version', '1.0')
        parameters: Dict[str, ParameterDefinition] = {}
        tables: Dict[str, TableDefinition] = {}

        # Parse parameters
        params_data = data.get('parameters', {})
        for name, param_data in params_data.items():
            if isinstance(param_data, dict):
                parameters[name] = self._parse_parameter_definition(name, param_data)

        # Parse tables
        tables_data = data.get('tables', {})
        for name, table_data in tables_data.items():
            if isinstance(table_data, dict):
                tables[name] = self._parse_table_definition(name, table_data)

        return Schema(version=version, parameters=parameters, tables=tables)

    def _parse_parameter_definition(
        self, name: str, data: Dict[str, Any]
    ) -> ParameterDefinition:
        """Parse a single parameter definition from v2 format."""
        return ParameterDefinition(
            name=name,
            type=data.get('type', 'string'),
            default=data.get('default'),
            options=data.get('options'),
            min_value=data.get('min'),
            max_value=data.get('max'),
            pattern=data.get('pattern'),
            description=data.get('description', ''),
            display_name=data.get('display_name', ''),
            category=data.get('category', ''),
        )

    def _parse_table_definition(
        self, name: str, data: Dict[str, Any]
    ) -> TableDefinition:
        """Parse a single table definition from v2 format."""
        attributes: list[AttributeDefinition] = []
        summary_attribute = data.get('summary_attribute')

        attrs_data = data.get('attributes', [])
        for attr_data in attrs_data:
            if isinstance(attr_data, dict):
                attr = self._parse_attribute_definition(attr_data)
                attributes.append(attr)

                # Track summary attribute
                if attr.is_summary and not summary_attribute:
                    summary_attribute = attr.name

        # Parse validation rules
        validation_rules: list[ValidationRule] = []
        rules_data = data.get('validation', [])
        for rule_data in rules_data:
            if isinstance(rule_data, dict):
                rule = ValidationRule(
                    expression=rule_data.get('rule', ''),
                    message=rule_data.get('message', 'Validation failed'),
                    scope=rule_data.get('scope', 'row'),
                )
                validation_rules.append(rule)

        return TableDefinition(
            name=name,
            display_name=data.get('display_name', name),
            attributes=attributes,
            nested_table=data.get('nested_table'),
            summary_attribute=summary_attribute,
            description=data.get('description', ''),
            validation_rules=validation_rules,
        )

    def _parse_attribute_definition(self, data: Dict[str, Any]) -> AttributeDefinition:
        """Parse a single attribute definition."""
        return AttributeDefinition(
            name=data.get('name', ''),
            type=data.get('type', 'string'),
            required=data.get('required', True),
            default=data.get('default'),
            options=data.get('options'),
            min_value=data.get('min'),
            max_value=data.get('max'),
            pattern=data.get('pattern'),
            description=data.get('description', ''),
            display_name=data.get('display_name', ''),
            is_summary=data.get('is_summary', False),
            unique=data.get('unique', False),
        )


class DataParser:
    """
    Parses user data (parameter values and table rows) from YAML files.

    This is used to load saved configurations that were previously
    generated through the GUI or CLI.
    """

    def __init__(self, schema: Schema):
        self.schema = schema

    def parse_file(self, filepath: str) -> Tuple[Dict[str, Any], Dict[str, Table]]:
        """
        Parse a data file containing parameter values and table data.

        Args:
            filepath: Path to the YAML data file.

        Returns:
            Tuple of (parameters dict, tables dict).
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise SchemaParseError(f"Data file not found: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SchemaParseError(f"Invalid YAML in data file: {e}")

        if not isinstance(data, dict):
            raise SchemaParseError("Data file must contain a YAML dictionary")

        return self.parse_dict(data)

    def parse_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Table]]:
        """
        Parse a dictionary containing parameter values and table data.

        Returns:
            Tuple of (parameters dict, tables dict).
        """
        parameters: Dict[str, Any] = {}
        tables: Dict[str, Table] = {}

        for key, value in data.items():
            if key in self.schema.parameters:
                # This is a simple parameter
                parameters[key] = value
            elif key in self.schema.tables:
                # This is table data
                table_def = self.schema.tables[key]
                table = self._parse_table_data(table_def, value)
                tables[key] = table
            else:
                # Unknown key - could be from an older schema version
                # Store as parameter for backward compatibility
                parameters[key] = value

        return parameters, tables

    def _parse_table_data(
        self, table_def: TableDefinition, data: Any
    ) -> Table:
        """Parse table data into a Table object."""
        if not isinstance(data, list):
            data = [data] if data else []

        rows: list[Row] = []
        for row_data in data:
            if isinstance(row_data, dict):
                row = self._parse_row_data(table_def, row_data)
                rows.append(row)

        return Table(definition=table_def, rows=rows)

    def _parse_row_data(
        self, table_def: TableDefinition, data: Dict[str, Any]
    ) -> Row:
        """Parse a single row's data."""
        # Separate children from attributes
        children_data = data.pop('children', [])
        attributes = dict(data)

        # Parse children if this table has nested tables
        children: list[Row] = []
        if table_def.nested_table and children_data:
            nested_def = self.schema.tables.get(table_def.nested_table)
            if nested_def:
                for child_data in children_data:
                    if isinstance(child_data, dict):
                        child_row = self._parse_row_data(nested_def, child_data)
                        children.append(child_row)

        return Row(attributes=attributes, children=children)
