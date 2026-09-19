"""Manifest value objects (moved from tools/lib/manifest.py)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    """One entry of config/manifest.json (frozen VO)."""

    id: str
    category: str
    binary: str
    is_mcp: bool
    description: str
    path: str
    alias: str | None = None
    mcp_binary: str | None = None
