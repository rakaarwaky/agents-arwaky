"""Blender updater — VERBATIM port of tools/update/update_blender.py.

Keep the ENTIRE original body: every function, every constant, every
print statement, every edge-case message, every subprocess call, exactly
as written in the original. The ONLY differences:
1. Import paths (all AES equivalents under modules/shared/src/).
"""
from __future__ import annotations

import subprocess
import sys

from modules.shared.src.utility_paths import repo_root

ROOT = repo_root()

from modules.shared.src.taxonomy_xdg_paths import tool_data_dir
from modules.installer.src.utility_venv_helpers import ensure_venv, install_package, setup_xdg_directories, setup_bin_links
from modules.shared.src.utility_git_update import update_submodule, write_install_stamp
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater_protocol import IToolUpdater

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [("blender-arwaky", "blender-arwaky"), ("ba", "blender-arwaky"), ("blender-mcp", "blender-mcp")]


# ─── Block 1: Class Definition & Constructor ──────────────
class BlenderUpdater(IToolUpdater):
    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    # ─── Block 2: Protocol ABC Method Implementation ──────────

    def update(self, spec: ToolSpec) -> UpdateResult:
        rc = main()
        return UpdateResult(rc == 0, spec.id, "blender-arwaky updated" if rc == 0 else "blender-arwaky update failed")

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    print(">>> Updating blender-arwaky (XDG compliant)...")

    update_submodule(ROOT, SRC_REL)

    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    python_bin = ensure_venv(TOOL_NAME, force=True)
    install_package(python_bin, SRC_DIR, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)

    # D2: write provenance stamp for rollback/audit
    write_install_stamp(python_bin.parent.parent, TOOL_NAME, SRC_DIR)

    print("\n>>> Successfully updated blender-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    return 0



