"""Harness-domain value objects for the AES harness feature."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import NewType

from modules.harness.src.taxonomy_harness_constant import ALL_HARNESS_IDS

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)


class HarnessVo:
    """Marker base for harness-domain VOs."""


@dataclass(frozen=True)
class HarnessConfig(HarnessVo):
    """Registration row for an agent harness connector (taxonomy data)."""

    id: str
    aliases: tuple[str, ...]
    env_target: str
    skill_link_verified: bool
    provider_id: str | None = None
    router_base_url: str | None = None


@dataclass(frozen=True)
class RouterCredentials(HarnessVo):
    """Resolved 9Router endpoint + key (secret referenced, never persisted)."""

    url: str
    key: str


class UnsupportedHarnessError(Exception):
    """Typed error for an unknown harness id; names the supported set.

    The capability layer raises this when a requested id is missing from the
    adapter registry; the CLI surfaces it rather than crashing.
    """

    def __init__(self, harness_id: str, supported: tuple[str, ...]) -> None:
        super().__init__(f"Unknown harness id '{harness_id}'. "
                         f"Supported: {', '.join(supported)}")
        self.harness_id = harness_id
        self.supported = supported


@dataclass
class ConnectOpts(HarnessVo):
    """FR-001 option bag; scope gates default off so everything runs."""

    force: bool = False
    dry_run: bool = False
    mcp_only: bool = False
    skills_only: bool = False
    env_only: bool = False
    router: bool = False
    copy_skills: bool = False
    adapters: dict[str, object] = field(default_factory=dict, repr=False)

    def adapter(self, harness_id: str):
        try:
            return self.adapters[harness_id]
        except KeyError:
            raise UnsupportedHarnessError(harness_id, ALL_HARNESS_IDS) from None


@dataclass
class DisconnectOpts(HarnessVo):
    """FR-002 option bag."""

    dry_run: bool = False
    adapters: dict[str, object] = field(default_factory=dict, repr=False)

    def adapter(self, harness_id: str):
        try:
            return self.adapters[harness_id]
        except KeyError:
            raise UnsupportedHarnessError(harness_id, ALL_HARNESS_IDS) from None


@dataclass
class SkillsOpts(HarnessVo):
    """FR-003 option bag."""

    copy: bool = False
    dry_run: bool = False
    force: bool = False
    adapters: dict[str, object] = field(default_factory=dict, repr=False)

    def adapter(self, harness_id: str):
        try:
            return self.adapters[harness_id]
        except KeyError:
            raise UnsupportedHarnessError(harness_id, ALL_HARNESS_IDS) from None


__all__ = [
    "ConnectOpts",
    "DisconnectOpts",
    "ExitCode",
    "HarnessConfig",
    "HarnessVo",
    "RouterCredentials",
    "SkillsOpts",
    "UnsupportedHarnessError",
]
