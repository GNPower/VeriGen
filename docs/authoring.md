# Authoring a Generator

A generator is a directory containing a definition file, the templates it
references, and (optionally) a Python extension module and an example values
config. Scaffold one with `verigen new <id>`.

## Definition format

```yaml
verigen_version: "1"
id: synchronizer            # identifier; letters, digits, underscore
name: Multi-bit Synchronizer
description: A parameterizable multi-flip-flop synchronizer.
version: "1.0.0"
category: CDC               # used to group entries in the catalog
icon: icons/logo.png        # optional, relative to the definition file
extension: ext.py           # optional Python hooks, relative to the definition

pages:
  - title: Settings
    elements:
      - id: module_name
        type: string
        label: Module Name
        default: synchronizer
      - id: width
        type: integer
        label: Data Width (bits)
        default: 1
        min: 1
        max: 4096
      - id: include_reset
        type: boolean
        label: Include async reset
        default: true

outputs:
  - template: templates/synchronizer.sv.j2
    destination: "{{ module_name }}.sv"
```

`pages` describe both the wizard layout and the input contract. `outputs` map a
template to a destination path. Both the path and the template body render with
the values, so destinations can be templated.

## Element types

| Type | Produces | Key fields |
| --- | --- | --- |
| `string` | one-line text | `default` |
| `text` | multi-line text | `default` |
| `integer` | whole number | `default`, `min`, `max` |
| `float` | decimal number | `default`, `min`, `max` |
| `choice` | one option | `options`, `default` |
| `boolean` | true/false | `default` |
| `dynamic_table` | a list of rows | `sub_elements`, `add_button_text`, `row_label` |
| `label` | display only | `text` |
| `image` | display only | `path`, `height` |

A scalar variable with no `default` is required. A `dynamic_table` row is built
from `sub_elements`, which are themselves scalar elements. Mark one row field
`is_summary: true` to use its value as the row's label in the wizard.

## Values config

A values config supplies the variables for one run:

```yaml
module_name: cdc_sync
width: 8
include_reset: true
```

Validation reports every problem at once: a missing required value, a number out
of range, a `choice` outside its options, an unknown variable, or a malformed
table row.

## Templates and filters

Templates render with [Jinja2](https://jinja.palletsprojects.com/) using
`StrictUndefined`, so an undefined variable raises an error instead of rendering
blank. Built-in filters:

- Text: `snake_case`, `kebab_case`, `camel_case`, `pascal_case`, `upper_case`,
  `comment_block`, `pad`.
- Numbers and bits: `clog2`, `mask`, `to_hex`, `to_bin`, `sv_hex`, `bits`.

`clog2` and `mask` are also available as functions, so a template can write
`clog2(depth)`. A `verigen` object exposes `name`, `id`, `version`, and
`description` for file headers.

For logic beyond filters and config, see [Extension Hooks](extensions.md).
