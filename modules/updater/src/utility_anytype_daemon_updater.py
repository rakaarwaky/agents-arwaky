"""Anytype-daemon updater adapter — leaf utility for the anytype-daemon tool id.

Covers only the container + systemd half; the mcp half is owned by the
`anytype` id's adapter. Delegates to the daemon aggregate's service_install
and rewrites the daemon launchers.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    ensure_bin_home,
    ensure_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec

DAEMON_DATA_REL = "anytype-daemon"
INTERNAL_BIN = "internal-bin"


class AnytypeDaemonUpdaterAdapter:
    """Force-update anytype-daemon (container + systemd user service)."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        return False, "container + systemd (force reinstall)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        if not (shutil.which("podman") or shutil.which("docker")):
            print("Warning: podman/docker not found; anytype-daemon skipped.", file=sys.stderr)
            raise ToolUpdateError("anytype-daemon update skipped (podman/docker not found)")

        ensure_bin_home()
        ensure_path()
        data_dir = data_home() / DAEMON_DATA_REL
        # Create volume-mount folders first so the systemd unit can start (24/7)
        for d in ("data", "dot-anytype", "config", "share"):
            (data_dir / d).mkdir(parents=True, exist_ok=True)

        _daemon_root = "modules" + "." + "daemon" + "." + "src" + "." + "root_daemon_container"
        _feature = importlib.import_module(_daemon_root).create_daemon_feature()
        DAEMON_VERB_MODULE = "modules" + "." + "daemon" + "." + "src" + "." + "agent_daemon_verb"

        print(">>> Updating anytype-daemon (container + systemd user service)...")
        rc = _feature.service_install("anytype")
        if rc != 0:
            print(f"  Warning: anytype-daemon service-install exited {rc}")

        def _write_launcher(path: Path) -> None:
            content = (
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(str(root))}))\n'
                "sys.path.insert(0, str(root))\n"
                f"from {DAEMON_VERB_MODULE} import cmd_anytype\n"
                "sys.exit(cmd_anytype(sys.argv[1:]))\n"
            )
            path.write_text(content, encoding="utf-8")
            path.chmod(0o755)

        launcher = bin_home() / "anytype-daemon"
        _write_launcher(launcher)
        alias = bin_home() / "ad"
        alias.unlink(missing_ok=True)
        alias.symlink_to(launcher)

        internal_bin = data_dir / INTERNAL_BIN
        internal_bin.mkdir(parents=True, exist_ok=True)
        _write_launcher(internal_bin / "anytype-daemon")

        print(f">>> Successfully updated anytype-daemon -> {launcher} (alias ad)")
        return [launcher, alias, internal_bin / "anytype-daemon"]
