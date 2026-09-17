"""Completion feature — public symbols.

Re-exports the completer utilities and surface entry point so feature
consumers can import from ``modules.completion`` directly.
"""
from __future__ import annotations

from modules.completion.src.surface_completion_command import cmd_completion
from modules.completion.src.utility_completer import (
    COMMANDS,
    HARNESSES,
    SERVICE_ACTIONS,
    SERVICE_TARGETS,
    TOOL_SUBCOMMANDS,
    generate_bash,
    generate_zsh,
    install,
)

__all__ = [
    "COMMANDS",
    "HARNESSES",
    "SERVICE_ACTIONS",
    "SERVICE_TARGETS",
    "TOOL_SUBCOMMANDS",
    "cmd_completion",
    "generate_bash",
    "generate_zsh",
    "install",
]
