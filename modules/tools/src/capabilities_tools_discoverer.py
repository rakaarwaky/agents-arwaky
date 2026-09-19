"""FR-007 capability — discover a tool's executable path (runner feature).

Universal discovery order, identical for every tool:
XDG bin launcher -> host PATH -> per-tool install dir.

The capability is read-only: it never mutates install state and never
invokes a package manager. Symlinked launchers are resolved to their
target. No candidate found -> None (the caller decides the message).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec


#: Sentinel launch marker: internal tools whose launcher is a runner script.
_INTERNAL_RUNNERS = ("cargo", "uv", "python")


class DiscovererCapability:
    """Resolve the concrete launch path for a ToolSpec (deterministic order).

    # Block 1: Candidate generation
    # Block 2: Discovery (first valid candidate wins)
    """

    # -- Block 1: Candidate generation -----------------------------------------
    @staticmethod
    def _names(spec: ToolSpec) -> list[str]:
        """Executable names to probe: mcp_binary (MCP tools) first, then binary."""
        names: list[str] = []
        if spec.is_mcp and spec.mcp_binary:
            names.append(spec.mcp_binary)
        names.append(spec.binary)
        return names

    def _candidates(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Ordered candidate paths: XDG bin launcher -> PATH -> install dir."""
        candidates: list[Path] = []
        for name in self._names(spec):
            # 1. XDG bin launcher (installer-registered, found even before the binary).
            launcher = bin_home() / name
            if launcher.exists() and os.access(launcher, os.X_OK):
                candidates.append(launcher.resolve())

            # 2. Host PATH.
            found = shutil.which(name)
            if found:
                p = Path(found)
                if p not in candidates:
                    candidates.append(p)

        # 3. Per-tool install dir (internal tools: runner candidates).
        if spec.category == "internal" and spec.path:
            tool_dir = root / spec.path
            runner = spec.runner or TOOL_RUNNERS.get(spec.id, "")
            if runner == "cargo" and shutil.which("cargo") and (tool_dir / "Cargo.toml").exists():
                candidates.append(tool_dir / "Cargo.toml")
            if runner in ("uv", "python"):
                if tool_dir.exists():
                    if shutil.which("uv"):
                        candidates.append(tool_dir)
                    elif shutil.which("python3"):
                        candidates.append(Path(spec.id))
        return candidates

    # -- Block 2: Discovery ------------------------------------------------------
    def discover(self, spec: ToolSpec, root: Path | None = None) -> Path | None:
        """First valid candidate in discovery order, resolved; None when absent."""
        base = root or repo_root
        for candidate in self._candidates(spec, base):
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate
            if candidate.suffix == ".toml" or candidate.name in (spec.id,):
                # Runner candidates are not directly executable; accept them as-is.
                return candidate
        return None


__all__ = ["DiscovererCapability"]
