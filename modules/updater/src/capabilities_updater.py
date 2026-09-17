"""Tool update capability — git pull + reinstall for a ToolSpec."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.logging.utility_logging import sub
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.installer.src.capabilities_installer import ToolInstaller


class ToolUpdater(IToolUpdater):
    """Pull the submodule to its remote tip and reinstall the tool.

    Ported from tools/update/update_*.py: every updater there is
    ``update_submodule(root, spec.path)`` followed by the same install
    path as the installer.

    # Block 1: Constructor
    # Block 2: Submodule update
    # Block 3: Reinstall dispatch + result shaping
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, root: Path | None = None, installer: ToolInstaller | None = None) -> None:
        self._root = root or repo_root()
        self._installer = installer or ToolInstaller(self._root)

    # -- Block 2: Submodule update ---------------------------------------------
    def _pull(self, spec: ToolSpec) -> bool:
        sub(f"Updating submodule {spec.path}...")
        return update_submodule(self._root, spec.path)

    # -- Block 3: Reinstall dispatch + result shaping ----------------------------
    def update(self, spec: ToolSpec) -> UpdateResult:
        if not self._pull(spec):
            return UpdateResult(False, spec.id, f"git pull failed for {spec.path}")
        result = self._installer.install(spec)
        return UpdateResult(result.success, spec.id, f"{result.message} (after pull)")
