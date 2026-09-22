"""Config engine contracts (ABCs) for the AES tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigTuple,
    EnvPairs,
    McpServersMap,
    Timestamp,
)


class IConfigWriter(ABC):
    """Reads/writes agent harness config files (json/jsonc/yaml/toml)."""

    @abstractmethod
    def load_file(self, path: Path) -> ConfigTuple:
        """Load the file into a dict; returns ``(data, format)``."""

    @abstractmethod
    def save_file(self, path: Path, data: ConfigData, fmt: ConfigFormat | None = None) -> bool:
        """Write the dict back preserving format; True on success."""

    @abstractmethod
    def detect_format(self, path: Path) -> ConfigFormat:
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
    def merge_mcp_servers(self, path: Path, servers: McpServersMap, force: bool = False) -> list[str]:
        """Merge MCP servers into the file's MCP map (fail-closed + backup)."""

    @abstractmethod
    def set_env_keys(self, path: Path, pairs: EnvPairs) -> None:
        """Set ``KEY=VALUE`` lines in a .env file (create if missing)."""

__all__ = [
    "ConfigData",
    "ConfigFormat",
    "ConfigTuple",
    "EnvPairs",
    "IConfigModifier",
    "IConfigWriter",
    "McpServersMap",
    "Timestamp",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigData": ConfigData,
    "ConfigFormat": ConfigFormat,
    "ConfigTuple": ConfigTuple,
    "EnvPairs": EnvPairs,
    "IConfigModifier": IConfigModifier,
    "IConfigWriter": IConfigWriter,
    "McpServersMap": McpServersMap,
    "Timestamp": Timestamp,
}
