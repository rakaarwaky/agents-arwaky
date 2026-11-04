"""Skills traces agent (AES agent layer).

Implements ``ISkillsAggregate`` for the traces feature: a single ``execute``
entry point that routes each trace sub-action to the injected
``ISkillsTracesProtocol`` capability. The agent depends only on contract
protocols and taxonomy; the composition root injects every capability.

This module lives in ``modules/skills_traces/src/`` (capabilities layer's
package tree) but is the agent layer - it imports only contract and
taxonomy from the shared kernel, plus the traces capability from the
capabilities layer. It never imports the surface or root.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.skills_traces.contract_skills_aggregate import ISkillsAggregate
from shared.src.skills_traces.contract_skills_protocol import ISkillsTracesProtocol
from shared.src.skills_traces.taxonomy_skills_error import SkillsError, SkillsUsageError
from shared.src.skills_traces.taxonomy_skills_request import SkillsOp, SkillsRequest
from shared.src.skills_traces.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.skills_traces.taxonomy_skills_vo import (
    GrokHome,
    TraceRunDir,
)


class SkillsAgent(ISkillsAggregate):
    """Dispatches every trace sub-action to the injected traces capability."""

    def __init__(
        self,
        traces: ISkillsTracesProtocol,
        default_root: Path | None = None,
    ) -> None:
        self._traces = traces
        self._default_root = default_root

    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching trace handler."""
        try:
            op = SkillsOp(request.op)
        except ValueError:
            return SkillsResult(
                ok=False,
                op=SkillsOp.LIST,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {request.op}",
            )

        if op != SkillsOp.TRACES:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Skills agent only handles TRACES op, got {op}",
            )

        try:
            return self._handler_for(request, op)
        except SkillsError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Route one TRACES request to its sub-action handler."""
        traces = self._require(self._traces, "traces")
        action = request.flags.get("traces_action", "")
        grok_home = request.flags.get("grok_home", "")
        run_dir = request.flags.get("run_dir", "")

        if action == "collect":
            days = int(request.flags.get("days", "0"))
            since_last = request.flags.get("since_last") == "1"
            min_turns = int(request.flags.get("min_turns", "1"))
            limit = int(request.flags.get("limit", "0"))
            scan = traces.scan_sessions(
                grok_home=GrokHome(grok_home),
                run_dir=TraceRunDir(run_dir),
                days=days,
                since_last=since_last,
                min_turns=min_turns,
                limit=limit,
            )
            usage = traces.build_usage(
                grok_home=GrokHome(grok_home), run_dir=TraceRunDir(run_dir)
            )
            kept = len(scan.records)
            seen = scan.sessions_seen
            return SkillsResult(
                ok=True,
                op=op,
                usage=usage,
                collect_summary=scan,
                message=f"{kept} of {seen} sessions kept → {run_dir}",
            )

        if action == "usage":
            usage = traces.build_usage(
                grok_home=GrokHome(grok_home), run_dir=TraceRunDir(run_dir)
            )
            return SkillsResult(ok=True, op=op, usage=usage)

        if action == "phrases":
            report = traces.build_phrases(
                grok_home=GrokHome(grok_home), run_dir=TraceRunDir(run_dir)
            )
            return SkillsResult(ok=True, op=op, phrases=report)

        if action == "materialize":
            if not run_dir:
                raise SkillsUsageError("traces materialize requires --run-dir")
            usage, phrases = traces.materialize(
                grok_home=GrokHome(grok_home), run_dir=TraceRunDir(run_dir)
            )
            return SkillsResult(
                ok=True,
                op=op,
                usage=usage,
                phrases=phrases,
                message=f"Materialized usage.json + phrases.json → {run_dir}",
            )

        if action == "state":
            return self._traces_state(traces, request, op)

        raise SkillsUsageError(f"Unknown traces action: {action}")

    def _traces_state(
        self, traces: ISkillsTracesProtocol, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """Drive the trace-learning lifecycle; the capability routes sub-actions."""
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

    @staticmethod
    def _require(capability: object, name: str) -> object:
        """Fail loudly when an op is used on an aggregate wired without it."""
        if capability is None:
            raise SkillsUsageError(f"Skills {name} capability is not configured")
        return capability


__all__ = ["SkillsAgent"]
