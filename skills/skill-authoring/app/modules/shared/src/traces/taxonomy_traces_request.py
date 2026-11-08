"""Trace request value objects (AES taxonomy layer, request side).

The typed envelope the surface and agent exchange for the traces feature.
``SkillsRequest`` carries the op, the skill name or search query, the
pack-root override, the write gate, and the per-op positional/optional
strings in ``flags``. ``SkillsOp`` names every operation the traces
aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import NewType

SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""

SkillsRoot = NewType("SkillsRoot", Path)
"""An explicit skills root; ``None`` on a request means 'use the default'."""


class SkillsOp(StrEnum):
    """Operations the traces aggregate understands."""

    PHRASES = "phrases"


@dataclass(frozen=True)
class SkillsRequest:
    """Input for one traces operation."""

    op: SkillsOp = SkillsOp.PHRASES
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))
    root: SkillsRoot | None = None
    apply: bool = False
    json: bool = False
    description: str = ""
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = ["SkillQuery", "SkillsOp", "SkillsRequest", "SkillsRoot"]
