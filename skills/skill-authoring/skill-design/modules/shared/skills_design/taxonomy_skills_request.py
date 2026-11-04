"""Skills request value objects (AES taxonomy layer, request side).

The typed envelope the surface and agent exchange: ``SkillsRequest``
carries the op, the skill name or search query, the pack-root
override, the write gate, and the per-op positional/optional strings.
``SkillsOp`` names every operation the aggregate understands.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import NewType

# These two primitive aliases are the canonical home for the
# request/response envelope modules: ``vo`` re-exports them back from
# this module so the legacy import path keeps working, and the
# request/response modules never import ``vo`` at runtime (no cycle,
# in either import order).
SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""

SkillsRoot = NewType("SkillsRoot", Path)
"""An explicit skills root; ``None`` on a request means 'use the default'."""

#: One op per capability the skills aggregate understands; the CLI
#: surface exposes 5 of them (list, read, lint, catalog, discover);
#: the remaining 4 (move, archive, create, traces) are reachable via
#: the agent/facade only.
class SkillsOp(StrEnum):
    LIST = "list"
    READ = "read"
    LINT = "lint"
    CATALOG = "catalog"
    DISCOVER = "discover"
    MOVE = "move"
    ARCHIVE = "archive"
    CREATE = "create"
    TRACES = "traces"


@dataclass(frozen=True)
class SkillsRequest:
    """Input for one skills operation.

    ``op`` selects the capability; ``query`` carries the skill name or the
    search query; ``root`` overrides the default pack root (explicit beats
    derived); ``apply`` is the only path to a write; ``flags`` carries the
    per-op positional/optional strings (``category``, ``target``,
    ``limit``, ``force``, ...). The traces sub-action (collect, usage,
    phrases, materialize, state-get/set/clear/trash/restrict/decide/wait)
    is carried in ``flags`` (``traces_action`` / ``state_action``) — no
    dedicated field; the surface and agent agree on the flag keys.
    """

    op: SkillsOp = SkillsOp.LIST
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))
    root: SkillsRoot | None = None
    apply: bool = False
    json: bool = False
    description: str = ""
    flags: Mapping[str, str] = field(default_factory=dict)


__all__ = ["SkillQuery", "SkillsOp", "SkillsRequest", "SkillsRoot"]
