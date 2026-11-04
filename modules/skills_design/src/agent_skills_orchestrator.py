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

The ``traces`` capability (injected by the composition root) is the one
op whose implementation lives in the sibling ``modules/skills_traces``
module; all other capabilities are design-side.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

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
from modules.shared.src.skills.taxonomy_skills_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from modules.shared.src.skills.taxonomy_skills_request import SkillsOp, SkillsRequest
from modules.shared.src.skills.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillRecord,
    SkillsRoot,
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
                    message="CATALOG.md not found — run with --build first",
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

    def _execute_traces(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Route one trace sub-action through the traces capability.

        The trace pipeline itself lives in the sibling ``modules/
        skills_traces`` module; the composition root wires its
        ``SkillsTraces`` capability into this agent, which dispatches
        the sub-action here through the shared protocol.
        """
        traces = self._require(self._traces, "traces")
        action = request.flags.get("traces_action", "")

        if action == "collect":
            return self._traces_collect(traces, request, op)
        if action == "usage":
            grok_home = request.flags.get("grok_home", "")
            run_dir = request.flags.get("run_dir", "")
            usage = traces.build_usage(grok_home=grok_home, run_dir=run_dir)
            return SkillsResult(ok=True, op=op, usage=usage)
        if action == "phrases":
            grok_home = request.flags.get("grok_home", "")
            run_dir = request.flags.get("run_dir", "")
            report = traces.build_phrases(grok_home=grok_home, run_dir=run_dir)
            return SkillsResult(ok=True, op=op, phrases=report)
        if action == "materialize":
            return self._traces_materialize(traces, request, op)
        if action == "state":
            return self._traces_state(traces, request, op)
        raise SkillsUsageError(f"Unknown traces action: {action}")

    # ── trace sub-action helpers ──────────────────────────────

    def _traces_collect(
        self, traces: ISkillsTracesProtocol, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Scan sessions then build usage: the collect half of the trace pipeline."""
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        days = int(request.flags.get("days", "0"))
        since_last = request.flags.get("since_last") == "1"
        min_turns = int(request.flags.get("min_turns", "1"))
        limit = int(request.flags.get("limit", "0"))

        scan = traces.scan_sessions(
            grok_home=grok_home,
            run_dir=run_dir,
            days=days,
            since_last=since_last,
            min_turns=min_turns,
            limit=limit,
        )
        usage = traces.build_usage(grok_home=grok_home, run_dir=run_dir)
        kept = len(scan.records)
        seen = scan.sessions_seen

        return SkillsResult(
            ok=True,
            op=op,
            usage=usage,
            collect_summary=scan,
            message=f"{kept} of {seen} sessions kept → {run_dir}",
        )

    def _traces_materialize(
        self, traces: ISkillsTracesProtocol, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Materialize usage.json + phrases.json into the run dir."""
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        if not run_dir:
            raise SkillsUsageError("traces materialize requires --run-dir")

        usage, report = traces.materialize(grok_home=grok_home, run_dir=run_dir)

        return SkillsResult(
            ok=True,
            op=op,
            usage=usage,
            phrases=report,
            message=f"Materialized usage.json + phrases.json → {run_dir}",
        )

    def _traces_state(
        self, traces: ISkillsTracesProtocol, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Drive the trace-learning lifecycle; the traces capability routes it."""
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        sub_action = request.flags.get("state_action", "")

        result = traces.dispatch(grok_home, run_dir, sub_action, request.flags)
        return SkillsResult(
            ok=True,
            op=op,
            state=result.state,
            state_status=result.state_status,
            lines=result.lines,
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
