"""Tool-domain uninstaller aggregate contract (AES102 ``_aggregate``).

Stable for the runner's ``ToolOrchestrator``: its ``uninstaller`` capability is
type-annotated against this module; the orchestrator implements it and the
aggregate delegates ``uninstall(spec)`` into the uninstaller agent.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult

__all__ = ["IUninstallerAggregate", "UninstallResult"]


class IUninstallerAggregate(ABC):
    """Uninstaller-feature aggregate surface consumed by the tool orchestrator."""

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall one tool spec (remove + verify)."""
        return None
