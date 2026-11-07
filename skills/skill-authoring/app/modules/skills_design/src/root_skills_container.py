"""Skills-design root container (AES composition root).

Wires the design-side capabilities (lister, reader, linter, catalog,
discover, mover, archiver, creator) into the design-side agent. The
package is fully self-contained: every contract / taxonomy / utility
module it needs lives under ``skills_design/src/``.

The traces capability of the sibling traces app is NOT imported
here — the two packages are independent (AES702). The agent accepts only design-side capabilities; the orchestrator-owned CLI entry point
(``modules/root_cli_entry.py``) composes them at the call site. The CLI
surface receives an ``ISkillsAggregate`` (the agent itself), injected
at the call site, so no root→surface coupling exists.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root
from shared.src.skills_design.contract_skills_aggregate import ISkillsAggregate
from shared.src.skills_design.contract_skills_bm25f_protocol import (
    IBM25FRankerProtocol,
)
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsDiscoverProtocol,
    ISkillsLinterProtocol,
    ISkillsListerProtocol,
    ISkillsMoverProtocol,
    ISkillsReaderProtocol,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.skills_design.taxonomy_skills_response import SkillsResult
from shared.src.skills_design.taxonomy_skills_vo import (
    SkillContent,
    SkillRecord,
)

from skills_design.src.agent_skills_orchestrator import SkillsAgent
from skills_design.src.capabilities_skills_archiver import SkillsArchiver
from skills_design.src.capabilities_skills_catalog import SkillsCatalog
from skills_design.src.capabilities_skills_creator import SkillsCreator
from skills_design.src.capabilities_skills_discover import (
    SkillsBm25fRanker,
    SkillsDiscover,
)
from skills_design.src.capabilities_skills_lifecycle import SkillsLifecycle
from skills_design.src.capabilities_skills_linter import SkillsLinter
from skills_design.src.capabilities_skills_lister import SkillsLister
from skills_design.src.capabilities_skills_mover import SkillsMover
from skills_design.src.capabilities_skills_reader import SkillsPackReader

__all__ = [
    "SkillsFacade",
    "default_aggregate",
]


def default_aggregate(
    lister: ISkillsListerProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    *,
    linter: ISkillsLinterProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discover: ISkillsDiscoverProtocol | None = None,
    ranker: IBM25FRankerProtocol | None = None,
    mover: ISkillsMoverProtocol | None = None,
    archiver: ISkillsArchiverProtocol | None = None,
    creator: ISkillsCreatorProtocol | None = None,
    lifecycle: SkillsLifecycle | None = None,
    default_root: Path | None = None,
) -> ISkillsAggregate:
    """Return an agent bound to the repo's ``skills/`` pack (or overrides).

    The agent has only design-side capabilities. ``SkillsOp.TRACES`` is
    not recognized — traces live only in the independent traces app.
    """
    root = default_root if default_root is not None else default_pack_root()
    wired_catalog = catalog or SkillsCatalog()
    wired_linter = linter or SkillsLinter()
    wired_ranker = ranker or SkillsBm25fRanker()
    wired_lifecycle = lifecycle or SkillsLifecycle()
    return SkillsAgent(
        lister or SkillsLister(root),
        reader or SkillsPackReader(root),
        linter=wired_linter,
        catalog=wired_catalog,
        discover=discover or SkillsDiscover(wired_catalog, ranker=wired_ranker),
        mover=mover or SkillsMover(),
        archiver=archiver or SkillsArchiver(lifecycle=wired_lifecycle),
        creator=creator or SkillsCreator(),
        lifecycle=wired_lifecycle,
        default_root=root,
    )


class SkillsFacade:
    """Composition root for the skills feature (read + authoring).

    Every wrapper returns the full ``SkillsResult`` so callers can read
    the plan, outcome, report, or rendered document without the facade
    inventing a second projection. ``list_skills``/``read_skill`` keep
    their historical shapes.
    """

    def __init__(
        self,
        lister: ISkillsListerProtocol | None = None,
        reader: ISkillsReaderProtocol | None = None,
        *,
        linter: ISkillsLinterProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discover: ISkillsDiscoverProtocol | None = None,
        ranker: IBM25FRankerProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        archiver: ISkillsArchiverProtocol | None = None,
        creator: ISkillsCreatorProtocol | None = None,
        default_root: Path | None = None,
    ) -> None:
        root = default_root if default_root is not None else default_pack_root()
        wired_catalog = catalog or SkillsCatalog()
        wired_linter = linter or SkillsLinter()
        wired_ranker = ranker or SkillsBm25fRanker()
        self._agent_cache = SkillsAgent(
            lister or SkillsLister(root),
            reader or SkillsPackReader(root),
            linter=wired_linter,
            catalog=wired_catalog,
            discover=discover or SkillsDiscover(wired_catalog, ranker=wired_ranker),
            mover=mover or SkillsMover(),
            archiver=archiver or SkillsArchiver(),
            creator=creator or SkillsCreator(),
            default_root=root,
        )

    def _agent(self) -> SkillsAgent:
        """Return the built agent (instantiated once, never per call)."""
        return self._agent_cache

    # ─── Read wrappers ───────────────────────────────────────
    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        return self._agent().execute(SkillsRequest(op=SkillsOp.LIST)).records

    def read_skill(self, name: str) -> SkillContent | None:
        """Return the raw SKILL.md content for *name*, or None when unknown."""
        return self._agent().execute(
            SkillsRequest(op=SkillsOp.READ, query=SkillQuery(name))
        ).content

    # ─── Authoring wrappers ──────────────────────────────────
    def lint(
        self,
        root: SkillsRoot | None = None,
        category: str | None = None,
    ) -> SkillsResult:
        """Run the full lint scan (13-rule checks + weed report)."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.LINT,
                root=root,
                flags={"category": category or ""},
            )
        )

    def catalog_rebuild(self, root: SkillsRoot | None = None) -> SkillsResult:
        """Rebuild ``catalog.json``."""
        return self._agent().execute(SkillsRequest(op=SkillsOp.CATALOG, root=root))

    def catalog_check(self, root: SkillsRoot | None = None) -> SkillsResult:
        """Run the catalog drift gate (never writes)."""
        return self._agent().execute(
            SkillsRequest(op=SkillsOp.CATALOG, root=root, flags={"check": "1"})
        )

    def discover(
        self, query: str, limit: int = 20, root: SkillsRoot | None = None
    ) -> SkillsResult:
        """Search the catalog."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.DISCOVER,
                query=SkillQuery(query),
                root=root,
                flags={"limit": str(limit)},
            )
        )

    def move(
        self,
        skill: str,
        target: str,
        apply: bool = False,
        root: SkillsRoot | None = None,
    ) -> SkillsResult:
        """Plan (default) or apply a move."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.MOVE,
                query=SkillQuery(skill),
                apply=apply,
                root=root,
                flags={"target": target},
            )
        )

    def archive(
        self, skill: str, apply: bool = False, root: SkillsRoot | None = None
    ) -> SkillsResult:
        """Plan (default) or apply an archive."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.ARCHIVE,
                query=SkillQuery(skill),
                apply=apply,
                root=root,
            )
        )

    def create_skill(
        self,
        skill: str,
        category: str,
        description: str = "",
        when_to_use: str = "",
        argument_hint: str = "",
        body: str = "",
        apply: bool = False,
        root: SkillsRoot | None = None,
    ) -> SkillsResult:
        """Plan (default) or apply creating a new skill SKILL.md."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.CREATE,
                query=SkillQuery(skill),
                description=description,
                apply=apply,
                root=root,
                flags={
                    "kind": "skill",
                    "category": category,
                    "when_to_use": when_to_use,
                    "argument_hint": argument_hint,
                    "body": body,
                },
            )
        )

    def create_category(
        self,
        name: str,
        description: str = "",
        force: bool = False,
        apply: bool = False,
        root: SkillsRoot | None = None,
    ) -> SkillsResult:
        """Plan (default) or apply a category creation."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.CREATE,
                query=SkillQuery(name),
                description=description,
                apply=apply,
                root=root,
                flags={"kind": "category", "force": "1" if force else "0"},
            )
        )
