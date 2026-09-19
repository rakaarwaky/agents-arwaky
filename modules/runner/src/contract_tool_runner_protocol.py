"""Tool-runner capability protocol contracts (AES102 `_protocol`).

Implemented by the runner capability modules (FR-001 discoverer, FR-002
executor), consumed by the runner agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec


class IToolDiscoverer(ABC):
    """FR-001: resolve the concrete launch path for a ToolSpec.

    Universal discovery order (identical for every tool): XDG bin launcher
    -> host PATH -> per-tool install dir. Read-only: never mutates install
    state, never invokes a package manager. No candidate found -> None.
    """

    @abstractmethod
    def discover(self, spec: ToolSpec, root: Path | None = None) -> Path | None:
        """Return the executable path to launch, resolved; None when absent."""
        return None


class IToolExecutor(ABC):
    """FR-002: launch a discovered executable and return its exit code.

    Every failure path returns an int; nothing raises out of `execute`
    into the CLI surface. A distinct non-zero sentinel is reserved for
    "executable vanished between discovery and launch".
    """

    @abstractmethod
    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """Run the resolved *executable* with *args*; return the child's exit code."""
        return None


__all__ = ["IToolDiscoverer", "IToolExecutor"]
