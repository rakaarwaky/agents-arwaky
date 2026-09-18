"""Unified version bump (moved from tools/build/bump_version.py)."""
from __future__ import annotations

from modules.shared.src.common.version.capabilities_version_cli import main
from modules.shared.src.common.version.utility_version import bump, read_version

__all__ = [
    "bump",
    "main",
    "read_version",
]
