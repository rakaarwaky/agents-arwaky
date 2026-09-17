"""Vision updater — VERBATIM port of tools/update/update_vision.py.

Keep the ENTIRE original body: every function, every constant, every
print statement, every edge-case message, every subprocess call, exactly
as written in the original. The ONLY differences:
1. Import paths (all AES equivalents under modules/shared/src/).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root

ROOT = repo_root()

from modules.shared.src.xdg.utility_xdg_paths import bin_home, tool_data_dir
from modules.shared.src.venv.capabilities_venv_installer import ensure_venv, install_package, setup_xdg_directories, setup_bin_links
from modules.shared.src.git.utility_git_update import update_submodule, write_install_stamp
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater

TOOL_NAME = "vision-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("vision-arwaky", "vision-arwaky-cli"),
    ("vision-arwaky-cli", "vision-arwaky-cli"),
    ("va", "vision-arwaky-cli"),
    ("vision-arwaky-mcp", "vision-arwaky-mcp"),
]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    print(">>> Updating vision-arwaky (XDG compliant)...")

    update_submodule(ROOT, SRC_REL)

    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    python_bin = ensure_venv(TOOL_NAME, force=True)
    install_package(python_bin, SRC_DIR, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)

    write_install_stamp(python_bin.parent.parent, TOOL_NAME, SRC_DIR)

    print("\n>>> Successfully updated vision-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    return 0


class VisionUpdater(IToolUpdater):
    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def update(self, spec: ToolSpec) -> UpdateResult:
        rc = main()
        return UpdateResult(rc == 0, spec.id, "vision-arwaky updated" if rc == 0 else "vision-arwaky update failed")
