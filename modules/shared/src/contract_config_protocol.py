"""Config engine contracts (one feature per capability ABC).

Config writer/modifier capabilities implement every feature ABC in their role;
injectors may type a full engine as the composites ``IConfigWriter`` /
``IConfigModifier``.
"""
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


class IConfigLoadProtocol(ABC):
    """FR: load a harness config file into a typed tuple."""

    @abstractmethod
    def load_file(self, path: Path) -> ConfigTuple:
        """Load the file into a dict; returns ``(data, format)``."""
        ...


class IConfigSaveProtocol(ABC):
    """FR: write a harness config file preserving format."""

    @abstractmethod
    def save_file(self, path: Path, data: ConfigData, fmt: ConfigFormat | None = None) -> bool:
        """Write the dict back preserving format; True on success."""
        ...


class IConfigDetectFormatProtocol(ABC):
    """FR: detect a harness config file's format."""

    @abstractmethod
    def detect_format(self, path: Path) -> ConfigFormat:
        """Detect the config file format (yaml/jsonc/json/toml)."""
        ...


class IConfigRemoveMcpProtocol(ABC):
    """FR: remove named MCP servers from a config file."""

    @abstractmethod
    def remove_mcp_servers(self, path: Path, servers: list[str], dry_run: bool = False) -> list[str]:
        """Remove named MCP servers (with backup); returns removed names."""
        ...


class IConfigRemoveEnvKeysProtocol(ABC):
    """FR: remove KEY lines from an env-style file."""

    @abstractmethod
    def remove_env_keys(self, path: Path, keys: list[str], dry_run: bool = False) -> list[str]:
        """Remove ``KEY=...`` lines from an env-style file; returns removed keys."""
        ...


class IConfigListMcpProtocol(ABC):
    """FR: list MCP server names present in a config file."""

    @abstractmethod
    def list_mcp_servers(self, path: Path) -> list[str]:
        """List the MCP server names present in the file."""
        ...


class IConfigMergeMcpProtocol(ABC):
    """FR: merge MCP servers into a config file's MCP map."""

    @abstractmethod
    def merge_mcp_servers(self, path: Path, servers: McpServersMap, force: bool = False) -> list[str]:
        """Merge MCP servers into the file's MCP map (fail-closed + backup)."""
        ...


class IConfigSetEnvKeysProtocol(ABC):
    """FR: set KEY=VALUE lines in a .env file."""

    @abstractmethod
    def set_env_keys(self, path: Path, pairs: EnvPairs) -> None:
        """Set ``KEY=VALUE`` lines in a .env file (create if missing)."""
        ...


class IConfigWriter(
    IConfigLoadProtocol,
    IConfigSaveProtocol,
    IConfigDetectFormatProtocol,
):
    """Composite DI type: full config-writer surface (no methods of its own)."""


class IConfigModifier(
    IConfigRemoveMcpProtocol,
    IConfigRemoveEnvKeysProtocol,
    IConfigListMcpProtocol,
    IConfigMergeMcpProtocol,
    IConfigSetEnvKeysProtocol,
):
    """Composite DI type: full config-modifier surface (no methods of its own)."""


__all__ = [
    "ConfigData",
    "ConfigFormat",
    "ConfigTuple",
    "EnvPairs",
    "IConfigDetectFormatProtocol",
    "IConfigListMcpProtocol",
    "IConfigLoadProtocol",
    "IConfigMergeMcpProtocol",
    "IConfigModifier",
    "IConfigRemoveEnvKeysProtocol",
    "IConfigRemoveMcpProtocol",
    "IConfigSaveProtocol",
    "IConfigSetEnvKeysProtocol",
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
    "IConfigDetectFormatProtocol": IConfigDetectFormatProtocol,
    "IConfigListMcpProtocol": IConfigListMcpProtocol,
    "IConfigLoadProtocol": IConfigLoadProtocol,
    "IConfigMergeMcpProtocol": IConfigMergeMcpProtocol,
    "IConfigModifier": IConfigModifier,
    "IConfigRemoveEnvKeysProtocol": IConfigRemoveEnvKeysProtocol,
    "IConfigRemoveMcpProtocol": IConfigRemoveMcpProtocol,
    "IConfigSaveProtocol": IConfigSaveProtocol,
    "IConfigSetEnvKeysProtocol": IConfigSetEnvKeysProtocol,
    "IConfigWriter": IConfigWriter,
    "McpServersMap": McpServersMap,
    "Timestamp": Timestamp,
}
