"""Workspace (google-workspace-mcp) updater — VERBATIM port of tools/update/update_workspace.py.

Keep the ENTIRE original body: every function, every constant, every
print statement, every edge-case message, every subprocess call, exactly
as written in the original. The ONLY differences:
1. Import paths (all AES equivalents under modules/shared/src/).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.utility_paths import repo_root

ROOT = repo_root()

from modules.installer.src.capabilities_launcher_writer import write_uv_launchers
from modules.shared.src.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater import IToolUpdater

SRC_REL = "vendor/google-workspace-mcp"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    # Pull latest from remote
    update_submodule(ROOT, SRC_REL)

    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully updated google-workspace-mcp")
    return 0


class WorkspaceUpdater(IToolUpdater):
    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def update(self, spec: ToolSpec) -> UpdateResult:
        rc = main()
        return UpdateResult(rc == 0, spec.id, "google-workspace-mcp updated" if rc == 0 else "google-workspace-mcp update failed")
