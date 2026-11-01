"""Skills trace-state capability (AES capabilities layer).

Ports the status machine, trash guard, decide log, wait logic, and restrict
out of the retired ``skills/skill-authoring/_trace-pipeline/scripts/state.py``
into the ``IStateProtocol`` seam.

Status machine (over ``GROK_HOME/learn/state.json``): collected → running →
report_ready → curating → done. Writes are atomic (tmp + ``os.replace``);
``done`` stamps ``last_completed_at`` / ``last_completed_dir``. The
capability returns the resulting status; the surface maps pending → exit 3.

Trash: path-shape guard VERBATIM — only a ``skills/<name>`` directory, a
``workflows/*.rhai`` file, or a ``hooks/*`` file under GROK_HOME /
``~/.agents`` / project ``.grok`` is moved into ``learn/trash/<run_name>``;
any other shape is refused.

Decide: appends one line to ``learn/decisions.jsonl`` in the legacy key order
(``TraceDecision.as_dict()`` pins it).

Wait: blocks until ``report.md`` + ``actions.json`` exist under the run dir;
phase-stall (no file change) / report-stall (verifiers finished, no report) /
deadline timeouts, with exit-code semantics (0 ready / 3 report-stall / 4
phase-stall / 2 deadline).

Restrict: chmod 0600 where the OS supports it.

No capability-to-capability imports: depends only on ``modules.shared``
contract + taxonomy. I/O is limited to ``GROK_HOME/learn`` and the run dir.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import stat
import time
from collections.abc import Callable, Mapping, Sequence
from typing import ClassVar

from modules.shared.src.skills.contract_skills_protocol import IStateProtocol
from modules.shared.src.skills.taxonomy_skills_error import SkillsUsageError
from modules.shared.src.skills.taxonomy_skills_vo import (
    TraceDecision,
    TraceStateDispatchResult,
    TraceStateStatus,
)

__all__ = [
    "STATUSES",
    "SkillsTraceState",
    "files_ready",
    "latest_synthesis",
    "load_state",
    "mark",
    "newest_mtime",
    "save_state",
    "state_path",
]

STATUSES = (
    TraceStateStatus.COLLECTED,
    TraceStateStatus.RUNNING,
    TraceStateStatus.REPORT_READY,
    TraceStateStatus.CURATING,
    TraceStateStatus.DONE,
)

# map user-facing status strings to enum members (reverse of StrEnum values)
_STATUS_BY_VALUE = {s.value: s for s in STATUSES}


def state_path(grok_home: str) -> str:
    return os.path.join(grok_home, "learn", "state.json")


def decisions_path(grok_home: str) -> str:
    return os.path.join(grok_home, "learn", "decisions.jsonl")


def load_state(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(path: str, state: dict) -> None:
    """Atomic write: tmp file then ``os.replace``."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, path)


def mark(
    path: str,
    run_dir: str,
    status: TraceStateStatus | str,
    extra: dict | None = None,
) -> dict:
    """Record ``status`` for ``run_dir`` as the pending run and save.

    ``done`` also stamps ``last_completed_at`` / ``last_completed_dir``.
    """
    status_enum = (
        status if isinstance(status, TraceStateStatus) else _STATUS_BY_VALUE[status]
    )
    state = load_state(path)
    now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    pending = state.get("pending") or {}
    if pending.get("run_dir") != run_dir:
        pending = {"run_dir": run_dir, "started_at": now}
    pending["status"] = status_enum.value
    pending["updated_at"] = now
    pending["report_ready"] = files_ready(run_dir)
    for k, v in (extra or {}).items():
        if v:
            pending[k] = v
    if status_enum is TraceStateStatus.DONE:
        state["last_completed_at"] = now
        state["last_completed_dir"] = run_dir
    state["pending"] = pending
    save_state(path, state)
    return state


