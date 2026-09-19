"""Shared per-tool adapter mechanics — stateless free functions (AES404).

Every concrete `utility_<tool>_adapter.py` is a stateless leaf that imports
ONLY from `modules/shared/...` (taxonomy/shared), stdlib, and this module.
AES404 forbids class definitions in the utility layer, so all shared
mechanics live here as module-level functions.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home


def run(cmd: list[str], cwd: Path | str | None = None) -> None:
    """Run with check=True; raises subprocess.CalledProcessError on failure."""
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def require(tool: str, reason: str = "") -> bool:
    """True when *tool* is on PATH; otherwise print the missing-tool diagnostic."""
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def ensure_source(root: Path, src_rel: str) -> Path:
    """Ensure `root/src_rel` exists, attempting a git submodule init first."""
    src = root / src_rel
    if not src.exists():
        print(f">>> Initializing submodule {src_rel}...")
        subprocess.run(
            ["git", "-C", str(root), "submodule", "update", "--init", src_rel],
            check=False,
        )
    return src


def copy_app(src: Path, app_dir: Path, ignore_patterns: list[str]) -> None:
    """Replace *app_dir* with a copy of *src*, dropping the listed patterns."""
    ignore = shutil.ignore_patterns(*ignore_patterns)
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src, app_dir, ignore=ignore)


def write_node_launcher(name: str, entry: Path) -> Path:
    """Write a node entry launcher via the shared launcher writer."""
    from modules.tools.src.utility_launcher_writer import write_node_entry_launcher
    launcher = write_node_entry_launcher(name, entry)
    print(f"  -> {launcher}")
    return launcher


def finish_bin() -> None:
    """Ensure bin home + PATH warning after launcher writes."""
    ensure_bin_home()
    warn_if_bin_not_on_path()


def generic_owned(
    spec,
    launcher_names: list[str],
    *,
    extra: list[Path] | None = None,
    config: list[str] | None = None,
) -> list[Path]:
    """Generic XDG owned set for one tool: bin launchers + data + cache.

    Adapters extend it with tool-specific extras (internal-bin copies,
    env files, daemon units) via *extra* and with installer-owned
    config subtrees (``config_home() / name``) via *config*.
    """
    from modules.shared.src.taxonomy_xdg_paths import cache_home, config_home, data_home

    paths: list[Path] = [bin_home() / name for name in launcher_names]
    paths.append(data_home() / spec.id)
    paths.append(cache_home() / spec.id)
    for name in config or []:
        paths.append(config_home() / name)
    paths.extend(extra or [])
    return paths


def satisfied(spec, root: Path | None = None) -> bool:
    """True when the tool is already installed at its pin (skip the adapter)."""
    return False


#: Standard ignore list for JS/TS project trees.
NODE_IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]

ROOT = REPO_ROOT

__all__ = [
    "NODE_IGNORES",
    "ROOT",
    "copy_app",
    "ensure_source",
    "finish_bin",
    "generic_owned",
    "require",
    "run",
    "satisfied",
    "write_node_launcher",
]
