"""Shared daemon-domain: taxonomy + contracts for daemon capabilities."""
from modules.shared.src.daemon.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.daemon.contract_daemon_protocol import IDaemonManager
from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonConfig, DaemonStatus

__all__ = [
    "DaemonConfig",
    "DaemonStatus",
    "IDaemonAggregate",
    "IDaemonManager",
]
