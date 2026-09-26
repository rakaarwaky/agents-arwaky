"""Config agent orchestrator — routes every config op to the owning capability.

Implements ``IConfigAggregate``: a single ``execute`` entry point that the
surface, root CLI and MCP call with a typed ``ConfigRequest``. Dispatch lives
here, against the two seam capabilities (reader + modifier), each of which
implements its own protocol. Both are injected by the composition root — the
agent layer depends on the contracts, never on the concrete capabilities.
"""
from __future__ import annotations

from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.contract_config_protocol import (
    IConfigModifierProtocol,
    IConfigReaderProtocol,
)
from modules.shared.src.taxonomy_common_vo import (
    ConfigOp,
    ConfigRequest,
    ConfigResult,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigOrchestrator(IConfigAggregate):
    """Config agent: single-execute aggregate over reader + modifier seams."""

    def __init__(
        self,
        writer: IConfigReaderProtocol,
        modifier: IConfigModifierProtocol,
    ) -> None:
        self._writer = writer
        self._modifier = modifier

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
