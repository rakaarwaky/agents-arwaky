#!/usr/bin/env python3
"""Installer codegraph (Python, shared node installer)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from utility_node_installer import install_node_tool  # noqa: E402


def main() -> int:
    return install_node_tool(
        tool_name="codegraph",
        vendor_subpath="vendor/codegraph",
        aliases=["codegraph-mcp", "codegraph"],
        entry_point="bin/codegraph.js",
    )


if __name__ == "__main__":
    raise SystemExit(main())
