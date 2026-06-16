# API Reference

VeriGen provides a Python API for programmatic use. This is useful for:

- Integrating VeriGen into build systems
- Creating custom generation scripts
- Extending VeriGen's functionality

## Module Overview

```python
from verigen import (
    # Data Models
    Schema,
    TableDefinition,
    AttributeDefinition,
    ParameterDefinition,
    ValidationRule,
    Table,
    Row,

    # Schema Parsing
    SchemaParser,
    DataParser,
    SchemaParseError,

    # Validation
    Validator,
    ValidationResult,
    ValidationError,

    # Template Engine
    TemplateEngine,
    TemplateError,
    generate_templates,
)
```

## Quick Example

```python
from verigen import SchemaParser, DataParser, Validator, generate_templates

# Parse schema
schema_parser = SchemaParser()
schema = schema_parser.parse_file("schema.yaml")

# Parse data
data_parser = DataParser(schema)
params, tables = data_parser.parse_file("data.yaml")

# Validate
validator = Validator(schema)
result = validator.validate_all(params, tables)

if not result.is_valid:
    print(result.format_errors())
else:
    # Generate templates
    project_data = {
        "templates": [
            {"source": "template.sv.j2", "destination": "output.sv"}
        ]
    }

    generated = generate_templates(
        project_data=project_data,
        project_base_dir="./project",
        output_dir="./output",
        user_params=params
    )

    print(f"Generated: {generated}")
```

## API Sections

<div class="grid cards" markdown>

-   **[Models](models.md)**

    ---

    Core data classes: `Schema`, `Table`, `Row`, `AttributeDefinition`

-   **[Schema Parsing](schema.md)**

    ---

    `SchemaParser` and `DataParser` for YAML file handling

-   **[Validation](validator.md)**

    ---

    `Validator` for schema-driven data validation

-   **[Template Engine](engine.md)**

    ---

    `TemplateEngine` and Jinja2 template rendering

</div>
