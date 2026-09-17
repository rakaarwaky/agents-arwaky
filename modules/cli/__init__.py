"""CLI feature package — unified agents-arwaky dispatcher (aa).

Public re-exports: entry point + router.
"""
from __future__ import annotations

from modules.cli.src import dispatch, main

__all__ = [
    "dispatch",
    "main",
]
