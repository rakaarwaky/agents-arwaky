"""FR-003 verb — uninstall a tool: remove owned state, verify residuals.

Sub-steps (internal, not separate public methods):
1. Remove: stop the daemon (if applicable) first — an active unit that
   refuses to stop becomes a named residual, never force-killed. Then
   remove launchers + XDG data/cache/config, scoped strictly to the
   owned set (adapter ``owned_paths`` plus per-tool daemon-unit flags
   from the constant table).
2. Verify: a failed removal still gets verified so residuals are
   surfaced, not hidden. Confirm launchers gone from XDG bin, binary
   absent from PATH, data/cache subtrees removed, daemon unit absent,
   and each explicitly-owned path gone. Anything surviving becomes a
   named residual. Verification failures append to the UninstallResult
   chain; nothing raises into the CLI surface.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolUninstaller
from modules.shared.src.taxonomy_common_vo import (
    ToolSpec,
    UninstallResult,
    bin_home,
    config_home,
    remove_tool_artifacts,
    tool_cache_dir,
    tool_data_dir,
)
from modules.shared.src.taxonomy_tools_constant import (
    DAEMON_NAMES,
    DAEMON_UNIT_TOOLS,
    KEEP_CONFIG,
    LAUNCHER_NAMES,
)


def _stop_daemon(daemons: object, tool_id: str) -> bool:
    """Stop the daemon's service/container before removal.

    *daemons* is anything exposing ``service_uninstall(name) -> int``
    (structural typing, resolved by the root layer's daemon aggregate).

    Returns False when the unit could not be stopped (active-service residual —
    container-isolation invariant: never force-killed). Raises on unknown
    daemon names, which the caller folds into a residual.
    """
    daemon_name = DAEMON_NAMES[tool_id]
    rc = daemons.service_uninstall(daemon_name)
    if rc == 0:
        return True
    unit = DAEMON_UNIT_TOOLS.get(tool_id)
    # P1-4: never invoke systemctl when it is absent (FileNotFoundError guard).
    if unit and shutil.which("systemctl") and (config_home() / "systemd" / "user" / unit).exists():
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


def _survivor_reason(path: Path) -> str:
    """Classify why a path survived removal."""
    if path.is_dir() and any(path.iterdir()):
        return "subtree still contains files"
    if path.is_symlink():
        return "symlink still present"
    return "foreign-owner: path reappeared"


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class UninstallerCapability(IToolUninstaller):
    """Business action uninstall(spec, owned_paths, dry_run): remove + verify."""

    def __init__(self, daemons: object | None = None) -> None:
        self._daemons = daemons

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def uninstall(
        self,
        spec: ToolSpec,
        owned_paths: list[Path],
        dry_run: bool = False,
    ) -> UninstallResult:
        # Sub-step 1: generic filesystem teardown + optional service stop.
        result = self._remove(spec, owned_paths, dry_run=dry_run)

        # Sub-step 2: confirm owned-set removal; a failed removal still
        # gets verified so residuals are surfaced, not hidden.
        return self._verify(spec, result, owned_paths)

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────────
    def _remove(
        self,
        spec: ToolSpec,
        owned_paths: list[Path],
        dry_run: bool = False,
    ) -> UninstallResult:
        notes: list[str] = []
        removed: list[Path] = []

        # Daemon teardown first: stop (or flag as residual), then remove unit.
        if spec.id in DAEMON_UNIT_TOOLS and not dry_run:
            if self._daemons is None:
                notes.append("residual: daemon aggregate unavailable, unit not stopped")
            else:
                try:
                    stopped = _stop_daemon(self._daemons, spec.id)
                # P1-4: FileNotFoundError (no systemctl), KeyError (daemon table
                # miss) and OSError must become named residuals, never CLI exceptions.
                except (ValueError, AttributeError, KeyError, OSError) as exc:
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
        clean_config = spec.id not in KEEP_CONFIG
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

    def _verify(
        self,
        spec: ToolSpec,
        uninstall_result: UninstallResult,
        owned_paths: list[Path] | None = None,
    ) -> UninstallResult:
        residuals: list[str] = []

        # Launchers must be gone from XDG bin.
        for name in LAUNCHER_NAMES.get(spec.id, []):
            p = bin_home() / name
            if p.exists():
                residuals.append(f"launcher {p} ({_survivor_reason(p)})")

        # Binary absent from PATH.
        if shutil.which(spec.binary) is not None:
            residuals.append(
                f"binary {spec.binary} still on PATH (race: reappeared during removal)"
            )

        # Daemon unit must be absent (inactive is acceptable for the unit file).
        unit = DAEMON_UNIT_TOOLS.get(spec.id)
        if unit:
            unit_path = config_home() / "systemd" / "user" / unit
            if unit_path.exists():
                residuals.append(f"daemon unit {unit_path} still present (active-service or race)")

        # Each explicitly-owned path must be gone.
        for p in (owned_paths or []):
            if p.exists():
                residuals.append(f"{p} ({_survivor_reason(p)})")

        if residuals:
            return UninstallResult(
                False,
                spec.id,
                f"{spec.id}: partial removal — {len(residuals)} residual(s): "
                + " | ".join(residuals),
            )

        base = uninstall_result.message
        if owned_paths:
            return UninstallResult(
                True, spec.id, f"{base} — {len(owned_paths)} path(s) verified clean"
            )
        return UninstallResult(True, spec.id, f"{base} — verified clean")


__all__ = ["UninstallerCapability"]
