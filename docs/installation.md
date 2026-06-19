# Installation

VeriGen requires Python 3.9 or newer.

## From PyPI

```bash
pip install verigen            # core engine + CLI
pip install verigen[gui]       # adds the graphical interface (NiceGUI)
```

The core install has three runtime dependencies: Jinja2, PyYAML, and Pydantic.
The interface is optional; the CLI and the library never import it.

## From a checkout

```bash
python -m venv .venv
. .venv/Scripts/activate        # Windows
env/bin/activate                # Unix
pip install -e ".[gui]"
```

## Verify

```bash
verigen --version
verigen list                    # lists the built-in example generators
```

## Optional HDL linters

The test suite lints generated SystemVerilog when `verible-verilog-lint` or
`verilator` is on `PATH`, and skips those checks otherwise. Neither tool is
required to install or use VeriGen.
