"""Tool-domain installer aggregate contract (AES102 `_aggregate`).

Stable for the runner's `ToolOrchestrator`: its `installer` capability is
type-annotated against this module; the orchestrator implements it and the
aggregate delegates `install(spec)` into the installer agent.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec

__all__ = ["IInstallerAggregate", "InstallResult"]


class IInstallerAggregate(ABC):
    """Installer-feature aggregate surface consumed by the tool orchestrator."""

    @abstractmethod
    def install(self, spec: ToolSpec) -> InstallResult:
        """Install one tool spec (provision + launcher registration)."""
        return None
