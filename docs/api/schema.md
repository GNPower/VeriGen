# Schema Parsing

The `verigen.core.schema` module handles parsing of schema and data files.

## SchemaParser

Parses schema definition files (YAML) into `Schema` objects.

::: verigen.core.schema.SchemaParser
    options:
      show_root_heading: true
      show_source: false
      members:
        - parse_file
        - parse_dict

### Supported Schema Versions

**Version 2.0** (recommended):

```yaml
version: "2.0"

parameters:
  module_name:
    type: string
    default: "my_module"

tables:
  registers:
    attributes:
      - name: name
        type: string
        required: true
```

**Version 1.0** (legacy UI spec format):

```yaml
pages:
  - title: "Settings"
    elements:
      - id: module_name
        type: string
        label: "Module Name"
        default: "my_module"
```

### Example Usage

```python
from verigen import SchemaParser

parser = SchemaParser()

# Parse from file
schema = parser.parse_file("schema.yaml")

# Parse from dictionary
schema = parser.parse_dict({
    "version": "2.0",
    "parameters": {
        "width": {"type": "integer", "default": 32}
    },
    "tables": {
        "items": {
            "attributes": [
                {"name": "id", "type": "integer", "required": True}
            ]
        }
    }
})

# Access parsed schema
print(schema.version)  # "2.0"
print(schema.parameters["width"].default)  # 32
print(schema.tables["items"].attributes[0].name)  # "id"
```

---

## DataParser

Parses data files against a schema, converting raw data into `Table` and `Row` objects.

::: verigen.core.schema.DataParser
    options:
      show_root_heading: true
      show_source: false
      members:
        - parse_file
        - parse_dict

### Example Usage

```python
from verigen import SchemaParser, DataParser

# First parse the schema
schema_parser = SchemaParser()
schema = schema_parser.parse_file("schema.yaml")

# Then parse data against the schema
data_parser = DataParser(schema)

# Parse from file
params, tables = data_parser.parse_file("data.yaml")

# Parse from dictionary
params, tables = data_parser.parse_dict({
    "module_name": "my_regfile",
    "registers": [
        {
            "name": "CTRL",
            "offset": 0,
            "children": [
                {"name": "enable", "bit_offset": 0, "bit_width": 1}
            ]
        }
    ]
})

# Access parsed data
print(params["module_name"])  # "my_regfile"

for row in tables["registers"].rows:
    print(f"Register: {row.name} @ {row.offset}")
    for field in row.children:
        print(f"  Field: {field.name}")
```

### Data File Format

Data files are YAML with parameter values and table rows:

```yaml
# Parameters (simple key-value)
module_name: "my_regfile"
data_width: 32

# Table data (list of rows)
registers:
  - name: CTRL
    offset: 0
    access: RW
    children:  # Nested table rows
      - name: enable
        bit_offset: 0
        bit_width: 1
      - name: mode
        bit_offset: 1
        bit_width: 2

  - name: STATUS
    offset: 4
    access: RO
    children:
      - name: ready
        bit_offset: 0
        bit_width: 1
```

---

## SchemaParseError

Exception raised when schema parsing fails.

::: verigen.core.schema.SchemaParseError
    options:
      show_root_heading: true
      show_source: false

### Example

```python
from verigen import SchemaParser, SchemaParseError

parser = SchemaParser()

try:
    schema = parser.parse_file("nonexistent.yaml")
except SchemaParseError as e:
    print(f"Failed to parse schema: {e}")
```
