"""Optional Python extension hooks for a generator definition.

The declarative path (templates + config + built-in filters) covers most needs.
When an author needs real logic (cross-field validation, derived values, custom
filters), their definition may set ``extension: some_module.py``. VeriGen imports
that file and calls its ``register(api)`` function. All such code lives in the
*author's* repository; VeriGen ships only this interface.

Trust model: loading a definition that declares an extension executes that
extension's Python code. This is acceptable for a local developer tool, the same
way running a Makefile or a setup.py is, but it is stated plainly here.

Example extension module::

    def register(api):
        @api.filter("double")
        def _double(value):
            return value * 2

        @api.validator
        def _check(values, definition):
            errors = []
            if values["width"] & (values["width"] - 1):
                errors.append("width must be a power of two")
            return errors

        @api.context
        def _derive(values, definition):
            return {"addr_width": max(1, (values["depth"] - 1).bit_length())}
"""

from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional

from verigen.core.errors import ExtensionError


class ExtensionRegistry:
    """Collects the hooks an extension module registers.

    Passed to the extension's ``register(api)`` as ``api``. Methods double as
    decorators so authors can write ``@api.filter("name")`` or ``@api.validator``.
    """

    def __init__(self) -> None:
        self.filters: Dict[str, Callable] = {}
        self.globals: Dict[str, object] = {}
        self.validators: List[Callable] = []
        self.context_providers: List[Callable] = []

    def filter(self, name: str) -> Callable[[Callable], Callable]:
        """Register a Jinja2 filter under ``name``. Use as a decorator."""

        def _decorator(func: Callable) -> Callable:
            self.filters[name] = func
            return func

        return _decorator

    def add_global(self, name: str, value: object) -> None:
        """Register a Jinja2 global (a value or callable) under ``name``."""
        self.globals[name] = value

    def validator(self, func: Callable) -> Callable:
        """Register a value validator ``(values, definition) -> list[str]``.

        Returns a (possibly empty) list of human-readable error strings; any
        non-empty result fails generation. Use as a decorator.
        """
        self.validators.append(func)
        return func

    def context(self, func: Callable) -> Callable:
        """Register a derived-context provider ``(values, definition) -> dict``.

        The returned mapping is merged into the render context. Use as a decorator.
        """
        self.context_providers.append(func)
        return func

    def run_validators(self, values: dict, definition) -> List[str]:
        errors: List[str] = []
        for func in self.validators:
            try:
                result = func(values, definition)
            except Exception as exc:  # noqa: BLE001 - surface author errors cleanly
                raise ExtensionError(f"validator {func.__name__!r} raised: {exc}") from exc
            if result:
                errors.extend(result)
        return errors

    def run_context_providers(self, values: dict, definition) -> dict:
        derived: dict = {}
        for func in self.context_providers:
            try:
                result = func(values, definition) or {}
            except Exception as exc:  # noqa: BLE001
                raise ExtensionError(
                    f"context provider {func.__name__!r} raised: {exc}"
                ) from exc
            if not isinstance(result, dict):
                raise ExtensionError(
                    f"context provider {func.__name__!r} must return a dict, "
                    f"got {type(result).__name__}"
                )
            derived.update(result)
        return derived


def load_extension(
    ext_ref: str, base_dir: Optional[Path]
) -> ExtensionRegistry:
    """Import an extension module and run its ``register`` function.

    Args:
        ext_ref: Path to the extension ``.py`` file (relative to ``base_dir``).
        base_dir: Directory the definition lives in; used to resolve ``ext_ref``.

    Returns:
        A populated :class:`ExtensionRegistry`.

    Raises:
        ExtensionError: The module is missing, fails to import, or lacks a usable
            ``register`` function.
    """
    ext_path = Path(ext_ref)
    if not ext_path.is_absolute() and base_dir is not None:
        ext_path = Path(base_dir) / ext_path

    if not ext_path.is_file():
        raise ExtensionError(f"extension module not found: {ext_path}")

    module_name = f"verigen_ext_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, ext_path)
    if spec is None or spec.loader is None:
        raise ExtensionError(f"could not load extension module: {ext_path}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001
        raise ExtensionError(f"extension module {ext_path} failed to import: {exc}") from exc

    register = getattr(module, "register", None)
    if not callable(register):
        raise ExtensionError(
            f"extension module {ext_path} must define a callable register(api)"
        )

    registry = ExtensionRegistry()
    try:
        register(registry)
    except Exception as exc:  # noqa: BLE001
        raise ExtensionError(f"extension register() failed: {exc}") from exc
    return registry
