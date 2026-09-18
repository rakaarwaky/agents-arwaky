"""Launcher value objects."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LauncherSpec:
    """One launcher to be written into $XDG_BIN_HOME."""

    name: str
    entry: str
    uv_args: tuple[str, ...] = ()
