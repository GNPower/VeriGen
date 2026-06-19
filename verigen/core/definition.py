"""Pydantic models for the VeriGen generator-definition format.

A *generator definition* is the file an implementer authors. It declares the
metadata, the variables (organized into wizard pages, which is also the input
contract), the output templates, and an optional Python extension module. These
models validate the *format itself* and give authors precise errors; they encode
nothing about any specific IP.

A separate *values config* (a plain ``{variable: value}`` mapping) is validated
against a loaded definition by :mod:`verigen.core.values`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class _Base(BaseModel):
    # Reject unknown keys so a typo in a definition is an error, not silently lost.
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# Scalar (value-producing) elements                                           #
# --------------------------------------------------------------------------- #
class _ScalarBase(_Base):
    id: str
    label: Optional[str] = None
    tooltip: Optional[str] = None
    is_summary: bool = False

    @model_validator(mode="after")
    def _check_id(self):
        if not _IDENT_RE.match(self.id):
            raise ValueError(
                f"element id {self.id!r} is not a valid identifier "
                "(letters, digits, underscore; not starting with a digit)"
            )
        return self


class StringVar(_ScalarBase):
    type: Literal["string"] = "string"
    default: Optional[str] = None


class TextVar(_ScalarBase):
    """A multi-line string (rendered as a textarea in the UIs)."""

    type: Literal["text"] = "text"
    default: Optional[str] = None


class IntegerVar(_ScalarBase):
    type: Literal["integer"] = "integer"
    default: Optional[int] = None
    min: int = 0
    max: int = 1000

    @model_validator(mode="after")
    def _check_range(self):
        if self.min > self.max:
            raise ValueError(f"{self.id}: min ({self.min}) is greater than max ({self.max})")
        if self.default is not None and not (self.min <= self.default <= self.max):
            raise ValueError(
                f"{self.id}: default ({self.default}) is outside [{self.min}, {self.max}]"
            )
        return self


class FloatVar(_ScalarBase):
    type: Literal["float"] = "float"
    default: Optional[float] = None
    min: float = 0.0
    max: float = 1.0e9

    @model_validator(mode="after")
    def _check_range(self):
        if self.min > self.max:
            raise ValueError(f"{self.id}: min ({self.min}) is greater than max ({self.max})")
        if self.default is not None and not (self.min <= self.default <= self.max):
            raise ValueError(
                f"{self.id}: default ({self.default}) is outside [{self.min}, {self.max}]"
            )
        return self


class ChoiceVar(_ScalarBase):
    type: Literal["choice"] = "choice"
    options: List[Union[str, int]] = Field(min_length=1)
    default: Optional[Union[str, int]] = None

    @model_validator(mode="after")
    def _check_default(self):
        if self.default is not None and self.default not in self.options:
            raise ValueError(
                f"{self.id}: default ({self.default!r}) is not one of options {self.options}"
            )
        return self


class BooleanVar(_ScalarBase):
    type: Literal["boolean"] = "boolean"
    default: bool = False


ScalarElement = Annotated[
    Union[StringVar, TextVar, IntegerVar, FloatVar, ChoiceVar, BooleanVar],
    Field(discriminator="type"),
]


# --------------------------------------------------------------------------- #
# Composite value element: a repeatable group (rows of scalars)               #
# --------------------------------------------------------------------------- #
class TableVar(_Base):
    type: Literal["dynamic_table"] = "dynamic_table"
    id: str
    label: Optional[str] = None
    tooltip: Optional[str] = None
    add_button_text: str = "Add Item"
    row_label: str = "Item"
    sub_elements: List[ScalarElement] = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self):
        if not _IDENT_RE.match(self.id):
            raise ValueError(f"table id {self.id!r} is not a valid identifier")
        seen = set()
        for sub in self.sub_elements:
            if sub.id in seen:
                raise ValueError(f"{self.id}: duplicate sub-element id {sub.id!r}")
            seen.add(sub.id)
        return self


# --------------------------------------------------------------------------- #
# Display-only elements (produce no value)                                    #
# --------------------------------------------------------------------------- #
class LabelElement(_Base):
    type: Literal["label"] = "label"
    text: str = ""


class ImageElement(_Base):
    type: Literal["image"] = "image"
    path: str
    height: Optional[int] = None


class SummaryElement(_Base):
    type: Literal["summary"] = "summary"
    id: str = "summary_view"
    label: str = "Summary"


class DirectorySelector(_Base):
    type: Literal["directory_selector"] = "directory_selector"
    id: str = "save_directory"
    label: str = "Output Directory"
    tooltip: Optional[str] = None


Element = Annotated[
    Union[
        StringVar,
        TextVar,
        IntegerVar,
        FloatVar,
        ChoiceVar,
        BooleanVar,
        TableVar,
        LabelElement,
        ImageElement,
        SummaryElement,
        DirectorySelector,
    ],
    Field(discriminator="type"),
]

# Element types that contribute a value to the values config / render context.
VALUE_TYPES = ("string", "text", "integer", "float", "choice", "boolean", "dynamic_table")


class Page(_Base):
    title: str = "Page"
    elements: List[Element] = Field(default_factory=list)


class OutputSpec(_Base):
    """One generated file: a template rendered to a (templated) destination path."""

    template: str
    destination: str


class GeneratorDefinition(_Base):
    """A complete generator definition (one IP entry in the catalog)."""

    verigen_version: str = "1"
    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    author: Optional[str] = None
    category: str = "General"
    icon: Optional[str] = None
    extension: Optional[str] = None
    default_size: Optional[str] = None
    pages: List[Page] = Field(min_length=1)
    outputs: List[OutputSpec] = Field(min_length=1)

    # Filled by the loader; not part of the on-disk format.
    _source_path: Optional[Path] = PrivateAttr(default=None)
    _base_dir: Optional[Path] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _check_unique_ids(self):
        if not _IDENT_RE.match(self.id):
            raise ValueError(f"definition id {self.id!r} is not a valid identifier")
        seen = set()
        for elem in self.value_elements():
            if elem.id in seen:
                raise ValueError(f"duplicate variable id {elem.id!r} across pages")
            seen.add(elem.id)
        return self

    # -- helpers ----------------------------------------------------------- #
    @property
    def base_dir(self) -> Optional[Path]:
        return self._base_dir

    @property
    def source_path(self) -> Optional[Path]:
        return self._source_path

    def _set_source(self, source_path: Path) -> None:
        self._source_path = Path(source_path)
        self._base_dir = Path(source_path).parent

    def iter_elements(self):
        """Yield every element across every page, in order."""
        for page in self.pages:
            for elem in page.elements:
                yield elem

    def value_elements(self) -> List[Element]:
        """Return the elements that produce a value (excludes display-only ones)."""
        return [e for e in self.iter_elements() if getattr(e, "type", None) in VALUE_TYPES]

    def element_by_id(self, element_id: str):
        for elem in self.iter_elements():
            if getattr(elem, "id", None) == element_id:
                return elem
        return None

    def directory_selector_id(self) -> Optional[str]:
        for elem in self.iter_elements():
            if getattr(elem, "type", None) == "directory_selector":
                return elem.id
        return None
