"""Tool-updater contracts (AES102 `_protocol`).

Defines the two business-action capabilities and the per-tool leaf adapter.
Capabilities implement FR-001 (bumper) and FR-002 (recorder); the adapter is
owned by the orchestrator and knows one tool's update sequence.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult


class IToolUpdaterAdapter(ABC):
    """Leaf adapter: knows exactly one manifest tool's update/build sequence.

    Adapters import only `modules/shared/...` and stdlib (no capability/agent/
    root/contract imports, no utility-to-utility imports).
    """

    @abstractmethod
    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Run this tool's package-manager/build sequence; return artifact paths.

        Raises ArwakyError (shared taxonomy) with the captured diagnostic on
        failure — the bumper folds it into the UpdateResult.
        """
        return []

    @abstractmethod
    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        """Return (satisfied, description) after comparing installed state to the
        manifest pin. The adapter decides what "installed" means for its tool."""
        return (False, "")


class IToolBumper(ABC):
    """FR-001: bring a tool to its manifest pin; never raises out."""

    @abstractmethod
    def bump(self, spec: ToolSpec, adapter: IToolUpdaterAdapter, dry_run: bool = False) -> UpdateResult:
        """Pin comparison → adapter dispatch → capture stderr into the result.

        Every failure path returns UpdateResult(success=False, message).
        """
        return None


class IToolRecorder(ABC):
    """FR-002: record the version transition after a successful bump."""

    @abstractmethod
    def record(self, spec: ToolSpec, update_result: UpdateResult) -> UpdateResult:
        """Log the transition and adjust launchers when the binary path changed.

        Idempotent: recording an already-recorded transition is a no-op.
        Runs only after FR-001 success; a failed bump yields no record.
        """
        return None


class IToolUpdater(ABC):
    """Single update verb over the two capabilities (orchestrator surface)."""

    @abstractmethod
    def update(self, spec: ToolSpec) -> UpdateResult:
        """Bump then record; returns the (possibly folded) UpdateResult."""
        return None


__all__ = [
    "IToolBumper",
    "IToolRecorder",
    "IToolUpdater",
    "IToolUpdaterAdapter",
]
