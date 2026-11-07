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

#: Operations the skills aggregate understands.
#: Unified skill operations: read-only, authoring mutations, and lifecycle.
class SkillsOp(StrEnum):
    # Core pack operations
    LIST = "list"
    READ = "read"
    LINT = "lint"
    CATALOG = "catalog"
    DISCOVER = "discover"
    MOVE = "move"
    ARCHIVE = "archive"
    CREATE = "create"

    # Integrated lifecycle operations
    STATUS = "status"
    USAGE = "usage"
    RUN = "run"
    PAUSE = "pause"
    RESUME = "resume"
    PIN = "pin"
    UNPIN = "unpin"
    LOCK = "lock"
    UNLOCK = "unlock"
    RESTORE = "restore"
    PRUNE = "prune"
    PURGE = "purge"
    ADOPT = "adopt"
    BACKUP = "backup"
    ROLLBACK = "rollback"
    LEDGER = "ledger"
    LIST_UNMANAGED = "list-unmanaged"
    LIST_ARCHIVED = "list-archived"


@dataclass(frozen=True)
class SkillsRequest:
    """The aggregate entry point's single argument (AES401)."""

    op: SkillsOp
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))
    description: str = ""
    apply: bool = False
    root: SkillsRoot | None = None
    flags: Mapping[str, str] = field(default_factory=dict)
