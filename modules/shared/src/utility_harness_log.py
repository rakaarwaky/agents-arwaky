"""Harness console log helpers — domain-agnostic print helpers (utility).

Shared by the three harness capabilities (connector / disconnector / skills);
no instance state, no side effects beyond stdout/stderr writes.
"""
from __future__ import annotations



def log_header(msg: str) -> None:
    """Print a section-header line to stdout."""


def log_sub(msg: str) -> None:
    """Print a sub-item line to stdout."""


def log_ok(msg: str) -> None:
    """Print a green checkmark confirmation line to stdout."""


def log_skip(msg: str) -> None:
    """Print a skip/unchanged line to stdout."""


def log_warn(msg: str) -> None:
    """Print a yellow warning line to stdout."""


def log_err(msg: str) -> None:
    """Print a red error line to stderr."""


__all__ = [
    "log_err",
    "log_header",
    "log_ok",
    "log_skip",
    "log_sub",
    "log_warn",
]
