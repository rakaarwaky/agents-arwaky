"""9Router updater (hybrid daemon + launcher) — port of tools/update/update_ninerouter.py.

Re-runs the daemon service-install and rewrites the 9router launcher. The
original script exec'd `tools/daemons/ninerouter_daemon.py service-install`
and wrote a launcher that pointed at that script; in the AES layout the
daemon logic lives in modules/daemon, so this delegates to
PodmanDaemonManager.service_install() and the launcher imports
cmd_9router from the daemon surface (same as the installer).
9Router is not a git submodule (it is daemon tooling under modules/daemon/deploy),
so there is no submodule pull — matching the original comment.
"""
from __future__ import annotations

import shutil
import sys

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater import IToolUpdater
from modules.shared.src.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.utility_xdg_paths import bin_home, data_home


DATA_DIR_NAME = "9router"
INTERNAL_BIN = "internal-bin"


class NinerouterUpdater(IToolUpdater):
    """Force-reinstall the 9Router hybrid daemon + launcher."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        # 9router is under modules/daemon/deploy (daemon service unit), not a submodule,
        # so there is nothing to pull — but keep the data dir in place.

        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DATA_DIR_NAME
        data_dir.mkdir(parents=True, exist_ok=True)

        # Delegate to the daemon module's service_install (modules/daemon/deploy/ninerouter.service)
        from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager

        print(">>> Updating 9Router hybrid architecture...")
        manager = PodmanDaemonManager()
        if shutil.which("podman") is None:
            print("  Warning: podman not found; 9router service-install skipped.", file=sys.stderr)
        else:
            rc = manager.service_install()
            if rc != 0:
                print(f"  Warning: 9router service-install exited {rc}")

        launcher_content = f'''#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))
sys.path.insert(0, str(root))
from modules.daemon.src.surface_daemon_command import cmd_9router
sys.exit(cmd_9router(sys.argv[1:]))
'''
        launcher = bin_home() / "9router"
        atomic_write_text(launcher, launcher_content)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher, internal_bin / "9router")
        (internal_bin / "9router").chmod(0o755)
        print(f">>> Successfully updated 9Router -> {launcher}")
        return UpdateResult(True, spec.id, "9router updated")
