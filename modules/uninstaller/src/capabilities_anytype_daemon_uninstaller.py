"""anytype-daemon uninstaller — strict verbatim port of tools/uninstall/uninstall_anytype_daemon.py.

Every statement of the original script is preserved. Import paths swapped to
AES equivalents (from xdg -> taxonomy_xdg_paths / taxonomy_xdg_atomic_io). The
original script's `--purge` argv flag is kept as the accepted `purge` flag
attribute on this capability (the CLI surface does not expose argv).
"""
from __future__ import annotations

import shutil
import subprocess

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller
from modules.shared.src.taxonomy_xdg_atomic_io import remove_tool_artifacts
from modules.shared.src.taxonomy_xdg_paths import config_home, data_home

ROOT = repo_root()


# ─── Block 1: Class Definition & Constructor ──────────────
class AnytypeDaemonUninstaller(IToolUninstaller):
    """AES facade over the verbatim original uninstall body."""

    def __init__(self, root=None, daemons: object | None = None) -> None:
        self._root = root or ROOT
        self._daemons = daemons
        self.purge: bool = False

    # ─── Block 2: Protocol ABC Method Implementation ──────────

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        rc = _uninstall(self.purge)
        return UninstallResult(rc == 0, spec.id, "anytype-daemon uninstalled (unit + launchers + data)")

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
def _uninstall(purge: bool) -> int:
    print(">>> Uninstalling anytype-daemon...")

    # Disable systemd user service if present
    unit = config_home() / "systemd/user/anytype-daemon.service"
    if unit.exists() and shutil.which("systemctl"):
        subprocess.run(["systemctl", "--user", "disable", "--now", "anytype-daemon.service"],
                       check=False, capture_output=True)
        unit.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
        print("  -> systemd service anytype-daemon removed")

    # Launcher + alias ad + per-tool internal-bin
    remove_tool_artifacts("anytype-daemon", ["anytype-daemon", "ad"], clean_config=False)
    (data_home() / "anytype-daemon/internal-bin/anytype-daemon").unlink(missing_ok=True)

    if purge:
        shutil.rmtree(data_home() / "anytype", ignore_errors=True)
        shutil.rmtree(data_home() / "anytype-mcp", ignore_errors=True)
        print("  -> anytype data purged")

    print(">>> anytype-daemon uninstalled.")
    return 0



