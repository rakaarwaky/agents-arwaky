"""MCP manifest reader (AES utility layer).

Stateless reader over the repo's MCP tool manifest. Shared by the two MCP
capabilities (config generator and writer) so neither imports the other —
``McpConfigWriter`` never imports ``capabilities_mcp_generator``.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "load_mcp_manifest",
]


def load_mcp_manifest(root: Path) -> dict:
    """Read the MCP manifest under *root*, returning {} when absent/unreadable."""
    manifest_path = root / "tools" / "mcp" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        data: dict = json.loads(manifest_path.read_text())
        return data
    except json.JSONDecodeError:
        return {}
