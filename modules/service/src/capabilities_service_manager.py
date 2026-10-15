#!/usr/bin/env python3
"""Unified service manager (Python) — pengganti service-manager.sh.

AES port of tools/service/service_manager.py: action bodies kept; the original
subprocess exec of the two daemon scripts is replaced by direct calls into
modules/daemon. The daemon managers are resolved via the daemon feature
aggregate (composition root) and injected.

``ServiceControl`` implements ``IServiceControlProtocol`` (start/stop/restart).
The CLI-verb dispatch helpers live in ``utility_service_daemon`` (shared
kernel) so no capability imports a sibling capability.
"""
from __future__ import annotations

import sys

from modules.shared.src.daemon.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.service.contract_service_protocol import IServiceControlProtocol
from modules.shared.src.service.taxonomy_service_vo import (
    TARGET_ALL,
    ExitCode,
    ServiceTarget,
)
from modules.shared.src.utility_service_daemon import (
    cmd_help,
    cmd_logs,
    cmd_restart,
    cmd_start,
    cmd_status,
    cmd_stop,
    set_daemon_aggregate,
)

__all__ = [
    "ServiceControl",
    "cmd_help",
]

# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceControl(IServiceControlProtocol):
    """Service mutation capability: start / stop / restart."""

    def __init__(self, daemons: IDaemonAggregate | None = None) -> None:
        if daemons is not None:
            set_daemon_aggregate(daemons)
        self._daemons = daemons

    # ─── Block 2: Protocol Method Implementation ──────────────
    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Start the named service(s). Return the exit code."""
        return ExitCode(cmd_start(str(target)))

    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Stop the named service(s). Return the exit code."""
        return ExitCode(cmd_stop(str(target)))

    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Restart the named service(s). Return the exit code."""
        return ExitCode(cmd_restart(str(target)))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "ServiceControl()"


# ─── Block 3: Dunder Methods, Factories & Helpers ─────────
def main(argv: list[str]) -> int:
    """Entry point for standalone service command execution."""
    if not argv or argv[0] in ("help", "-h", "--help"):
        return cmd_help()
    action = argv[0]
    target = argv[1] if len(argv) > 1 else "all"
    if action == "status":
        return cmd_status()
    if action == "start":
        return cmd_start(target)
    if action == "stop":
        return cmd_stop(target)
    if action == "restart":
        return cmd_restart(target)
    if action == "logs":
        return cmd_logs(target)
    print(f"Unknown service action: {action}", file=sys.stderr)
    return cmd_help()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
