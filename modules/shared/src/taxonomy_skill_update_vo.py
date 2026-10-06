"""Skill-update value objects (AES taxonomy layer, frozen VOs).

Holds the input envelope the surface hands to the update capability and the
result VO the capability returns after a merge run.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

#: Tool identifier accepted by the update command.
UpdateToolId = NewType("UpdateToolId", str)

#: Flag bag carried by an update request.
UpdateFlags = NewType("UpdateFlags", dict)

#: Optional per-skill override flags.
SkillUpdateFlags = NewType("SkillUpdateFlags", dict)

#: Empty default values for optional update request fields.
UPDATE_TOOL_ID_EMPTY: UpdateToolId = UpdateToolId("")
UPDATE_FLAGS_EMPTY: UpdateFlags = UpdateFlags({})
SKILL_UPDATE_FLAGS_EMPTY: SkillUpdateFlags = SkillUpdateFlags({})


@dataclass(frozen=True)
class SourceSkillEntry:
    """One discoverable skill source inside an internal submodule."""

    tool_id: str
    source_path: str
    skill_name: str
    category: str
    description: str
    relative_source: str = ""


@dataclass(frozen=True)
class UpdateResult:
    """Outcome of running ``aa skill update``."""

    success: bool
    tool_id: str
    merged: int
    conflicted: int = 0
    skipped: int = 0
    message: str = ""
    conflicts: tuple[str, ...] = ()


__all__ = [
    "SKILL_UPDATE_FLAGS_EMPTY",
    "UPDATE_FLAGS_EMPTY",
    "UPDATE_TOOL_ID_EMPTY",
    "SkillUpdateFlags",
    "SourceSkillEntry",
    "UpdateFlags",
    "UpdateResult",
    "UpdateToolId",
]
