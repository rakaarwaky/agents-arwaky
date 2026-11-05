"""Skills orchestrator (AES agent layer).

Implements ``ISkillsAggregate``: a single ``execute`` entry point that
the surface, root CLI, and other features call with a typed
``SkillsRequest``. The agent is the only layer allowed to sequence
capabilities — in particular the rule that a mutation rebuilds the
catalog *after* it applies belongs here, never in a capability (no
inter-capability calls) and never in the surface (no business
sequencing in the UI layer).

The agent depends only on contract protocols and taxonomy; the
composition root injects every capability implementation.

The ``traces`` op is owned by the independent traces app; this package never
imports the sibling tree and never dispatches ``SkillsOp.TRACES``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

from shared.src.skills_design.contract_skills_aggregate import ISkillsAggregate
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
from shared.src.skills_design.taxonomy_skills_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.skills_design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.skills_design.taxonomy_skills_vo import (
    SkillContent,
    SkillRecord,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsAgent(ISkillsAggregate):
    """Dispatches every skills op and owns the mutation→catalog pipeline."""

    def __init__(
        self,
        lister: ISkillsListerProtocol,
        reader: ISkillsReaderProtocol,
        *,
        linter: ISkillsLinterProtocol | None = None,
        catalog: ISkillsCatalogProtocol | None = None,
        discover: ISkillsDiscoverProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        archiver: ISkillsArchiverProtocol | None = None,
        creator: ISkillsCreatorProtocol | None = None,
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
        self._default_root = default_root

    # ─── Block 2: Aggregate Method Implementation ────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching capability; return the response."""
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

    # ─── Block 3: Per-Op Handlers ─────────────────────────────
    def _handler_for(
        self, op: SkillsOp
    ) -> Callable[[SkillsRequest, SkillsOp], SkillsResult]:
        """The typed handler for one op; ``KeyError`` for an unknown one."""
        name = f"_execute_{op.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[SkillsRequest, SkillsOp], SkillsResult], handler)

    def _execute_list(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """List every skill in the pack."""
        lister = self._require(self._lister, "lister")
        records = tuple(lister.list_skills(request.root))
        return SkillsResult(
            ok=True,
            op=op,
            records=records,
            message="" if records else "No skills found",
        )

    def _execute_read(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Return one skill's raw SKILL.md content."""
        content = self._reader.show_skill(request.query, request.root)
        if content is None:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=f"Skill not found: {request.query}",
            )
        return SkillsResult(ok=True, op=op, content=content)

    def _execute_lint(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Run the full lint scan (13-rule checks + weed report) over the root."""
        linter = self._require(self._linter, "linter")
        category = request.flags.get("category") or None
        report = linter.lint(self._root(request), category=category)

        exit_code = (
            SkillsExitCode.CLEAN
            if report.unfiltered_issue_count == 0
            else SkillsExitCode.ISSUES_FOUND
        )
        return SkillsResult(
            ok=exit_code == SkillsExitCode.CLEAN,
            op=op,
            exit_code=exit_code,
            lint_report=report,
            root=report.skills_root,
        )

    def _execute_catalog(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Rebuild the catalog and/or read it back, per the ``build``/``read`` flags.

        The ``check`` flag (drift gate, exit 3) stays available at the
        capability/agent level but is no longer routed from the CLI.
        """
        catalog = self._require(self._catalog, "catalog")
        root = self._root(request)

        if request.flags.get("check") == "1":
            check = catalog.check(root)
            exit_code = (
                SkillsExitCode.CLEAN
                if check.in_sync
                else SkillsExitCode.CATALOG_DRIFT
            )
            return SkillsResult(
                ok=check.in_sync,
                op=op,
                exit_code=exit_code,
                check=check,
                message=check.message,
                root=root,
            )

        # CLI surface: the parser tri-state resolves to an explicit flag
        # value; no flag at all → both (build then print).
        # Facade: a bare catalog request (no build/read keys) → build only.
        build = (
            request.flags.get("build", "1") == "1"
            if "build" in request.flags or "read" in request.flags
            else True
        )
        read = request.flags.get("read", "0") == "1"

        if build:
            report = catalog.rebuild(root)
        else:
            report = None

        if read:
            text = catalog.read(root)
            if not text:
                return SkillsResult(
                    ok=False,
                    op=op,
                    exit_code=SkillsExitCode.ISSUES_FOUND,
                    message="catalog.json not found — run with --build first",
                    root=root,
                )
            return SkillsResult(
                ok=True,
                op=op,
                catalog=report,
                catalog_text=text,
                root=root,
            )

        return SkillsResult(ok=True, op=op, catalog=report, root=root)

    def _execute_discover(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Score the catalog against the query, with the drift fallback."""
        discover = self._require(self._discover, "discover")
        limit = int(request.flags.get("limit", "20"))
        root = self._root(request)
        # Optional ranker override: the agent swaps the capability for a
        # BM25F variant when the flag is set (default stays legacy).
        ranker = request.flags.get("ranker", "legacy")
        if ranker == "bm25f":
            from skills_design.src.capabilities_skills_discover import (
                SkillsDiscover,
            )
            discover = SkillsDiscover(
                self._require(self._catalog, "catalog"), ranker="bm25f"
            )
        result = discover.discover(str(request.query), root, limit)

        return SkillsResult(
            ok=True,
            op=op,
            matches=result.matches,
            warning=result.warning or None,
            message=result.warning_detail,
            root=root,
        )

    def _execute_move(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Move a skill folder to another category — preview by default."""
        mover = self._require(self._mover, "mover")
        root = self._root(request)
        plan = mover.plan_move(
            str(request.query), request.flags.get("target", ""), root
        )

        if plan.already_in_category or not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = mover.apply_move(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_archive(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Archive a skill into ``_archive/`` — preview by default."""
        archiver = self._require(self._archiver, "archiver")
        root = self._root(request)
        plan = archiver.plan_archive(str(request.query), root)

        if not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = archiver.apply_archive(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_create(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Create a skill or a category in the pack — preview by default.

        ``flags["kind"]`` selects the verb: ``"skill"`` (default) or
        ``"category"``. The agent routes to the matching creator method
        and, on an applied write, rebuilds the catalog.
        """
        creator = self._require(self._creator, "creator")
        root = self._root(request)
        kind = request.flags.get("kind", "skill")

        if kind == "category":
            name = str(request.query)
            description = request.description or ""
            force = request.flags.get("force") == "1"
            plan = creator.create_category(
                name=name,
                description=description,
                root=root,
                force=force,
                apply=request.apply,
            )
            if not request.apply:
                return SkillsResult(ok=True, op=op, new_category=plan, root=root)
            catalog = self._require(self._catalog, "catalog").rebuild(root)
            return SkillsResult(
                ok=True,
                op=op,
                new_category=plan,
                catalog=catalog,
                root=root,
            )

        # kind == "skill" (default)
        skill = str(request.query)
        category = request.flags.get("category", "")
        if not category:
            raise SkillsUsageError(
                "Missing --category: pass --category <cat> for the new skill folder"
            )

        description = request.description
        when_to_use = request.flags.get("when_to_use", "")
        argument_hint = request.flags.get("argument_hint", "")
        body = request.flags.get("body", "")

        plan = creator.create_skill(
            skill=skill,
            category=category,
            description=description,
            when_to_use=when_to_use,
            argument_hint=argument_hint,
            body=body,
            root=root,
            apply=request.apply,
        )

        if plan.already_exists or not request.apply:
            return SkillsResult(ok=True, op=op, create_plan=plan, root=root)

        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True,
            op=op,
            create_plan=plan,
            catalog=catalog,
            root=root,
        )

    def _root(self, request: SkillsRequest) -> SkillsRoot:
        """Resolve the request's root: explicit beats derived, never silent."""
        if request.root is not None:
            path = request.root
            if not path.is_dir():
                raise SkillsRootError(f"Skills root does not exist: {path}")
            return path
        if self._default_root is not None:
            return self._default_root
        raise SkillsUsageError("No skills root configured")

    @staticmethod
    def _require(capability: object, name: str) -> object:
        """Fail loudly when an op is used on an aggregate wired without it."""
        if capability is None:
            raise SkillsUsageError(f"Skills {name} capability is not configured")
        return capability

    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        """Convenience pass-through to the lister (used by tests; the facade builds its own request)."""
        return self._lister.list_skills(root)

    def show_skill(
        self, name: str, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Convenience pass-through to the reader (used by the facade)."""
        return self._reader.show_skill(SkillQuery(name), root)
