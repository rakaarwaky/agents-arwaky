"""Config-domain capability protocol — one ABC per seam.

Pure capability ABCs: every config operation is a distinct typed method so the
agent can call the right one without a dispatch bag. Two seams exist because
reading and mutating a config file touch disjoint code paths in the shared
kernel; splitting them keeps each capability self-contained.

- ``IConfigReaderProtocol`` — read / write / inspect / help.
- ``IConfigModifierProtocol`` — merge / set-env / remove.
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


class IConfigReaderProtocol(ABC):
    """Reader seam: load, save, inspect, help."""

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
    def inspect(self, path: Path) -> ConfigSnapshot:
        """Read-only snapshot: format, data, and server names."""
        ...

    @abstractmethod
    def help(self) -> HelpText:
        """Usage text for every config op."""
        ...


class IConfigModifierProtocol(ABC):
    """Modifier seam: merge servers, set env, remove entries."""

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
    "IConfigReaderProtocol",
    "IConfigModifierProtocol",
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
    "IConfigReaderProtocol": IConfigReaderProtocol,
    "IConfigModifierProtocol": IConfigModifierProtocol,
    "McpServersMap": McpServersMap,
}
