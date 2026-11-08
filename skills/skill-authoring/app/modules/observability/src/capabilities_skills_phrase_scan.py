"""Phrase scan capability (AES capabilities layer, self-contained in ``app``).

Scans ``$GROK_HOME/sessions`` and mines repeated prompts from ``<user_query>``
tags in session chat history. Depends only on the trace contract + taxonomy
from the shared kernel. Never imports ``skill-traces``.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

from shared.src.traces.contract_traces_protocol import ISkillsTracesProtocol
from shared.src.traces.taxonomy_traces_vo import (
    GrokHome,
    PhraseRow,
    PhrasesReport,
    ScanResult,
    TraceRunDir,
    TraceSessionRecord,
)

__all__ = ["SkillsPhraseScan"]

# Reused across the module (constant definitions live in one place).
_MIN_PHRASE_LEN = 12
_MIN_LINE_WORDS = 5
_MIN_LINE_CHARS = 24
_EXACT_MIN_SESSIONS = 2
_STEM_MIN_SESSIONS = 3
_LINE_MIN_SESSIONS = 3
_TOP = 60

USER_QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
SLASH_RE = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}")
SLASH_ONLY = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}$")
DEFAULT_DROP_PATTERNS = [r"^the user invoked `/feedback`"]
TURN_CAP = 2000


class SkillsPhraseScan(ISkillsTracesProtocol):
    """Scans sessions and mines repeated phrases."""

    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        days: int = 0,
        since_last: bool = False,
        min_turns: int = 1,
        limit: int = 0,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome.

        Writes ``manifest.json`` plus ``sessions/*.json`` into *run_dir*.
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
            state_path_ = os.path.join(grok_home, "learn", "state.json")
            try:
                cutoff = _parse_time(_read_json(state_path_).get("last_completed_at"))
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
                    info = summary.get("info") or {}
                    cwd = info.get("cwd") or urllib.parse.unquote(enc_cwd)
                    if any(_under(cwd, p) for p in exclude_cwd) or any(
                        s in cwd for s in ("grok-e2e",)
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
            single = Counter(
                _normalize(r["turns"][0]) for r in kept if r["human_turns"] == 1
            )
            for r in kept:
                r["repeated_single_turn"] = bool(
                    r["human_turns"] == 1 and single[_normalize(r["turns"][0])] >= 3
                )
            kept = [r for r in kept if not r["repeated_single_turn"]]
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

        return ScanResult(
            records=tuple(records),
            sessions_seen=seen,
            dropped=dict(dropped),
        )

    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        min_sessions: int = 2,
    ) -> PhrasesReport:
        """Read session records from ``run_dir`` and return repeated phrases."""
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
                if rec.get("repeated_single_turn"):
                    continue
                for t in rec.get("turns") or []:
                    n = _normalize(t)
                    if len(n) < _MIN_PHRASE_LEN:
                        continue
                    stripped = t.strip()
                    if SLASH_RE.fullmatch(stripped) or SLASH_ONLY.fullmatch(n):
                        continue
                    exact[n].append(rid)
                    words = n.split(" ")
                    if len(words) >= 6:
                        stems[" ".join(words[:12])].append(rid)
                    for ln in t.splitlines():
                        ln_n = _normalize(ln)
                        if (
                            len(ln_n.split(" ")) >= _MIN_LINE_WORDS
                            and len(ln_n) >= _MIN_LINE_CHARS
                        ):
                            lines[ln_n].add(rid)

        return PhrasesReport(
            exact_prompts=self._top(exact, min_sessions, "phrase"),
            stems=self._top(stems, _STEM_MIN_SESSIONS, "stem"),
            repeated_instruction_lines=self._top(lines, _LINE_MIN_SESSIONS, "line"),
        )

    # ─── Helpers (module-private, no capability coupling) ──────────

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


# ─── Module-level helpers ──────────────────────────────────────────


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
    path, base = os.path.normcase(os.path.normpath(path)), os.path.normcase(
        os.path.normpath(base)
    )
    return path == base or path.startswith(base.rstrip(os.sep) + os.sep)


def _default_exclude_cwd() -> list[str]:
    tmp = os.environ.get("TMPDIR", os.path.expanduser("~/.cache"))
    return sorted(
        {
            os.path.normcase(os.path.normpath(p))
            for p in (
                tmp,
                os.path.realpath(tmp),
                os.path.expanduser("~/.cache"),
                os.path.expanduser("~/.local/share"),
            )
        }
    )


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _scan_session(sess_dir: str, summary: dict, drop_patterns: list[re.Pattern]) -> dict | None:
    """Scan one session dir; return a compact record dict or None."""
    chat = os.path.join(sess_dir, "chat_history.jsonl")
    if not os.path.isfile(chat):
        return None

    turns: list[str] = []
    tools: Counter[str] = Counter()
    skill_loads: Counter[str] = Counter()
    skill_load_paths: dict[str, str] = {}
    slash: Counter[str] = Counter()
    paths_touched: Counter[str] = Counter()
    subagents = 0
    workflow_launches = 0
    parse_errors = 0
    dropped_turns = 0

    skill_path_re = re.compile(r"[/\\]skills[/\\]([^/\\]+)[/\\]SKILL\.md$")

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
                        mcp_tools_key = tn.split("__", 1)[0] if "__" in tn else tn
                    elif name == "spawn_subagent":
                        subagents += 1
                    elif name == "workflow":
                        workflow_launches += 1
                    target = a.get("target_file") or a.get("file_path") or a.get("path")
                    if isinstance(target, str) and target:
                        sm = skill_path_re.search(target)
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
        for t in turns
    ]

    return {
        "id": summary.get("id") or os.path.basename(sess_dir),
        "cwd": cwd,
        "git_root": git_root,
        "branch": summary.get("head_branch") or "",
        "title": summary.get("generated_title") or "",
        "updated_at": summary.get("updated_at") or "",
        "model": summary.get("current_model_id"),
        "human_turns": len(turns),
        "dropped_turns": dropped_turns,
        "parse_errors": parse_errors,
        "smoke_test": smoke_test,
        "turns": capped_turns,
        "slash_commands": dict(slash.most_common()),
        "skills_loaded": dict(skill_loads.most_common()),
        "skill_load_paths": skill_load_paths,
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
        updated_at=r.get("updated_at") or "",
        turns=tuple(r.get("turns") or ()),
        slash_commands=r.get("slash_commands") or {},
        skills_loaded=r.get("skills_loaded") or {},
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
                "title": r.get("title", ""),
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
