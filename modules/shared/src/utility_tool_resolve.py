"""Tool / submodule path resolvers — shared doctor + status diagnostics (utility).

Stateless path lookups used by the doctor env/tools capabilities and any
other caller that needs a PATH-aware executable or submodule-missing check.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_vo import bin_home


def resolve_executable(binary: str) -> Path | None:
    """shutil.which + bin_home executable fallback."""
    found = shutil.which(binary)
    if found:
        return Path(found)
    local = bin_home() / binary
    if local.exists() and os.access(local, os.X_OK):
        return local
    return None


def is_submodule_missing(path_str: str) -> bool:
    """A submodule path is missing when its target (or .git) does not exist."""
    root = REPO_ROOT
    target = root / path_str
    if not target.exists() or not (target / ".git").exists():
        gitmodules = root / ".gitmodules"
        if gitmodules.exists():
            try:
                text = gitmodules.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return False
            return f"path = {path_str}" in text
        return False
    return False


__all__ = ["is_submodule_missing", "resolve_executable"]
