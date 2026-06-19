# Extension Hooks

The declarative path (templates, config, and built-in filters) covers most
generators. When you need real logic, a definition can declare a Python module:

```yaml
extension: ext.py            # relative to the definition file
```

VeriGen imports that module and calls its `register(api)` function. The module
lives in your repository, not in VeriGen.

## The three hook kinds

```python
def register(api):
    @api.filter("shout")
    def _shout(value):
        """A custom Jinja filter."""
        return f"{str(value).upper()}!"

    @api.validator
    def _depth_is_power_of_two(values, definition):
        """Return a list of error strings; non-empty fails generation."""
        depth = values["depth"]
        if depth & (depth - 1):
            return [f"depth ({depth}) must be a power of two"]
        return []

    @api.context
    def _derive_address_width(values, definition):
        """Return a dict merged into the render context."""
        return {"addr_width": max(1, (values["depth"] - 1).bit_length())}
```

- **Filters** (`api.filter("name")`) add Jinja filters. Use `api.add_global(name,
  value)` for globals.
- **Validators** (`api.validator`) receive the normalized values and the
  definition, and return a list of human-readable errors. Any non-empty result
  stops generation and is reported alongside the built-in validation.
- **Context providers** (`api.context`) receive the values and the definition and
  return a dict merged into the render context. This is where derived values such
  as computed address widths belong.

Validators run after the built-in checks pass, so they can assume values are
present and the right type. Context providers run after validation, so they can
assume valid input.

## Trust model

Loading a definition that declares an extension executes that extension's Python
code, the same as running a build script or a `setup.py`. Only run definitions
you trust.
