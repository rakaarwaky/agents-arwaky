"""Harness console log helpers — domain-agnostic print helpers (utility).

Shared by the three harness capabilities (connector / disconnector / skills);
no instance state, no side effects beyond stdout/stderr writes.
"""
from __future__ import annotations

import sys


def log_header(msg: str) -> None:
    print(f"==> {msg}")


def log_sub(msg: str) -> None:
    print(f"  -> {msg}")


def log_ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def log_skip(msg: str) -> None:
    print(f"  ⟳ {msg}")


def log_warn(msg: str) -> None:
    print(f"  ⚠ {msg}")


def log_err(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)


__all__ = [
    "log_err",
    "log_header",
    "log_ok",
    "log_skip",
    "log_sub",
    "log_warn",
]
