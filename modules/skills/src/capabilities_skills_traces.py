"""Skills traces capability (AES capabilities layer).

Ports the session-scanning / redaction / usage-building logic from
``capabilities_skills_tracker.py`` and the repeated-prompt /
repeated-instruction-line mining logic from
``capabilities_skills_phrases.py`` into the single
``ISkillsTracesProtocol`` seam.

The phrases half depends on the scan half through run-dir files only
(the tracker writes ``manifest.json`` + ``sessions/*.json``; phrases
reads them back) — there is no capability-to-capability import between
them here.

The trace-state lifecycle (status machine, trash guard, decide log,
wait, restrict) is ported from the retired
``skills/skill-authoring/_trace-pipeline/scripts/state.py`` and lives
in this same capability so the whole pipeline is one class behind
one protocol.

Status machine (over ``GROK_HOME/learn/state.json``): collected →
running → report_ready → curating → done. Writes are atomic (tmp +
``os.replace``); ``done`` stamps ``last_completed_at`` /
``last_completed_dir``. The capability returns the resulting status;
the surface maps pending → exit 3.

Trash: path-shape guard VERBATIM — only a ``skills/<name>`` directory,
a ``workflows/*.rhai`` file, or a ``hooks/*`` file under GROK_HOME /
``~/.agents`` / project ``.grok`` is moved into
``learn/trash/<run_name>``; any other shape is refused.

Decide: appends one line to ``learn/decisions.jsonl`` in the legacy key
order (``TraceDecision.as_dict()`` pins it).

Wait: blocks until ``report.md`` + ``actions.json`` exist under the run
dir; phase-stall (no file change) / report-stall (verifiers finished,
no report) / deadline timeouts, with exit-code semantics (0 ready / 3
report-stall / 4 phase-stall / 2 deadline).

Restrict: chmod 0600 where the OS supports it.

No capability-to-capability imports: depends only on ``modules.shared``
contract + taxonomy. I/O is limited to ``GROK_HOME/learn`` and the run
dir.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import stat
import time
import urllib.parse
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from modules.shared.src.common.utility_skill_pack import (
    SLASH_RE,
    WORD_RE,
    parse_skill_frontmatter,
)
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsTracesProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    PhrasesReport,
    UsageReport,
)
from modules.shared.src.skills.taxonomy_skills_error import SkillsUsageError
from modules.shared.src.skills.taxonomy_skills_vo import (
    PhraseRow,
    ScanResult,
    SkillUsageItem,
    TraceDecision,
    TraceSessionRecord,
    TraceStateDispatchResult,
    TraceStateStatus,
)

__all__ = [
    "SECRET_RES",
    "STATUSES",
    "TURN_CAP",
    "SkillsTraces",
    "files_ready",
    "latest_synthesis",
    "load_state",
    "mark",
    "newest_mtime",
    "normalize",
    "redact",
    "save_state",
    "state_path",
]

TURN_CAP = 2000
"""Max characters kept per human prompt (longer prompts are truncated)."""

USER_QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
SUBAGENT_KINDS = {"subagent", "subagent_resume", "subagent_fork"}
DEFAULT_EXCLUDE_SUBSTR = ["grok-e2e"]
SKILL_PATH_RE = re.compile(r"[/\\]skills[/\\]([^/\\]+)[/\\]SKILL\.md$")
# a slash command, not a path segment (~/x, ./x, a/b) and not followed by more path
DEFAULT_DROP_PATTERNS = [r"^the user invoked `/feedback`"]

# ── trace-state lifecycle constants ──────────────────────────────────

STATUSES = (
    TraceStateStatus.COLLECTED,
    TraceStateStatus.RUNNING,
    TraceStateStatus.REPORT_READY,
    TraceStateStatus.CURATING,
    TraceStateStatus.DONE,
)

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

# pasted credentials must not be copied into the run directory
# a credential is one unbroken run of letters and digits with digits in it;
# hyphenated words (npm-package-for-widgets, sk-learn-utils) and 40-hex git SHAs
# are not credentials
SECRET_RES = [
    # prefixed keys: sk-…, sk-proj-…, ghp_…, xai-…; hyphens allowed inside but at
    # least three digits, so package names stay
    re.compile(r"\b(xai|sk|ghp|gho|ghu|ghs|glpat|npm)[-_](?=(?:[A-Za-z_\-]*\d){3})[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[abpsr]-\d[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\b[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\b"),  # JWT
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-./+=]{20,}"),
    re.compile(r"(?i)\b(token|api[_-]?key|secret|password|passwd)\b\s*[:=]\s*['\"]?(?=[A-Za-z0-9_\-./+=]*\d)[A-Za-z0-9_\-./+=]{16,}"),
    re.compile(r"\b[a-f0-9]{64,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY.*?-----END [A-Z ]*PRIVATE KEY", re.DOTALL),  # PEM key blocks
    re.compile(r'"private_key"\s*:\s*"[^"]{16,}"'),  # JSON-shaped pasted private keys
]

_SLASH_ONLY = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}")

_EXACT_MIN_SESSIONS = 2
_STEM_MIN_SESSIONS = 3
_LINE_MIN_SESSIONS = 3
_TOP = 60
_MIN_PHRASE_LEN = 12
_MIN_LINE_WORDS = 5
_MIN_LINE_CHARS = 24


def redact(text: str) -> str:
    """Redact secrets verbatim from the retired collector (security-critical)."""
    for rx in SECRET_RES:
        text = rx.sub(lambda m: m.group(0)[:8] + "…[redacted]", text)
    return text


def normalize(s: str) -> str:
    return WORD_RE.sub(" ", s.strip().lower())


def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_time(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def _under(path: str, base: str) -> bool:
    path, base = os.path.normcase(os.path.normpath(path)), os.path.normcase(os.path.normpath(base))
    return path == base or path.startswith(base.rstrip(os.sep) + os.sep)


def _default_exclude_cwd() -> list[str]:
    import tempfile

    return sorted(
        {
            os.path.normcase(os.path.normpath(p))
            for p in (
                tempfile.gettempdir(),
                os.path.realpath(tempfile.gettempdir()),
                "/tmp",
                "/private/tmp",
                "/var/folders",
            )
        }
    )


# ─── Block 1: SkillsTraces class definition & protocol methods ──────────────
class SkillsTraces(ISkillsTracesProtocol):
    """Scans sessions, builds skills-only usage, and mines repeated phrases."""

    # ── ISkillsTracesProtocol ──────────────────────────────────────────

    def scan_sessions(
        self,
        grok_home: str,
        run_dir: str,
        days: int = 0,
        since_last: bool = False,
        min_turns: int = 1,
        limit: int = 0,
        include_headless: bool = False,
        include_subagents: bool = False,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        Applies the subagent/headless/temp-cwd/grok-e2e/window/min-turns
        filters, redacts secrets verbatim, caps prompts at ``TURN_CAP`` chars,
        drops smoke-test sessions, writes ``manifest.json`` +
        ``sessions/NNNN-<id>.json`` into ``run_dir``, and returns the kept
        records plus the ``sessions_seen`` / ``dropped`` counters as a
        ``ScanResult`` VO.
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        sessions_root = os.path.join(grok_home, "sessions")
        run_dir = os.path.abspath(run_dir)
        os.makedirs(os.path.join(run_dir, "sessions"), exist_ok=True)

        exclude_cwd = _default_exclude_cwd()
        drop_patterns = [re.compile(p, re.IGNORECASE) for p in DEFAULT_DROP_PATTERNS]

        cutoff = None
        if days > 0:
            cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
        if since_last:
            state_path = os.path.join(grok_home, "learn", "state.json")
            try:
                cutoff = _parse_time(_read_json(state_path).get("last_completed_at"))
            except (OSError, ValueError):
                cutoff = None

        kept: list[dict] = []
        seen = 0
        dropped: Counter[str] = Counter()

        if os.path.isdir(sessions_root):
            for enc_cwd in sorted(os.listdir(sessions_root)):
                cwd_dir = os.path.join(sessions_root, enc_cwd)
                if not os.path.isdir(cwd_dir):
                    continue
                for sid in sorted(os.listdir(cwd_dir)):
                    sess_dir = os.path.join(cwd_dir, sid)
                    if not os.path.isdir(sess_dir):
                        continue
                    seen += 1
                    summ_path = os.path.join(sess_dir, "summary.json")
                    if not os.path.isfile(summ_path):
                        dropped["no_summary"] += 1
                        continue
                    try:
                        summary = _read_json(summ_path)
                    except (OSError, ValueError):
                        dropped["summary_unreadable"] += 1
                        continue
                    if not isinstance(summary, dict):
                        dropped["summary_unreadable"] += 1
                        continue
                    kind = summary.get("session_kind")
                    if kind in SUBAGENT_KINDS and not include_subagents:
                        dropped["subagent"] += 1
                        continue
                    if kind == "headless" and not include_headless:
                        dropped["headless"] += 1
                        continue
                    info = summary.get("info") or {}
                    cwd = info.get("cwd") or urllib.parse.unquote(enc_cwd)
                    if any(_under(cwd, p) for p in exclude_cwd) or any(
                        s in cwd for s in DEFAULT_EXCLUDE_SUBSTR
                    ):
                        dropped["excluded_cwd"] += 1
                        continue
                    if cutoff is not None:
                        ts = _parse_time(summary.get("updated_at"))
                        if ts is None or ts < cutoff:
                            dropped["older_than_window"] += 1
                            continue
                    rec = _scan_session(sess_dir, summary, drop_patterns)
                    if rec is None or rec["human_turns"] < min_turns:
                        dropped["no_human_turns"] += 1
                        continue
                    kept.append(rec)

        kept.sort(key=lambda r: r.get("updated_at") or "", reverse=True)

        # single-turn sessions that repeat one identical prompt across sessions
        # look like automation; exclude them
        single = Counter(
            normalize(r["turns"][0]) for r in kept if r["human_turns"] == 1
        )
        for r in kept:
            r["repeated_single_turn"] = bool(
                r["human_turns"] == 1 and single[normalize(r["turns"][0])] >= 3
            )

        kept = [r for r in kept if not r["repeated_single_turn"]]

        # "hi" / "Test" sessions with no real tool use are smoke tests, not habits
        kept = [r for r in kept if not r["smoke_test"]]

        if limit > 0 and len(kept) > limit:
            dropped["beyond_limit"] += len(kept) - limit
            kept = kept[:limit]

        records: list[TraceSessionRecord] = []
        for i, r in enumerate(kept):
            r["index"] = i
            session_file = os.path.join(
                run_dir, "sessions", f"{i:04d}-{r['id']}.json"
            )
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(r, f, indent=1, ensure_ascii=False)
            records.append(_record_from_dict(r))

        _write_manifest(
            grok_home,
            run_dir,
            records,
            kept,
            seen,
            dropped,
            days,
            since_last,
            min_turns,
            limit,
        )
        return ScanResult(records=tuple(records), sessions_seen=seen, dropped=dict(dropped))

    def build_usage(self, grok_home: str, run_dir: str) -> UsageReport:
        """Build the skills-only usage report from session records in ``run_dir``.

        Aggregates per-skill hit counts (hits, sessions, last_used) from the
        session records the tracker wrote, and derives ``unused_loaded``
        (loaded, zero hits, not in slash-mru). Keeps the user-level slash-mru
        read so the disuse verdict stays correct. ``kept_sessions`` is the
        number of kept compact session records (not the number of skills with hits).
        """
        grok_home = os.path.abspath(os.path.expanduser(grok_home))
        run_dir = os.path.abspath(run_dir)
        sessions_dir = os.path.join(run_dir, "sessions")

        usage: dict[str, dict] = defaultdict(
            lambda: {"count": 0, "sessions": [], "last_used": None}
        )
        kept_sessions = 0
        if os.path.isdir(sessions_dir):
            for name in sorted(os.listdir(sessions_dir)):
                if not name.endswith(".json"):
                    continue
                try:
                    rec = _read_json(os.path.join(sessions_dir, name))
                except (OSError, ValueError):
                    continue
                kept_sessions += 1
                rid = rec.get("id") or ""
                updated = rec.get("updated_at") or ""
                for sname, n in (rec.get("skills_loaded") or {}).items():
                    u = usage[sname]
                    u["count"] += int(n)
                    if rid and rid not in u["sessions"] and len(u["sessions"]) < 8:
                        u["sessions"].append(rid)
                    if updated > (u["last_used"] or ""):
                        u["last_used"] = updated

        catalog = _load_skill_catalog(grok_home)
        items: list[SkillUsageItem] = []
        for sname, info in catalog.items():
            u = usage.get(sname, {"count": 0, "sessions": [], "last_used": None})
            items.append(
                SkillUsageItem(
                    name=sname,
                    source=info["source"],
                    path=info["path"],
                    loaded=info["loaded"],
                    count=u["count"],
                    sessions=tuple(u["sessions"]),
                    last_used=u["last_used"] or None,
                    in_slash_mru=info["in_slash_mru"],
                )
            )
        items.sort(key=lambda it: it.name)

        unused_loaded = tuple(
            it.name
            for it in items
            if it.loaded and it.count == 0 and not it.in_slash_mru
        )

        return UsageReport(
            kept_sessions=kept_sessions,
            items=tuple(items),
            unused_loaded=unused_loaded,
        )

    def build_phrases(self, grok_home: str, run_dir: str) -> PhrasesReport:
        """Read session records from ``run_dir`` and return repeated phrases.

        Counts are distinct sessions; single-turn sessions repeated 3+ times
        are excluded as likely automation.
        """
        sessions_dir = os.path.join(run_dir, "sessions")
        exact: dict[str, list[str]] = defaultdict(list)
        stems: dict[str, list[str]] = defaultdict(list)
        lines: dict[str, set[str]] = defaultdict(set)

        if os.path.isdir(sessions_dir):
            for name in sorted(os.listdir(sessions_dir)):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(sessions_dir, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        rec = json.load(f)
                except (OSError, ValueError):
                    continue
                rid = rec.get("id") or ""
                # sessions flagged repeated_single_turn are automation — excluded
                if rec.get("repeated_single_turn"):
                    continue
                for t in rec.get("turns") or []:
                    n = normalize(t)
                    if len(n) < _MIN_PHRASE_LEN:
                        continue
                    stripped = t.strip()
                    if SLASH_RE.fullmatch(stripped) or _SLASH_ONLY.fullmatch(n):
                        continue
                    exact[n].append(rid)
                    words = n.split(" ")
                    if len(words) >= 6:
                        stems[" ".join(words[:12])].append(rid)
                    for ln in t.splitlines():
                        ln_n = normalize(ln)
                        if (
                            len(ln_n.split(" ")) >= _MIN_LINE_WORDS
                            and len(ln_n) >= _MIN_LINE_CHARS
                        ):
                            lines[ln_n].add(rid)

        exact_prompts = self._top(exact, _EXACT_MIN_SESSIONS, "phrase")
        prompt_stems = self._top(stems, _STEM_MIN_SESSIONS, "stem")
        instruction_lines = self._top(lines, _LINE_MIN_SESSIONS, "line")

        return PhrasesReport(
            exact_prompts=tuple(exact_prompts),
            stems=tuple(prompt_stems),
            repeated_instruction_lines=tuple(instruction_lines),
        )

    @staticmethod
    def _top(data: dict, min_count: int, key_name: str) -> tuple[PhraseRow, ...]:
        rows: list[PhraseRow] = []
        for k, ids in data.items():
            id_list = list(ids)
            sessions = len(set(id_list))
            if sessions >= min_count:
                rows.append(
                    PhraseRow(
                        phrase=k[:400],
                        sessions=sessions,
                        occurrences=len(id_list),
                        session_ids=tuple(sorted(set(id_list))[:8]),
                    )
                )
        rows.sort(key=lambda x: (-x.sessions, -x.occurrences, x.phrase))
        return tuple(rows[:_TOP])

    # ── Trace-state lifecycle ──────────────────────────────────────

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
        if run_name in ("", ".", "..") or os.path.basename(run_name) != run_name:
            raise ValueError("run-name must be a single path component")
        dest_dir = os.path.join(grok_home, "learn", "trash", run_name)
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


# ─── Block 2: inherent helper functions used by the class ──────────────


def _scan_session(sess_dir: str, summary: dict, drop_patterns: list[re.Pattern]) -> dict | None:
    """Scan one session dir; return a compact record dict or None."""
    chat = os.path.join(sess_dir, "chat_history.jsonl")
    if not os.path.isfile(chat):
        return None

    turns: list[str] = []
    tools: Counter[str] = Counter()
    mcp_tools: Counter[str] = Counter()
    skill_loads: Counter[str] = Counter()
    skill_load_paths: dict[str, str] = {}
    slash: Counter[str] = Counter()
    paths_touched: Counter[str] = Counter()
    subagents = 0
    workflow_launches = 0

    parse_errors = 0
    dropped_turns = 0

    with open(chat, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                parse_errors += 1
                continue
            if not isinstance(r, dict):
                parse_errors += 1
                continue
            t = r.get("type")
            if t == "user" and not r.get("synthetic_reason"):
                for q in _human_turns(r.get("content")):
                    if any(p.search(q) for p in drop_patterns):
                        dropped_turns += 1
                        continue
                    turns.append(q)
                    for m in SLASH_RE.findall(q):
                        slash[m] += 1
            elif t == "assistant":
                for call in r.get("tool_calls") or []:
                    if not isinstance(call, dict):
                        continue
                    name = call.get("name") or ""
                    tools[name] += 1
                    try:
                        a = json.loads(call.get("arguments") or "{}")
                    except ValueError:
                        a = {}
                    if not isinstance(a, dict):
                        a = {}
                    if name == "use_tool":
                        tn = a.get("tool_name") or ""
                        mcp_tools[tn.split("__", 1)[0] if "__" in tn else tn] += 1
                    elif name == "spawn_subagent":
                        subagents += 1
                    elif name == "workflow":
                        workflow_launches += 1
                    target = a.get("target_file") or a.get("file_path") or a.get("path")
                    if isinstance(target, str) and target:
                        sm = SKILL_PATH_RE.search(target)
                        if sm:
                            skill_loads[sm.group(1)] += 1
                            skill_load_paths.setdefault(sm.group(1), target)
                        elif name in ("read_file", "write", "search_replace"):
                            paths_touched[target] += 1

    if not turns:
        return None

    real_tools = sum(n for name, n in tools.items() if name != "send_feedback")
    smoke_test = real_tools == 0 and all(len(t.split()) < 3 for t in turns)

    info = summary.get("info") or {}
    cwd = info.get("cwd") or ""
    git_root = summary.get("git_root_dir") or ""
    base = git_root or cwd
    dirs: Counter[str] = Counter()
    for p, n in paths_touched.items():
        rel = p
        if base and _under(p, base):
            rel = os.path.relpath(p, base)
        parts = [x for x in re.split(r"[\\/]+", rel) if x]
        key = "/".join(parts[:2]) if len(parts) > 2 else (parts[0] if parts else rel)
        dirs[key] += n

    capped_turns = [
        (t[:TURN_CAP] + ("…" if len(t) > TURN_CAP else ""))
        for t in (redact(t) for t in turns)
    ]

    return {
        "id": (summary.get("id") or os.path.basename(sess_dir)),
        "cwd": cwd,
        "git_root": git_root,
        "branch": summary.get("head_branch") or "",
        "title": summary.get("generated_title") or "",
        "session_kind": summary.get("session_kind"),
        "created_at": summary.get("created_at"),
        "updated_at": summary.get("updated_at"),
        "model": summary.get("current_model_id"),
        "human_turns": len(turns),
        "dropped_turns": dropped_turns,
        "parse_errors": parse_errors,
        "smoke_test": smoke_test,
        "turns": capped_turns,
        "slash_commands": dict(slash.most_common()),
        "skills_loaded": dict(skill_loads.most_common()),
        "skill_load_paths": skill_load_paths,
        "mcp_servers_used": dict(mcp_tools.most_common()),
        "tools": dict(tools.most_common(25)),
        "subagent_spawns": subagents,
        "workflow_launches": workflow_launches,
        "top_dirs_touched": dict(dirs.most_common(10)),
        "trace_path": chat,
        "repeated_single_turn": False,
    }


def _human_turns(content) -> list[str]:
    if isinstance(content, str):
        txt = content
    elif isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text") or "")
            elif isinstance(c, str):
                parts.append(c)
        txt = "\n".join(parts)
    else:
        txt = ""
    found = [m.strip() for m in USER_QUERY_RE.findall(txt)]
    return [t for t in found if t]


def _record_from_dict(r: dict) -> TraceSessionRecord:
    return TraceSessionRecord(
        id=r["id"],
        index=r.get("index", 0),
        cwd=r.get("cwd", ""),
        branch=r.get("branch", ""),
        title=r.get("title", ""),
        session_kind=r.get("session_kind") or "",
        updated_at=r.get("updated_at") or "",
        model=r.get("model") or "",
        human_turns=r.get("human_turns", 0),
        turns=tuple(r.get("turns") or ()),
        slash_commands=r.get("slash_commands") or {},
        skills_loaded=r.get("skills_loaded") or {},
        skill_load_paths=r.get("skill_load_paths") or {},
        mcp_servers_used=r.get("mcp_servers_used") or {},
        tools=r.get("tools") or {},
        subagent_spawns=r.get("subagent_spawns", 0),
        workflow_launches=r.get("workflow_launches", 0),
        top_dirs_touched=r.get("top_dirs_touched") or {},
        repeated_single_turn=bool(r.get("repeated_single_turn")),
        trace_path=r.get("trace_path") or "",
    )


def _write_manifest(
    grok_home: str,
    run_dir: str,
    records: list[TraceSessionRecord],
    kept: list[dict],
    seen: int,
    dropped: Counter[str],
    days: int,
    since_last: bool,
    min_turns: int,
    limit: int,
) -> None:
    manifest = {
        "grok_home": grok_home,
        "run_dir": run_dir,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "sessions_seen": seen,
        "sessions_kept": len(kept),
        "dropped": dict(dropped),
        "human_turns_total": sum(r["human_turns"] for r in kept),
        "kept": [
            {
                "index": r["index"],
                "id": r["id"],
                "cwd": r["cwd"],
                "turns": r["human_turns"],
                "updated_at": r["updated_at"],
                "title": r["title"],
            }
            for r in kept
        ],
        "params": {
            "days": days,
            "since_last": since_last,
            "min_turns": min_turns,
            "limit": limit,
        },
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)


def _load_skill_catalog(grok_home: str) -> dict[str, dict]:
    """Load the user skill catalog: name -> {source, path, loaded, in_slash_mru}.

    Skills-only, user-level: walks ``$GROK_HOME/skills/<cat>/<name>/SKILL.md``,
    parses frontmatter via the shared utility, applies the ``[skills] disabled``
    list from ``config.toml``, and reads the user slash-mru for the
    ``in_slash_mru`` flag.
    """
    catalog: dict[str, dict] = {}
    skills_dir = os.path.join(grok_home, "skills")
    disabled: set[str] = set()
    cfg = os.path.join(grok_home, "config.toml")
    if os.path.isfile(cfg):
        try:
            with open(cfg, encoding="utf-8", errors="replace") as f:
                config_text = f.read()
        except OSError:
            config_text = ""
        disabled = set(_toml_string_array(config_text, "skills", "disabled") or [])

    slash_mru: set[str] = set()
    mru_path = os.path.join(grok_home, "slash-mru.json")
    if os.path.isfile(mru_path):
        try:
            slash_mru = set((_read_json(mru_path).get("by_command") or {}).keys())
        except (OSError, ValueError):
            pass

    if os.path.isdir(skills_dir):
        for cat in sorted(os.listdir(skills_dir)):
            cat_dir = os.path.join(skills_dir, cat)
            if not os.path.isdir(cat_dir):
                continue
            for name in sorted(os.listdir(cat_dir)):
                skill_dir = os.path.join(cat_dir, name)
                sk_path = os.path.join(skill_dir, "SKILL.md")
                if not os.path.isfile(sk_path):
                    continue
                sname, _description = parse_skill_frontmatter(Path(sk_path))
                sname = sname or name
                loaded = sname not in disabled
                catalog[sname] = {
                    "source": "user",
                    "path": sk_path,
                    "loaded": loaded,
                    "in_slash_mru": sname in slash_mru,
                }
    return catalog


def _toml_string_array(text: str, table: str, key: str) -> list[str] | None:
    """Read ``key = [ "a", "b" ]`` under ``[table]`` without YAML/TOML deps."""
    m = re.search(r"^\[" + re.escape(table) + r"\]\s*$", text, re.MULTILINE)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^\[", rest, re.MULTILINE)
    if nxt:
        rest = rest[: nxt.start()]
    km = re.search(r"^" + re.escape(key) + r"\s*=\s*\[", rest, re.MULTILINE)
    if not km:
        return None
    depth, i = 0, km.end() - 1
    start = i
    while i < len(rest):
        if rest[i] == "[":
            depth += 1
        elif rest[i] == "]":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return re.findall(r'"([^"]+)"', rest[start : i + 1])
