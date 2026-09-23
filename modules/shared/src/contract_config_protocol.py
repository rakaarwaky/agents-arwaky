"""Config capability contract — a single ``execute`` method.

Every config capability (writer, modifier) implements this one ABC; the
config agent calls ``execute(op, path, payload)`` for all six ops. One
method replaces the former leaf/composite protocol lattice.
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


class IConfigProtocol(ABC):
    """Single-method contract for every config capability."""

    @abstractmethod
    def execute(
        self,
        op: str,
        path: Path,
        payload: dict | None = None,
    ) -> ConfigTuple | bool | list[str] | dict | ConfigFormat | None:
        """Dispatch *op* against *path* with *payload*; return the op's result."""
        ...


__all__ = [
    "ConfigData",
    "ConfigFormat",
    "ConfigTuple",
    "EnvPairs",
    "IConfigProtocol",
    "McpServersMap",
    "Timestamp",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigData": ConfigData,
    "ConfigFormat": ConfigFormat,
    "ConfigTuple": ConfigTuple,
    "EnvPairs": EnvPairs,
    "IConfigProtocol": IConfigProtocol,
    "McpServersMap": McpServersMap,
    "Timestamp": Timestamp,
}
