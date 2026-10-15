"""Skills orchestrator (AES agent layer).

Implements ``ISkillsAggregate``: a single ``execute`` entry point that the
surface, root CLI and other features call with a typed ``SkillsRequest``.
The agent coordinates two subsystems — the pack index (list) and the pack
reader (show) — both injected by the composition root.
"""

from __future__ import annotations

from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsIndexProtocol,
    ISkillsReaderProtocol,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsRequest,
    SkillsResult,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsAgent(ISkillsAggregate):
    """Read-only agent over the skill pack: list and show."""

    def __init__(
        self,
        index: ISkillsIndexProtocol,
        reader: ISkillsReaderProtocol,
    ) -> None:
        self._index = index
        self._reader = reader

    # ─── Block 2: Aggregate Method Implementation ────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching subsystem; return the response."""
        op = request.op
        if op == "list":
            records = tuple(self._index.list_skills())
            return SkillsResult(
                ok=True,
                records=records,
                message="" if records else "No skills found",
            )
        if op == "show":
            query = request.query
            content = self._reader.show_skill(query)
            if content is None:
                return SkillsResult(
                    ok=False,
                    content=None,
                    message=f"Skill not found: {query}",
                )
            return SkillsResult(ok=True, content=content)
        return SkillsResult(ok=False, message=f"Unknown skills op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def list_skills(self):
        """Convenience pass-through to the index (used by the facade)."""
        return self._index.list_skills()

    def show_skill(self, name: str):
        """Convenience pass-through to the reader (used by the facade)."""
        from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery

        return self._reader.show_skill(SkillQuery(name))
