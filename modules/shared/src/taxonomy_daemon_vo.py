"""Daemon-domain value objects for the AES daemon feature."""
from __future__ import annotations

from dataclasses import dataclass, field


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
