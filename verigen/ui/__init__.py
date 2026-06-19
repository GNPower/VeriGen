"""VeriGen's graphical interface (NiceGUI).

A single UI that runs as a local web page or, with pywebview installed, as a
standalone desktop window. It is the optional ``gui`` extra:
``pip install verigen[gui]``. The headless core and the CLI never import it.

The presentation layer is isolated in :mod:`verigen.ui.theme` and
``verigen/ui/static/theme.css`` so the look and feel can be reworked without
touching the backend logic in :mod:`verigen.ui.forms` or :mod:`verigen.core`.
"""
