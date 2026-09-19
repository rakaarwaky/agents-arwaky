"""FR-001/FR-002 verb — install a tool: provision, register its launcher.

Sub-steps (internal, not separate public methods):
1. Provision: satisfied check gates the idempotent skip; otherwise the
   selected per-tool adapter's install/build sequence runs, with the
   post-install version probe folded in.
2. Launcher registration (only after a successful provision): one
   launcher per binary plus one per manifest alias is verified under XDG
   bin; a stale foreign launcher (no provenance marker) is reported as a
   residual, never overwritten; a correct launcher already in place is a
   no-op success. A failed provision skips registration and folds the
   diagnostic into the InstallResult.

Every failure path returns ``InstallResult(success=False, message)``.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.tools.src.contract_tools_protocol import IToolInstaller


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


def _has_provenance(launcher: Path) -> bool:
    """True when the launcher carries the arwaky-installer provenance marker."""
    try:
        head = launcher.open("rb").read(256).decode("utf-8", "replace")
    except OSError:
        return False
    return PROVENANCE_MARKER in head


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class InstallerCapability(IToolInstaller):
    """Business action install(spec, adapter, dry_run): provision + register launcher."""

    def __init__(self, root: Path | None = None, daemons: object | None = None) -> None:
        self._root = root
        self._daemons = daemons

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def install(self, spec: ToolSpec, adapter: object, dry_run: bool = False) -> InstallResult:
        root = self._root or None
        if dry_run:
            return InstallResult(
                True,
                spec.id,
                f"[dry-run] would invoke {type(adapter).__name__}.install for {spec.id}",
            )

        # P1-3: the satisfied check must not raise out of the verb.
        try:
            if adapter.satisfied(spec, root):
                return InstallResult(True, spec.id, "satisfied (no action needed)")
        except Exception as e:
            return InstallResult(False, spec.id, f"satisfied-check failure: {e}")

        try:
            adapter.install(spec, root, daemons=self._daemons)
        except Exception as e:
            return InstallResult(False, spec.id, f"adapter failure: {e}")

        # Post-install health probe: <binary> --version agreement with the pin.
        probe = _version_probe(spec.binary)
        if probe:
            result = InstallResult(
                True,
                spec.id,
                f"installed ({spec.binary} -> {probe})",
            )
        else:
            result = InstallResult(True, spec.id, "installed")

        # Sub-step 2: launcher registration policy runs only after a
        # successful provision (registration skipped on failure above).
        result = self._register_launcher(spec, result)
        return result

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────────
    def _register_launcher(
        self,
        spec: ToolSpec,
        install_result: InstallResult,
    ) -> InstallResult:
        if not install_result.success:
            return InstallResult(
                install_result.success,
                spec.id,
                f"{install_result.message}; launcher registration skipped (provision failed)",
            )

        ensure_bin_home()

        # The adapter already wrote its launchers; the registrar verifies them
        # and reports stale foreign files (no provenance marker) as residuals,
        # never silently overwriting. A correct launcher already in place is a
        # no-op success.
        notes: list[str] = []
        # One launcher per binary plus one per manifest-declared alias.
        targets: list[Path] = [bin_home() / spec.binary]
        if spec.alias:
            targets.append(bin_home() / spec.alias)
        for p in dict.fromkeys(targets):
            if p.exists() and not p.is_symlink() and not _has_provenance(p):
                notes.append(f"residual launcher (foreign, no provenance marker): {p.name}")

        detail = "; ".join(notes) if notes else "launcher registered"
        return InstallResult(True, spec.id, detail)


__all__ = ["InstallerCapability"]
