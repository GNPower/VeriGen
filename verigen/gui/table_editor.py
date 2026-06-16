"""
VeriGen Hierarchical Table Editor

A master-detail editor for schema-defined hierarchical data structures.
Parent items (e.g., registers) and child items (e.g., fields) have
separate tables with their own column headers.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMenu, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QMessageBox, QAbstractItemView, QSplitter, QLabel,
    QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ..core.models import TableDefinition, AttributeDefinition, Schema


class AttributeTableWidget(QTableWidget):
    """
    A table widget for editing items with schema-defined attributes.
    Each column corresponds to an attribute from the TableDefinition.
    """

    data_changed = Signal()

    def __init__(self, table_def: TableDefinition, parent=None):
        super().__init__(parent)
        self.table_def = table_def
        self._setup_columns()
        self._setup_table()

        # Connect signals
        self.cellChanged.connect(self._on_cell_changed)

    def _setup_table(self):
        """Configure table appearance."""
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

    def _setup_columns(self):
        """Set up columns based on table definition attributes."""
        # Build list of attributes to show as columns
        self.column_attrs = []
        headers = []

        for attr in self.table_def.attributes:
            self.column_attrs.append(attr)
            label = attr.display_name or attr.name
            headers.append(label)

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Set column tooltips
        for i, attr in enumerate(self.column_attrs):
            if attr.description:
                self.horizontalHeaderItem(i).setToolTip(attr.description)

    def add_row(self, data: Optional[Dict[str, Any]] = None) -> int:
        """Add a new row with default or provided values."""
        row = self.rowCount()
        self.insertRow(row)

        self.blockSignals(True)
        for col, attr in enumerate(self.column_attrs):
            value = data.get(attr.name, attr.default) if data else attr.default
            self._set_cell_widget(row, col, attr, value)
        self.blockSignals(False)

        self.data_changed.emit()
        return row

    def _set_cell_widget(self, row: int, col: int, attr: AttributeDefinition, value: Any):
        """Create and set the appropriate widget for a cell based on attribute type."""
        if attr.type in ('choice', 'enum'):
            # Dropdown for choice types
            combo = QComboBox()
            if attr.options:
                for opt in attr.options:
                    combo.addItem(str(opt), opt)
            if value is not None:
                idx = combo.findData(value)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(lambda: self.data_changed.emit())
            if attr.description:
                combo.setToolTip(attr.description)
            self.setCellWidget(row, col, combo)

        elif attr.type in ('boolean', 'bool'):
            # Checkbox for booleans
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(4, 0, 4, 0)
            layout.setAlignment(Qt.AlignCenter)
            checkbox = QCheckBox()
            checkbox.setChecked(bool(value) if value is not None else False)
            checkbox.stateChanged.connect(lambda: self.data_changed.emit())
            if attr.description:
                checkbox.setToolTip(attr.description)
            layout.addWidget(checkbox)
            self.setCellWidget(row, col, widget)

        elif attr.type in ('integer', 'int'):
            # Spinbox for integers
            spinbox = QSpinBox()
            spinbox.setMinimum(attr.min_value if attr.min_value is not None else -2147483648)
            spinbox.setMaximum(attr.max_value if attr.max_value is not None else 2147483647)
            spinbox.setValue(int(value) if value is not None else 0)
            spinbox.valueChanged.connect(lambda: self.data_changed.emit())
            if attr.description:
                spinbox.setToolTip(attr.description)
            self.setCellWidget(row, col, spinbox)

        else:
            # Text item for strings and other types
            item = QTableWidgetItem(str(value) if value is not None else "")
            if attr.description:
                item.setToolTip(attr.description)
            self.setItem(row, col, item)

    def get_cell_value(self, row: int, col: int) -> Any:
        """Get the value from a cell, handling different widget types."""
        attr = self.column_attrs[col]
        widget = self.cellWidget(row, col)

        if widget:
            if isinstance(widget, QComboBox):
                return widget.currentData()
            elif isinstance(widget, QSpinBox):
                return widget.value()
            elif isinstance(widget, QWidget):
                # Check for checkbox in container widget
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    return checkbox.isChecked()
        else:
            item = self.item(row, col)
            if item:
                text = item.text()
                # Convert to appropriate type
                if attr.type in ('integer', 'int'):
                    try:
                        return int(text) if text else 0
                    except ValueError:
                        return 0
                return text

        return attr.default

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """Get all data from a row as a dictionary."""
        data = {}
        for col, attr in enumerate(self.column_attrs):
            data[attr.name] = self.get_cell_value(row, col)
        return data

    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all rows as a list of dictionaries."""
        return [self.get_row_data(row) for row in range(self.rowCount())]

    def set_data(self, data_list: List[Dict[str, Any]]):
        """Set table data from a list of dictionaries."""
        self.setRowCount(0)
        for data in data_list:
            self.add_row(data)

    def delete_selected(self):
        """Delete the currently selected row."""
        row = self.currentRow()
        if row >= 0:
            self.removeRow(row)
            self.data_changed.emit()

    def move_row_up(self):
        """Move the selected row up."""
        row = self.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)
            self.selectRow(row - 1)
            self.data_changed.emit()

    def move_row_down(self):
        """Move the selected row down."""
        row = self.currentRow()
        if row < self.rowCount() - 1:
            self._swap_rows(row, row + 1)
            self.selectRow(row + 1)
            self.data_changed.emit()

    def _swap_rows(self, row1: int, row2: int):
        """Swap two rows in the table."""
        data1 = self.get_row_data(row1)
        data2 = self.get_row_data(row2)

        self.blockSignals(True)
        for col, attr in enumerate(self.column_attrs):
            self._set_cell_widget(row1, col, attr, data2.get(attr.name))
            self._set_cell_widget(row2, col, attr, data1.get(attr.name))
        self.blockSignals(False)

    def _on_cell_changed(self, row: int, col: int):
        """Handle cell value changes."""
        self.data_changed.emit()


