"""Discovery agent (AES agent layer).

Implements ``ISkillsDiscoveryAggregate`` over the discovery-side capabilities:
catalog, discover, lister, reader. Owns the ops: list, read, lint, catalog,
discover.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from discovery.contract_discovery_aggregate import ISkillsDiscoveryAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.governance.taxonomy_skills_error import (
    SkillsError,
    SkillsRootError,
)
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.design.taxonomy_skills_vo import (
    SkillContent,
    SkillRecord,
)

from discovery.capabilities_skills_catalog import SkillsCatalog
from discovery.capabilities_skills_discover import SkillsBm25fRanker, SkillsDiscover
from discovery.capabilities_skills_lister import SkillsLister
from discovery.capabilities_skills_reader import SkillsPackReader

__all__ = [
    "SkillsDiscoveryAgent",
    "ISkillsDiscoveryAggregate",
]


class SkillsDiscoveryAgent(ISkillsDiscoveryAggregate):
    """Discovery-side agent: list / read / lint / catalog / discover."""

    def __init__(
        self,
        catalog: SkillsCatalog | None = None,
        discover: SkillsDiscover | None = None,
        lister: SkillsLister | None = None,
        reader: SkillsPackReader | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._catalog = catalog if catalog is not None else SkillsCatalog()
        self._discover = (
            discover
            if discover is not None
            else SkillsDiscover(self._catalog, SkillsBm25fRanker())
        )
        self._lister = lister if lister is not None else SkillsLister()
        self._reader = reader if reader is not None else SkillsPackReader()
        self._default_root = default_root

    # ─── Block 1: helpers ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"discovery capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> Path:
        if request.root:
            return Path(request.root)
        if self._default_root is not None:
            return Path(self._default_root)
        return Path()

    # ─── Block 2: Aggregate Method Implementation ────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching discovery capability."""
        try:
            op = SkillsOp(request.op)
        except ValueError:
            return SkillsResult(
                ok=False,
                op=SkillsOp.LIST,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {request.op}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: SkillsOp
    ) -> Callable[[SkillsRequest, SkillsOp], SkillsResult]:
        name = f"_execute_{op.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[SkillsRequest, SkillsOp], SkillsResult], handler)

    # ─── Block 3: per-op handlers ────────────────────────────────
    def _execute_list(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LIST: enumerate every skill record."""
        lister = self._require(self._lister, "lister")
        root = self._root(request)
        records = lister.list_skills(root)
        return SkillsResult(ok=True, op=op, records=records, root=root)

    def _execute_read(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """READ: show one skill's SKILL.md content."""
        reader = self._require(self._reader, "reader")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        content = reader.show_skill(SkillQuery(str(request.query).strip()), root)
        if content is None:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=f"Skill not found: {request.query}",
            )
        return SkillsResult(ok=True, op=op, content=content, root=root)

    def _execute_lint(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Lint is a design-side op; delegate returns discovery-not-handled."""
        return SkillsResult(
            ok=False,
            op=op,
            exit_code=SkillsExitCode.USAGE_ERROR,
            message="lint is owned by the design agent",
        )

    def _execute_catalog(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """CATALOG: build/check the catalog.json artifact."""
        catalog = self._require(self._catalog, "catalog")
        root = self._root(request)
        if request.flags.get("check"):
            report = catalog.check(root)
            return SkillsResult(
                ok=report.exit_code == SkillsExitCode.CLEAN,
                op=op,
                exit_code=report.exit_code,
                catalog_report=report,
                root=root,
            )
        report = catalog.rebuild(root)
        return SkillsResult(
            ok=True, op=op, catalog_report=report, root=root
        )

    def _execute_discover(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """DISCOVER: BM25F-ranked search over catalog rows."""
        discover = self._require(self._discover, "discover")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Query required",
            )
        limit = int(request.flags.get("limit", "20") or 20)
        result = discover.discover(SkillQuery(str(request.query).strip()), root, limit)
        return SkillsResult(ok=True, op=op, discovery=result, root=root)

    def show_skill(self, name: str, root: SkillsRoot | None = None):
        """Pass-through to the reader (used by the facade)."""
        return self._reader.show_skill(SkillQuery(name), root)
