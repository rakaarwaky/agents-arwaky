"""Harness-domain value objects for the AES harness feature."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HarnessConfig:
    """Registration row for an agent harness connector."""

    id: str
    aliases: tuple[str, ...]
    env_target: str
    skill_link_verified: bool
    provider_id: str | None = None
    router_base_url: str | None = None
