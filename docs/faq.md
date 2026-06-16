# Frequently Asked Questions

## General

### What is VeriGen?

VeriGen is a schema-driven template engine for generating SystemVerilog, Verilog, and related files. It uses Jinja2 templates and YAML configuration to generate code from structured data.

### How is VeriGen different from other register generators?

VeriGen is **generic** - it doesn't hardcode concepts like "registers" or "fields". You define your own data structures through schemas. This means you can use it for:

- Register files (like AirHDL or SystemRDL tools)
- State machines
- Memory maps
- Configuration tables
- Any hierarchical hardware structure

### What file formats can VeriGen generate?

Any text-based format! VeriGen uses Jinja2 templates, so you can generate:

- SystemVerilog/Verilog RTL
- C/C++ headers
- Python bindings
- Markdown documentation
- TCL scripts
- JSON/YAML configuration
- And more...

---

## Installation

### What Python version do I need?

Python 3.8 or higher is required.

### Can I use VeriGen without the GUI?

Yes! The CLI works independently:

```bash
verigen generate project.verigen.yaml -o output/
```

If you want to skip PySide6 installation:

```bash
pip install jinja2 pyyaml
pip install --no-deps verigen
```

### Why does PySide6 fail to install?

On some Linux systems, you may need system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install libxcb-xinerama0 libxcb-cursor0
```

---

## Schema & Configuration

### What's the difference between v1 and v2 schema format?

**Version 2.0** (recommended) separates parameters and table definitions clearly:

```yaml
version: "2.0"
parameters:
  width: {type: integer, default: 32}
tables:
  items: {attributes: [...]}
```

**Version 1.0** (legacy) uses a UI-centric format with pages and elements:

```yaml
pages:
  - title: "Settings"
    elements:
      - {id: width, type: integer, default: 32}
```

Both formats are supported, but v2 is cleaner for complex schemas.

### How do I define nested tables?

Use `nested_table` to reference a child table:

```yaml
tables:
  registers:
    attributes: [...]
    nested_table: fields  # Children come from 'fields' table

  fields:
    attributes: [...]
```

In templates, access children via `.children`:

```jinja2
{% for reg in registers %}
  {% for field in reg.children %}
    {{ field.name }}
  {% endfor %}
{% endfor %}
```

### How do I enforce unique values?

Add `unique: true` to the attribute:

```yaml
attributes:
  - name: offset
    type: integer
    unique: true  # No two rows can have the same offset
```

### Can I have custom validation rules?

Yes! Add `validation` rules to tables:

```yaml
tables:
  registers:
    validation:
      - rule: "offset % 4 == 0"
        message: "Offset must be 4-byte aligned"
```

Rules can reference any attribute or parameter.

---

## Templates

### How do I access nested data in templates?

Use `.children` for nested rows:

```jinja2
{% for register in registers %}
{{ register.name }}:
  {% for field in register.children %}
  - {{ field.name }}: [{{ field.bit_offset }}]
  {% endfor %}
{% endfor %}
```

### What filters are available?

See the [Template Engine API](api/engine.md#built-in-filters) for the full list. Common ones:

- `hex_format(digits)` - Format as hex: `{{ 255 | hex_format(4) }}` → `0x00FF`
- `verilog_hex(width)` - Verilog literal: `{{ 255 | verilog_hex(8) }}` → `8'hFF`
- `bit_range` - Bit range: `{{ field | bit_range }}` → `[7:0]`
- `snake_case` - Convert: `{{ "CamelCase" | snake_case }}` → `camel_case`

### How do I handle optional values?

Use Jinja2's `default` filter:

```jinja2
{{ field.reset_value | default(0) }}
{{ field.description | default("No description") }}
```

### Can I use template inheritance?

Yes! Standard Jinja2 inheritance works:

```jinja2
{# base.sv.j2 #}
// Header
{% block content %}{% endblock %}
// Footer

{# module.sv.j2 #}
{% extends "base.sv.j2" %}
{% block content %}
module {{ module_name }};
endmodule
{% endblock %}
```

---

## GUI

### How do I launch the GUI?

```bash
verigen gui path/to/project.verigen.yaml
```

### Can I edit the schema in the GUI?

Currently, the GUI is for editing **data** against a schema, not the schema itself. Edit schema files in a text editor.

### How do I add rows in the table editor?

- Click the **"+"** button to add a row
- Select a row and click **"+"** to add a child (nested) row
- Use the **"-"** button to delete selected rows

---

## Troubleshooting

### "Undefined variable" error in template

The variable isn't in your context. Check:

1. Is it defined in your data file?
2. Is the schema correct?
3. Use `{{ var | default("fallback") }}` for optional values

### Validation fails but data looks correct

Check:

1. Required fields are present
2. Types match (e.g., integer vs string)
3. Values are in allowed ranges
4. Choice values exactly match options
5. Unique constraints aren't violated

### Generated files have wrong line endings

Jinja2 preserves template line endings. Ensure your `.j2` files use the desired line ending style (LF for Unix, CRLF for Windows).

---

## Still have questions?

- Open a [Discussion](https://github.com/GNPower/VeriGen/discussions)
- Check the [API Reference](api/index.md)
- Browse [Example Projects](https://github.com/GNPower/VeriGen/tree/main/my_ip_projects)
