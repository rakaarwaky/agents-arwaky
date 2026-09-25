"""Doctor agent orchestrator — routes diagnose/readiness/report."""
from __future__ import annotations

from collections.abc import Mapping

from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.taxonomy_common_vo import ExitCode, Timestamp


# ─── Block 1: Class Definition & Constructor ──────────────
class DoctorOrchestrator(IDoctorAggregate):
    """Coordinate the two diagnostic runners (zero I/O; surface renders)."""

    def __init__(self, env_runner: IDoctorProtocol, tools_runner: IDoctorProtocol) -> None:
        """Wire the two diagnostic runners for orchestrator dispatch."""
        self._env = env_runner
        self._tools = tools_runner

    # ─── Block 2: Aggregate Method Implementation ──────────
    def diagnose(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Run both environment and tool diagnostics; return OR'd exit code."""
        rc = int(self._env.execute(flags))
        rc |= int(self._tools.execute(flags))
        return ExitCode(rc)

    def readiness(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Run tools-only diagnostics and return the exit code."""
        return self._tools.execute(flags)

    def report(
        self,
        report: object,
        flags: Mapping[str, bool | str] | None = None,
    ) -> ExitCode:
        """Rendering lives on the surface (AES agent: zero I/O)."""
        return ExitCode(0)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "DoctorOrchestrator()"


__all__ = ["ExitCode", "Timestamp"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "Timestamp": Timestamp}
