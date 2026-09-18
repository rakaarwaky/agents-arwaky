"""Tool-domain protocol contracts (capability ABCs)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec


class IToolExecutor(ABC):
    """Capability contract for locating and executing installed tools."""

    @abstractmethod
    def find_executable(self, spec: ToolSpec) -> Path | None:
        """Return the path of the runnable binary, or None when not runnable."""
        raise NotImplementedError

    @abstractmethod
    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Execute the tool binary with *args*; return a process exit code."""
        raise NotImplementedError
