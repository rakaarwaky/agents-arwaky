"""Harness console log helpers — domain-agnostic print helpers (utility).

Shared by the three harness capabilities (connector / disconnector / skills);
no instance state, no side effects beyond stdout/stderr writes.
"""
from __future__ import annotations

import sys


def _color(code: int) -> str:
    """Return a truecolor SGR code, or empty when stdout is not a TTY."""
    if not sys.stdout.isatty():
        return ""
    return f"\033[{code}m"


def _reset() -> str:
    """Return the SGR reset code, or empty when stdout is not a TTY."""
    if not sys.stdout.isatty():
        return ""
    return "\033[0m"


def log_header(msg: str) -> None:
    """Print a bold cyan section-header line to stdout."""
    print(f"{_color(36)}{_color(1)}{msg}{_reset()}")


def log_sub(msg: str) -> None:
    """Print an indented sub-item line to stdout."""
    print(f"  {msg}")


def log_ok(msg: str) -> None:
    """Print a green checkmark confirmation line to stdout."""
    print(f"{_color(32)}\u2713{_reset()} {msg}")


def log_skip(msg: str) -> None:
    """Print a yellow skip/unchanged line to stdout."""
    print(f"{_color(33)}\u21b7{_reset()} {msg}")


def log_warn(msg: str) -> None:
    """Print a yellow warning line to stdout."""
    print(f"{_color(33)}\u26a0 {_reset()}{msg}", file=sys.stderr)


def log_err(msg: str) -> None:
    """Print a red error line to stderr."""
    print(f"{_color(31)}\u2717{_reset()} {msg}", file=sys.stderr)


__all__ = [
    "log_err",
    "log_header",
    "log_ok",
    "log_skip",
    "log_sub",
    "log_warn",
]
