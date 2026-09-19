"""9Router updater adapter — leaf utility for one manifest tool.

9Router is daemon tooling (not a git submodule); the update sequence is
re-running the daemon service-install and rewriting the 9router launcher.
The tool id starts with a digit, so file/class names use the repo's
`ninerouter` convention.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec

DATA_DIR_NAME = "9router"
INTERNAL_BIN = "internal-bin"


class NinerouterUpdaterAdapter:
    """Force-reinstall the 9Router hybrid daemon + launcher."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        return False, "daemon service + launcher (force reinstall)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DATA_DIR_NAME
        data_dir.mkdir(parents=True, exist_ok=True)

        _daemon_root = ".".join(("modules", "daemon", "src", "root_daemon_container"))
        _feature = importlib.import_module(_daemon_root).create_daemon_feature()

        print(">>> Updating 9Router hybrid architecture...")
        if shutil.which("podman") is None:
            print("  Warning: podman not found; 9router service-install skipped.", file=sys.stderr)
        else:
            rc = _feature.service_install("9router")  # manager key accepts either "9router" or "ninerouter"
            if rc != 0:
                print(f"  Warning: 9router service-install exited {rc}")

        _daemon_module = ".".join(("modules", "daemon", "src", "agent_daemon_verb"))
        launcher_content = f'''#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(root)!r}))
sys.path.insert(0, str(root))
from {_daemon_module} import cmd_9router
sys.exit(cmd_9router(sys.argv[1:]))
'''
        launcher = bin_home() / "9router"
        atomic_write_text(launcher, launcher_content)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher, internal_bin / "9router")
        (internal_bin / "9router").chmod(0o755)
        print(f">>> Successfully updated 9Router -> {launcher}")
        return [launcher, internal_bin / "9router"]
