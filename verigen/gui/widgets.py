"""
VeriGen GUI Widgets

Schema-driven widgets for parameter editing.
"""

from typing import Any, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QTextEdit,
    QFrame
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..core.models import ParameterDefinition


class ParameterWidget(QWidget):
    """
    Base class for parameter editing widgets.

    Emits value_changed signal when the value changes.
    """

    value_changed = Signal(object)

    def __init__(self, name: str, param: ParameterDefinition, parent=None):
        super().__init__(parent)
        self.name = name
        self.param = param
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI. Override in subclasses."""
        pass

    def get_value(self) -> Any:
        """Get the current value. Override in subclasses."""
        raise NotImplementedError

    def set_value(self, value: Any):
        """Set the current value. Override in subclasses."""
        raise NotImplementedError


class StringParameterWidget(ParameterWidget):
    """Widget for string parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # Label
        label = QLabel(self.param.display_name or self.name)
        label.setMinimumWidth(150)
        layout.addWidget(label)

        # Input
        self.input = QLineEdit()
        if self.param.description:
            self.input.setToolTip(self.param.description)
        if self.param.pattern:
            self.input.setPlaceholderText(f"Pattern: {self.param.pattern}")

        self.input.textChanged.connect(self._on_changed)
        layout.addWidget(self.input, 1)

    def _on_changed(self, text: str):
        self.value_changed.emit(text)

    def get_value(self) -> str:
        return self.input.text()

    def set_value(self, value: Any):
        self.input.setText(str(value) if value is not None else "")


class IntegerParameterWidget(ParameterWidget):
    """Widget for integer parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # Label
        label = QLabel(self.param.display_name or self.name)
        label.setMinimumWidth(150)
        layout.addWidget(label)

        # Input
        self.input = QSpinBox()
        self.input.setMinimum(self.param.min_value if self.param.min_value is not None else -2147483648)
        self.input.setMaximum(self.param.max_value if self.param.max_value is not None else 2147483647)

        if self.param.description:
            self.input.setToolTip(self.param.description)

        self.input.valueChanged.connect(self._on_changed)
        layout.addWidget(self.input)
        layout.addStretch()

    def _on_changed(self, value: int):
        self.value_changed.emit(value)

    def get_value(self) -> int:
        return self.input.value()

    def set_value(self, value: Any):
        if value is not None:
            self.input.setValue(int(value))


class BooleanParameterWidget(ParameterWidget):
    """Widget for boolean parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # Checkbox includes the label
        self.checkbox = QCheckBox(self.param.display_name or self.name)

        if self.param.description:
            self.checkbox.setToolTip(self.param.description)

        self.checkbox.stateChanged.connect(self._on_changed)
        layout.addWidget(self.checkbox)
        layout.addStretch()

    def _on_changed(self, state: int):
        self.value_changed.emit(state == Qt.Checked)

    def get_value(self) -> bool:
        return self.checkbox.isChecked()

    def set_value(self, value: Any):
        self.checkbox.setChecked(bool(value) if value is not None else False)


class ChoiceParameterWidget(ParameterWidget):
    """Widget for choice/enum parameters."""

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # Label
        label = QLabel(self.param.display_name or self.name)
        label.setMinimumWidth(150)
        layout.addWidget(label)

        # Combo box
        self.combo = QComboBox()
        if self.param.options:
            for opt in self.param.options:
                self.combo.addItem(str(opt), opt)

        if self.param.description:
            self.combo.setToolTip(self.param.description)

        self.combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.combo)
        layout.addStretch()

    def _on_changed(self, index: int):
        value = self.combo.currentData()
        self.value_changed.emit(value)

    def get_value(self) -> Any:
        return self.combo.currentData()

    def set_value(self, value: Any):
        if value is not None:
            index = self.combo.findData(value)
            if index >= 0:
                self.combo.setCurrentIndex(index)


class TextParameterWidget(ParameterWidget):
    """Widget for multi-line text parameters."""

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        # Label
        label = QLabel(self.param.display_name or self.name)
        layout.addWidget(label)

        # Text edit
        self.input = QTextEdit()
        self.input.setMaximumHeight(100)

        if self.param.description:
            self.input.setToolTip(self.param.description)

        self.input.textChanged.connect(self._on_changed)
        layout.addWidget(self.input)

    def _on_changed(self):
        self.value_changed.emit(self.input.toPlainText())

    def get_value(self) -> str:
        return self.input.toPlainText()

    def set_value(self, value: Any):
        self.input.setPlainText(str(value) if value is not None else "")


def create_parameter_widget(
    name: str,
    param: ParameterDefinition,
    parent: Optional[QWidget] = None
) -> Optional[ParameterWidget]:
    """
    Create the appropriate widget for a parameter based on its type.

    Args:
        name: Parameter name.
        param: Parameter definition.
        parent: Parent widget.

    Returns:
        A ParameterWidget instance or None if type is unsupported.
    """
    type_map = {
        'string': StringParameterWidget,
        'integer': IntegerParameterWidget,
        'int': IntegerParameterWidget,
        'boolean': BooleanParameterWidget,
        'bool': BooleanParameterWidget,
        'choice': ChoiceParameterWidget,
        'enum': ChoiceParameterWidget,
        'text': TextParameterWidget,
    }

    widget_class = type_map.get(param.type.lower())

    if widget_class:
        return widget_class(name, param, parent)

    # Default to string widget for unknown types
    return StringParameterWidget(name, param, parent)
