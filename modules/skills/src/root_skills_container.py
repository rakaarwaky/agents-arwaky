"""Skills root container (AES composition root).

Wires the eight capabilities (index, reader, validator, catalog,
discoverer, mutator, merge planner, rules renderer) into the agent. The
CLI surface receives an ``ISkillsAggregate`` (the agent itself), injected
at the call site, so no root→surface coupling exists.

The discoverer receives the catalog through its contract protocol: the
two capabilities never import each other.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscovererProtocol,
    ISkillsIndexProtocol,
    ISkillsMergePlannerProtocol,
    ISkillsMutatorProtocol,
    ISkillsReaderProtocol,
    ISkillsRulesRendererProtocol,
    ISkillsValidatorProtocol,
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
from modules.shared.src.utility_skill_pack import default_pack_root
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_catalog import SkillsCatalog
from modules.skills.src.capabilities_skills_discoverer import SkillsDiscoverer
from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder
from modules.skills.src.capabilities_skills_merge_planner import SkillsMergePlanner
from modules.skills.src.capabilities_skills_mutator import SkillsMutator
from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader
from modules.skills.src.capabilities_skills_rules_renderer import SkillsRulesRenderer
from modules.skills.src.capabilities_skills_validator import SkillsValidator

__all__ = [
    "SkillsFacade",
    "default_aggregate",
    "default_facade",
]


def default_aggregate(
    index: ISkillsIndexProtocol | None = None,
    reader: ISkillsReaderProtocol | None = None,
    *,
    validator: ISkillsValidatorProtocol | None = None,
    catalog: ISkillsCatalogProtocol | None = None,
    discoverer: ISkillsDiscovererProtocol | None = None,
    mutator: ISkillsMutatorProtocol | None = None,
    merge_planner: ISkillsMergePlannerProtocol | None = None,
    rules_renderer: ISkillsRulesRendererProtocol | None = None,
) -> ISkillsAggregate:
    """Return an agent bound to the repo's ``skills/`` pack (or overrides)."""
    root = default_pack_root()
    wired_catalog = catalog or SkillsCatalog()
    return SkillsAgent(
        index or SkillsIndexBuilder(root),
        reader or SkillsPackReader(root),
        validator=validator or SkillsValidator(),
        catalog=wired_catalog,
        discoverer=discoverer or SkillsDiscoverer(wired_catalog),
        mutator=mutator or SkillsMutator(),
        merge_planner=merge_planner or SkillsMergePlanner(),
        rules_renderer=rules_renderer or SkillsRulesRenderer(),
        default_root=root,
    )


def default_facade() -> SkillsFacade:
    """Return a facade bound to the repo's ``skills/`` pack."""
    return SkillsFacade()


class SkillsFacade:
    """Composition root for the skills feature (read + authoring).

    Every wrapper returns the full ``SkillsResult`` so callers can read
    the plan, outcome, report, or rendered document without the facade
    inventing a second projection. ``list_skills``/``show_skill`` keep
    their historical shapes.
    """

    def __init__(
        self,
        index: ISkillsIndexProtocol | None = None,
        reader: ISkillsReaderProtocol | None = None,
        *,
        validator: ISkillsValidatorProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discoverer: ISkillsDiscovererProtocol | None = None,
        mutator: ISkillsMutatorProtocol | None = None,
        merge_planner: ISkillsMergePlannerProtocol | None = None,
        rules_renderer: ISkillsRulesRendererProtocol | None = None,
        default_root: Path | None = None,
    ) -> None:
        self._index = index
        self._reader = reader
        self._validator = validator
        self._catalog = catalog
        self._discoverer = discoverer
        self._mutator = mutator
        self._merge_planner = merge_planner
        self._rules_renderer = rules_renderer
        self._default_root = default_root

    def _agent(self) -> SkillsAgent:
        """Build the agent lazily, defaulting every missing capability."""
        root = default_pack_root()
        catalog = self._catalog or SkillsCatalog()
        return SkillsAgent(
            self._index or SkillsIndexBuilder(root),
            self._reader or SkillsPackReader(root),
            validator=self._validator or SkillsValidator(),
            catalog=catalog,
            discoverer=self._discoverer or SkillsDiscoverer(catalog),
            mutator=self._mutator or SkillsMutator(),
            merge_planner=self._merge_planner or SkillsMergePlanner(),
            rules_renderer=self._rules_renderer or SkillsRulesRenderer(),
            default_root=self._default_root or root,
        )

    # ─── Read wrappers ───────────────────────────────────────
    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        return self._agent().execute(SkillsRequest(op=SkillsOp.LIST)).records

    def show_skill(self, name: str) -> SkillContent | None:
        """Return the raw SKILL.md content for *name*, or None when unknown."""
        return self._agent().execute(
            SkillsRequest(op=SkillsOp.SHOW, query=SkillQuery(name))
        ).content

    # ─── Authoring wrappers ──────────────────────────────────
    def validate(self, root: SkillsRoot | None = None) -> SkillsResult:
        """Run the 13-rule validator."""
        return self._agent().execute(SkillsRequest(op=SkillsOp.VALIDATE, root=root))

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

    def weed(self, root: SkillsRoot | None = None) -> SkillsResult:
        """Report duplicates, empty categories, and missing descriptions."""
        return self._agent().execute(SkillsRequest(op=SkillsOp.WEED, root=root))

    def repair(
        self, apply: bool = False, root: SkillsRoot | None = None
    ) -> SkillsResult:
        """Plan (default) or apply the mechanical repairs."""
        return self._agent().execute(
            SkillsRequest(op=SkillsOp.REPAIR, apply=apply, root=root)
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

    def new_category(
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
                op=SkillsOp.NEW_CATEGORY,
                query=SkillQuery(name),
                description=description,
                apply=apply,
                root=root,
                flags={"force": "1" if force else "0"},
            )
        )

    def merge_plan(
        self, ref_a: str, ref_b: str, root: SkillsRoot | None = None
    ) -> SkillsResult:
        """Build the read-only merge plan."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.MERGE_PLAN,
                query=SkillQuery(ref_a),
                root=root,
                flags={"target": ref_b},
            )
        )

    def rules(self, markdown: bool = False) -> SkillsResult:
        """Render the rule SSOT (markdown or summary form)."""
        return self._agent().execute(
            SkillsRequest(
                op=SkillsOp.RULES,
                flags={"markdown": "1" if markdown else "0"},
            )
        )
