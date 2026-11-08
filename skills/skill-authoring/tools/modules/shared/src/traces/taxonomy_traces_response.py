"""Trace response value objects (AES taxonomy layer, response side).

The typed response envelope: ``SkillsResult`` is what the surface
renders after one traces op. Reuses ``SkillsOp`` from the design
request module (which defines ``TRACES = "traces"``).

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

from shared.src.design.taxonomy_skills_request import SkillsOp

if TYPE_CHECKING:
    from shared.src.traces.taxonomy_traces_vo import PhraseRow, ScanResult


class SkillsExitCode(IntEnum):
    """Single source of truth for the CLI exit-code contract."""

    CLEAN = 0
    ISSUES_FOUND = 1
    USAGE_ERROR = 2
    CATALOG_DRIFT = 3


@dataclass(frozen=True)
class SkillsResult:
    """Response to a traces operation.

    ``exit_code`` is the CLI contract: 0 clean / 1 issues / 2 usage /
    3 catalog drift. Payload fields are populated per op; the surface
    renders them and never reaches back into a capability.
    """

    ok: bool
    op: SkillsOp = SkillsOp.TRACES
    exit_code: int = 0
    message: str = ""
    root: Path | None = None
    phrases_exact: tuple["PhraseRow", ...] = ()
    phrases_stems: tuple["PhraseRow", ...] = ()
    phrases_lines: tuple["PhraseRow", ...] = ()
    scan_summary: "ScanResult | None" = None


__all__ = ["SkillsExitCode", "SkillsResult"]
