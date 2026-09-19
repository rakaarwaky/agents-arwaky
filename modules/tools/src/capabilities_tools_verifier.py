"""FR-006 capability — confirm the owned set is gone and produce the removal report.

Runs only after FR-005 completes (success OR partial) — a failed removal still
gets verified so residuals are surfaced, not hidden. Verification failures
append to the ``UninstallResult`` chain; nothing raises into the CLI surface.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.taxonomy_xdg_paths import bin_home, config_home

from modules.tools.src.contract_tools_protocol import IToolVerifier
from modules.tools.src.taxonomy_tools_constant import (
    DAEMON_UNIT_TOOLS,
    LAUNCHER_NAMES,
)


def _survivor_reason(path: Path) -> str:
    """Classify why a path survived removal."""
    if path.is_dir() and any(path.iterdir()):
        return "subtree still contains files"
    if path.is_symlink():
        return "symlink still present"
    return "foreign-owner: path reappeared"


class VerifierCapability(IToolVerifier):
    """Confirm owned-set removal and report named residuals (FR-006)."""

    def verify(
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


__all__ = ["VerifierCapability"]
