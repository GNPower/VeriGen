"""
VeriGen Main Application

PySide6-based GUI for configuring and generating code from VeriGen projects.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QGroupBox, QScrollArea, QFileDialog, QMessageBox,
    QStatusBar, QMenuBar, QMenu, QSplitter, QFrame, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QAction, QFont, QIcon

import yaml

from ..core.schema import SchemaParser, DataParser
from ..core.validator import Validator
from ..core.models import Table, Row
from ..core.engine import generate_templates, TemplateError
from ..utils.paths import get_project_base_dir, get_icons_dir

from .widgets import ParameterWidget, create_parameter_widget
from .table_editor import HierarchicalTableEditor


class VeriGenApp(QMainWindow):
    """
    Main application window for VeriGen.

    Provides a schema-driven GUI that adapts to any VeriGen project.
    """

    def __init__(self, manifest_path: Optional[str] = None):
        super().__init__()

        self.manifest_path = manifest_path
        self.manifest: Dict[str, Any] = {}
        self.schema = None
        self.project_base_dir = ""
        self.current_values: Dict[str, Any] = {}
        self.parameter_widgets: Dict[str, ParameterWidget] = {}
        self.table_editors: Dict[str, HierarchicalTableEditor] = {}

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()

        if manifest_path:
            self.load_project(manifest_path)

    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("VeriGen - Code Generator")
        self.setMinimumSize(1000, 700)

        # Set window icon
        icon_path = get_icons_dir() / "256.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Project info header
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(self.header_frame)

        self.project_label = QLabel("No project loaded")
        self.project_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(self.project_label)

        header_layout.addStretch()

        self.load_config_btn = QPushButton("Load Config")
        self.load_config_btn.clicked.connect(self._load_config)
        header_layout.addWidget(self.load_config_btn)

        self.save_config_btn = QPushButton("Save Config")
        self.save_config_btn.clicked.connect(self._save_config)
        header_layout.addWidget(self.save_config_btn)

        main_layout.addWidget(self.header_frame)

        # Tab widget for pages
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.generate_tab_index = -1  # Will be set when tab is created
        main_layout.addWidget(self.tab_widget, 1)

        # Bottom action bar
        action_layout = QHBoxLayout()

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Output directory...")
        action_layout.addWidget(QLabel("Output:"))
        action_layout.addWidget(self.output_dir_edit, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output_dir)
        action_layout.addWidget(browse_btn)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setMinimumWidth(120)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        self.generate_btn.clicked.connect(self._generate)
        action_layout.addWidget(self.generate_btn)

        main_layout.addLayout(action_layout)

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        load_config_action = QAction("&Load Configuration...", self)
        load_config_action.setShortcut("Ctrl+L")
        load_config_action.triggered.connect(self._load_config)
        file_menu.addAction(load_config_action)

        save_config_action = QAction("&Save Configuration...", self)
        save_config_action.setShortcut("Ctrl+S")
        save_config_action.triggered.connect(self._save_config)
        file_menu.addAction(save_config_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Generate menu
        gen_menu = menubar.addMenu("&Generate")

        generate_action = QAction("&Generate All", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(self._generate)
        gen_menu.addAction(generate_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def load_project(self, manifest_path: str):
        """Load a VeriGen project from manifest file."""
        try:
            abs_path = os.path.abspath(manifest_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                raw_manifest = yaml.safe_load(f)

            self.manifest_path = abs_path
            self.project_base_dir = str(get_project_base_dir(abs_path))

            # Parse manifest
            if 'verigen_version' in raw_manifest or 'project' in raw_manifest:
                project = raw_manifest.get('project', {})
                self.manifest = {
                    '_version': raw_manifest.get('verigen_version', '2.0'),
                    '_raw': raw_manifest,
                    'name': project.get('name', 'VeriGen Project'),
                    'description': project.get('description', ''),
                    'schema': raw_manifest.get('schema'),
                    'ui': raw_manifest.get('ui'),
                    'templates': raw_manifest.get('templates', []),
                }
            else:
                self.manifest = raw_manifest
                self.manifest['_version'] = '1.0'

            # Load schema
            schema_path = self.manifest.get('schema')
            if schema_path:
                full_schema_path = os.path.join(self.project_base_dir, schema_path)
                parser = SchemaParser()
                self.schema = parser.parse_file(full_schema_path)

            # Update UI
            self._rebuild_ui()
            self.project_label.setText(self.manifest.get('name', 'Unknown Project'))
            self.statusbar.showMessage(f"Loaded: {abs_path}")

            # Set default output directory
            self.output_dir_edit.setText(os.path.join(self.project_base_dir, "output"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")

    def _rebuild_ui(self):
        """Rebuild the UI based on loaded schema."""
        # Clear existing tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        self.parameter_widgets.clear()
        self.table_editors.clear()

        if not self.schema:
            return

        # Create Parameters tab
        if self.schema.parameters:
            params_tab = self._create_parameters_tab()
            self.tab_widget.addTab(params_tab, "Parameters")

        # Create Tables tab(s)
        for table_name, table_def in self.schema.tables.items():
            # Only create tabs for top-level tables (not nested ones)
            is_nested = False
            for other_table in self.schema.tables.values():
                if other_table.nested_table == table_name:
                    is_nested = True
                    break

            if not is_nested:
                table_tab = self._create_table_tab(table_name, table_def)
                display_name = table_def.display_name or table_name.title()
                self.tab_widget.addTab(table_tab, display_name)

        # Create Generate tab
        gen_tab = self._create_generate_tab()
        self.tab_widget.addTab(gen_tab, "Generate")
        self.generate_tab_index = self.tab_widget.count() - 1

    def _create_parameters_tab(self) -> QWidget:
        """Create the parameters configuration tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # Group parameters by category if they have one, otherwise use "General"
        groups: Dict[str, List] = {"General": []}

        for name, param in self.schema.parameters.items():
            category = getattr(param, 'category', None) or "General"
            if category not in groups:
                groups[category] = []
            groups[category].append((name, param))

        for category, params in groups.items():
            if not params:
                continue

            group = QGroupBox(category)
            group_layout = QVBoxLayout(group)

            for name, param in params:
                widget = create_parameter_widget(name, param)
                if widget:
                    self.parameter_widgets[name] = widget
                    group_layout.addWidget(widget)

                    # Set default value
                    if param.default is not None:
                        widget.set_value(param.default)
                        self.current_values[name] = param.default

                    # Connect value changed signal
                    widget.value_changed.connect(
                        lambda val, n=name: self._on_parameter_changed(n, val)
                    )

            layout.addWidget(group)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_table_tab(self, table_name: str, table_def) -> QWidget:
        """Create a tab for editing a hierarchical table."""
        editor = HierarchicalTableEditor(table_def, self.schema)
        self.table_editors[table_name] = editor

        # Initialize with empty data
        self.current_values[table_name] = []

        # Connect data changed signal
        editor.data_changed.connect(
            lambda data, n=table_name: self._on_table_changed(n, data)
        )

        return editor

    def _create_generate_tab(self) -> QWidget:
        """Create the generation summary and actions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Templates list
        templates_group = QGroupBox("Templates")
        templates_layout = QVBoxLayout(templates_group)

        self.template_checkboxes = {}
        for template in self.manifest.get('templates', []):
            source = template.get('source', '')
            desc = template.get('description', source)
            cb = QCheckBox(desc)
            cb.setChecked(True)
            cb.setProperty('template_source', source)
            self.template_checkboxes[source] = cb
            templates_layout.addWidget(cb)

        layout.addWidget(templates_group)

        # Summary
        summary_group = QGroupBox("Configuration Summary")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        summary_layout.addWidget(self.summary_text)

        layout.addWidget(summary_group)

        # Refresh summary button
        refresh_btn = QPushButton("Refresh Summary")
        refresh_btn.clicked.connect(self._update_summary)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        return widget

    def _on_parameter_changed(self, name: str, value: Any):
        """Handle parameter value changes."""
        self.current_values[name] = value
        self.statusbar.showMessage(f"Changed: {name} = {value}")

    def _on_table_changed(self, name: str, data: List[Dict]):
        """Handle table data changes."""
        self.current_values[name] = data

    def _on_tab_changed(self, index: int):
        """Handle tab changes - auto-update summary when switching to Generate tab."""
        if index == self.generate_tab_index:
            self._update_summary()

    def _update_summary(self):
        """Update the configuration summary."""
        lines = []
        lines.append("=== Parameters ===")
        for name, value in self.current_values.items():
            if not isinstance(value, list):
                lines.append(f"  {name}: {value}")

        for table_name, editor in self.table_editors.items():
            lines.append(f"\n=== {table_name.title()} ===")
            data = editor.get_data()
            lines.append(f"  Count: {len(data)}")
            for i, row in enumerate(data):
                name_val = row.get('name', f'Item {i}')
                lines.append(f"  - {name_val}")

        self.summary_text.setPlainText('\n'.join(lines))

    def _open_project(self):
        """Open a project file dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open VeriGen Project",
            "",
            "VeriGen Projects (*.verigen.yaml);;YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            self.load_project(path)

    def _load_config(self):
        """Load configuration from a YAML file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            self.project_base_dir,
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Update parameter widgets
                for name, value in config.items():
                    if name in self.parameter_widgets:
                        self.parameter_widgets[name].set_value(value)
                        self.current_values[name] = value
                    elif name in self.table_editors:
                        self.table_editors[name].set_data(value)
                        self.current_values[name] = value

                self.statusbar.showMessage(f"Loaded configuration: {path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration:\n{e}")

    def _save_config(self):
        """Save current configuration to a YAML file."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            self.project_base_dir,
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            try:
                # Collect current values
                config = dict(self.current_values)

                # Get table data
                for name, editor in self.table_editors.items():
                    config[name] = editor.get_data()

                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

                self.statusbar.showMessage(f"Saved configuration: {path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")

    def _browse_output_dir(self):
        """Browse for output directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_edit.text() or self.project_base_dir
        )
        if path:
            self.output_dir_edit.setText(path)

    def _generate(self):
        """Generate code from templates."""
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            QMessageBox.warning(self, "Warning", "Please specify an output directory.")
            return

        try:
            # Collect all values
            params = dict(self.current_values)

            # Get table data
            for name, editor in self.table_editors.items():
                params[name] = editor.get_data()

            # Validate before generating
            if self.schema:
                validation_errors = self._validate_data(params)
                if validation_errors:
                    error_msg = "Validation failed:\n\n"
                    for error in validation_errors[:10]:  # Show first 10 errors
                        error_msg += f"• {error}\n"
                    if len(validation_errors) > 10:
                        error_msg += f"\n...and {len(validation_errors) - 10} more errors"
                    QMessageBox.warning(self, "Validation Errors", error_msg)
                    return

            # Filter templates if checkboxes exist
            templates = self.manifest.get('templates', [])
            if self.template_checkboxes:
                templates = [
                    t for t in templates
                    if self.template_checkboxes.get(t.get('source'), QCheckBox()).isChecked()
                ]

            project_data = dict(self.manifest)
            project_data['templates'] = templates

            # Generate
            generated = generate_templates(
                project_data=project_data,
                project_base_dir=self.project_base_dir,
                output_dir=output_dir,
                user_params=params
            )

            # Update summary
            self._update_summary()

            # Show success message
            msg = f"Successfully generated {len(generated)} files:\n\n"
            for path in generated:
                rel_path = os.path.relpath(path, output_dir)
                msg += f"  - {rel_path}\n"

            QMessageBox.information(self, "Generation Complete", msg)
            self.statusbar.showMessage(f"Generated {len(generated)} files to {output_dir}")

        except TemplateError as e:
            QMessageBox.critical(self, "Template Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Generation failed:\n{e}")

    def _validate_data(self, params: Dict[str, Any]) -> List[str]:
        """Validate the current data against the schema."""
        errors = []

        # Convert table data to Table objects for validation
        tables: Dict[str, Table] = {}
        param_values: Dict[str, Any] = {}

        for key, value in params.items():
            if key in self.schema.tables:
                # Convert list of dicts to Table with Row objects
                table_def = self.schema.tables[key]
                rows = self._convert_to_rows(value)
                tables[key] = Table(definition=table_def, rows=rows)
            else:
                param_values[key] = value

        # Run validation
        validator = Validator(self.schema)
        result = validator.validate_all(param_values, tables)

        for error in result.errors:
            if error.severity == "error":
                errors.append(str(error))

        return errors

    def _convert_to_rows(self, data: Any) -> List[Row]:
        """Convert list of dictionaries to Row objects."""
        if not isinstance(data, list):
            return []

        rows = []
        for item in data:
            if isinstance(item, dict):
                children_data = item.get('children', [])
                children = self._convert_to_rows(children_data)
                attributes = {k: v for k, v in item.items() if k != 'children'}
                rows.append(Row(attributes=attributes, children=children))

        return rows

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About VeriGen",
            "VeriGen - A Generic Code Generation Tool\n\n"
            "Version 2.0\n\n"
            "Generate SystemVerilog, C headers, documentation, and more\n"
            "from Jinja2 templates with schema-driven validation."
        )


def run_gui(manifest_path: Optional[str] = None) -> int:
    """
    Run the VeriGen GUI application.

    Args:
        manifest_path: Optional path to a project manifest file.

    Returns:
        Exit code from the application.
    """
    # Windows taskbar icon fix - must be called before QApplication is created
    # This gives the application a unique identity separate from python.exe
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID('gnpower.verigen.gui.2.0')
        except Exception:
            pass  # Silently fail if API unavailable

    app = QApplication(sys.argv)
    app.setApplicationName("VeriGen")
    app.setOrganizationName("VeriGen")

    # Set application icon
    icon_path = get_icons_dir() / "256.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Set application style
    app.setStyle("Fusion")

    window = VeriGenApp(manifest_path)
    window.show()

    return app.exec()
