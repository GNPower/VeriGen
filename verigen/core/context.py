"""Assemble the render context handed to Jinja2.

The context is the normalized values plus any derived values contributed by an
extension's context providers. Derived values may reference (and override)
declared variables, which is how an author computes things like address maps.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from verigen.core.extensions import ExtensionRegistry


def build_context(
    definition,
    values: Dict[str, Any],
    registry: Optional[ExtensionRegistry] = None,
) -> Dict[str, Any]:
    """Merge normalized ``values`` with extension-derived context."""
    context: Dict[str, Any] = dict(values)
    if registry is not None:
        context.update(registry.run_context_providers(values, definition))
    return context
