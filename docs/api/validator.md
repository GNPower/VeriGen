# Validation

The `verigen.core.validator` module provides schema-driven validation for parameters and table data.

## Validator

Main validation class that checks data against schema rules.

::: verigen.core.validator.Validator
    options:
      show_root_heading: true
      show_source: false
      members:
        - validate_parameters
        - validate_table
        - validate_all
        - validate_schema

### Example Usage

```python
from verigen import SchemaParser, DataParser, Validator

# Parse schema and data
schema = SchemaParser().parse_file("schema.yaml")
params, tables = DataParser(schema).parse_file("data.yaml")

# Create validator
validator = Validator(schema)

# Validate parameters only
param_errors = validator.validate_parameters(params)

# Validate a specific table
table_errors = validator.validate_table("registers", tables["registers"], params)

# Validate everything at once
result = validator.validate_all(params, tables)

if result.is_valid:
    print("All validations passed!")
else:
    print(result.format_errors())
```

### What Gets Validated

**Parameters:**

- Type checking (string, integer, boolean, choice)
- Range validation (min/max for integers)
- Pattern matching (regex for strings)
- Choice validation (value in options list)
- Unknown parameter warnings

**Tables:**

- Required attributes present
- Type validation for each attribute
- Uniqueness constraints
- Custom validation rules (expressions)
- Nested table validation (recursive)

---

## ValidationResult

Container for validation results with helper methods.

::: verigen.core.validator.ValidationResult
    options:
      show_root_heading: true
      show_source: false
      members:
        - errors
        - is_valid
        - error_count
        - warning_count
        - get_errors
        - get_warnings
        - format_errors

### Example

```python
from verigen import Validator

result = validator.validate_all(params, tables)

# Check if valid (only errors count, not warnings)
if result.is_valid:
    print("Valid!")
else:
    print(f"Found {result.error_count} errors, {result.warning_count} warnings")

    # Get only errors
    for error in result.get_errors():
        print(f"ERROR: {error.path}: {error.message}")

    # Get formatted output
    print(result.format_errors())
```

---

## ValidationError

Represents a single validation error or warning.

::: verigen.core.validator.ValidationError
    options:
      show_root_heading: true
      show_source: false
      members:
        - path
        - message
        - severity

### Severity Levels

- `"error"` - Validation failure, data is invalid
- `"warning"` - Potential issue, but data can still be used

### Example

```python
from verigen import ValidationError

# Create an error manually
error = ValidationError(
    path="registers[0].offset",
    message="Offset must be 4-byte aligned",
    severity="error"
)

print(error)  # "[ERROR] registers[0].offset: Offset must be 4-byte aligned"
```

---

## Custom Validation Rules

Define custom validation logic in your schema:

```yaml
tables:
  registers:
    attributes:
      - name: offset
        type: integer
        unique: true  # Built-in uniqueness check

    validation:
      # Custom expression-based rules
      - rule: "offset % 4 == 0"
        message: "Offset must be 4-byte aligned"

      - rule: "offset < 4096"
        message: "Offset exceeds address space"
```

Rules have access to:

- All attributes of the current row
- All schema parameters
- Python operators and built-in functions

```yaml
validation:
  # Using parameters in rules
  - rule: "bit_offset + bit_width <= data_width"
    message: "Field exceeds register width"

  # Complex expressions
  - rule: "len(name) <= 32"
    message: "Name too long (max 32 characters)"
```

---

## Schema Self-Validation

Validate the schema itself for consistency:

```python
from verigen import SchemaParser, Validator

schema = SchemaParser().parse_file("schema.yaml")
validator = Validator(schema)

# Check schema consistency
result = validator.validate_schema()

if not result.is_valid:
    print("Schema has issues:")
    print(result.format_errors())
```

This checks for:

- Duplicate attribute names in tables
- Invalid `nested_table` references
- Circular table dependencies
- Invalid default values