class HierarchicalTableEditor(QWidget):
    """
    A master-detail editor for hierarchical data structures.

    Shows parent items (e.g., registers) in the top table and
    child items (e.g., fields) for the selected parent in the bottom table.
    """

    data_changed = Signal(list)

    def __init__(
        self,
        table_def: TableDefinition,
        schema: Schema,
        parent=None
    ):
        super().__init__(parent)
        self.table_def = table_def
        self.schema = schema
        self.nested_table_def = None

        # Storage for children data (keyed by parent row index)
        self._children_data: Dict[int, List[Dict[str, Any]]] = {}

        # Get nested table definition if exists
        if table_def.nested_table and table_def.nested_table in schema.tables:
            self.nested_table_def = schema.tables[table_def.nested_table]

        self._setup_ui()

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        if self.nested_table_def:
            # Use splitter for parent/child tables
            splitter = QSplitter(Qt.Vertical)

            # Parent table section
            parent_widget = QWidget()
            parent_layout = QVBoxLayout(parent_widget)
            parent_layout.setContentsMargins(0, 0, 0, 0)

            parent_label = QLabel(f"<b>{self.table_def.display_name or self.table_def.name}</b>")
            parent_layout.addWidget(parent_label)

            parent_toolbar = self._create_toolbar(is_parent=True)
            parent_layout.addLayout(parent_toolbar)

            self.parent_table = AttributeTableWidget(self.table_def)
            self.parent_table.data_changed.connect(self._on_parent_changed)
            self.parent_table.itemSelectionChanged.connect(self._on_parent_selection_changed)
            parent_layout.addWidget(self.parent_table)

            splitter.addWidget(parent_widget)

            # Child table section
            child_widget = QWidget()
            child_layout = QVBoxLayout(child_widget)
            child_layout.setContentsMargins(0, 0, 0, 0)

            self.child_label = QLabel(f"<b>{self.nested_table_def.display_name or self.nested_table_def.name}</b> <i>(select a {self.table_def.display_name or 'parent'} above)</i>")
            child_layout.addWidget(self.child_label)

            child_toolbar = self._create_toolbar(is_parent=False)
            child_layout.addLayout(child_toolbar)

            self.child_table = AttributeTableWidget(self.nested_table_def)
            self.child_table.data_changed.connect(self._on_child_changed)
            self.child_table.setEnabled(False)
            child_layout.addWidget(self.child_table)

            splitter.addWidget(child_widget)

            # Set initial sizes (60% parent, 40% child)
            splitter.setSizes([300, 200])

            layout.addWidget(splitter)

        else:
            # Single table (no nesting)
            toolbar = self._create_toolbar(is_parent=True)
            layout.addLayout(toolbar)

            self.parent_table = AttributeTableWidget(self.table_def)
            self.parent_table.data_changed.connect(self._on_parent_changed)
            layout.addWidget(self.parent_table)

            self.child_table = None

    def _create_toolbar(self, is_parent: bool) -> QHBoxLayout:
        """Create a toolbar for add/delete/move operations."""
        toolbar = QHBoxLayout()

        if is_parent:
            table_def = self.table_def
            table = lambda: self.parent_table
        else:
            table_def = self.nested_table_def
            table = lambda: self.child_table

        add_btn = QPushButton(f"Add {table_def.display_name or 'Item'}")
        add_btn.setToolTip(f"Add a new {table_def.display_name or 'item'}")
        if is_parent:
            add_btn.clicked.connect(self._add_parent)
        else:
            add_btn.clicked.connect(self._add_child)
        toolbar.addWidget(add_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setToolTip("Delete the selected item")
        if is_parent:
            delete_btn.clicked.connect(self._delete_parent)
        else:
            delete_btn.clicked.connect(self._delete_child)
        toolbar.addWidget(delete_btn)

        toolbar.addStretch()

        move_up_btn = QPushButton("Move Up")
        move_up_btn.setToolTip("Move the selected item up")
        move_up_btn.clicked.connect(lambda: table().move_row_up())
        toolbar.addWidget(move_up_btn)

        move_down_btn = QPushButton("Move Down")
        move_down_btn.setToolTip("Move the selected item down")
        move_down_btn.clicked.connect(lambda: table().move_row_down())
        toolbar.addWidget(move_down_btn)

        return toolbar

    def _add_parent(self):
        """Add a new parent item."""
        row = self.parent_table.add_row()
        self._children_data[row] = []
        self.parent_table.selectRow(row)

    def _delete_parent(self):
        """Delete the selected parent and its children."""
        row = self.parent_table.currentRow()
        if row >= 0:
            # Remove children data
            if row in self._children_data:
                del self._children_data[row]
            # Shift children data for rows after the deleted one
            new_children = {}
            for r, children in self._children_data.items():
                if r > row:
                    new_children[r - 1] = children
                elif r < row:
                    new_children[r] = children
            self._children_data = new_children

            self.parent_table.delete_selected()
            self._update_child_table()

    def _add_child(self):
        """Add a new child to the selected parent."""
        parent_row = self.parent_table.currentRow()
        if parent_row < 0:
            QMessageBox.information(
                self, "Select Parent",
                f"Please select a {self.table_def.display_name or 'parent'} first."
            )
            return

        self.child_table.add_row()

    def _delete_child(self):
        """Delete the selected child."""
        self.child_table.delete_selected()

    def _on_parent_changed(self):
        """Handle parent table changes."""
        self._emit_data_changed()

    def _on_child_changed(self):
        """Handle child table changes - save to storage."""
        parent_row = self.parent_table.currentRow()
        if parent_row >= 0:
            self._children_data[parent_row] = self.child_table.get_all_data()
        self._emit_data_changed()

    def _on_parent_selection_changed(self):
        """Handle parent selection change - update child table."""
        self._update_child_table()

    def _update_child_table(self):
        """Update child table based on selected parent."""
        if not self.child_table:
            return

        parent_row = self.parent_table.currentRow()
        if parent_row >= 0:
            # Get parent name for label
            parent_data = self.parent_table.get_row_data(parent_row)
            parent_name = parent_data.get('name', f'Row {parent_row}')
            self.child_label.setText(
                f"<b>{self.nested_table_def.display_name or self.nested_table_def.name}</b> "
                f"for <i>{parent_name}</i>"
            )

            # Load children for this parent
            children = self._children_data.get(parent_row, [])
            self.child_table.blockSignals(True)
            self.child_table.set_data(children)
            self.child_table.blockSignals(False)
            self.child_table.setEnabled(True)
        else:
            self.child_label.setText(
                f"<b>{self.nested_table_def.display_name or self.nested_table_def.name}</b> "
                f"<i>(select a {self.table_def.display_name or 'parent'} above)</i>"
            )
            self.child_table.setRowCount(0)
            self.child_table.setEnabled(False)

    def _emit_data_changed(self):
        """Emit the data_changed signal with current data."""
        data = self.get_data()
        self.data_changed.emit(data)

    def get_data(self) -> List[Dict[str, Any]]:
        """Get all data including nested children."""
        data = []

        for row in range(self.parent_table.rowCount()):
            row_data = self.parent_table.get_row_data(row)

            # Add children if available
            if self.nested_table_def:
                children = self._children_data.get(row, [])
                if children:
                    row_data['children'] = children

            data.append(row_data)

        return data

    def set_data(self, data: List[Dict[str, Any]]):
        """Set all data including nested children."""
        self._children_data.clear()
        self.parent_table.blockSignals(True)
        self.parent_table.set_data(data)
        self.parent_table.blockSignals(False)

        # Store children data
        for row, row_data in enumerate(data):
            if 'children' in row_data:
                self._children_data[row] = row_data['children']

        # Update child table if a row is selected
        if self.child_table:
            self._update_child_table()
