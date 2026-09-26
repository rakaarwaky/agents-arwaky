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

#: Operation token carried by a DaemonRequest (lifecycle, unit ops, ...).
DaemonOp = NewType("DaemonOp", str)

#: Tuple of daemon names the orchestrator can route to.
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


@dataclass(frozen=True)
class DaemonRequest:
    """One daemon request the surface/root/CLI hands to the aggregate.

    Every consumer verb of the daemon feature is a value of ``op``; the
    aggregate dispatches to the matching protocol method internally, so the
    aggregate keeps a single ``execute`` entry point.
    """

    op: DaemonOp
    name: DaemonName | None = None
    unit: DaemonUnit | None = None


@dataclass(frozen=True)
class DaemonOutcome:
    """Result of one daemon request: outcome flag, exit code, status, message."""

    success: bool
    exit_code: int | None = None
    status: DaemonStatus | None = None
    message: str = ""


#: Daemon response envelope returned by ``IDaemonAggregate.execute``.
DaemonResponse = DaemonOutcome


__all__ = [
    "DaemonConfig",
    "DaemonName",
    "DaemonNames",
    "DaemonOp",
    "DaemonOutcome",
    "DaemonRequest",
    "DaemonResponse",
    "DaemonStatus",
    "DaemonUnit",
    "ExitCode",
]
