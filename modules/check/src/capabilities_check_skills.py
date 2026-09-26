"""Skills check capability — delegates to the shared skill_pack domain."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_check_protocol import ICheckProtocol
from modules.shared.src.taxonomy_check_vo import CheckExitCode, CheckScope
from modules.shared.src.taxonomy_common_constant import (
    DESCRIPTION_BUDGET_BYTES,
)
from modules.shared.src.taxonomy_common_vo import (
    audit_pack,
    iter_skill_files,
)
from modules.shared.src.utility_logging_setup import err, info, ok
from modules.shared.src.utility_paths_resolver import repo_root

# ─── Block 1: Class Definition & Constructor ──────────────


class SkillsCheckRunner(ICheckProtocol):
    """Gate the skill pack on the loadability invariants."""

    #: CLI key for ``aa check skill``.
    name = "skill"
    #: Progress line printed by the orchestrator (step index is prefixed there).
    title = "Validating skill pack loadability..."

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()
        self._pack = self._root / "skills"

    # ─── Block 2: Protocol Method Implementation ──────────────
    def run(self, scope: CheckScope) -> CheckExitCode:
        """Run the skill-pack audit; *scope* routing happens in the orchestrator."""
        findings = audit_pack(self._pack)
        total = len(iter_skill_files(self._pack))
        for finding in findings:
            err(f"{finding.code}: {finding.message}")
        if not findings:
            categories = {p.relative_to(self._pack).parts[0] for p in iter_skill_files(self._pack)}
            ok(f"{total} skills across {len(categories)} categories; names unique, layout loadable")
        else:
            info(f"  ({total} SKILL.md files scanned, budget {DESCRIPTION_BUDGET_BYTES} bytes)")
        return CheckExitCode(len(findings))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillsCheckRunner()"


__all__ = ["CheckExitCode"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode}
