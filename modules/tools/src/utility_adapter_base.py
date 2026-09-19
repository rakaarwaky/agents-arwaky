"""Per-tool adapter base — shared leaf mechanics.

Every concrete `utility_<tool>_adapter.py` is a stateless leaf: it imports ONLY
from `modules/shared/...`, stdlib, and this base module. AES forbids
utility-to-utility imports between adapters, so shared mechanics live here.
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


class AdapterBase:
    """Stateless helpers shared by all per-tool adapters (no tool knowledge)."""

    # -- Satisfied check (idempotence gate; provisioner consults this first) -------
    def satisfied(self, spec, root: Path | None = None) -> bool:
        """True when the tool is already installed at its pin (skip the adapter)."""
        return False

    # -- Source bootstrap ----------------------------------------------------------
    def ensure_source(self, root: Path, src_rel: str) -> Path:
        """Ensure `root/src_rel` exists, attempting a git submodule init first."""
        src = root / src_rel
        if not src.exists():
            print(f">>> Initializing submodule {src_rel}...")
            subprocess.run(
                ["git", "-C", str(root), "submodule", "update", "--init", src_rel],
                check=False,
            )
        return src

    # -- Shell-out -----------------------------------------------------------------
    def run(self, cmd: list[str], cwd: Path | str | None = None) -> None:
        """Run with check=True; raises subprocess.CalledProcessError on failure."""
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

    def require(self, tool: str, reason: str = "") -> bool:
        """True when *tool* is on PATH; otherwise print the missing-tool diagnostic."""
        if shutil.which(tool):
            return True
        print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
        return False

    # -- Copying -------------------------------------------------------------------
    def copy_app(self, src: Path, app_dir: Path, ignore_patterns: list[str]) -> None:
        """Replace *app_dir* with a copy of *src*, dropping the listed patterns."""
        ignore = shutil.ignore_patterns(*ignore_patterns)
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(src, app_dir, ignore=ignore)

    # -- Launchers (write mechanics delegated to utility_launcher_writer) ----------
    def write_node_launcher(self, name: str, entry: Path) -> Path:
        from modules.tools.src.utility_launcher_writer import write_node_entry_launcher
        launcher = write_node_entry_launcher(name, entry)
        print(f"  -> {launcher}")
        return launcher

    def finish_bin(self) -> None:
        """Ensure bin home + PATH warning after launcher writes."""
        ensure_bin_home()
        warn_if_bin_not_on_path()

    # -- Owned teardown data (uninstall source of truth) ---------------------------
    def generic_owned(
        self,
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


#: Standard ignore list for JS/TS project trees.
NODE_IGNORES = [
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
]

def repo_root():
    return REPO_ROOT


ROOT = repo_root

__all__ = ["AdapterBase", "NODE_IGNORES", "ROOT"]