def files_ready(run_dir: str) -> bool:
    return bool(run_dir) and os.path.isfile(
        os.path.join(run_dir, "report.md")
    ) and os.path.isfile(os.path.join(run_dir, "actions.json"))


def newest_mtime(run_dir: str) -> float:
    """Latest mtime of any file under the run dir (0 if none) — the heartbeat."""
    newest = 0.0
    for root, _dirs, files in os.walk(run_dir):
        for f in files:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(root, f)))
            except OSError:
                pass
    return newest


def latest_synthesis(run_dir: str) -> str | None:
    """Newest reducer output; best available result when report.md never appears."""
    d = os.path.join(run_dir, "reduce")
    if not os.path.isdir(d):
        return None
    files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".md")]
    return max(files, key=os.path.getmtime) if files else None


class SkillsTraceState(IStateProtocol):
    """Drive the trace-learning lifecycle (status machine, trash, decisions)."""

    # ── IStateProtocol ──────────────────────────────────────────

    def set_status(
        self,
        grok_home: str,
        run_dir: str,
        status: TraceStateStatus,
    ) -> TraceStateStatus:
        """Record ``status`` for the pending run; ``done`` stamps last_completed."""
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        path = state_path(grok_home)
        result = mark(path, run_dir, status)
        pending = result.get("pending") or {}
        return TraceStateStatus(pending["status"])

    def get_status(self, grok_home: str) -> TraceStateStatus:
        """Return the current pending status.

        ``done``-less pending runs exit 3 (the surface maps to exit 3); the
        capability returns the status, the caller maps it to an exit code.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        path = state_path(grok_home)
        state = load_state(path)
        pending = state.get("pending") or {}
        if (
            pending.get("status")
            in (TraceStateStatus.COLLECTED.value, TraceStateStatus.RUNNING.value)
            and files_ready(pending.get("run_dir") or "")
        ):
            state = mark(path, pending["run_dir"], TraceStateStatus.REPORT_READY)
            pending = state.get("pending") or {}
        return TraceStateStatus(pending.get("status") or "done")

    def trash(
        self,
        grok_home: str,
        run_name: str,
        paths: Sequence[str],
    ) -> tuple[str, ...]:
        """Move the validated paths into ``learn/trash/<run_name>``.

        Only a ``skills/<name>`` directory, a ``workflows/*.rhai`` file, or a
        ``hooks/*`` file under GROK_HOME / ``~/.agents`` / project ``.grok``
        is moved; anything else is refused (exit 2 equivalent).
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        # the run name is one directory component under learn/trash; anything
        # else lands somewhere unintended
        if run_name in ("", ".", "..") or os.path.basename(run_name) != run_name:
            raise ValueError("run-name must be a single path component")
        dest_dir = os.path.join(grok_home, "learn", "trash", run_name)
        # only these shapes are ever deleted by the skill: a skill directory,
        # a workflow file, a hook file, under GROK_HOME, ~/.agents, or a
        # project .grok directory. Sessions, config, and roots never move.
        home_real = os.path.realpath(grok_home)
        agents_real = os.path.realpath(os.path.expanduser("~/.agents"))
        moved: list[str] = []
        validated: list[str] = []
        for src in paths:
            src = os.path.abspath(os.path.expanduser(src))
            real = os.path.realpath(src)
            if not os.path.exists(src):
                raise FileNotFoundError(f"missing: {src}")
            parent = os.path.dirname(real)
            kind = os.path.basename(parent)
            grand = os.path.dirname(parent)
            is_skill_dir = (
                os.path.isdir(real)
                and kind == "skills"
                and (grand in (home_real, agents_real) or grand.endswith(os.sep + ".grok"))
            )
            is_workflow = (
                os.path.isfile(real)
                and real.endswith(".rhai")
                and kind == "workflows"
                and (grand == home_real or grand.endswith(os.sep + ".grok"))
            )
            is_hook = (
                os.path.isfile(real)
                and kind == "hooks"
                and (grand == home_real or grand.endswith(os.sep + ".grok"))
            )
            if not (is_skill_dir or is_workflow or is_hook):
                raise ValueError(
                    "refusing: only a skills/<name> directory, a workflows/*.rhai "
                    "file, or a hooks/* file under GROK_HOME, ~/.agents, or a "
                    "project .grok directory can be trashed"
                )
            validated.append(src)
        os.makedirs(dest_dir, exist_ok=True)
        for src in validated:
            dest = os.path.join(dest_dir, os.path.basename(src.rstrip("\\/")))
            if os.path.exists(dest):
                dest += "-" + dt.datetime.now(dt.UTC).strftime("%H%M%S")
            shutil.move(src, dest)
            moved.append(dest)
        return tuple(moved)

    def decide(
        self,
        grok_home: str,
        run_dir: str,
        decision: TraceDecision,
    ) -> TraceDecision:
        """Append one decision line to ``learn/decisions.jsonl`` and return it.

        The line is emitted in the legacy key order pinned by
        ``TraceDecision.as_dict()``.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        dec_path = decisions_path(grok_home)
        os.makedirs(os.path.dirname(dec_path), exist_ok=True)
        line = decision.as_dict()
        with open(dec_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        return decision

    def wait(
        self,
        grok_home: str,
        run_dir: str,
        timeout_min: int = 90,
        phase_stall_min: int = 60,
        report_stall_min: int = 45,
    ) -> TraceStateStatus:
        """Block until the run dir holds ``report.md`` + ``actions.json``.

        Returns a distinct ``TraceStateStatus`` per outcome so the surface can
        map exit codes explicitly: ``REPORT_READY`` (0), ``REPORT_STALL`` (3),
        ``PHASE_STALL`` (4), ``DEADLINE`` (2). No exit-code logic lives in the
        capability.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        path = state_path(grok_home)
        deadline = time.time() + timeout_min * 60
        report = os.path.join(run_dir, "report.md")
        actions = os.path.join(run_dir, "actions.json")
        verify_dir = os.path.join(run_dir, "verify")
        last_phase: str | None = None
        verify_done_at: float | None = None
        last_progress = (newest_mtime(run_dir), time.time())
        while time.time() < deadline:
            if os.path.isfile(report) and os.path.isfile(actions):
                mark(path, run_dir, TraceStateStatus.REPORT_READY)
                return TraceStateStatus.REPORT_READY
            phase = next(
                (
                    p
                    for p in ("verify", "reduce")
                    if os.path.isdir(os.path.join(run_dir, p))
                    and os.listdir(os.path.join(run_dir, p))
                ),
                None,
            )
            if phase is None:
                # mappers write map*.md at the run root, not under map/
                phase = (
                    "map"
                    if any(
                        f.startswith("map") and f.endswith(".md")
                        for f in os.listdir(run_dir)
                    )
                    else TraceStateStatus.COLLECTED.value
                )
            if phase != last_phase:
                last_phase = phase
            newest = newest_mtime(run_dir)
            if newest > last_progress[0]:
                last_progress = (newest, time.time())
            elif time.time() - last_progress[1] > phase_stall_min * 60:
                mark(
                    path,
                    run_dir,
                    TraceStateStatus.RUNNING,
                    {
                        "note": (
                            f"no file changed under the run dir for {phase_stall_min} min"
                        )
                    },
                )
                return TraceStateStatus.PHASE_STALL
            verdicts = [
                f
                for f in ("phrases.md", "stale.md", "deletes.md")
                if os.path.isfile(os.path.join(verify_dir, f))
            ]
            if len(verdicts) == 3:
                verify_done_at = verify_done_at or time.time()
                if time.time() - verify_done_at > report_stall_min * 60:
                    mark(
                        path,
                        run_dir,
                        TraceStateStatus.RUNNING,
                        {
                            "note": (
                                f"verifiers finished; no report.md after "
                                f"{report_stall_min} min"
                            )
                        },
                    )
                    return TraceStateStatus.REPORT_STALL
            time.sleep(30)
        mark(path, run_dir, TraceStateStatus.RUNNING, {"note": "deadline exceeded"})
        return TraceStateStatus.DEADLINE

    def restrict(self, paths: Sequence[str]) -> tuple[str, ...]:
        """chmod 0600 where the OS supports it; silently skip what it cannot."""
        restricted: list[str] = []
        for p in paths:
            try:
                os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
                restricted.append(p)
            except OSError:
                pass
        return tuple(restricted)

    # ── dispatch: one router call instead of seven branches upstream ──

    @staticmethod
    def _split_paths(flag_value: str) -> tuple[str, ...]:
        return tuple(p.strip() for p in flag_value.split(",") if p.strip())

    # ── sub-action handlers ──────────────────────────────────────

    def _do_set(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        status = TraceStateStatus(flags.get("status", "collected"))
        got = self.set_status(grok_home, run_dir, status)
        return TraceStateDispatchResult(state=got)

    def _do_get(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        got = self.get_status(grok_home)
        return TraceStateDispatchResult(state=got)

    def _do_clear(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        self.set_status(grok_home, run_dir, TraceStateStatus.DONE)
        return TraceStateDispatchResult(state=TraceStateStatus.DONE)

    def _do_trash(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        run_name = flags.get("run_name", "")
        moved = self.trash(grok_home, run_name, self._split_paths(flags.get("trash_paths", "")))
        return TraceStateDispatchResult(lines=moved)

    def _do_restrict(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        restricted = self.restrict(self._split_paths(flags.get("restrict_paths", "")))
        return TraceStateDispatchResult(lines=restricted)

    def _do_decide(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        decision = TraceDecision(
            date=flags.get("date", ""),
            run_dir=run_dir,
            decision_id=flags.get("id", ""),
            kind=flags.get("kind", ""),
            action=flags.get("decide_action", ""),
            target=flags.get("target", ""),
            target_path=flags.get("path", ""),
            decision=flags.get("decision", ""),
            undo=flags.get("undo") or None,
        )
        got = self.decide(grok_home, run_dir, decision)
        return TraceStateDispatchResult(lines=(json.dumps(got.as_dict(), ensure_ascii=False),))

    def _do_wait(self, grok_home: str, run_dir: str, flags: Mapping[str, str]) -> TraceStateDispatchResult:
        timeout_min = int(flags.get("timeout_min", "90"))
        got = self.wait(grok_home, run_dir, timeout_min=timeout_min)
        return TraceStateDispatchResult(state_status=got)

    # ── router ───────────────────────────────────────────────────

    _DISPATCH: ClassVar[dict[str, Callable[..., TraceStateDispatchResult]]] = {
        "set": lambda self, g, r, f: self._do_set(g, r, f),
        "get": lambda self, g, r, f: self._do_get(g, r, f),
        "clear": lambda self, g, r, f: self._do_clear(g, r, f),
        "trash": lambda self, g, r, f: self._do_trash(g, r, f),
        "restrict": lambda self, g, r, f: self._do_restrict(g, r, f),
        "decide": lambda self, g, r, f: self._do_decide(g, r, f),
        "wait": lambda self, g, r, f: self._do_wait(g, r, f),
    }

    def dispatch(
        self,
        grok_home: str,
        run_dir: str,
        action: str,
        flags: Mapping[str, str],
    ) -> TraceStateDispatchResult:
        """Route one trace-state sub-action; the thin router the agent calls.

        Dispatches via a class-level dict so each sub-action is individually
        testable. Unknown actions raise ``SkillsUsageError`` (exit 2).
        """
        handler = self._DISPATCH.get(action)
        if handler is None:
            raise SkillsUsageError(f"Unknown trace-state action: {action}")
        return handler(self, grok_home, run_dir, flags)
