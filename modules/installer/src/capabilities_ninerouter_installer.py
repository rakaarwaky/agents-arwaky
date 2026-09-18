"""9Router installer (hybrid daemon + launcher) — port of tools/install/install_ninerouter.py.

9Router is a Podman/daemon service, not a compiled binary. The installer:
- registers the systemd user unit (modules/daemon/deploy/ninerouter.service) via the
  daemon module's PodmanDaemonManager.service_install()
- writes a python3 launcher into ~/.local/bin/9router that imports
  modules.daemon.src.surface_daemon_command.cmd_9router with AGENTS_ARWAKY_ROOT baked in
- mirrors the launcher into $XDG_DATA_HOME/9router/internal-bin/ so the
  daemon container can find it (same pattern as anytype-daemon).
"""
from __future__ import annotations

import shutil

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


DATA_DIR_NAME = "9router"
INTERNAL_BIN = "internal-bin"


class NinerouterInstaller(IToolInstaller):
    """Set up the 9Router hybrid daemon + launcher (no compile step)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "9router").exists():
            return InstallResult(True, spec.id, "9router is already installed")

        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DATA_DIR_NAME
        data_dir.mkdir(parents=True, exist_ok=True)

        # Delegate to the daemon module's service_install (modules/daemon/deploy/ninerouter.service)
        from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager

        print(">>> Setting up 9Router hybrid architecture...")
        manager = PodmanDaemonManager()
        if shutil.which("podman") is None:
            return InstallResult(True, spec.id, "9router skipped (podman not found)")
        rc = manager.service_install()
        if rc != 0:
            return InstallResult(True, spec.id, f"9router service-install exited {rc} (see 'aa 9router logs')")

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
        print(f">>> Successfully installed 9Router -> {launcher}")
        return InstallResult(True, spec.id, "9router installed")
