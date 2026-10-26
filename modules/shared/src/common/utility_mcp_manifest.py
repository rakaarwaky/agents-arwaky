"""MCP manifest reader (AES utility layer).

The repository's canonical manifest is ``config/manifest.json``. The reader
normalizes its camel-case ``isMcp`` field into the ``mcp`` flag consumed by MCP
capabilities. A legacy ``tools/mcp/manifest.json`` map is still accepted for
older integrations, but is not the source of truth for this checkout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "load_mcp_manifest",
]


def load_mcp_manifest(root: Path) -> dict[str, dict[str, Any]]:
    """Read *root*'s canonical tool manifest into an id-keyed mapping.

    Missing, malformed, or structurally invalid manifests degrade to an empty
    mapping so callers can report an empty registry without raising.
    """
    manifest_path = root / "config" / "manifest.json"
    if not manifest_path.is_file():
        manifest_path = root / "tools" / "mcp" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    entries = data.get("tools") if isinstance(data, dict) else None
    if isinstance(entries, list):
        normalized: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                continue
            tool = dict(entry)
            tool["mcp"] = bool(tool.get("isMcp", tool.get("mcp", False)))
            normalized[tool["id"]] = tool
        return normalized

    # Compatibility with the historical id-keyed manifest shape.
    if isinstance(data, dict) and all(isinstance(value, dict) for value in data.values()):
        return data
    return {}
