"""Config aggregate contract — the 7 bare methods exposed to the root CLI.

The config agent orchestrator and the ``aa config`` surface both implement
this ABC; the root CLI routes each token to the matching method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigKeys,
    ConfigSnapshot,
    ConfigTuple,
    EnvPairs,
    HelpText,
    McpServersMap,
)


class IConfigAggregate(ABC):
    """Aggregate surface the root CLI dispatches into (AES405)."""

    @abstractmethod
    def load(self, path: Path) -> ConfigTuple:
        """Read the config file; returns ``(data, format)``."""
        ...

    @abstractmethod
    def save(
        self,
        path: Path,
        data: ConfigData,
        fmt: ConfigFormat | None = None,
    ) -> bool:
        """Write *data* back preserving format; True on success."""
        ...

    @abstractmethod
    def merge_servers(
        self,
        path: Path,
        servers: McpServersMap,
    ) -> ConfigKeys:
        """Merge MCP server entries into the file; returns merged names."""
        ...

    @abstractmethod
    def set_env(self, path: Path, pairs: EnvPairs) -> None:
        """Upsert KEY=VALUE pairs into an env-style file (create if missing)."""
        ...

    @abstractmethod
    def remove_entries(
        self,
        path: Path,
        keys: ConfigKeys,
        dry_run: bool = False,
    ) -> ConfigKeys:
        """Drop named server or env entries; dry-run reports without writing."""
        ...

    @abstractmethod
    def inspect(self, path: Path) -> ConfigSnapshot:
        """Read-only snapshot: format, data, and server names."""
        ...

    @abstractmethod
    def help(self) -> HelpText:
        """Print (or return) usage for every config op."""
        ...


__all__ = [
    "ConfigData",
    "ConfigFormat",
    "ConfigKeys",
    "ConfigSnapshot",
    "ConfigTuple",
    "EnvPairs",
    "HelpText",
    "IConfigAggregate",
    "McpServersMap",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigData": ConfigData,
    "ConfigFormat": ConfigFormat,
    "ConfigKeys": ConfigKeys,
    "ConfigSnapshot": ConfigSnapshot,
    "ConfigTuple": ConfigTuple,
    "EnvPairs": EnvPairs,
    "HelpText": HelpText,
    "IConfigAggregate": IConfigAggregate,
    "McpServersMap": McpServersMap,
}
