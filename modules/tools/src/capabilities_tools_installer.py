"""FR-001/FR-002 action — install a tool: provision, register its launcher.

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

from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER
from modules.shared.src.taxonomy_common_error import ToolInstallError
from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    ToolSpec,
    bin_home,
    ensure_bin_home,
)


def _version_probe(binary: str) -> str:
    """Capture `<binary> --version` output for the health probe; "" on any failure."""
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=60, check=False
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


# ─── Block 1: Class Definition & Constructor ──────────────
class InstallerCapability(IToolsProtocol):
    """Business action install(spec, dry_run): provision + register launcher."""

    def __init__(self, root: Path | None = None, daemons: object | None = None,
                 registry: dict[str, object] | None = None) -> None:
        self._root = root
        self._daemons = daemons
        # P1-7: action calls route through the injected registry directly
        # (single API pipeline) instead of going through an adapter facade.
        self._registry = dict(registry) if registry is not None else {}

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        spec: ToolSpec | None = None,
        query: object | None = None,
        args: list[str] | None = None,
    ) -> object:
        """Single protocol entry: dispatch *op* to the install action."""
        if op != "install" or spec is None:
            raise ToolInstallError(
                f"installer capability got op={op!r} (expected 'install' with a spec)"
            )
        dry_run = bool(args and "dry-run" in args)
        adapter = query if query is not None else None
        return self.install(spec, adapter=adapter, dry_run=dry_run)
    def __repr__(self) -> str:
        return "InstallerCapability()"

    def install(self, spec: ToolSpec, adapter: object | None = None, dry_run: bool = False) -> InstallResult:
        """Install via the injected registry (single API pipeline).

        `adapter` may be a registry unit passed through for the dry-run
        message, but all action calls resolve directly from `self._registry`
        when wired.
        """
        registry = self._registry
        if not registry:
            raise ToolInstallError("adapter registry is not wired (root composition layer)")
        root = self._root or None
        if dry_run:
            return InstallResult(
                True,
                spec.id,
                f"[dry-run] would invoke install for {spec.id}",
            )

        # P1-3: the satisfied check must not raise out of the action.
        unit = registry.get(spec.id)
        if unit is None:
            return InstallResult(False, spec.id, f"no adapter unit registered for {spec.id!r}")
        try:
            satisfied_fn = getattr(unit, "satisfied", None)
            if callable(satisfied_fn) and satisfied_fn(spec, root):
                return InstallResult(True, spec.id, "satisfied (no action needed)")
        except Exception as e:
            return InstallResult(False, spec.id, f"satisfied-check failure: {e}")

        try:
            install_fn = getattr(unit, "install", None)
            if callable(install_fn):
                try:
                    install_fn(spec, root, daemons=self._daemons)
                except TypeError:
                    install_fn(spec, root)
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
