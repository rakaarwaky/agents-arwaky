"""Skills response value objects (AES taxonomy layer, response side).

The typed response envelope: ``SkillsResult`` is what the surface
renders after one aggregate op (payload fields are populated per op,
never re-read from a capability). ``SkillsExitCode`` is the single
source of truth for the CLI exit-code contract.

The authoring VO fields (``ValidationReport``, ``LintReport``,
``CatalogReport``, ...) are imported under ``TYPE_CHECKING`` only — the
authoring module re-imports this module's names at the bottom of its own
body, so runtime imports would cycle; PEP 563 keeps the annotations as
strings.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

from shared.src.design.taxonomy_skills_request import SkillsOp

if TYPE_CHECKING:
    # Discovery payloads carry common-layer VO types at type-check time.
    # PEP 563 keeps annotations as strings, so the runtime import stays
    # one-directional: design response imports only its own request module.
    from shared.src.common.taxonomy_common_vo import (
        CatalogCheckResult,
        CatalogReport,
        DiscoveryMatch,
        SkillContent,
        SkillRecord,
    )
    from shared.src.design.taxonomy_skills_vo import (
        LintReport,
        MutationOutcome,
        MutationPlan,
        NewCategoryPlan,
        SkillCreatePlan,
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
    """

    ok: bool
    op: SkillsOp = SkillsOp.LIST
    exit_code: int = 0
    message: str = ""
    records: tuple[SkillRecord, ...] = ()
    content: SkillContent | None = None
    lint_report: LintReport | None = None
    catalog: CatalogReport | None = None
    check: CatalogCheckResult | None = None
    catalog_text: str | None = None
    matches: tuple[DiscoveryMatch, ...] = ()
    plan: MutationPlan | None = None
    outcome: MutationOutcome | None = None
    new_category: NewCategoryPlan | None = None
    create_plan: SkillCreatePlan | None = None
    warning: str | None = None
    root: Path | None = None


__all__ = ["SkillsExitCode", "SkillsResult"]