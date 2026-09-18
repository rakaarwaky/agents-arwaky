"""Skills check capability — delegates to the shared skill_pack domain."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.check.contract_check_protocol import ICheckRunner
from modules.shared.src.logging.utility_logging import err, info, ok
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill.capabilities_skill_pack import (
    DESCRIPTION_BUDGET_BYTES,
    audit_pack,
    iter_skill_files,
)


class SkillsCheckRunner(ICheckRunner):
    """Gate the skill pack on the loadability invariants.

    # Block 1: Configuration
    # Block 2: Audit
    # Block 3: Report
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()
        self._pack = self._root / "skills"

    # -- Block 2: Audit --------------------------------------------------------------
    def run(self, strict: bool = False) -> int:
        print("[4/5] Validating skill pack loadability...")
        findings = audit_pack(self._pack)
        total = len(iter_skill_files(self._pack))
        for finding in findings:
            err(f"{finding.code}: {finding.message}")
        if not findings:
            categories = {p.relative_to(self._pack).parts[0] for p in iter_skill_files(self._pack)}
            ok(f"{total} skills across {len(categories)} categories; names unique, layout loadable")
        else:
            info(f"  ({total} SKILL.md files scanned, budget {DESCRIPTION_BUDGET_BYTES} bytes)")
        return len(findings)
