#!/usr/bin/env python3
"""Installer ponytail (Python, shared node installer)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from node_installer import (  # type: ignore[import-not-found]
    install_node_tool,
)


def main() -> int:
    return install_node_tool(
        tool_name="ponytail",
        vendor_subpath="vendor/ponytail",
        aliases=['ponytail-mcp'],
        entry_point="index.js",
    )


if __name__ == "__main__":
    raise SystemExit(main())
