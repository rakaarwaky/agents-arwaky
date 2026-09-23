"""Config agent orchestrator — routes the six config ops to two capabilities.

Implements ``IConfigAggregate`` (the 7 bare methods) by composing two
injected ``IConfigProtocol`` capabilities (writer + modifier) through their
single ``execute`` dispatcher.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.contract_config_protocol import IConfigProtocol
from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigSnapshot,
    ConfigTuple,
    EnvPairs,
    HelpText,
    McpServersMap,
)

#: Usage text returned by ``help`` and printed by the surface on unknown ops.
_USAGE = (
    "Usage: aa config <op> ...\n"
    "  load PATH                    Read config; print data + detected format\n"
    "  save PATH DATA [--fmt FMT]   Write DATA (JSON) back in detected/explicit format\n"
    "  merge_servers PATH SERVERS   Merge SERVERS (JSON map) into the MCP config\n"
    "  set_env PATH PAIRS           Upsert PAIRS (JSON map) into the env file\n"
    "  remove_entries PATH KEYS...  Drop named server/env entries (--dry-run supported)\n"
    "  inspect PATH                 Print a read-only snapshot (format, data, servers)\n"
    "  help                         Print this usage\n"
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigOrchestrator(IConfigAggregate):
    """Config agent: aggregate facade over writer + modifier capabilities."""

    def __init__(self, writer: IConfigProtocol, modifier: IConfigProtocol) -> None:
        self._writer = writer
        self._modifier = modifier

    # ─── Block 2: Aggregate Method Implementation ──────────
    def load(self, path: Path) -> ConfigTuple:
        """Load via the writer capability; returns ``(data, format)``."""
        return self._writer.execute("load", path)

    def save(
        self,
        path: Path,
        data: ConfigData,
        fmt: ConfigFormat | None = None,
    ) -> bool:
        """Save via the writer capability; True on success."""
        payload: dict = {"data": dict(data)}
        if fmt is not None:
            payload["fmt"] = fmt
        return self._writer.execute("save", path, payload)

    def inspect(self, path: Path) -> ConfigSnapshot:
        """Read-only snapshot: format, data, and server names."""
        data, fmt = self._writer.execute("load", path)
        servers = self._modifier.execute("list_servers", path)
        return ConfigSnapshot({
            "path": str(path),
            "format": str(fmt),
            "data": dict(data),
            "servers": list(servers or []),
        })

    def merge_servers(
        self,
        path: Path,
        servers: McpServersMap,
    ) -> list[str]:
        """Merge MCP servers via the modifier capability; returns merged names."""
        return self._modifier.execute("merge_servers", path, {"servers": dict(servers)})

    def set_env(self, path: Path, pairs: EnvPairs) -> None:
        """Upsert env pairs via the modifier capability."""
        self._modifier.execute("set_env", path, {"pairs": dict(pairs)})

    def remove_entries(
        self,
        path: Path,
        keys: list[str],
        dry_run: bool = False,
    ) -> list[str]:
        """Drop named entries (env or server) via the modifier capability."""
        return self._modifier.execute(
            "remove_entries",
            path,
            {"keys": list(keys), "dry_run": dry_run},
        )

    def help(self) -> HelpText:
        return HelpText(_USAGE)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "ConfigOrchestrator()"
