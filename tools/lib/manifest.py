"""Helper manifest.json (Python)."""
from __future__ import annotations

import functools
import json
import os
from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    env_root = os.environ.get("AGENTS_ARWAKY_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def manifest_path() -> Path:
    return repo_root() / "tools" / "config" / "manifest.json"


@dataclass
class Tool:
    id: str
    category: str
    binary: str
    is_mcp: bool
    description: str
    path: str
    alias: str | None = None


@functools.lru_cache(maxsize=1)
def load_tools() -> list[Tool]:
    path = manifest_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    tools: list[Tool] = []
    for item in data.get("tools", []):
        # Validasi field wajib (C-2)
        missing = [f for f in ("id", "binary", "path") if not item.get(f)]
        if missing:
            raise ValueError(f"manifest tool entry missing required fields {missing}: {item.get('id', '?')}")
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
    query = query.strip()
    if not query:
        return None
    for tool in load_tools():
        if query == tool.id or query == tool.binary or (tool.alias and query == tool.alias):
            return tool
    return None
