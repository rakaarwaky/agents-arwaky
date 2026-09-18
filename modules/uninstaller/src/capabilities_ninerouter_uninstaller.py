"""9Router uninstaller (daemon + launchers + secrets) — port of tools/uninstall/uninstall_ninerouter.py.

The original script ran `tools/daemons/ninerouter_daemon.py service-uninstall`
to stop the Podman daemon service; in the AES layout that logic lives in the
daemon module, so this capability delegates to
PodmanDaemonManager.service_uninstall() instead.
"""
from __future__ import annotations

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller
from modules.shared.src.utility_xdg_atomic_io import remove_tool_artifacts
from modules.shared.src.utility_xdg_paths import agents_arwaky_config_dir, data_home


LAUNCHERS = ["9router"]


class NinerouterUninstaller(IToolUninstaller):
    """Remove 9Router's daemon service, launchers, data/config, and secrets."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        print(">>> Uninstalling 9Router...")

        # Stop daemon if registered (tools/daemons/ninerouter_daemon.py
        # service-uninstall, now provided by the daemon module)
        from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager

        rc = PodmanDaemonManager().service_uninstall()
        if rc != 0:
            print(f"  Warning: 9router service-uninstall exited {rc}")

        # Remove launcher + XDG artifacts via shared helper
        remove_tool_artifacts("9router", LAUNCHERS, clean_config=True)

        # Remove container-internal binary (per-tool internal-bin)
        (data_home() / "9router/internal-bin/9router").unlink(missing_ok=True)

        # Remove secret env files (tool-specific, not handled by remove_tool_artifacts)
        (agents_arwaky_config_dir() / "ninerouter.env").unlink(missing_ok=True)

        print(">>> 9router uninstalled (launchers + data + config + cache + secrets).")
        return UninstallResult(True, spec.id, "9router uninstalled (daemon service + launchers + data + config + secrets)")
