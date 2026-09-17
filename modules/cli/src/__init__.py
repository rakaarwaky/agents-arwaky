"""CLI feature — public symbols.

Re-exports the dispatch router, entry point, and help doc so feature
consumers can import from ``modules.cli`` directly.
"""
from __future__ import annotations

from modules.cli.src.root_cli_entry import HELP_DOC, main
from modules.cli.src.surface_cli_router import dispatch

__all__ = [
    "HELP_DOC",
    "dispatch",
    "main",
]
