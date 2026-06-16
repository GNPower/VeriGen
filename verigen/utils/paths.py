"""
VeriGen Path Utilities

Provides path resolution utilities for consistent path handling
across the application.
"""

import os
from pathlib import Path
from typing import Optional


def resolve_path(path: str, base_dir: Optional[str] = None) -> Path:
    """
    Resolve a path, making it absolute if relative.

    Args:
        path: The path to resolve.
        base_dir: Base directory for relative paths. Uses CWD if not provided.

    Returns:
        Resolved absolute Path object.
    """
    path_obj = Path(path)

    if path_obj.is_absolute():
        return path_obj

    if base_dir:
        return Path(base_dir) / path_obj
    else:
        return Path.cwd() / path_obj


def get_project_base_dir(manifest_path: str) -> Path:
    """
    Get the base directory for a project from its manifest path.

    The project base directory is the directory containing the manifest file.

    Args:
        manifest_path: Path to the project manifest file.

    Returns:
        Path to the project base directory.
    """
    manifest = Path(manifest_path)
    return manifest.parent.resolve()


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.

    Returns:
        Path object for the directory.
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_relative_path(path: str, base_dir: str) -> Path:
    """
    Get a path relative to a base directory.

    Args:
        path: The path to make relative.
        base_dir: The base directory.

    Returns:
        Relative path, or the original path if not relative to base.
    """
    try:
        return Path(path).relative_to(base_dir)
    except ValueError:
        # Path is not relative to base_dir
        return Path(path)


def get_package_dir() -> Path:
    """
    Get the verigen package directory.

    Returns:
        Path to the verigen package directory.
    """
    return Path(__file__).parent.parent


def get_icons_dir() -> Path:
    """
    Get the icons directory within the verigen package.

    Returns:
        Path to the icons directory.
    """
    return get_package_dir() / "icons"


def find_project_root(start_path: Optional[str] = None) -> Optional[Path]:
    """
    Find the project root by looking for a .verigen.yaml file.

    Searches upward from the start path until a manifest is found
    or the filesystem root is reached.

    Args:
        start_path: Directory to start searching from. Uses CWD if not provided.

    Returns:
        Path to project root, or None if not found.
    """
    if start_path:
        current = Path(start_path).resolve()
    else:
        current = Path.cwd().resolve()

    while current != current.parent:
        # Look for any .verigen.yaml file
        verigen_files = list(current.glob('*.verigen.yaml'))
        if verigen_files:
            return current

        current = current.parent

    return None
