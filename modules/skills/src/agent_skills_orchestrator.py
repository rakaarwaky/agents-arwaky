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
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

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
from modules.shared.src.skills.taxonomy_skills_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillRecord,
    SkillsExitCode,
    SkillsOp,
    SkillsRequest,
    SkillsResult,
    SkillsRoot,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsAgent(ISkillsAggregate):
    """Dispatches every skills op and owns the mutation→catalog pipeline."""

    def __init__(
        self,
        index: ISkillsIndexProtocol,
        reader: ISkillsReaderProtocol,
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
        records = tuple(self._index.list_skills(request.root))
        return SkillsResult(
            ok=True,
            op=op,
            records=records,
            message="" if records else "No skills found",
        )

    def _execute_show(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Print one skill's raw SKILL.md content."""
        content = self._reader.show_skill(request.query, request.root)
        if content is None:
            # ``show`` predates the authoring exit-code contract and keeps
            # its historical exit 1 for an unknown name.
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=f"Skill not found: {request.query}",
            )
        return SkillsResult(ok=True, op=op, content=content)

    def _execute_validate(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Run the 13-rule validator over the resolved root."""
        validator = self._require(self._validator, "validator")
        report = validator.validate(self._root(request))

        exit_code = (
            SkillsExitCode.CLEAN
            if report.issue_count == 0
            else SkillsExitCode.ISSUES_FOUND
        )
        return SkillsResult(
            ok=exit_code == SkillsExitCode.CLEAN,
            op=op,
            exit_code=exit_code,
            report=report,
            root=report.skills_root,
        )

    def _execute_catalog(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Rebuild the catalog, or with ``--check`` only test for drift."""
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

        report = catalog.rebuild(root)
        return SkillsResult(ok=True, op=op, catalog=report, root=root)

    def _execute_discover(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Score the catalog against the query, with the drift fallback."""
        discoverer = self._require(self._discoverer, "discoverer")
        limit = int(request.flags.get("limit", "20"))
        root = self._root(request)
        result = discoverer.discover(str(request.query), root, limit)

        return SkillsResult(
            ok=True,
            op=op,
            matches=result.matches,
            warning=result.warning or None,
            message=result.warning_detail,
            root=root,
        )

    def _execute_weed(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Report weeds; any weed line makes the exit code 1."""
        mutator = self._require(self._mutator, "mutator")
        root = self._root(request)
        plan = mutator.plan_weed(root)
        exit_code = (
            SkillsExitCode.ISSUES_FOUND if plan.lines else SkillsExitCode.CLEAN
        )
        return SkillsResult(
            ok=not plan.lines,
            op=op,
            exit_code=exit_code,
            plan=plan,
            root=root,
        )

    def _execute_repair(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Apply safe mechanical repairs — preview by default."""
        mutator = self._require(self._mutator, "mutator")
        root = self._root(request)
        plan = mutator.plan_repair(root)

        if not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = mutator.apply(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_move(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Move a skill folder to another category — preview by default."""
        mutator = self._require(self._mutator, "mutator")
        root = self._root(request)
        plan = mutator.plan_move(
            str(request.query), request.flags.get("target", ""), root
        )

        if plan.already_in_category or not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = mutator.apply(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_archive(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Archive a skill into ``_archive/`` — preview by default."""
        mutator = self._require(self._mutator, "mutator")
        root = self._root(request)
        plan = mutator.plan_archive(str(request.query), root)

        if not request.apply:
            return SkillsResult(ok=True, op=op, plan=plan, root=root)

        outcome = mutator.apply(plan)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True, op=op, plan=plan, outcome=outcome, catalog=catalog, root=root
        )

    def _execute_new_category(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Create a category folder and its ``DESCRIPTION.md`` — preview by default."""
        mutator = self._require(self._mutator, "mutator")
        root = self._root(request)
        plan = mutator.plan_new_category(
            str(request.query),
            request.description or None,
            root,
            force=request.flags.get("force") == "1",
        )

        if not request.apply:
            return SkillsResult(ok=True, op=op, new_category=plan, root=root)

        wrote = mutator.apply_new_category(plan)
        plan = replace(plan, created=wrote)
        catalog = self._require(self._catalog, "catalog").rebuild(root)
        return SkillsResult(
            ok=True,
            op=op,
            new_category=plan,
            catalog=catalog,
            root=root,
        )

    def _execute_merge_plan(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Emit the read-only merge plan; nothing is executed."""
        planner = self._require(self._merge_planner, "merge planner")
        root = self._root(request)
        plan = planner.plan(
            str(request.query), request.flags.get("target", ""), root
        )
        return SkillsResult(
            ok=True, op=op, merge=plan, lines=planner.render(plan), root=root
        )

    def _execute_rules(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Render the rule SSOT: the markdown doc or the summary form."""
        renderer = self._require(self._rules_renderer, "rules renderer")
        document = renderer.render_markdown()
        if request.flags.get("markdown") == "1":
            return SkillsResult(ok=True, op=op, document=document.markdown)
        return SkillsResult(ok=True, op=op, document=renderer.render_summary())

    # ─── Block 4: Helpers ────────────────────────────────────
    def _root(self, request: SkillsRequest) -> SkillsRoot:
        """Resolve the request's root: explicit beats derived, never silent."""
        if request.root is not None:
            path = Path(request.root)
            if not path.is_dir():
                raise SkillsRootError(f"Skills root does not exist: {path}")
            return SkillsRoot(path)
        if self._default_root is not None:
            return SkillsRoot(self._default_root)
        raise SkillsUsageError("No skills root configured")

    @staticmethod
    def _require(capability: Any, name: str) -> Any:
        """Fail loudly when an op is used on an aggregate wired without it."""
        if capability is None:
            raise SkillsUsageError(f"Skills {name} capability is not configured")
        return capability

    # ─── Block 5: Dunder Methods, Factories & Read Helpers ────
    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        """Convenience pass-through to the index (used by the facade)."""
        return self._index.list_skills(root)

    def show_skill(
        self, name: str, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Convenience pass-through to the reader (used by the facade)."""
        return self._reader.show_skill(SkillQuery(name), root)
