"""VeriGen graphical interface (NiceGUI).

Presents a catalog of generator definitions and a dynamic wizard per generator,
with live validation, a generated-file preview, download-as-zip, and values
upload/download. Runs as a local web page or, with pywebview, a desktop window.
It reuses the same core pipeline as the CLI, so output is identical.

Visual styling lives in :mod:`verigen.ui.theme` and ``static/theme.css``; this
module only describes structure and behaviour.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Dict

import yaml
from nicegui import ui

import verigen
from verigen.core.catalog import builtin_examples_dir, discover
from verigen.core.definition import GeneratorDefinition
from verigen.core.errors import ValidationError, VeriGenError
from verigen.core.loader import load_definition
from verigen.core.pipeline import render
from verigen.core.values import normalize_values
from verigen.ui import forms, theme

_FAVICON = Path(verigen.__file__).parent / "resources" / "icons" / "favicon.ico"


def _build_element(config: dict, scalar_inputs: dict, table_grids: dict, base_dir) -> None:
    """Render one element and record value-producing controls."""
    etype = config["type"]
    label = config.get("label") or config.get("id", "")
    default = config.get("default")

    if etype == "string":
        element = ui.input(label=label, value=default or "")
    elif etype == "text":
        element = ui.textarea(label=label, value=default or "")
    elif etype == "integer":
        element = ui.number(
            label=label,
            value=default if default is not None else config.get("min", 0),
            min=config.get("min"),
            max=config.get("max"),
            step=1,
        )
    elif etype == "float":
        element = ui.number(
            label=label,
            value=default if default is not None else config.get("min", 0.0),
            min=config.get("min"),
            max=config.get("max"),
        )
    elif etype == "choice":
        options = list(config["options"])
        element = ui.select(
            options=options,
            value=default if default is not None else options[0],
            label=label,
        )
    elif etype == "boolean":
        element = ui.switch(label, value=bool(default or False))
    elif etype == "dynamic_table":
        _build_table(config, table_grids)
        return
    elif etype == "label":
        ui.markdown(config.get("text", ""))
        return
    elif etype == "image":
        path = os.path.join(base_dir, config.get("path", ""))
        if os.path.isfile(path):
            ui.image(path).classes("max-w-xs")
        return
    else:
        # summary / directory_selector are not used in the web UI.
        return

    if config.get("tooltip"):
        element.tooltip(config["tooltip"])
    element.classes("w-full")
    scalar_inputs[config["id"]] = element


def _build_table(config: dict, table_grids: dict) -> None:
    with ui.column().classes("w-full gap-1"):
        ui.label(config.get("label") or config["id"]).classes("font-medium")
        grid = (
            ui.aggrid(
                {
                    "columnDefs": forms.aggrid_column_defs(config),
                    "rowData": [],
                    "rowSelection": "multiple",
                    "stopEditingWhenCellsLoseFocus": True,
                }
            )
            .classes("w-full")
            .style("height: 220px")
        )

        async def add_row():
            data = await grid.get_client_data()
            data.append(forms.table_row_default(config))
            grid.options["rowData"] = data
            grid.update()

        async def remove_selected():
            selected = await grid.get_selected_rows()
            data = await grid.get_client_data()
            grid.options["rowData"] = [row for row in data if row not in selected]
            grid.update()

        with ui.row().classes("gap-2"):
            ui.button(config.get("add_button_text", "Add Item"), on_click=add_row).props(
                theme.OUTLINE_BUTTON + " size=sm"
            )
            ui.button("Remove selected", on_click=remove_selected).props(
                theme.OUTLINE_BUTTON + " size=sm color=negative"
            )
    table_grids[config["id"]] = (grid, config)


async def _collect_values(scalar_inputs: dict, table_grids: dict) -> dict:
    scalars = {vid: element.value for vid, element in scalar_inputs.items()}
    tables = {}
    for vid, (grid, _cfg) in table_grids.items():
        tables[vid] = await grid.get_client_data()
    return forms.merge_values(scalars, tables)


def _populate(scalar_inputs: dict, table_grids: dict, values: dict) -> None:
    for vid, element in scalar_inputs.items():
        if vid in values:
            element.value = values[vid]
    for vid, (grid, _cfg) in table_grids.items():
        if vid in values:
            grid.options["rowData"] = list(values[vid])
            grid.update()


def _build_wizard(definition: GeneratorDefinition, show_back: bool) -> None:
    base_dir = definition.base_dir or Path.cwd()
    scalar_inputs: dict = {}
    table_grids: dict = {}

    with theme.page():
        theme.header(definition.name, definition.description, show_back=show_back)

        for page in definition.pages:
            card = theme.section(page.title)
            with card:
                for element in page.elements:
                    _build_element(element.model_dump(), scalar_inputs, table_grids, base_dir)

        results = ui.column().classes("w-full gap-2")

        async def do_generate():
            values = await _collect_values(scalar_inputs, table_grids)
            try:
                outputs, _ = render(definition, values)
            except ValidationError as exc:
                for message in exc.errors:
                    ui.notify(message, type="negative")
                return
            except VeriGenError as exc:
                ui.notify(str(exc), type="negative")
                return
            results.clear()
            with results:
                ui.label("Generated files").classes(theme.RESULT_TITLE_CLASSES)
                with ui.tabs() as tabs:
                    tab_objects = [ui.tab(output.relative_path) for output in outputs]
                with ui.tab_panels(tabs, value=tab_objects[0]).classes("w-full"):
                    for output, tab_object in zip(outputs, tab_objects):
                        with ui.tab_panel(tab_object):
                            ui.code(output.content).classes("w-full")
                ui.button(
                    "Download ZIP",
                    icon="download",
                    on_click=lambda o=outputs: ui.download.content(
                        forms.zip_outputs(o), f"{definition.id}.zip"
                    ),
                ).props(theme.PRIMARY_BUTTON)
            ui.notify(f"Generated {len(outputs)} file(s).", type="positive")

        async def do_download_values():
            values = await _collect_values(scalar_inputs, table_grids)
            try:
                _, normalized = render(definition, values)
            except VeriGenError as exc:
                ui.notify(str(exc), type="negative")
                return
            ui.download.content(forms.values_yaml(normalized), f"{definition.id}.values.yaml")

        def on_upload(event):
            try:
                data = yaml.safe_load(event.content.read())
                normalized = normalize_values(definition, data)
            except (yaml.YAMLError, VeriGenError) as exc:
                ui.notify(f"Load failed: {exc}", type="negative")
                return
            _populate(scalar_inputs, table_grids, normalized)
            ui.notify("Values loaded.", type="positive")

        with ui.row().classes("w-full gap-2 items-center"):
            ui.button("Generate", icon="bolt", on_click=do_generate).props(theme.PRIMARY_BUTTON)
            ui.button("Download values", on_click=do_download_values).props(theme.OUTLINE_BUTTON)
            ui.upload(label="Load values", auto_upload=True, on_upload=on_upload).props(
                "flat"
            ).classes("max-w-xs")


def _build_catalog(entries) -> None:
    with theme.page():
        theme.header("VeriGen", "Choose a generator")
        by_category: Dict[str, list] = {}
        for entry in entries:
            by_category.setdefault(entry.category or "General", []).append(entry)
        for category in sorted(by_category):
            ui.label(category).classes(theme.SECTION_TITLE_CLASSES + " mt-2")
            for entry in by_category[category]:
                with ui.card().classes(theme.CARD_CLASSES):
                    ui.label(entry.name).classes("text-base font-medium")
                    if entry.description:
                        ui.label(entry.description).classes(theme.SUBTITLE_CLASSES)
                    ui.button(
                        "Open",
                        on_click=lambda gid=entry.id: ui.navigate.to(f"/g/{gid}"),
                    ).props(theme.PRIMARY_BUTTON + " size=sm")
        if not entries:
            ui.label("No generator definitions found.")


def launch(
    definition=None,
    catalog_paths=None,
    *,
    native: bool = False,
    port: int = 8080,
    show: bool = True,
    reload: bool = False,
) -> None:
    """Run the graphical interface.

    Args:
        definition: A definition path or object to open directly. If omitted, the
            catalog of discovered generators is shown at ``/``.
        catalog_paths: Where to discover generators (default: the built-in examples).
        native: Open in a native desktop window (requires pywebview) instead of a browser.
        port: HTTP port.
        show: Open a browser/window on start.
        reload: Auto-reload on file changes (leave False for normal use).
    """
    paths = catalog_paths or [builtin_examples_dir()]
    entries = [entry for entry in discover(paths) if entry.valid]

    loaders: Dict[str, Callable[[], GeneratorDefinition]] = {
        entry.id: (lambda p=entry.path: load_definition(p)) for entry in entries
    }

    single_id = None
    if definition is not None:
        defn = (
            definition
            if isinstance(definition, GeneratorDefinition)
            else load_definition(definition)
        )
        single_id = defn.id
        loaders[defn.id] = lambda d=defn: d
        if defn.id not in {entry.id for entry in entries}:
            from verigen.core.catalog import CatalogEntry

            entries.append(
                CatalogEntry(
                    path=defn.source_path or Path(defn.id),
                    id=defn.id,
                    name=defn.name,
                    description=defn.description,
                    category=defn.category,
                )
            )

    @ui.page("/")
    def index():
        theme.setup()
        if single_id is not None:
            _build_wizard(loaders[single_id](), show_back=False)
        else:
            _build_catalog(entries)

    @ui.page("/g/{gen_id}")
    def wizard_page(gen_id: str):
        theme.setup()
        loader = loaders.get(gen_id)
        if loader is None:
            with theme.page():
                ui.label(f"Unknown generator: {gen_id}")
                ui.button("Catalog", on_click=lambda: ui.navigate.to("/")).props(
                    theme.FLAT_BUTTON
                )
            return
        try:
            definition_obj = loader()
        except VeriGenError as exc:
            with theme.page():
                ui.label(str(exc))
            return
        _build_wizard(definition_obj, show_back=True)

    ui.run(
        title="VeriGen",
        port=port,
        show=show,
        native=native,
        reload=reload,
        favicon=str(_FAVICON) if _FAVICON.exists() else None,
    )
