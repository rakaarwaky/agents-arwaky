"""CLI feature — public symbols.

Re-exports the dispatch router and entry point so feature consumers can
import from ``modules.cli`` directly.
"""
from __future__ import annotations

from modules.cli.src.root_cli_entry import main
from modules.cli.src.surface_cli_router import dispatch

__all__ = [
    "dispatch",
    "main",
]
