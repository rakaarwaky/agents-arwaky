"""Config-domain capability protocol — one named method per operation.

Pure capability ABC: every config operation is a distinct typed method so the
agent can call the right one without a dispatch bag. The root CLI and surface
layer talk to the aggregate, not this protocol directly.
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


class IConfigProtocol(ABC):
    """Capability contract for config: one method per operation."""

    @abstractmethod
    def load(self, path: Path) -> ConfigTuple:
        """Read *path*; returns ``(data, format)``."""
        ...

    @abstractmethod
    def save(
        self,
        path: Path,
        data: ConfigData,
        fmt: ConfigFormat | None = None,
    ) -> bool:
        """Write *data* to *path* in *fmt* (or detected); True on success."""
        ...

    @abstractmethod
    def merge_servers(
        self,
        path: Path,
        servers: McpServersMap,
    ) -> ConfigKeys:
        """Merge *servers* into the file; returns merged names."""
        ...

    @abstractmethod
    def set_env(self, path: Path, pairs: EnvPairs) -> None:
        """Upsert KEY=VALUE pairs into an env-style file."""
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
        """Usage text for every config op."""
        ...


__all__ = [
    "ConfigData",
    "ConfigFormat",
    "ConfigKeys",
    "ConfigSnapshot",
    "ConfigTuple",
    "EnvPairs",
    "HelpText",
    "IConfigProtocol",
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
    "IConfigProtocol": IConfigProtocol,
    "McpServersMap": McpServersMap,
}
