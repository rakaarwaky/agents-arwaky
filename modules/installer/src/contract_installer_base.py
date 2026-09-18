"""Shared installer capability base class (contract layer — taxonomy-only deps)."""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home, ensure_path


class InstallerBase:
    """Common helpers every per-tool installer capability reuses.

    # Block 1: Submodule bootstrap
    # Block 2: Result helpers
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root

    # -- Block 1: Submodule bootstrap ------------------------------------------
    def _ensure_submodule(self, spec: ToolSpec) -> bool:
        src_rel = spec.path
        if not (self._root / src_rel).exists():
            subprocess.run(
                ["git", "-C", str(self._root), "submodule", "update", "--init", src_rel],
                check=False,
            )
        return (self._root / src_rel).exists()

    # -- Block 2: Result helpers ------------------------------------------------
    @staticmethod
    def ok(spec: ToolSpec, message: str) -> InstallResult:
        return InstallResult(True, spec.id, message)

    @staticmethod
    def fail(spec: ToolSpec, message: str) -> InstallResult:
        return InstallResult(False, spec.id, message)

    @staticmethod
    def prepare_env() -> None:
        ensure_bin_home()
        ensure_path()
