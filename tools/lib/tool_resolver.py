"""Tool installer/uninstaller resolution — capabilities layer (P4-A1)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from manifest import Tool, repo_root  # type: ignore[import-not-found]
from xdg import bin_home  # type: ignore[import-untyped]


def install_dir_candidates(tool: Tool) -> list[Path]:
    overrides = {"workspace": "google-workspace-mcp", "fetch": "fetch-mcp", "anytype": "anytype-mcp", "anytype-daemon": "anytype-mcp", "9router": "ninerouter"}
    names = []
    if tool.id in overrides:
        names.append(overrides[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    return [repo_root() / "tools/install" / f"install_{n.replace(chr(45), chr(95))}.py" for n in names if n]


def find_installer(tool: Tool):
    for candidate in install_dir_candidates(tool):
        if candidate.exists():
            return candidate
    return None


def update_dir_candidates(tool: Tool) -> list[Path]:
    overrides = {"workspace": "google-workspace-mcp", "fetch": "fetch-mcp", "anytype": "anytype-mcp", "anytype-daemon": "anytype-mcp", "9router": "ninerouter"}
    names = []
    if tool.id in overrides:
        names.append(overrides[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    return [repo_root() / "tools/update" / f"update_{n.replace(chr(45), chr(95))}.py" for n in names if n]


def find_updater(tool: Tool):
    for candidate in update_dir_candidates(tool):
        if candidate.exists():
            return candidate
    return None


def uninstall_dir_candidates(tool: Tool) -> list[Path]:
    overrides = {"workspace": "google-workspace-mcp", "fetch": "fetch-mcp", "anytype": "anytype-mcp", "9router": "ninerouter"}
    names = []
    if tool.id in overrides:
        names.append(overrides[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    return [repo_root() / "tools/uninstall" / f"uninstall_{n.replace(chr(45), chr(95))}.py" for n in names if n]


def find_uninstaller(tool: Tool):
    for candidate in uninstall_dir_candidates(tool):
        if candidate.exists():
            return candidate
    return None


def executable_path(binary: str):
    found = shutil.which(binary)
    if found:
        return Path(found)
    local = bin_home() / binary
    if local.exists() and os.access(local, os.X_OK):
        return local
    return None
