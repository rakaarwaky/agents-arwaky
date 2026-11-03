"""Trace-state lifecycle helpers (shared kernel).

Ported from the retired
``skills/skill-authoring/_trace-pipeline/scripts/state.py``. These are the
I/O-bound state helpers that drive the trace-learning lifecycle
(status machine, trash guard, decide log, wait, restrict). They are
consumed by ``capabilities_skills_traces.SkillsTraces`` so the traces
capability stays under the AES301 line cap and focuses on scan /
usage / phrases.

Status machine (over ``GROK_HOME/learn/state.json``): collected →
running → report_ready → curating → done. Writes are atomic (tmp +
``os.replace``); ``done`` stamps ``last_completed_at`` /
``last_completed_dir``.

Trash: path-shape guard verbatim — only a ``skills/<name>`` directory,
a ``workflows/*.rhai`` file, or a ``hooks/*`` file under GROK_HOME /
``~/.agents`` / project ``.grok`` is moved into
``learn/trash/<run_name>``; anything else is refused.

Decide: appends one line to ``learn/decisions.jsonl`` in the legacy key
order pinned by ``TraceDecision.as_dict()``.

Wait: blocks until ``report.md`` + ``actions.json`` exist under the run
dir; phase-stall / report-stall / deadline timeouts with distinct status
returns (no exit-code logic here).

Restrict: chmod 0600 where the OS supports it.

Depends only on ``modules.shared`` (standard library + taxonomy VOs).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import stat
import time

from modules.shared.src.skills.taxonomy_skills_error import SkillsUsageError
from modules.shared.src.skills.taxonomy_skills_vo import (
    TraceDecision,
    TraceStateDispatchResult,
    TraceStateStatus,
)

__all__ = [
    "SECRET_RES",
    "STATUSES",
    "TURN_CAP",
    "decisions_path",
    "dispatch",
    "files_ready",
    "latest_synthesis",
    "load_state",
    "mark",
    "newest_mtime",
    "normalize",
    "redact",
    "restrict",
    "save_state",
    "state_path",
]

TURN_CAP = 2000
"""Max characters kept per human prompt (longer prompts are truncated)."""

STATUSES = (
    TraceStateStatus.COLLECTED,
    TraceStateStatus.RUNNING,
    TraceStateStatus.REPORT_READY,
    TraceStateStatus.CURATING,
    TraceStateStatus.DONE,
)

_STATUS_BY_VALUE = {s.value: s for s in STATUSES}


# ─── lifecycle paths ─────────────────────────────────────────────


def state_path(grok_home: str) -> str:
    return os.path.join(grok_home, "learn", "state.json")


def decisions_path(grok_home: str) -> str:
    return os.path.join(grok_home, "learn", "decisions.jsonl")


# ─── state read / write ──────────────────────────────────────────


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


# ─── secrets redaction ───────────────────────────────────────────


SECRET_RES = [
    # prefixed keys: sk-…, sk-proj-…, ghp_…, xai-…; hyphens allowed inside but at
    # least three digits, so package names stay
    re.compile(
        r"\b(xai|sk|ghp|gho|ghu|ghs|glpat|npm)[-_](?=(?:[A-Za-z_\-]*\d){3})[A-Za-z0-9_\-]{16,}\b"
    ),
    re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[abpsr]-\d[A-Za-z0-9-]{20,}\b"),
    re.compile(
        r"\b[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\b"
    ),  # JWT
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-./+=]{20,}"),
    re.compile(
        r"(?i)\b(token|api[_-]?key|secret|password|passwd)\b\s*[:=]\s*['\"]?(?=[A-Za-z0-9_\-./+=]*\d)[A-Za-z0-9_\-./+=]{16,}"
    ),
    re.compile(r"\b[a-f0-9]{64,}\b"),
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY.*?-----END [A-Z ]*PRIVATE KEY", re.DOTALL
    ),  # PEM key blocks
    re.compile(r'"private_key"\s*:\s*"[^"]{16,}"'),  # JSON-shaped pasted keys
]

_SLASH_ONLY = None  # not used by state helpers; lives in the traces capability
_WORD_RE = None  # normalize helper lives in the traces capability


def redact(text: str) -> str:
    """Redact secrets verbatim from the retired collector (security-critical)."""
    for rx in SECRET_RES:
        text = rx.sub(lambda m: m.group(0)[:8] + "…[redacted]", text)
    return text


def normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


# ─── trash / restrict / wait lifecycle methods ───────────────────


def _grand_ok(grand: str, home_real: str) -> bool:
    home_parts = (os.path.expanduser("~"), os.path.expanduser("~/.agents"))
    return (
        grand in home_parts
        or grand == home_real
        or grand.endswith(os.sep + ".grok")
    )


def trash(
    grok_home: str,
    run_name: str,
    paths: list[str],
) -> tuple[str, ...]:
    """Move the validated paths into ``learn/trash/<run_name>``.

    Only a ``skills/<name>`` directory, a ``workflows/*.rhai`` file, or a
    ``hooks/*`` file under GROK_HOME / ``~/.agents`` / project ``.grok``
    is moved; anything else is refused.
    """
    grok_home = os.path.abspath(os.path.expanduser(grok_home))
    if run_name in ("", ".", "..") or os.path.basename(run_name) != run_name:
        raise ValueError("run-name must be a single path component")
    dest_dir = os.path.join(grok_home, "learn", "trash", run_name)
    home_real = os.path.realpath(grok_home)
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
            and _grand_ok(grand, home_real)
        )
        is_workflow = (
            os.path.isfile(real)
            and real.endswith(".rhai")
            and kind == "workflows"
            and _grand_ok(grand, home_real)
        )
        is_hook = (
            os.path.isfile(real)
            and kind == "hooks"
            and _grand_ok(grand, home_real)
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


def restrict(paths: list[str]) -> tuple[str, ...]:
    """chmod 0600 where the OS supports it; silently skip what it cannot."""
    restricted: list[str] = []
    for p in paths:
        try:
            os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
            restricted.append(p)
        except OSError:
            pass
    return tuple(restricted)


def wait(
    grok_home: str,
    run_dir: str,
    timeout_min: int = 90,
    phase_stall_min: int = 60,
    report_stall_min: int = 45,
) -> TraceStateStatus:
    """Block until the run dir holds ``report.md`` + ``actions.json``.

    Returns a distinct ``TraceStateStatus`` per outcome so the surface can
    map exit codes explicitly: ``REPORT_READY`` (0), ``REPORT_STALL`` (3),
    ``PHASE_STALL`` (4), ``DEADLINE`` (2). No exit-code logic lives here.
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


def dispatch(
    grok_home: str,
    run_dir: str,
    action: str,
    flags: dict[str, str],
) -> TraceStateDispatchResult:
    """Route one trace-state sub-action through these helpers.

    Handlers: set / get / clear / trash / restrict / decide / wait.
    Unknown actions raise ``SkillsUsageError`` (exit 2).
    """
    grok_home = os.path.abspath(os.path.expanduser(grok_home))
    if action == "set":
        status = TraceStateStatus(flags.get("status", "collected"))
        got = mark(state_path(grok_home), run_dir, status)
        pending = got.get("pending") or {}
        return TraceStateDispatchResult(state=TraceStateStatus(pending["status"]))

    if action == "get":
        state = load_state(state_path(grok_home))
        pending = state.get("pending") or {}
        if (
            pending.get("status")
            in (TraceStateStatus.COLLECTED.value, TraceStateStatus.RUNNING.value)
            and files_ready(pending.get("run_dir") or "")
        ):
            state = mark(
                state_path(grok_home), pending["run_dir"], TraceStateStatus.REPORT_READY
            )
            pending = state.get("pending") or {}
        return TraceStateDispatchResult(state=TraceStateStatus(pending.get("status") or "done"))

    if action == "clear":
        mark(state_path(grok_home), run_dir, TraceStateStatus.DONE)
        return TraceStateDispatchResult(state=TraceStateStatus.DONE)

    if action == "trash":
        run_name = flags.get("run_name", "")
        moved = trash(grok_home, run_name, _split_paths(flags.get("trash_paths", "")))
        return TraceStateDispatchResult(lines=moved)

    if action == "restrict":
        restricted = restrict(_split_paths(flags.get("restrict_paths", "")))
        return TraceStateDispatchResult(lines=restricted)

    if action == "decide":
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
        dec_path = decisions_path(grok_home)
        os.makedirs(os.path.dirname(dec_path), exist_ok=True)
        line = decision.as_dict()
        with open(dec_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        return TraceStateDispatchResult(lines=(json.dumps(line, ensure_ascii=False),))

    if action == "wait":
        timeout_min = int(flags.get("timeout_min", "90"))
        got = wait(grok_home, run_dir, timeout_min=timeout_min)
        return TraceStateDispatchResult(state_status=got)

    raise SkillsUsageError(f"Unknown trace-state action: {action}")


def _split_paths(flag_value: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in flag_value.split(",") if p.strip())
