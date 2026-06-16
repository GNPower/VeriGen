# Data Models

The `verigen.core.models` module contains the core data classes used throughout VeriGen.

## Schema Definition Classes

### AttributeDefinition

Defines a single attribute (column) in a table.

::: verigen.core.models.AttributeDefinition
    options:
      show_root_heading: true
      show_source: false
      members:
        - name
        - type
        - required
        - default
        - options
        - min_value
        - max_value
        - pattern
        - unique
        - description
        - validate_value

**Example:**

```python
from verigen import AttributeDefinition

# String attribute with pattern validation
name_attr = AttributeDefinition(
    name="module_name",
    type="string",
    required=True,
    pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    description="Valid Verilog identifier"
)

# Integer attribute with range
offset_attr = AttributeDefinition(
    name="offset",
    type="integer",
    required=True,
    min_value=0,
    max_value=4096,
    unique=True
)

# Choice attribute
access_attr = AttributeDefinition(
    name="access",
    type="choice",
    options=["RW", "RO", "WO"],
    default="RW"
)
```

---

### TableDefinition

Defines a table structure with its attributes and optional nesting.

::: verigen.core.models.TableDefinition
    options:
      show_root_heading: true
      show_source: false
      members:
        - name
        - display_name
        - attributes
        - nested_table
        - summary_attribute
        - validation_rules
        - description
        - get_attribute

**Example:**

```python
from verigen import TableDefinition, AttributeDefinition

registers_table = TableDefinition(
    name="registers",
    display_name="Registers",
    attributes=[
        AttributeDefinition(name="name", type="string", required=True),
        AttributeDefinition(name="offset", type="integer", unique=True),
    ],
    nested_table="fields",  # Can contain 'fields' rows
    summary_attribute="name"
)
```

---

### ParameterDefinition

Defines a simple (non-table) parameter.

::: verigen.core.models.ParameterDefinition
    options:
      show_root_heading: true
      show_source: false
      members:
        - name
        - type
        - default
        - options
        - min_value
        - max_value
        - pattern
        - description
        - get_default
        - validate_value

**Example:**

```python
from verigen import ParameterDefinition

width_param = ParameterDefinition(
    name="data_width",
    type="choice",
    options=[32, 64, 128],
    default=32,
    description="AXI data bus width"
)

# Get default value
print(width_param.get_default())  # 32

# Validate a value
errors = width_param.validate_value(64)  # []
errors = width_param.validate_value(16)  # ["Invalid choice..."]
```

---

### ValidationRule

Defines a custom validation rule for a table.

::: verigen.core.models.ValidationRule
    options:
      show_root_heading: true
      show_source: false

**Example:**

```python
from verigen import ValidationRule

# Alignment rule
alignment_rule = ValidationRule(
    expression="offset % 4 == 0",
    message="Offset must be 4-byte aligned"
)

# Range rule using parameters
range_rule = ValidationRule(
    expression="bit_offset + bit_width <= data_width",
    message="Field exceeds register width"
)
```

---

### Schema

The complete schema containing parameters and table definitions.

::: verigen.core.models.Schema
    options:
      show_root_heading: true
      show_source: false
      members:
        - version
        - parameters
        - tables
        - get_all_parameter_defaults

**Example:**

```python
from verigen import Schema, ParameterDefinition, TableDefinition

schema = Schema(
    version="2.0",
    parameters={
        "module_name": ParameterDefinition(name="module_name", type="string", default="my_mod"),
    },
    tables={
        "registers": TableDefinition(name="registers", attributes=[...]),
    }
)

# Get all defaults
defaults = schema.get_all_parameter_defaults()
# {"module_name": "my_mod"}
```

---

## Data Classes

### Row

A single row of data in a table, with support for dot-notation access in templates.

::: verigen.core.models.Row
    options:
      show_root_heading: true
      show_source: false
      members:
        - attributes
        - children
        - get
        - to_dict
        - from_dict

**Example:**

```python
from verigen import Row

# Create a row with attributes
row = Row(attributes={
    "name": "CTRL",
    "offset": 0x00,
    "access": "RW"
})

# Dot notation access (for templates)
print(row.name)    # "CTRL"
print(row.offset)  # 0

# With nested children
register = Row(
    attributes={"name": "STATUS", "offset": 0x04},
    children=[
        Row(attributes={"name": "ready", "bit_offset": 0, "bit_width": 1}),
        Row(attributes={"name": "error", "bit_offset": 1, "bit_width": 1}),
    ]
)

for field in register.children:
    print(f"  {field.name}: [{field.bit_offset}]")
```

---

### Table

A collection of rows with validation support.

::: verigen.core.models.Table
    options:
      show_root_heading: true
      show_source: false
      members:
        - definition
        - rows
        - validate

**Example:**

```python
from verigen import Table, TableDefinition, AttributeDefinition, Row

# Define table structure
table_def = TableDefinition(
    name="registers",
    attributes=[
        AttributeDefinition(name="name", type="string", required=True),
        AttributeDefinition(name="offset", type="integer", unique=True),
    ]
)

# Create table with data
table = Table(
    definition=table_def,
    rows=[
        Row(attributes={"name": "CTRL", "offset": 0}),
        Row(attributes={"name": "STATUS", "offset": 4}),
    ]
)

# Validate
errors = table.validate()
if errors:
    for error in errors:
        print(error)
```
