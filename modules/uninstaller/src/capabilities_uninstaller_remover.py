"""FR-001: remove a tool's owned state — launchers, XDG data/cache/bin, daemon units.

Daemon teardown is delegated to the daemon feature module (container-isolation
invariant: only 9Router and Anytype are containerized; an active unit that
refuses to stop becomes a residual, never force-killed).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.taxonomy_xdg_atomic_io import remove_tool_artifacts
from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)

from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolRemover


class _DaemonStopper(Protocol):
    """Structural type: anything with a service_uninstall(name) -> int method."""

    def service_uninstall(self, name: str) -> int: ...


# Tool ids that have a systemd user unit managed under $XDG_CONFIG_HOME.
_DAEMON_UNIT_TOOLS: dict[str, str] = {
    "9router": "9router.service",
    "anytype-daemon": "anytype-daemon.service",
}

# Tool id -> daemon feature name (keyed on manifest id; "anytype-daemon"
# routes to the "anytype" daemon manager in the daemon orchestrator).
_DAEMON_NAMES: dict[str, str] = {
    "9router": "9router",
    "anytype-daemon": "anytype",
}

# Per-tool launcher names the installer registered under $XDG_BIN_HOME.
# Folded from the 13 per-tool capability files (superseded).
_LAUNCHERS: dict[str, list[str]] = {
    "anytype": ["anytype-mcp"],
    "anytype-daemon": ["anytype-daemon", "ad"],
    "blender": ["blender-arwaky", "ba", "blender-mcp"],
    "codegraph": ["codegraph-mcp", "codegraph"],
    "context7": ["context7-mcp", "ctx7"],
    "fetch": ["fetch-mcp", "mcp-fetch"],
    "lint": ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui", "lac"],
    "mnemosyne": ["mnemosyne", "mnemosyne-mcp"],
    "9router": ["9router"],
    "ponytail": ["ponytail-mcp"],
    "qwen-web": ["qwen-web-arwaky", "qwa", "qwen-web-cli", "qwen-web-mcp", "qwc"],
    "vision": ["vision-arwaky", "vision-arwaky-cli", "va", "vision-arwaky-mcp"],
    "workspace": ["workspace-mcp", "google-workspace-mcp"],
}

# Tools whose XDG config subtree is installer-owned and removed with the tool.
# anytype-daemon keeps its config (the daemon owns it across updates).
_CLEAN_CONFIG: dict[str, bool] = {
    "anytype-daemon": False,
    "9router": True,
}

# Tool id -> extra owned paths the installer created outside the generic XDG
# layout (folded from the per-tool capability files).
_EXTRA_OWNED: dict[str, list[Path]] = {
    "9router": [
        data_home() / "9router" / "internal-bin" / "9router",
        agents_arwaky_config_dir() / "ninerouter.env",
    ],
    "anytype-daemon": [
        data_home() / "anytype-daemon" / "internal-bin" / "anytype-daemon",
    ],
}


def _stop_daemon(daemons: _DaemonStopper, tool_id: str) -> bool:
    """Stop the daemon's service/container before removal.

    Returns False when the unit could not be stopped (active-service residual —
    container-isolation invariant: never force-killed). Raises on unknown
    daemon names, which the caller folds into a residual.
    """
    daemon_name = _DAEMON_NAMES[tool_id]
    rc = daemons.service_uninstall(daemon_name)
    if rc == 0:
        return True
    unit = _DAEMON_UNIT_TOOLS.get(tool_id)
    if unit and (config_home() / "systemd" / "user" / unit).exists():
        active = subprocess.run(
            ["systemctl", "--user", "is-active", unit],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        if active == "active":
            return False
    return True


class UninstallerRemover(IToolRemover):
    """Generic filesystem teardown + optional service stop (FR-001)."""

    def __init__(self, daemons: _DaemonStopper | None = None) -> None:
        self._daemons = daemons

    def remove(self, spec: ToolSpec, owned_paths: list[Path], dry_run: bool = False) -> UninstallResult:
        notes: list[str] = []
        removed: list[Path] = []

        # Daemon teardown first: stop (or flag as residual), then remove unit.
        if spec.id in _DAEMON_UNIT_TOOLS and not dry_run:
            if self._daemons is None:
                notes.append("residual: daemon aggregate unavailable, unit not stopped")
            else:
                try:
                    stopped = _stop_daemon(self._daemons, spec.id)
                except (ValueError, AttributeError) as exc:
                    notes.append(f"residual: daemon stop failed ({exc})")
                    stopped = False
                if stopped:
                    unit = _DAEMON_UNIT_TOOLS[spec.id]
                    unit_path = config_home() / "systemd" / "user" / unit
                    if unit_path.exists():
                        unit_path.unlink(missing_ok=True)
                        removed.append(unit_path)
                        subprocess.run(
                            ["systemctl", "--user", "daemon-reload"],
                            check=False, capture_output=True,
                        )
                else:
                    unit = _DAEMON_UNIT_TOOLS[spec.id]
                    notes.append(f"residual: unit {unit} still active, not force-killed")

        # Generic XDG teardown (launchers, data, cache, optionally config).
        launchers = _LAUNCHERS.get(spec.id, [])
        clean_config = _CLEAN_CONFIG.get(spec.id, True)
        if dry_run:
            planned: list[str] = [f"launcher {n}" for n in launchers]
            planned += [f"data {spec.id}", f"cache {spec.id}"]
            if clean_config:
                planned.append(f"config {spec.id}")
            notes.append(f"dry-run: planned deletions: {', '.join(planned)}")
        else:
            remove_tool_artifacts(spec.id, launchers, clean_config=clean_config)

        # Tool-specific extra owned paths (internal-bin, secrets).
        for extra in _EXTRA_OWNED.get(spec.id, []):
            if dry_run:
                notes.append(f"dry-run: would remove {extra}")
                continue
            if extra.is_dir():
                shutil.rmtree(extra, ignore_errors=True)
            else:
                extra.unlink(missing_ok=True)
            removed.append(extra)

        # Callers may pass owned paths beyond the known set; remove what exists.
        for path in owned_paths:
            if dry_run:
                notes.append(f"dry-run: would remove {path}")
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            removed.append(path)

        if not notes and not removed and not dry_run:
            return UninstallResult(True, spec.id, f"{spec.id}: nothing to do (never installed)")

        message = f"{spec.id} uninstalled"
        if notes:
            message += " | " + "; ".join(notes)
        success = not any(n.startswith("residual") for n in notes)
        return UninstallResult(success, spec.id, message)
