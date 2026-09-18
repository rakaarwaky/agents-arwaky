"""Tool resolver helpers — ported candidate-name lookups for uninstaller capabilities.

Verbatim PORT of the original tools/lib/tool_resolver.py
``uninstall_dir_candidates`` + ``find_uninstaller`` logic: the candidate names
(override / id / id-mcp, in that order) and the existence check are the
original tool_resolver behaviour, only the target directory is the AES
per-tool uninstaller capability tree instead of the deleted tools/uninstall/
scripts.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_constant import UNINSTALL_OVERRIDES
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root


def find_uninstaller_candidate(tool) -> Path | None:
    """AES per-tool uninstaller capability path (original tools/uninstall/ scripts deleted)."""
    names = []
    if tool.id in UNINSTALL_OVERRIDES:
        names.append(UNINSTALL_OVERRIDES[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    root = repo_root / "modules" / "uninstaller" / "src"
    for name in names:
        candidate = root / f"capabilities_{name.replace('-', '_')}_uninstaller.py"
        if candidate.exists():
            return candidate
    return None
