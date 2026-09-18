"""Venv value objects."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VenvInfo:
    """A venv install location for a Python tool."""

    tool_name: str
    venv_dir: str
    python_bin: str
