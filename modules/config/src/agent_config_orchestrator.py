"""Config agent orchestrator — routes every config op to the owning capability.

Implements ``IConfigAggregate``: a single ``execute`` entry point that the
surface, root CLI and MCP call with a typed ``ConfigRequest``. Dispatch lives
here, against the two rich ``IConfigProtocol`` capabilities (writer +
modifier), each of which implements the whole protocol.
"""
from __future__ import annotations

from modules.config.src.capabilities_config_modifier import ConfigModifier
from modules.config.src.capabilities_config_writer import ConfigWriter
from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.contract_config_protocol import IConfigProtocol
from modules.shared.src.taxonomy_common_vo import (
    ConfigOp,
    ConfigRequest,
    ConfigResult,
    HelpText,
)

#: Usage text returned by ``help`` and printed by the surface on unknown ops.
_USAGE = HelpText(
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
    """Config agent: single-execute aggregate over writer + modifier capabilities."""

    def __init__(
        self,
        writer: IConfigProtocol | None = None,
        modifier: IConfigProtocol | None = None,
    ) -> None:
        self._writer = writer if writer is not None else ConfigWriter(_USAGE)
        self._modifier = modifier if modifier is not None else ConfigModifier(_USAGE)

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: ConfigRequest) -> ConfigResult:
        """Route *request* to the owning capability; return the response."""
        op = ConfigOp(request.op)
        try:
            if op == "load":
                return ConfigResult(True, self._writer.load(request.path))
            if op == "save":
                ok = self._writer.save(request.path, request.data, request.fmt)
                return ConfigResult(ok, None, "" if ok else "save failed")
            if op == "merge_servers":
                merged = self._modifier.merge_servers(request.path, request.servers)
                return ConfigResult(True, merged)
            if op == "set_env":
                self._modifier.set_env(request.path, request.pairs)
                return ConfigResult(True)
            if op == "remove_entries":
                removed = self._modifier.remove_entries(
                    request.path,
                    request.keys,
                    request.dry_run,
                )
                return ConfigResult(True, removed)
            if op == "inspect":
                return ConfigResult(True, self._writer.inspect(request.path))
            if op == "help":
                return ConfigResult(True, self._writer.help())
        except Exception as exc:  # the surface reports the failure to the caller
            return ConfigResult(False, None, str(exc))
        return ConfigResult(False, None, f"Unknown config op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "ConfigOrchestrator()"


__all__ = [
    "ConfigOrchestrator",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigOrchestrator": ConfigOrchestrator,
}
