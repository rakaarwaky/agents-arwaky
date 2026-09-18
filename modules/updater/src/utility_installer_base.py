"""Tool resolver helpers — ported candidate-name lookups for updater capabilities.

Verbatim PORT of the original tools/lib/tool_resolver.py ``update_dir_candidates``
+ ``find_updater`` logic: the candidate names (override / id / id-mcp, in that
order) and the existence check are the original tool_resolver behaviour, only
the target directory is the AES per-tool updater capability tree instead of the
deleted tools/update/ scripts.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.common.taxonomy_core_constant import INSTALL_OVERRIDES
from modules.shared.src.paths.utility_paths import repo_root


def find_updater_candidate(tool) -> Path | None:
    """AES per-tool updater capability path (original tools/update/ scripts deleted)."""
    names = []
    if tool.id in INSTALL_OVERRIDES:
        names.append(INSTALL_OVERRIDES[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    root = repo_root() / "modules" / "updater" / "src"
    for name in names:
        candidate = root / f"capabilities_{name.replace('-', '_')}_updater.py"
        if candidate.exists():
            return candidate
    return None
