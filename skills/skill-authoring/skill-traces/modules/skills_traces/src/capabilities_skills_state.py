"""Skills traces state capability (AES capabilities layer).

Implements ISkillsTraceStateProtocol: the trace-learning lifecycle state
machine (status, trash, decisions, wait, restrict, dispatch). Delegates all
I/O to the shared helpers in utility_skills_trace_state. Never imports the
scan capability.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence

from shared.src.skills_traces.contract_skills_protocol import ISkillsTraceStateProtocol
from shared.src.skills_traces.taxonomy_skills_vo import (
    TraceDecision,
    TraceRunDir,
    TraceRunName,
    TraceStateDispatchResult,
    TraceStateStatus,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    decisions_path,
    files_ready,
    load_state,
    mark,
    state_path,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    dispatch as _state_dispatch,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    restrict as _restrict,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    trash as _trash,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    wait as _wait,
)

__all__ = ["SkillsTracesState"]


# ─── Block 1: Class Definition & Constructor ──────────────


class SkillsTracesState(ISkillsTraceStateProtocol):
    """Trace-learning lifecycle: status machine, trash, decisions, wait, restrict, dispatch."""

    # ─── Block 2: Protocol Method Implementation ──────────────
    def set_status(
        self,
        grok_home: TraceRunDir | str,
        run_dir: TraceRunDir,
        status: TraceStateStatus,
    ) -> TraceStateStatus:
        """Record ``status`` for the pending run; ``done`` stamps last_completed."""
        state = mark(state_path(grok_home), run_dir, status)
        return TraceStateStatus(state.get("pending", {}).get("status", status.value))

    def get_status(self, grok_home: TraceRunDir | str) -> TraceStateStatus:
        """Return the current pending status."""
        state = load_state(state_path(grok_home))
        pending = state.get("pending") or {}
        if (
            pending.get("status")
            in (TraceStateStatus.COLLECTED.value, TraceStateStatus.RUNNING.value)
            and files_ready(pending.get("run_dir") or "")
        ):
            state = mark(state_path(grok_home), pending["run_dir"], TraceStateStatus.REPORT_READY)
            pending = state.get("pending") or {}
        return TraceStateStatus(pending.get("status") or TraceStateStatus.DONE.value)

    def trash(
        self,
        grok_home: TraceRunDir | str,
        run_name: TraceRunName,
        paths: Sequence[str],
    ) -> tuple[str, ...]:
        """Move the validated paths into ``learn/trash/<run_name>``."""
        return _trash(grok_home, run_name, list(paths))

    def decide(
        self,
        grok_home: TraceRunDir | str,
        run_dir: TraceRunDir,
        decision: TraceDecision,
    ) -> TraceDecision:
        """Append one decision line to ``learn/decisions.jsonl`` and return it."""
        dec_path = decisions_path(grok_home)
        os.makedirs(os.path.dirname(dec_path), exist_ok=True)
        line = decision.as_dict()
        with open(dec_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        return decision

    def wait(
        self,
        grok_home: TraceRunDir | str,
        run_dir: TraceRunDir,
        timeout_min: int = 90,
        phase_stall_min: int = 60,
        report_stall_min: int = 45,
    ) -> TraceStateStatus:
        """Block until the run dir holds ``report.md`` + ``actions.json``."""
        return _wait(grok_home, run_dir, timeout_min=timeout_min)

    def restrict(self, paths: Sequence[str]) -> tuple[str, ...]:
        """chmod 0600 where the OS supports it; silently skip what it cannot."""
        return _restrict(list(paths))

    def dispatch(
        self,
        grok_home: str,
        run_dir: str,
        action: str,
        flags: Mapping[str, str],
    ) -> TraceStateDispatchResult:
        """Route one trace-state sub-action through the shared helper."""
        return _state_dispatch(grok_home, run_dir, action, dict(flags))


# ─── Block 3: Dunder Methods, Factories & Helpers ─────────
