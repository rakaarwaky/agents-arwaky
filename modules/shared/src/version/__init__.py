"""Version bump + CLI (P1-CI3).\n\nMoved from common.version; consumers import from ``modules.shared.src.version``.\n"""
from __future__ import annotations

from modules.shared.src.version.utility_version import bump, read_version
from modules.shared.src.version.utility_version_cli import main as version_main

__all__ = [
    "bump",
    "read_version",
    "version_main",
]
