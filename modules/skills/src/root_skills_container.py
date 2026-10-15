"""Skills root container (AES composition root).

Wires the two capabilities (index + reader) into the agent. The CLI surface
receives an ``ISkillsAggregate`` (the agent itself), injected at the call
site, so no root→surface coupling exists.
"""

from __future__ import annotations

from collections.abc import Sequence

from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsIndexProtocol,
    ISkillsReaderProtocol,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillRecord,
    SkillsRequest,
    SkillsResult,
)
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
    SkillsPackReader,
    default_pack_root,
)


def default_aggregate(
    index: ISkillsIndexProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
) -> ISkillsAggregate:
    """Return an agent bound to the repo's ``skills/`` pack (or overrides)."""
    root = default_pack_root()
    return SkillsAgent(
        index or SkillsIndexBuilder(root),
        reader or SkillsPackReader(root),
    )


def default_facade() -> SkillsFacade:
    """Return a facade bound to the repo's ``skills/`` pack."""
    root = default_pack_root()
    return SkillsFacade(index=SkillsIndexBuilder(root), reader=SkillsPackReader(root))


class SkillsFacade:
    """Composition root for the skills feature (list + show, read-only)."""

    def __init__(
        self,
        index: ISkillsIndexProtocol | None = None,
        reader: ISkillsReaderProtocol | None = None,
    ) -> None:
        self._index = index
        self._reader = reader

    def _resolve_index(self) -> ISkillsIndexProtocol:
        if self._index is None:
            self._index = SkillsIndexBuilder(default_pack_root())
        return self._index

    def _resolve_reader(self) -> ISkillsReaderProtocol:
        if self._reader is None:
            self._reader = SkillsPackReader(default_pack_root())
        return self._reader

    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        return self._execute(SkillsRequest(op="list")).records

    def show_skill(self, name: str) -> SkillContent | None:
        """Return the raw SKILL.md content for *name*, or None when unknown."""
        return self._execute(
            SkillsRequest(op="show", query=SkillQuery(name))
        ).content

    def _execute(self, request: SkillsRequest) -> SkillsResult:
        """Run *request* against a wired agent."""
        return SkillsAgent(self._resolve_index(), self._resolve_reader()).execute(
            request
        )
