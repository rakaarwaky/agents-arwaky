"""Skill-domain value objects for the AES skill feature."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillInfo:
    """Registration row for a tool: id, category, description."""

    tool_id: str
    category: str
    description: str


@dataclass(frozen=True)
class SkillProvisionResult:
    """Outcome of provisioning/unprovisioning skills for one tool."""

    success: bool
    tool_id: str
    provisioned: int
    message: str
