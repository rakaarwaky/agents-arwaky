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

import json
import os
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import cast

from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.contract_skills_protocol import (
    IPhrasesProtocol,
    ISkillsCatalogProtocol,
    ISkillsDiscovererProtocol,
    ISkillsIndexProtocol,
    ISkillsMergePlannerProtocol,
    ISkillsMutatorProtocol,
    ISkillsReaderProtocol,
    ISkillsRulesRendererProtocol,
    ISkillsValidatorProtocol,
    IStateProtocol,
    ITrackerProtocol,
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
    TraceDecision,
    TraceStateStatus,
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
        tracker: ITrackerProtocol | None = None,
        phrases: IPhrasesProtocol | None = None,
        state: IStateProtocol | None = None,
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
        self._tracker = tracker
        self._phrases = phrases
        self._state = state
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

    def _execute_trace_collect(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Scan sessions then build usage: the collect half of the trace pipeline."""
        tracker = self._require(self._tracker, "tracker")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        days = int(request.flags.get("days", "0"))
        since_last = request.flags.get("since_last") == "1"
        min_turns = int(request.flags.get("min_turns", "1"))
        limit = int(request.flags.get("limit", "0"))

        records = tracker.scan_sessions(
            grok_home=grok_home,
            run_dir=run_dir,
            days=days,
            since_last=since_last,
            min_turns=min_turns,
            limit=limit,
        )
        usage = tracker.build_usage(grok_home=grok_home, run_dir=run_dir)
        kept = len(records)
        seen = 0
        try:
            with open(os.path.join(run_dir, "manifest.json"), encoding="utf-8") as f:
                seen = int(json.load(f).get("sessions_seen", 0))
        except (OSError, ValueError):
            seen = kept

        return SkillsResult(
            ok=True,
            op=op,
            usage=usage,
            message=f"{kept} of {seen} sessions kept → {run_dir}",
            root=Path(run_dir) if run_dir else None,
        )

    def _execute_trace_usage(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Read the last run's usage report from the tracker."""
        tracker = self._require(self._tracker, "tracker")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        usage = tracker.build_usage(grok_home=grok_home, run_dir=run_dir)
        return SkillsResult(ok=True, op=op, usage=usage)

    def _execute_trace_phrases(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Mine repeated prompts and instruction lines from the session records."""
        phrases = self._require(self._phrases, "phrases")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        report = phrases.build_phrases(grok_home=grok_home, run_dir=run_dir)
        return SkillsResult(ok=True, op=op, phrases=report)

    def _execute_trace_state(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """Drive the trace-learning lifecycle: set/get/clear/trash/restrict/decide/wait."""
        state = self._require(self._state, "state")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")
        action = request.flags.get("state_action", "")

        if action == "set":
            status = TraceStateStatus(request.flags.get("status", "collected"))
            got = state.set_status(grok_home, run_dir, status)
            return SkillsResult(ok=True, op=op, state=got)

        if action == "get":
            got, _view = state.get_status(grok_home)
            return SkillsResult(ok=True, op=op, state=got)

        if action == "clear":
            state.set_status(grok_home, run_dir, TraceStateStatus.DONE)
            return SkillsResult(ok=True, op=op, state=TraceStateStatus.DONE)

        if action == "trash":
            run_name = request.flags.get("run_name", "")
            paths = [
                p.strip()
                for p in request.flags.get("trash_paths", "").split(",")
                if p.strip()
            ]
            moved = state.trash(grok_home, run_name, paths)
            return SkillsResult(ok=True, op=op, lines=moved)

        if action == "restrict":
            paths = [
                p.strip()
                for p in request.flags.get("restrict_paths", "").split(",")
                if p.strip()
            ]
            restricted = state.restrict(paths)
            return SkillsResult(ok=True, op=op, lines=restricted)

        if action == "decide":
            decision = TraceDecision(
                date=request.flags.get("date", ""),
                run_dir=run_dir,
                decision_id=request.flags.get("id", ""),
                kind=request.flags.get("kind", ""),
                action=request.flags.get("decide_action", ""),
                target=request.flags.get("target", ""),
                target_path=request.flags.get("path", ""),
                decision=request.flags.get("decision", ""),
                undo=request.flags.get("undo") or None,
            )
            got = state.decide(grok_home, run_dir, decision)
            return SkillsResult(ok=True, op=op, lines=(json.dumps(got.as_dict(), ensure_ascii=False),))

        if action == "wait":
            timeout_min = int(request.flags.get("timeout_min", "90"))
            got = state.wait(grok_home, run_dir, timeout_min=timeout_min)
            return SkillsResult(ok=True, op=op, state_status=got)

        raise SkillsUsageError(f"Unknown trace-state action: {action}")

        raise SkillsUsageError(f"Unknown trace-state action: {action}")

    # ─── Block 3: Helpers, Factories & Read Helpers ────────────
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
        """Convenience pass-through to the index (used by the facade)."""
        return self._index.list_skills(root)

    def show_skill(
        self, name: str, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Convenience pass-through to the reader (used by the facade)."""
        return self._reader.show_skill(SkillQuery(name), root)
