# Graphical Interface

The `gui` extra adds a graphical interface built on [NiceGUI](https://nicegui.io).
The same app runs as a native desktop window or, with `--web`, as a local web page.

```bash
pip install verigen[gui]
verigen gui
```

The native window uses `pywebview`, which ships with the `gui` extra, so the
desktop experience works out of the box.

## Catalog and wizard

With no argument, `verigen gui` shows a catalog of the generators it discovers (by
default the built-in examples), grouped by category. Selecting one opens its
wizard. Passing a definition opens that generator directly:

```bash
verigen gui path/to/definition.yaml
```

The wizard renders one section per definition page. Each element maps to a
control: text and number inputs, dropdowns, switches, and an editable table (AG
Grid) for `dynamic_table` elements, with buttons to add and remove rows.

## Generate, preview, download

`Generate` validates the inputs through the same pipeline as the CLI. Validation
problems appear as notifications. On success, each generated file is shown in a
tab, and `Download ZIP` packages them. `Download values` saves the current inputs
as a values config, and `Load values` uploads one to refill the form. A values
config produced here reproduces the same output through the CLI.

## Browser vs native window

```bash
verigen gui            # native desktop window (default)
verigen gui --web      # serve in the browser instead
verigen gui --port N   # choose the HTTP port
```

## Styling

The interface separates presentation from behaviour, so the look and feel can be
reworked without touching any backend logic:

- `verigen/ui/theme.py` holds the design tokens (colors, fonts), the Tailwind/
  Quasar class constants, button props, and small component helpers (`page`,
  `header`, `section`).
- `verigen/ui/static/theme.css` holds the global CSS.
- `verigen/ui/app.py` describes the page structure and references the theme.

Editing those three files restyles the app. The backend (`verigen/core/` and
`verigen/ui/forms.py`) is independent and does not need to change.
