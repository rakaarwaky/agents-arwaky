"""Service inspect capability (AES capabilities layer).

``ServiceInspect`` implements ``IServiceInspectProtocol`` (read ops:
status / logs / help).
"""
from __future__ import annotations

from modules.shared.src.common.utility_service_daemon import (
    cmd_help,
    cmd_logs,
    cmd_status,
    set_daemon_aggregate,
)
from modules.shared.src.daemon.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.service.contract_service_protocol import IServiceInspectProtocol
from modules.shared.src.service.taxonomy_service_vo import (
    TARGET_OMNIROUTE,
    ExitCode,
    ServiceTarget,
)

__all__ = ["ServiceInspect"]

# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceInspect(IServiceInspectProtocol):
    """Service inspection capability: status / logs / help."""

    def __init__(self, daemons: IDaemonAggregate | None = None) -> None:
        if daemons is not None:
            set_daemon_aggregate(daemons)
        self._daemons = daemons

    # ─── Block 2: Protocol Method Implementation ──────────────
    def status(self) -> ExitCode:
        """Report the health of every registered service. Return the exit code."""
        return ExitCode(cmd_status())

    def logs(self, target: ServiceTarget = TARGET_OMNIROUTE) -> ExitCode:
        """Stream the named service's logs. Return the exit code."""
        return ExitCode(cmd_logs(str(target)))

    def help(self) -> ExitCode:
        """Print the service command usage. Return the exit code."""
        return ExitCode(cmd_help())

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "ServiceInspect()"
