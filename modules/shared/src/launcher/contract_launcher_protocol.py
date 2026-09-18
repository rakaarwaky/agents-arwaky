"""Launcher writer contract for the AES tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ILauncherWriter(ABC):
    """Writes host launcher scripts into $XDG_BIN_HOME."""

    @abstractmethod
    def write_uv_launchers(
        self,
        src_rel: str,
        launchers: list[tuple[str, str]],
        root: Path | None = None,
        uv_args: list[str] | None = None,
    ) -> list[Path]:
        """Write uv-run launchers for a Python tool. Returns created paths."""

    @abstractmethod
    def write_generic_launcher(
        self, tool_name: str, content: str, aliases: list[str] | None = None
    ) -> Path:
        """Write a generic launcher with aliases. Returns the launcher path."""
