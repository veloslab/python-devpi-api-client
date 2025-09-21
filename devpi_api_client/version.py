"""Version helpers for devpi_api_client."""

from __future__ import annotations

import re
from importlib import metadata as importlib_metadata
from importlib.metadata import PackageNotFoundError
from pathlib import Path


def _read_version_from_pyproject() -> str | None:
    """Read the project version from the local pyproject.toml file if available."""
    # Locate repository root relative to this file
    root = Path(__file__).resolve().parent.parent
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        return None

    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r"^version\s*=\s*\"([^\"]+)\"", content, flags=re.MULTILINE)
    if match:
        return match.group(1)
    return None


def get_version() -> str:
    """Return the package version as declared in pyproject.toml."""
    package_name = "devpi-api-client"
    try:
        return importlib_metadata.version(package_name)
    except PackageNotFoundError:
        fallback = _read_version_from_pyproject()
        return fallback or "0.0.0"


__all__ = ["__version__", "get_version"]

__version__ = get_version()

