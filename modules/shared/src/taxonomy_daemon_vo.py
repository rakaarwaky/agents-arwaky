"""Daemon-domain value objects for the AES daemon feature."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Daemon name used as a routing key in the aggregate ("9router", "anytype").
DaemonName = NewType("DaemonName", str)

#: systemd user-unit filename the unit ops act on ("9router.service", ...).
DaemonUnit = NewType("DaemonUnit", str)

#: Operation token dispatched through ``IDaemonProtocol.execute``.
DaemonOp = NewType("DaemonOp", str)

#: Tuple of daemon names returned by ``IDaemonAggregate.list_known``.
DaemonNames = NewType("DaemonNames", tuple)


@dataclass(frozen=True)
class DaemonConfig:
    """Immutable configuration for a daemon manager."""

    name: str
    container_name: str
    image_name: str
    port: str
    data_dir: object
    unit_file: object
    env_candidates: tuple[object, ...] = ()


@dataclass(frozen=True)
class DaemonStatus:
    """Snapshot of a daemon's health, ready for CLI rendering."""

    container_state: str
    service_state: str
    api_ready: bool
    data_dir: str
    ok: bool
    details: tuple[str, ...] = field(default=())


__all__ = [
    "DaemonConfig",
    "DaemonName",
    "DaemonNames",
    "DaemonOp",
    "DaemonStatus",
    "DaemonUnit",
    "ExitCode",
]
