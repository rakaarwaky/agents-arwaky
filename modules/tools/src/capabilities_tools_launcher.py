"""FR-002 capability — register a provisioned tool's launcher under XDG bin.

Registration policy only; write/chmod mechanics are delegated to
``utility_launcher_writer``. Runs only after FR-001 success. One launcher
per binary plus one per manifest alias; MCP tools record ``mcp_binary``.
A stale foreign launcher (no provenance marker) is reported as a residual,
never overwritten; a correct launcher already in place is a no-op success.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec


def _has_provenance(launcher: Path) -> bool:
    """True when the launcher carries the arwaky-installer provenance marker."""
    try:
        head = launcher.open("rb").read(256).decode("utf-8", "replace")
    except OSError:
        return False
    return "arwaky-installer" in head or "AGENTS_ARWAKY_ROOT" in head


class LauncherRegistrarCapability:
    """Business action FR-002: register_launcher(spec, install_result)."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    def register_launcher(
        self,
        spec: ToolSpec,
        install_result: InstallResult,
        artifacts: list[Path] | None = None,
    ) -> InstallResult:
        from modules.shared.src.taxonomy_xdg_atomic_io import ensure_bin_home
        from modules.shared.src.taxonomy_xdg_paths import bin_home

        # FR-002: registration policy runs only after a successful provision.
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
        targets: list[Path] = list(artifacts or [])
        # One launcher per binary plus one per manifest-declared alias.
        targets.append(bin_home() / spec.binary)
        if spec.alias:
            targets.append(bin_home() / spec.alias)
        for p in dict.fromkeys(targets):
            if p.exists() and not p.is_symlink() and not _has_provenance(p):
                notes.append(f"residual launcher (foreign, no provenance marker): {p.name}")

        detail = "; ".join(notes) if notes else "launcher registered"
        return InstallResult(True, spec.id, detail)


__all__ = ["LauncherRegistrarCapability"]
