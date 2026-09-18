"""Venv installer contract for the AES tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IVenvInstaller(ABC):
    """Venv provisioning operations for Python-based tools."""

    @abstractmethod
    def ensure_venv(self, tool_name: str, force: bool = False) -> Path:
        """Create/refresh the tool's venv; returns the python binary path."""

    @abstractmethod
    def install_package(self, python_bin: Path, src_dir: Path, tool_name: str) -> None:
        """pip install -e the tool source into its venv."""

    @abstractmethod
    def setup_xdg_directories(self, tool_name: str) -> None:
        """Create the per-tool XDG data/config/state/cache directories."""

    @abstractmethod
    def setup_bin_links(self, python_bin: Path, launchers: list[tuple[str, str]]) -> None:
        """Symlink venv entry points into $XDG_BIN_HOME."""
