"""Completion feature package — bash/zsh completion generation for the aa CLI.

Public re-exports: surface entry point + completer utilities.
"""
from __future__ import annotations

from modules.completion.src import cmd_completion, generate_bash, generate_zsh, install

__all__ = [
    "cmd_completion",
    "generate_bash",
    "generate_zsh",
    "install",
]
