"""Phrase agent (AES agent layer, self-contained in ``app``).

Implements ``ISkillsTracesAggregate`` over the phrase scan capability:
scan sessions and mine repeated phrases. Owns the op ``traces``
(phrases sub-action carried in ``flags``). The agent is the only layer
allowed to sequence capabilities. No import of ``skill-traces``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import tempfile

from shared.src.traces.contract_traces_aggregate import ISkillsTracesAggregate
from shared.src.traces.contract_traces_protocol import ISkillsTracesProtocol
from shared.src.common.taxonomy_common_error import SkillsError
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.traces.taxonomy_traces_response import (
    SkillsExitCode,
    SkillsResult,
)

from observability.src.capabilities_skills_phrase_scan import SkillsPhraseScan

__all__ = ["SkillsPhraseAgent", "ISkillsTracesAggregate"]


class SkillsPhraseAgent(ISkillsTracesAggregate):
    """Phrase-side agent: scan sessions and mine repeated phrases."""

    def __init__(
        self,
        scan: ISkillsTracesProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._scan = scan if scan is not None else SkillsPhraseScan()
        self._default_root = default_root

    # ─── Block 1: helpers ────────────────────────────────────────
    def _root(self, request: SkillsRequest) -> Path:
        if request.root:
            return Path(request.root)
        if self._default_root is not None:
            return Path(self._default_root)
        return Path()

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching trace handler."""
        try:
            op = SkillsOp(request.op)
        except ValueError:
            return SkillsResult(
                ok=False,
                op=SkillsOp.LIST,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown traces op: {request.op}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown traces op: {op}",
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
        return handler

    # ─── Block 3: per-op handlers ────────────────────────────────
    def _execute_traces(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """TRACES: route on ``flags['traces_action']`` (only 'phrases' today)."""
        traces_action = request.flags.get("traces_action", "")
        if traces_action != "phrases":
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown traces action: {traces_action or '(none)'}",
            )
        return self._execute_phrases(request, op)

    def _execute_phrases(
        self, request: SkillsRequest, op: SkillsOp
    ) -> SkillsResult:
        """PHRASES: mine repeated prompts from session traces."""
        scan = self._scan
        grok_home = request.flags.get("grok_home", "") or str(Path.home() / ".grok")
        run_dir = request.flags.get("run_dir", "") or ""
        if not run_dir:
            run_dir = tempfile.mkdtemp(prefix="sac-phrases-")
            request.flags["run_dir"] = run_dir

        # Scan sessions first (builds session records in run_dir).
        scan_result = scan.scan_sessions(
            grok_home,
            run_dir,
            days=int(request.flags.get("days", "0")),
            since_last=request.flags.get("since_last", "0") == "1",
            min_turns=int(request.flags.get("min_turns", "1")),
            limit=int(request.flags.get("limit", "0")),
        )

        # Mine repeated phrases from the records written to run_dir.
        report = scan.build_phrases(
            grok_home,
            run_dir,
            min_sessions=int(request.flags.get("min_sessions", "2")),
        )

        return SkillsResult(
            ok=True,
            op=op,
            exit_code=SkillsExitCode.CLEAN,
            message=f"Phrases mined → {run_dir}",
            phrases_exact=report.exact_prompts,
            phrases_stems=report.stems,
            phrases_lines=report.repeated_instruction_lines,
            scan_summary=scan_result,
            root=self._root(request),
        )