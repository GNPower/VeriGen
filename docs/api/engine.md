# Template Engine

The `verigen.core.engine` module provides Jinja2-based template rendering with hardware-focused filters.

## TemplateEngine

Main template rendering engine with built-in filters for hardware development.

::: verigen.core.engine.TemplateEngine
    options:
      show_root_heading: true
      show_source: false
      members:
        - render_template
        - render_string
        - add_filter
        - add_global

### Example Usage

```python
from verigen import TemplateEngine

engine = TemplateEngine()

# Render a template file
result = engine.render_template(
    template_name="module.sv.j2",
    template_dir="./templates",
    context={"module_name": "my_design", "width": 32}
)

# Render a string template
result = engine.render_string(
    template_string="module {{ module_name }};",
    template_dir="./templates",  # For includes
    context={"module_name": "my_design"}
)

print(result)
```

### Adding Custom Filters

```python
from verigen import TemplateEngine

engine = TemplateEngine()

# Add a custom filter
def reverse_bits(value, width):
    """Reverse the bits of a value."""
    result = 0
    for i in range(width):
        if value & (1 << i):
            result |= 1 << (width - 1 - i)
    return result

engine.add_filter("reverse_bits", reverse_bits)

# Use in template
result = engine.render_string(
    "{{ 0b1010 | reverse_bits(4) }}",  # Output: 5 (0b0101)
    template_dir=".",
    context={}
)
```

### Adding Global Variables

```python
engine = TemplateEngine()

# Add globals available in all templates
engine.add_global("tool_version", "2.0.0")
engine.add_global("author", "VeriGen")

# Use in template: {{ tool_version }}
```

---

## generate_templates

High-level function to generate all templates for a project.

::: verigen.core.engine.generate_templates
    options:
      show_root_heading: true
      show_source: false

### Example Usage

```python
from verigen import generate_templates

project_data = {
    "templates": [
        {
            "source": "templates/rtl/module.sv.j2",
            "destination": "rtl/{{ module_name }}.sv"
        },
        {
            "source": "templates/sw/regs.h.j2",
            "destination": "sw/{{ module_name }}_regs.h"
        }
    ]
}

user_params = {
    "module_name": "my_regfile",
    "data_width": 32,
    "registers": [
        {"name": "CTRL", "offset": 0, "children": [...]},
        {"name": "STATUS", "offset": 4, "children": [...]}
    ]
}

generated_files = generate_templates(
    project_data=project_data,
    project_base_dir="./my_project",
    output_dir="./output",
    user_params=user_params
)

for path in generated_files:
    print(f"Generated: {path}")
```

---

## TemplateError

Exception raised when template rendering fails.

::: verigen.core.engine.TemplateError
    options:
      show_root_heading: true
      show_source: false

### Common Causes

- **Undefined variable**: Accessing a variable not in context
- **Template not found**: Invalid template path
- **Syntax error**: Invalid Jinja2 syntax
- **Filter error**: Filter raised an exception

```python
from verigen import TemplateEngine, TemplateError

engine = TemplateEngine()

try:
    result = engine.render_string(
        "{{ undefined_var }}",
        template_dir=".",
        context={}
    )
except TemplateError as e:
    print(f"Template error: {e}")
```

---

## Built-in Filters

VeriGen provides hardware-focused Jinja2 filters:

### Number Formatting

| Filter | Description | Example | Output |
|--------|-------------|---------|--------|
| `hex_format(digits)` | Format as hex with prefix | `{{ 255 \| hex_format(4) }}` | `0x00FF` |
| `verilog_hex(width)` | Verilog hex literal | `{{ 255 \| verilog_hex(8) }}` | `8'hFF` |
| `format_bin(width)` | Binary with padding | `{{ 5 \| format_bin(8) }}` | `00000101` |

### Bit Operations

| Filter | Description | Example | Output |
|--------|-------------|---------|--------|
| `bit_range` | Verilog bit range | `{{ field \| bit_range }}` | `[7:0]` |
| `mask` | Bit mask value | `{{ field \| mask }}` | `255` |
| `range_str(low)` | Range string | `{{ 31 \| range_str(0) }}` | `[31:0]` |
| `count_ones` | Population count | `{{ 0xF0 \| count_ones }}` | `4` |

### Math Functions

| Filter | Description | Example | Output |
|--------|-------------|---------|--------|
| `log2` | Log base 2 | `{{ 256 \| log2 }}` | `8` |
| `clog2` | Ceiling log base 2 | `{{ 257 \| clog2 }}` | `9` |
| `pow2` | Power of 2 | `{{ 8 \| pow2 }}` | `256` |
| `align(boundary)` | Align to boundary | `{{ 100 \| align(64) }}` | `128` |

### String Conversion

| Filter | Description | Example | Output |
|--------|-------------|---------|--------|
| `snake_case` | To snake_case | `{{ "CamelCase" \| snake_case }}` | `camel_case` |
| `upper_snake_case` | To UPPER_SNAKE | `{{ "CamelCase" \| upper_snake_case }}` | `CAMEL_CASE` |
| `camel_case` | To camelCase | `{{ "snake_case" \| camel_case }}` | `snakeCase` |
| `pascal_case` | To PascalCase | `{{ "snake_case" \| pascal_case }}` | `SnakeCase` |

### Utility

| Filter | Description | Example | Output |
|--------|-------------|---------|--------|
| `plural(word)` | Pluralize | `{{ 5 \| plural("register") }}` | `registers` |

---

## Template Examples

### Register File Header

```jinja2
// {{ module_name }}.sv
// Generated by VeriGen {{ tool_version }}

module {{ module_name }} #(
    parameter DATA_WIDTH = {{ data_width }},
    parameter ADDR_WIDTH = {{ addr_width | default(12) }}
)(
    input wire clk,
    input wire rst_n
);

// Address definitions
{% for reg in registers %}
localparam logic [ADDR_WIDTH-1:0] ADDR_{{ reg.name | upper }} = {{ reg.offset | verilog_hex(addr_width) }};
{% endfor %}

endmodule
```

### C Header with Bit Fields

```jinja2
// {{ module_name }}_regs.h
#ifndef {{ module_name | upper }}_REGS_H
#define {{ module_name | upper }}_REGS_H

{% for reg in registers %}
// {{ reg.name }} @ offset {{ reg.offset | hex_format(4) }}
{% for field in reg.children %}
#define {{ module_name | upper }}_{{ reg.name }}_{{ field.name | upper }}_OFFSET {{ field.bit_offset }}
#define {{ module_name | upper }}_{{ reg.name }}_{{ field.name | upper }}_WIDTH  {{ field.bit_width }}
#define {{ module_name | upper }}_{{ reg.name }}_{{ field.name | upper }}_MASK   {{ field | mask | hex_format(8) }}
{% endfor %}

{% endfor %}
#endif
```

### Accessing Nested Data

```jinja2
{% for register in registers %}
Register: {{ register.name }}
  Offset: {{ register.offset | hex_format(4) }}
  Access: {{ register.access }}
  {% if register.children %}
  Fields:
  {% for field in register.children %}
    - {{ field.name }} {{ field | bit_range }}: {{ field.access }}
  {% endfor %}
  {% endif %}

{% endfor %}
```
