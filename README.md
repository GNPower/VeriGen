# VeriGen

VeriGen is a general, config-driven generator for Verilog and SystemVerilog. You
describe a module once as a *generator definition* (metadata, the input variables,
the wizard UI, and the output templates), and VeriGen renders Jinja2 templates
from that definition and a set of values.

VeriGen ships no IP-specific logic. Registers, FIFOs, bus bridges, and the like
are authored by you as templates plus config in your own repository, VeriGen just
loads and renders them.

## How it works

Two kinds of file drive a run:

- A **generator definition** (authored once, by the template author): one YAML
  file declaring the metadata, the variables grouped into wizard pages, the
  output templates, and an optional Python extension module.
- A **values config** (per use): a plain `variable: value` mapping. The CLI reads
  one to generate headlessly. The desktop wizard writes one when you save your
  inputs and reads one when you reload them. The same values file reproduces the
  same output through either interface.

The pipeline is one path shared by the CLI and the UI:

```
load definition -> validate values -> build context -> render templates -> write files
```

## Install

```bash
pip install verigen            # core engine + CLI
pip install verigen[gui]       # adds the graphical interface (NiceGUI)
```

For development from a checkout:

```bash
python -m venv env
. env/Scripts/activate        # Windows
env/bin/activate              # Unix
pip install -e ".[gui]"
```

## Quick start

Scaffold a generator, then render it:

```bash
verigen new my_module                       # writes my_module/ with a starter generator
verigen generate my_module/definition.yaml -c my_module/values.example.yaml -o out
```

List the built-in example generators, or any directory of definitions:

```bash
verigen list                                # built-in examples
verigen list path/to/your/generators        # your own
```

Validate a definition (and optionally a values config) without writing files:

```bash
verigen validate my_module/definition.yaml -c my_module/values.example.yaml
```

Open the graphical interface (a catalog plus a wizard per generator), or point it
at one definition directly:

```bash
verigen gui                                 # catalog of the built-in examples
verigen gui my_module/definition.yaml       # open one generator's wizard
verigen gui --web                           # use the browser instead of a window
```

By default the interface opens in a native desktop window (via pywebview, which
ships with the `gui` extra); pass `--web` to use the browser instead. Export the
definition format as JSON Schema for editor autocompletion:

```bash
verigen schema -o verigen.schema.json
```

## Defining a generator

A minimal definition:

```yaml
verigen_version: "1"
id: synchronizer
name: Multi-bit Synchronizer
description: A parameterizable multi-flip-flop synchronizer.
category: CDC

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

Element types: `string`, `text` (multi-line), `integer` and `float` (with
`min`/`max`), `choice` (with `options`), `boolean`, and `dynamic_table` (a
repeatable group of rows, each row built from `sub_elements`). Display-only
elements are `label` and `image`. Both the `destination` path and the template
body are rendered with the values, so output filenames can be templated.

Templates render with [Jinja2](https://jinja.palletsprojects.com/). Undefined
variables raise an error rather than rendering blank. Built-in filters cover
common code-generation needs: `snake_case`, `camel_case`, `pascal_case`,
`upper_case`, `comment_block`, `clog2`, `mask`, `to_hex`, `to_bin`, `sv_hex`, and
`bits`. A `verigen` object exposes the definition name, id, version, and
description for file headers.

## Optional Python hooks

When templates and config are not enough (cross-field validation, derived values,
custom filters), a definition can point at a Python module in its own directory:

```yaml
extension: ext.py
```

```python
def register(api):
    @api.filter("shout")
    def _shout(value):
        return f"{str(value).upper()}!"

    @api.validator
    def _depth_is_power_of_two(values, definition):
        depth = values["depth"]
        if depth & (depth - 1):
            return [f"depth ({depth}) must be a power of two"]
        return []

    @api.context
    def _derive(values, definition):
        return {"addr_width": max(1, (values["depth"] - 1).bit_length())}
```

This code lives in your repository, never in VeriGen. Loading a definition that
declares an extension runs that extension's code, the same as running a build
script.

## Examples

The package ships generic examples under `verigen/examples/`:

- `synchronizer`: parameters, conditional ports, and the `clog2` filter.
- `mux`: a variable-length input list via `dynamic_table`.
- `extension_demo`: a custom filter, a value validator, and a derived value.
- `params_demo`: every scalar input type, including `text` and `float`.

Run `verigen list` to see them, then generate any one with `verigen generate`.

## Development

```bash
pip install -e ".[all]"
pip install pytest
pytest
```

Tests cover the loader, values validation, filters, the pipeline (including
byte-for-byte golden comparison of the examples), the extension hooks, catalog
discovery, the UI helpers, and a live NiceGUI server check. Tests that need the
`gui` extra skip when it is not installed. Generated SystemVerilog is linted
against `verible-verilog-lint` or `verilator` when either is on `PATH`, and
skipped otherwise.

## License

MIT. See [LICENSE](LICENSE).
