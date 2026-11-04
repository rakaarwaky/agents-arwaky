"""Skills-design root container (AES composition root).

Wires the design-side capabilities (lister, reader, linter, catalog,
discover, mover, archiver, creator) into the design-side agent. The
package is fully self-contained: every contract / taxonomy / utility
module it needs lives under ``skills_design/src/``.

The traces capability of the sibling ``skills_traces`` package is NOT
imported here — the two packages are independent (AES702). The agent
accepts an optional ``traces`` protocol object (injected at the call
site); the orchestrator-owned CLI entry point
(``modules/root_cli_entry.py``) is the only place that knows both
packages exist and composes them. The CLI surface receives an
``ISkillsAggregate`` (the agent itself), injected at the call site, so
no root→surface coupling exists.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from skills_design.src.utility_skill_pack import default_pack_root
from skills_design.src.contract_skills_aggregate import ISkillsAggregate
from skills_design.src.contract_skills_protocol import (
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
from skills_design.src.taxonomy_skills_request import SkillsOp, SkillsRequest
from skills_design.src.taxonomy_skills_response import SkillsResult
from skills_design.src.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillRecord,
    SkillsRoot,
)
from skills_design.src.agent_skills_orchestrator import SkillsAgent
from skills_design.src.capabilities_skills_archiver import SkillsArchiver
from skills_design.src.capabilities_skills_catalog import SkillsCatalog
from skills_design.src.capabilities_skills_creator import SkillsCreator
from skills_design.src.capabilities_skills_discover import SkillsDiscover
from skills_design.src.capabilities_skills_linter import SkillsLinter
from skills_design.src.capabilities_skills_lister import SkillsLister
from skills_design.src.capabilities_skills_mover import SkillsMover
from skills_design.src.capabilities_skills_reader import SkillsPackReader

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
    """Return an agent bound to the repo's ``skills/`` pack (or overrides).

    ``traces`` stays optional: when omitted, the agent has no traces
    capability and ``SkillsOp.TRACES`` requests are usage errors. The
    orchestrator-owned CLI entry point injects the concrete
    ``skills_traces.SkillsTraces`` implementation, so this package
    never imports the sibling tree.
    """
    root = default_root if default_root is not None else default_pack_root()
    wired_catalog = catalog or SkillsCatalog()
    wired_linter = linter or SkillsLinter()
    return SkillsAgent(
        lister or SkillsLister(root),
        reader or SkillsPackReader(root),
        linter=wired_linter,
        catalog=wired_catalog,
        discover=discover or SkillsDiscover(wired_catalog),
        mover=mover or SkillsMover(),
        archiver=archiver or SkillsArchiver(),
        creator=creator or SkillsCreator(),
        traces=traces,
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
        root = default_root if default_root is not None else default_pack_root()
        wired_catalog = catalog or SkillsCatalog()
        wired_linter = linter or SkillsLinter()
        self._agent_cache = SkillsAgent(
            lister or SkillsLister(root),
            reader or SkillsPackReader(root),
            linter=wired_linter,
            catalog=wired_catalog,
            discover=discover or SkillsDiscover(wired_catalog),
            mover=mover or SkillsMover(),
            archiver=archiver or SkillsArchiver(),
            creator=creator or SkillsCreator(),
            traces=traces,
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
