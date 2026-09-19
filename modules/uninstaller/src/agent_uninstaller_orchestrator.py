"""Uninstaller orchestrator — the single agent over the two business-action
capabilities (remover, verifier).

# Block 1: Constructor
# Block 2: uninstall dispatch (remove → verify)
# Block 3: Target resolution & owned-path computation (agent-layer glue)
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from modules.shared.src.taxonomy_core_error import ToolUninstallError
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    cache_home,
    config_home,
    data_home,
)
from modules.shared.src.utility_manifest_reader import find_tool
from modules.shared.src.utility_paths import repo_root

from modules.uninstaller.src.capabilities_uninstaller_remover import UninstallerRemover
from modules.uninstaller.src.capabilities_uninstaller_verifier import UninstallerVerifier
from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller

__all__ = ["UninstallerOrchestrator"]


class _DaemonStopper(Protocol):
    """Structural type: anything with a service_uninstall(name) -> int method."""

    def service_uninstall(self, name: str) -> int: ...


# Tool id -> the launcher / alias names the installer registers under XDG bin.
# Kept here (agent layer) because the owned-path set is an agent concern;
# the remover uses its own copy for its specific removal mechanics.
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

# Tool id -> XDG config dir is removed with the tool (installer-owned).
# anytype-daemon keeps its config (daemon owns it across updates).
_CLEAN_CONFIG: dict[str, bool] = {
    "anytype-daemon": False,
}

# Tool id -> extra owned paths outside the generic XDG layout.
_EXTRA_OWNED: dict[str, list[Path]] = {
    "9router": [
        data_home() / "9router" / "internal-bin" / "9router",
        config_home() / "agents-arwaky" / "ninerouter.env",
    ],
    "anytype-daemon": [
        data_home() / "anytype-daemon" / "internal-bin" / "anytype-daemon",
    ],
}


def _spec_from_tool(tool) -> ToolSpec:
    from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
    return ToolSpec(
        id=tool.id,
        category=tool.category,
        binary=tool.binary,
        is_mcp=tool.is_mcp,
        description=tool.description,
        path=tool.path,
        alias=tool.alias,
        mcp_binary=getattr(tool, "mcp_binary", None),
        runner=TOOL_RUNNERS.get(tool.id, ""),
    )


class UninstallerOrchestrator(IToolUninstaller):
    """Single agent: resolve target set → compute owned paths → remove → verify.

    Adding a tool is a manifest entry, never a new module or orchestrator edit.
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        daemons: _DaemonStopper | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._remover = UninstallerRemover(daemons=daemons)
        self._verifier = UninstallerVerifier()

    # -- Block 2: uninstall dispatch ---------------------------------------------
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Remove then verify; returns the (possibly folded) UninstallResult."""
        owned = self._owned_paths(spec)
        result = self._remover.remove(spec, owned, dry_run=False)
        return self._verifier.verify(spec, result, owned_paths=owned)

    # -- Block 3: Target resolution & owned-path computation -------------------
    def resolve_targets(self, query: str | None = None) -> list[ToolSpec]:
        """Omitted/empty query = all manifest tools; unknown id raises ToolUninstallError."""
        from modules.shared.src.utility_manifest_reader import load_tools
        if query is None:
            return [_spec_from_tool(t) for t in load_tools()]
        tool = find_tool(query)
        if tool is None:
            raise ToolUninstallError(f"unknown tool id: {query!r}")
        return [_spec_from_tool(tool)]

    def _owned_paths(self, spec: ToolSpec) -> list[Path]:
        """Compute the full owned-path set for a tool from manifest + XDG layout."""
        paths: list[Path] = []

        # Launchers / aliases under XDG bin.
        for name in _LAUNCHERS.get(spec.id, []):
            paths.append(bin_home() / name)

        # XDG data + cache subtrees.
        paths.append(data_home() / spec.id)
        paths.append(cache_home() / spec.id)

        # XDG config subtree only when the installer owns it.
        if _CLEAN_CONFIG.get(spec.id, True):
            paths.append(config_home() / spec.id)

        # Daemon unit file (only 9router and anytype-daemon have one).
        from modules.uninstaller.src.capabilities_uninstaller_remover import _DAEMON_UNIT_TOOLS
        unit = _DAEMON_UNIT_TOOLS.get(spec.id)
        if unit:
            paths.append(config_home() / "systemd" / "user" / unit)

        # Tool-specific extras (internal-bin, secrets).
        paths.extend(_EXTRA_OWNED.get(spec.id, []))

        # De-duplicate, preserving order.
        seen: set[Path] = set()
        unique: list[Path] = []
        for p in paths:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique
