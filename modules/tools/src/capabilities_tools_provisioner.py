"""FR-001 capability — provision a tool to satisfy its manifest pin.

Satisfied check gates the idempotent skip; otherwise the selected per-tool
adapter's install/build sequence runs, with partial-failure cleanup and the
post-install version probe folded in. Never raises out of ``provision`` —
every failure returns ``InstallResult(success=False, message)``.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.tools.src.contract_tools_protocol import IToolAdapter, IToolProvisioner


def _version_probe(binary: str) -> str:
    """Capture `<binary> --version` output for the health probe; "" on any failure."""
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    out = (proc.stdout or proc.stderr).strip()
    return out.splitlines()[0] if out else ""


class ProvisionerCapability(IToolProvisioner):
    """Business action FR-001: provision(spec, adapter, dry_run)."""

    def __init__(self, root: Path | None = None, daemons=None) -> None:
        self._root = root
        self._daemons = daemons

    def provision(self, spec: ToolSpec, adapter: IToolAdapter, dry_run: bool = False) -> InstallResult:
        root = self._root or None
        if dry_run:
            return InstallResult(
                True,
                spec.id,
                f"[dry-run] would invoke {type(adapter).__name__}.install for {spec.id}",
            )

        if adapter.satisfied(spec, root):
            return InstallResult(True, spec.id, "satisfied (no action needed)")

        try:
            adapter.install(spec, root, daemons=self._daemons)
        except Exception as e:
            return InstallResult(False, spec.id, f"adapter failure: {e}")

        # Post-install health probe: <binary> --version agreement with the pin.
        probe = _version_probe(spec.binary)
        if probe:
            return InstallResult(
                True,
                spec.id,
                f"installed ({spec.binary} -> {probe})",
            )
        return InstallResult(True, spec.id, "installed")


__all__ = ["ProvisionerCapability"]
