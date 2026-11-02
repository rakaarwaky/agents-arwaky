"""Skills root container (AES composition root).

Wires the capabilities (lister, reader, linter, catalog, discover,
mover, archiver, creator, traces) into the agent. The
CLI surface receives an ``ISkillsAggregate`` (the agent itself), injected
at the call site, so no root→surface coupling exists.

The discover receives the catalog through its contract protocol: the
two capabilities never import each other.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from modules.shared.src.common.utility_skill_pack import default_pack_root
from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsDiscoverProtocol,
    ISkillsLinterProtocol,
    ISkillsListerProtocol,
    ISkillsMoverProtocol,
    ISkillsReaderProtocol,
    ISkillsTracesProtocol,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillRecord,
    SkillsOp,
    SkillsRequest,
    SkillsResult,
    SkillsRoot,
)
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_archiver import SkillsArchiver
from modules.skills.src.capabilities_skills_catalog import SkillsCatalog
from modules.skills.src.capabilities_skills_creator import SkillsCreator
from modules.skills.src.capabilities_skills_discover import SkillsDiscover
from modules.skills.src.capabilities_skills_linter import SkillsLinter
from modules.skills.src.capabilities_skills_lister import SkillsLister
from modules.skills.src.capabilities_skills_mover import SkillsMover
from modules.skills.src.capabilities_skills_reader import SkillsPackReader
from modules.skills.src.capabilities_skills_traces import SkillsTraces

__all__ = [
    "SkillsFacade",
    "default_aggregate",
    "default_facade",
]


def default_aggregate(
    lister: ISkillsListerProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    *,
    linter: ISkillsLinterProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discover: ISkillsDiscoverProtocol | None = None,
    mover: ISkillsMoverProtocol | None = None,
    archiver: ISkillsArchiverProtocol | None = None,
    creator: ISkillsCreatorProtocol | None = None,
    traces: ISkillsTracesProtocol | None = None,
    default_root: Path | None = None,
) -> ISkillsAggregate:
    """Return an agent bound to the repo's ``skills/`` pack (or overrides)."""
    root = default_root if default_root is not None else default_pack_root()
    wired_catalog = catalog or SkillsCatalog()
    return SkillsAgent(
        lister or SkillsLister(root),
        reader or SkillsPackReader(root),
        linter=linter or SkillsLinter(),
        catalog=wired_catalog,
        discover=discover or SkillsDiscover(wired_catalog),
        mover=mover or SkillsMover(),
        archiver=archiver or SkillsArchiver(),
        creator=creator or SkillsCreator(),
        traces=traces or SkillsTraces(),
        default_root=root,
    )


def default_facade() -> SkillsFacade:
    """Return a facade bound to the repo's ``skills/`` pack."""
    return SkillsFacade()


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
        mover: ISkillsMoverProtocol | None = None,
        archiver: ISkillsArchiverProtocol | None = None,
        creator: ISkillsCreatorProtocol | None = None,
        traces: ISkillsTracesProtocol | None = None,
        default_root: Path | None = None,
    ) -> None:
        self._lister = lister
        self._reader = reader
        self._linter = linter
        self._catalog = catalog
        self._discover = discover
        self._mover = mover
        self._archiver = archiver
        self._creator = creator
        self._traces = traces
        self._default_root = default_root

    def _agent(self) -> SkillsAgent:
        """Build the agent lazily, defaulting every missing capability."""
        root = default_pack_root()
        catalog = self._catalog or SkillsCatalog()
        return SkillsAgent(
            self._lister or SkillsLister(root),
            self._reader or SkillsPackReader(root),
            linter=self._linter or SkillsLinter(),
            catalog=catalog,
            discover=self._discover or SkillsDiscover(catalog),
            mover=self._mover or SkillsMover(),
            archiver=self._archiver or SkillsArchiver(),
            creator=self._creator or SkillsCreator(),
            traces=self._traces or SkillsTraces(),
            default_root=self._default_root or root,
        )

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
        """Rebuild ``CATALOG.md``."""
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
