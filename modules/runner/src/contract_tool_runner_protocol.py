"""Tool-runner capability protocol contract (AES102 `_protocol`).

Implemented by every per-tool runner capability, consumed by the runner
agent orchestrator.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_tool_vo import ToolSpec


class IToolExecutor(ABC):
    """Capability contract for locating and executing installed tools."""

    @abstractmethod
    def find_executable(self, spec: ToolSpec) -> Path | None:
        """Return the path of the runnable binary, or None when not runnable."""
        return None

    @abstractmethod
    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Execute the tool binary with *args*; return a process exit code."""
        return None
