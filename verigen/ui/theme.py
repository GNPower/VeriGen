"""Presentation layer for the VeriGen UI.

Everything that controls look and feel lives here and in
``verigen/ui/static/theme.css``. The page structure in :mod:`verigen.ui.app`
references the tokens and helpers below, so a designer can restyle the app by
editing this file and the stylesheet without touching any backend logic.

To rework the visual design, edit:
  - the color tokens and class constants in this module,
  - the component helpers (``page``, ``header``, ``section``, button props),
  - ``verigen/ui/static/theme.css`` for global CSS.
"""

from __future__ import annotations

from pathlib import Path

from nicegui import ui

# --------------------------------------------------------------------------- #
# Design tokens                                                               #
# --------------------------------------------------------------------------- #
COLORS = {
    "primary": "#2563eb",
    "secondary": "#475569",
    "accent": "#7c3aed",
    "positive": "#16a34a",
    "negative": "#dc2626",
    "warning": "#d97706",
}

FONT_HREF = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
)

# Tailwind/Quasar utility classes used across the app.
PAGE_CLASSES = "w-full max-w-4xl mx-auto gap-5 p-6"
CARD_CLASSES = "vg-card w-full p-5 gap-3"
TITLE_CLASSES = "text-2xl font-semibold"
SUBTITLE_CLASSES = "text-sm text-gray-500"
SECTION_TITLE_CLASSES = "text-base font-semibold text-gray-700"
RESULT_TITLE_CLASSES = "text-lg font-semibold"

# Quasar button props.
PRIMARY_BUTTON = "color=primary unelevated no-caps rounded"
OUTLINE_BUTTON = "outline no-caps rounded"
FLAT_BUTTON = "flat no-caps rounded"


def _stylesheet() -> str:
    path = Path(__file__).resolve().parent / "static" / "theme.css"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def setup() -> None:
    """Apply colors, fonts, and the stylesheet. Call once at the top of a page."""
    ui.colors(**COLORS)
    ui.add_head_html(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        f'<link href="{FONT_HREF}" rel="stylesheet">'
    )
    ui.add_css(_stylesheet())


def page():
    """The outer page container (returns a NiceGUI element for use with ``with``)."""
    return ui.column().classes(PAGE_CLASSES)


def header(title: str, subtitle: str = "", *, show_back: bool = False) -> None:
    """A page header with an optional back-to-catalog button."""
    with ui.row().classes("w-full items-center justify-between"):
        with ui.column().classes("gap-0"):
            ui.label(title).classes(TITLE_CLASSES)
            if subtitle:
                ui.label(subtitle).classes(SUBTITLE_CLASSES)
        if show_back:
            ui.button(
                "Catalog", icon="arrow_back", on_click=lambda: ui.navigate.to("/")
            ).props(FLAT_BUTTON)


def section(title: str):
    """A titled card section (returns the card element for use with ``with``)."""
    card = ui.card().classes(CARD_CLASSES)
    with card:
        ui.label(title).classes(SECTION_TITLE_CLASSES)
    return card
