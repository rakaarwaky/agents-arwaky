"""Config engine contracts (ABCs) for the AES tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IConfigWriter(ABC):
    """Reads/writes agent harness config files (json/jsonc/yaml/toml)."""

    @abstractmethod
    def load_file(self, path: Path) -> tuple[dict, str]:
        """Load the file into a dict; returns ``(data, format)``."""

    @abstractmethod
    def save_file(self, path: Path, data: dict, fmt: str | None = None) -> bool:
        """Write the dict back preserving format; True on success."""

    @abstractmethod
    def detect_format(self, path: Path) -> str:
        """Detect the config file format (yaml/jsonc/json/toml)."""


class IConfigModifier(ABC):
    """Modifies harness configs: MCP server and env-key operations."""

    @abstractmethod
    def remove_mcp_servers(self, path: Path, servers: list[str], dry_run: bool = False) -> list[str]:
        """Remove named MCP servers (with backup); returns removed names."""

    @abstractmethod
    def remove_env_keys(self, path: Path, keys: list[str], dry_run: bool = False) -> list[str]:
        """Remove ``KEY=...`` lines from an env-style file; returns removed keys."""

    @abstractmethod
    def list_mcp_servers(self, path: Path) -> list[str]:
        """List the MCP server names present in the file."""

    @abstractmethod
    def merge_mcp_servers(self, path: Path, servers: dict, force: bool = False) -> list[str]:
        """Merge MCP servers into the file's MCP map (fail-closed + backup)."""

    @abstractmethod
    def set_env_keys(self, path: Path, pairs: dict) -> None:
        """Set ``KEY=VALUE`` lines in a .env file (create if missing)."""
