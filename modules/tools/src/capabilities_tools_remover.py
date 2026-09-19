"""FR-005 capability — remove a tool's owned state (launchers, XDG dirs, daemon units).

Daemon teardown is delegated to the daemon feature module (container-isolation
invariant: only 9Router and Anytype are containerized; an active unit that
refuses to stop becomes a residual, never force-killed). The owned-path set
is the adapter's ``owned_paths`` (launchers, data/cache trees, extras) plus
the per-tool daemon-unit flags from the constant table.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.taxonomy_xdg_atomic_io import remove_tool_artifacts
from modules.shared.src.taxonomy_xdg_paths import bin_home, config_home

from modules.tools.src.taxonomy_tools_constant import (
    DAEMON_NAMES,
    DAEMON_UNIT_TOOLS,
    LAUNCHER_NAMES,
)


class _DaemonStopper(Protocol):
    """Structural type: anything with a service_uninstall(name) -> int method."""

    def service_uninstall(self, name: str) -> int: ...


# Tool ids whose XDG config subtree is NOT installer-owned and is kept on
# removal (anytype-daemon keeps its config: the daemon owns it across updates).
_KEEP_CONFIG: frozenset[str] = frozenset({"anytype-daemon"})


def _stop_daemon(daemons: _DaemonStopper, tool_id: str) -> bool:
    """Stop the daemon's service/container before removal.

    Returns False when the unit could not be stopped (active-service residual —
    container-isolation invariant: never force-killed). Raises on unknown
    daemon names, which the caller folds into a residual.
    """
    daemon_name = DAEMON_NAMES[tool_id]
    rc = daemons.service_uninstall(daemon_name)
    if rc == 0:
        return True
    unit = DAEMON_UNIT_TOOLS.get(tool_id)
    if unit and (config_home() / "systemd" / "user" / unit).exists():
        active = subprocess.run(
            ["systemctl", "--user", "is-active", unit],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        if active == "active":
            return False
    return True


def _extras(owned_paths: list[Path], spec: ToolSpec, launchers: list[str]) -> list[Path]:
    """Adapter-owned paths beyond the generic launcher/data/cache teardown.

    The generic part (bin launchers, data, cache, optionally config) is
    handled by ``remove_tool_artifacts``; this returns everything else the
    adapter reported (internal-bin copies, env files, daemon unit paths).
    """
    from modules.shared.src.taxonomy_xdg_paths import tool_data_dir, tool_cache_dir

    generic = {bin_home() / name for name in launchers}
    generic.add(tool_data_dir(spec.id))
    generic.add(tool_cache_dir(spec.id))
    seen: set[Path] = set()
    extras: list[Path] = []
    for p in owned_paths:
        if p in generic or p in seen:
            continue
        seen.add(p)
        extras.append(p)
    return extras


class RemoverCapability:
    """Generic filesystem teardown + optional service stop (FR-005)."""

    def __init__(self, daemons: _DaemonStopper | None = None) -> None:
        self._daemons = daemons

    def remove(self, spec: ToolSpec, owned_paths: list[Path], dry_run: bool = False) -> UninstallResult:
        from modules.shared.src.taxonomy_xdg_paths import tool_data_dir, tool_cache_dir

        notes: list[str] = []
        removed: list[Path] = []

        # Daemon teardown first: stop (or flag as residual), then remove unit.
        if spec.id in DAEMON_UNIT_TOOLS and not dry_run:
            if self._daemons is None:
                notes.append("residual: daemon aggregate unavailable, unit not stopped")
            else:
                try:
                    stopped = _stop_daemon(self._daemons, spec.id)
                except (ValueError, AttributeError) as exc:
                    notes.append(f"residual: daemon stop failed ({exc})")
                    stopped = False
                if stopped:
                    unit = DAEMON_UNIT_TOOLS[spec.id]
                    unit_path = config_home() / "systemd" / "user" / unit
                    if unit_path.exists():
                        unit_path.unlink(missing_ok=True)
                        removed.append(unit_path)
                        subprocess.run(
                            ["systemctl", "--user", "daemon-reload"],
                            check=False, capture_output=True,
                        )
                else:
                    unit = DAEMON_UNIT_TOOLS[spec.id]
                    notes.append(f"residual: unit {unit} still active, not force-killed")

        # Generic XDG teardown (launchers, data, cache, optionally config).
        launchers = LAUNCHER_NAMES.get(spec.id, [])
        clean_config = spec.id not in _KEEP_CONFIG
        if dry_run:
            planned: list[str] = [f"launcher {n}" for n in launchers]
            planned += [f"data {spec.id}", f"cache {spec.id}"]
            if clean_config:
                planned.append(f"config {spec.id}")
            notes.append(f"dry-run: planned deletions: {', '.join(planned)}")
        else:
            remove_tool_artifacts(spec.id, launchers, clean_config=clean_config)
            removed.extend(bin_home() / name for name in launchers)
            removed.append(tool_data_dir(spec.id))
            removed.append(tool_cache_dir(spec.id))

        # Tool-specific extra owned paths (internal-bin, secrets, unit files).
        for extra in _extras(owned_paths, spec, launchers):
            if dry_run:
                notes.append(f"dry-run: would remove {extra}")
                continue
            if extra.is_dir():
                shutil.rmtree(extra, ignore_errors=True)
            else:
                extra.unlink(missing_ok=True)
            removed.append(extra)

        if not notes and not removed and not dry_run:
            return UninstallResult(True, spec.id, f"{spec.id}: nothing to do (never installed)")

        message = f"{spec.id} uninstalled"
        if notes:
            message += " | " + "; ".join(notes)
        success = not any(n.startswith("residual") for n in notes)
        return UninstallResult(success, spec.id, message)


__all__ = ["RemoverCapability"]
