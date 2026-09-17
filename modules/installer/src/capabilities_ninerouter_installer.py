"""9Router installer (hybrid daemon + launcher) — port of tools/install/install_ninerouter.py.

9Router is a Podman/daemon service, not a compiled binary. The installer:
- registers the systemd user unit (tools/deploy/ninerouter.service) via
  `ninerouter_daemon.py service-install`
- writes a python3 launcher into ~/.local/bin/9router that execs
  tools/daemons/ninerouter_daemon.py with AGENTS_ARWAKY_ROOT baked in
- mirrors the launcher into $XDG_DATA_HOME/9router/internal-bin/ so the
  daemon container can find it (same pattern as anytype-daemon).
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, data_home


TOOL_DIR_REL = "tools/daemons"
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

        daemon_py = root / TOOL_DIR_REL / "ninerouter_daemon.py"
        print(">>> Setting up 9Router hybrid architecture...")
        if daemon_py.exists():
            subprocess.run(
                [sys.executable, str(daemon_py), "service-install"],
                check=False,
            )

        launcher_content = f'''#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))
daemon = root / "{TOOL_DIR_REL}/ninerouter_daemon.py"
os.execvpe("python3", ["python3", str(daemon), *sys.argv[1:]], os.environ.copy())
'''
        launcher = bin_home() / "9router"
        atomic_write_text(launcher, launcher_content)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher, internal_bin / "9router")
        (internal_bin / "9router").chmod(0o755)
        print(f">>> Successfully installed 9Router -> {launcher}")
        return InstallResult(True, spec.id, "9router installed")
