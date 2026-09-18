"""Manifest reader (capabilities layer, moved from tools/lib/manifest.py)."""
from __future__ import annotations

import functools
import json
import sys
from pathlib import Path

from modules.shared.src.common.taxonomy_core_error import ManifestParseError
from modules.shared.src.manifest.taxonomy_manifest_vo import Tool
from modules.shared.src.paths.utility_paths import repo_root


def manifest_path() -> Path:
    return repo_root() / "modules" / "shared" / "config" / "manifest.json"


@functools.lru_cache(maxsize=1)
def load_tools() -> list[Tool]:
    """Load all tools from the manifest.

    A manifest with missing required fields raises :class:`ManifestParseError`
    (the legacy tools/lib/manifest.py raised bare ``ValueError``; this is the
    documented adaptation to the domain error hierarchy).
    """
    path = manifest_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"Warning: failed to parse {path}: {e}", file=sys.stderr)
        return []
    tools: list[Tool] = []
    for item in data.get("tools", []):
        # Validasi field wajib (C-2)
        missing = [f for f in ("id", "binary", "path") if not item.get(f)]
        if missing:
            raise ManifestParseError(
                f"manifest tool entry missing required fields {missing}: "
                f"{item.get('id', '?')}"
            )
        tools.append(Tool(
            id=item.get("id", ""),
            category=item.get("category", ""),
            binary=item.get("binary", ""),
            is_mcp=bool(item.get("isMcp", False)),
            description=item.get("description", ""),
            path=item.get("path", ""),
            alias=item.get("alias"),
        ))
    return tools


def find_tool(query: str) -> Tool | None:
    """Find a tool by id, binary name, or alias."""
    query = query.strip()
    if not query:
        return None
    for tool in load_tools():
        if (
            query == tool.id
            or query == tool.binary
            or (tool.alias and query == tool.alias)
        ):
            return tool
    return None
