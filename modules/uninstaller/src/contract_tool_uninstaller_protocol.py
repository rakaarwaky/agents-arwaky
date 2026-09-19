"""Tool-uninstaller capability contracts (AES102 ``_protocol``).

Implemented by the two business-action capabilities (remover, verifier);
consumed by the agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult


class IToolRemover(ABC):
    """FR-001: delete a tool's owned state; never raises out of ``remove``."""

    @abstractmethod
    def remove(self, spec: ToolSpec, owned_paths: list[Path], dry_run: bool = False) -> UninstallResult:
        """Stop the daemon (if applicable) then remove launchers + XDG data/cache/bin.

        Scoped strictly to the owned set. Every failure path returns
        ``UninstallResult(success=False, message)``.
        """
        return None


class IToolVerifier(ABC):
    """FR-002: confirm the owned set is gone; report residuals by name."""

    @abstractmethod
    def verify(self, spec: ToolSpec, uninstall_result: UninstallResult) -> UninstallResult:
        """Runs after FR-001 (success or partial); a failed removal still gets
        verified so residuals are surfaced, not hidden. Nothing raises into the
        CLI surface — verification failures append to the ``UninstallResult``."""
        return None


class IToolUninstaller(ABC):
    """Single uninstall verb over the two capabilities (orchestrator surface)."""

    @abstractmethod
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Remove then verify; returns the (possibly folded) UninstallResult."""
        return None


__all__ = ["IToolRemover", "IToolUninstaller", "IToolVerifier"]
