"""anytype-daemon uninstaller (systemd + launchers) — port of tools/uninstall/uninstall_anytype_daemon.py.

Removes the anytype-daemon systemd user unit, its launchers (`anytype-daemon`
+ alias `ad`), and the per-tool internal-bin mirror. With `purge=True` the
anytype / anytype-mcp XDG data trees are rmtree'd as well (the original
script accepted a `--purge` argv flag; the CLI surface does not expose it,
so it is kept as an optional flag on this capability).
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.tool.contract_tool_protocol import IToolUninstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import remove_tool_artifacts
from modules.shared.src.xdg.utility_xdg_paths import config_home, data_home


LAUNCHERS = ["anytype-daemon", "ad"]


class AnytypeDaemonUninstaller(IToolUninstaller):
    """Remove anytype-daemon's systemd unit, launchers, and XDG artifacts."""

    def __init__(self, root=None) -> None:
        self._root = root or None
        self.purge: bool = False

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        print(">>> Uninstalling anytype-daemon...")

        # Disable systemd user service if present (same as the daemon module's
        # AnytypeDaemonManager unit layout: $XDG_CONFIG_HOME/systemd/user).
        unit = config_home() / "systemd/user/anytype-daemon.service"
        if unit.exists() and shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "disable", "--now", "anytype-daemon.service"],
                           check=False, capture_output=True)
            unit.unlink(missing_ok=True)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
            print("  -> systemd service anytype-daemon removed")

        # Launcher + alias ad + per-tool internal-bin (mirror of the original)
        remove_tool_artifacts("anytype-daemon", LAUNCHERS, clean_config=False)
        (data_home() / "anytype-daemon/internal-bin/anytype-daemon").unlink(missing_ok=True)

        if self.purge:
            shutil.rmtree(data_home() / "anytype", ignore_errors=True)
            shutil.rmtree(data_home() / "anytype-mcp", ignore_errors=True)
            print("  -> anytype data purged")

        print(">>> anytype-daemon uninstalled.")
        return UninstallResult(True, spec.id, "anytype-daemon uninstalled (unit + launchers + data)")
