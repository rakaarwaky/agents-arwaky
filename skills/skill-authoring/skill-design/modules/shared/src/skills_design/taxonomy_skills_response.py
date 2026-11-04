"""Skills response value objects (AES taxonomy layer, response side).

The typed response envelope: ``SkillsResult`` is what the surface
renders after one aggregate op (payload fields are populated per op,
never re-read from a capability). ``SkillsExitCode`` is the single
source of truth for the CLI exit-code contract.

The authoring VO fields (``ValidationReport``, ``LintReport``,
``CatalogReport``, ...) and the trace-primitive fields (``SkillRecord``,
``ScanResult``, ...) are imported under ``TYPE_CHECKING`` only — the
authoring module (and, through it, ``taxonomy_skills_vo``) re-imports
this module's names, so runtime imports would cycle; PEP 563 keeps the
annotations as strings.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

from skills_design.src.taxonomy_skills_request import SkillsOp

if TYPE_CHECKING:
    # ``SkillsResult`` annotates the authoring VOs (``ValidationReport``,
    # ``LintReport``, ``CatalogReport``, ...). Those classes live in the
    # authoring module, which imports the trace primitives back from
    # ``taxonomy_skills_vo`` at the bottom — a runtime import here would
    # cycle, so the names are reserved for type-checking (PEP 563 string
    # annotations, same pattern the old vo module used).
    from skills_design.src.taxonomy_skills_authoring_vo import (
        CatalogCheckResult,
        CatalogReport,
        DiscoveryMatch,
        LintReport,
        MutationOutcome,
        MutationPlan,
        NewCategoryPlan,
        PhrasesReport,
        SkillCreatePlan,
        UsageReport,
        ValidationReport,
    )

    # The trace primitives also live in ``taxonomy_skills_vo``, which
    # re-imports this module's names at the bottom of its own body (after
    # the primitives are defined). Importing that module back at the top
    # of this one would cycle, so the annotation names are reserved for
    # type-checking too; PEP 563 keeps them as strings.
    from skills_design.src.taxonomy_skills_vo import (
        ScanResult,
        SkillContent,
        SkillRecord,
        TraceStateStatus,
    )


class SkillsExitCode(IntEnum):
    """Single source of truth for the CLI exit-code contract.

    The surface maps ``SkillsResult.exit_code`` against this enum;
    capabilities never emit exit codes themselves — they set them on the
    errors they raise, and the agent derives them from check results.
    """

    CLEAN = 0
    ISSUES_FOUND = 1
    USAGE_ERROR = 2
    CATALOG_DRIFT = 3


@dataclass(frozen=True)
class SkillsResult:
    """Response to a skills operation.

    ``exit_code`` is the CLI contract: 0 clean / 1 issues / 2 usage /
    3 catalog drift. Payload fields are populated per op; the surface
    renders them and never reaches back into a capability.

    ``state`` is populated by trace-state set/get/clear; ``state_status``
    is the ``wait`` outcome. ``collect_summary`` carries the tracker
    scan counters (``ScanResult``) for trace-collect.
    """

    ok: bool
    op: SkillsOp = SkillsOp.LIST
    exit_code: int = 0
    message: str = ""
    records: tuple[SkillRecord, ...] = ()
    content: SkillContent | None = None
    report: ValidationReport | None = None
    lint_report: LintReport | None = None
    catalog: CatalogReport | None = None
    check: CatalogCheckResult | None = None
    catalog_text: str | None = None
    matches: tuple[DiscoveryMatch, ...] = ()
    plan: MutationPlan | None = None
    outcome: MutationOutcome | None = None
    new_category: NewCategoryPlan | None = None
    create_plan: SkillCreatePlan | None = None
    lines: tuple[str, ...] = ()
    warning: str | None = None
    root: Path | None = None
    usage: UsageReport | None = None
    phrases: PhrasesReport | None = None
    state: TraceStateStatus | None = None
    state_status: TraceStateStatus | None = None
    collect_summary: ScanResult | None = None


__all__ = ["SkillsExitCode", "SkillsResult"]
