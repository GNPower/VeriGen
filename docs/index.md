# VeriGen

**A generic code generation tool for SystemVerilog and Verilog using Jinja2 templates.**

[![PyPI version](https://badge.fury.io/py/VeriGen.svg)](https://badge.fury.io/py/VeriGen)
[![Testing](https://github.com/GNPower/VeriGen/actions/workflows/test.yml/badge.svg)](https://github.com/GNPower/VeriGen/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is VeriGen?

VeriGen is a **schema-driven template engine** designed for hardware engineers. It allows you to:

- Define **hierarchical data structures** through YAML schema files
- Create **Jinja2 templates** for any output format (RTL, headers, documentation)
- Generate code using a **CLI** or **GUI** interface
- **Validate** your data against schema-defined rules

Unlike domain-specific tools, VeriGen is **generic**. You define what your data means (registers, FSM states, memory maps, etc.) - VeriGen handles the generation.

## Key Features

- **Schema-Driven**: Define parameters, tables, and validation rules in YAML
- **Hierarchical Data**: Support for nested tables (e.g., registers containing fields)
- **Rich Validation**: Type checking, ranges, patterns, uniqueness, and custom rules
- **Template Flexibility**: Full Jinja2 power with hardware-focused filters
- **Dual Interface**: CLI for automation, PySide6 GUI for interactive editing
- **Project-Based**: Organize schemas, templates, and data in reusable projects

## Quick Example

Define a schema for your data structure:

```yaml
# schema.yaml
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
      - name: offset
        type: integer
        unique: true
    nested_table: fields

  fields:
    attributes:
      - name: bit_offset
        type: integer
      - name: bit_width
        type: integer
```

Create a Jinja2 template:

```jinja2
// {{ module_name }}.sv
module {{ module_name }} (
    input wire clk,
    input wire rst_n
);

{% for reg in registers %}
// Register: {{ reg.name }} @ offset {{ reg.offset | hex_format(4) }}
{% for field in reg.children %}
//   [{{ field.bit_offset + field.bit_width - 1 }}:{{ field.bit_offset }}] {{ field.name }}
{% endfor %}
{% endfor %}

endmodule
```

Generate your code:

```bash
verigen generate my_project.verigen.yaml -o output/
```

## Use Cases

VeriGen excels at generating:

- **AXI/Wishbone Register Files** - RTL, software headers, documentation
- **Memory Maps** - Address decoders, configuration tables
- **State Machines** - FSM templates with state/transition definitions
- **Test Infrastructure** - Testbenches, simulation scripts
- **Documentation** - Markdown, HTML from the same data source

## Getting Started

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Installation**

    ---

    Install VeriGen with pip in one command

    [:octicons-arrow-right-24: Install now](installation.md)

-   :material-rocket-launch:{ .lg .middle } **Quick Start**

    ---

    Create your first VeriGen project in minutes

    [:octicons-arrow-right-24: Get started](usage.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Full Python API documentation

    [:octicons-arrow-right-24: API docs](api/index.md)

-   :material-github:{ .lg .middle } **Examples**

    ---

    Browse example projects on GitHub

    [:octicons-arrow-right-24: Examples](https://github.com/GNPower/VeriGen/tree/main/my_ip_projects)

</div>
