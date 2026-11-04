"""Skills traces scan capability (AES capabilities layer).

Implements ISkillsTraceScanProtocol: scan sessions, build skills-only usage,
mine repeated phrases, materialize usage.json + phrases.json. Depends only on
contract + taxonomy from the shared kernel plus shared trace-state helpers
(imported from utility_skills_trace_state). Never imports the state capability.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

from shared.src.skills_traces.contract_skills_protocol import ISkillsTraceScanProtocol
from shared.src.skills_traces.taxonomy_skills_authoring_vo import (
    PhrasesReport,
    UsageReport,
)
from shared.src.skills_traces.taxonomy_skills_vo import (
    GrokHome,
    PhraseRow,
    ScanResult,
    SkillUsageItem,
    TraceRunDir,
    TraceSessionRecord,
)
from shared.src.skills_traces.utility_skill_pack import (
    SLASH_RE,
    parse_skill_frontmatter,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    DEFAULT_DROP_PATTERNS,
    DEFAULT_EXCLUDE_SUBSTR,
    SKILL_PATH_RE,
    SUBAGENT_KINDS,
    TURN_CAP,
    _default_exclude_cwd,
    _read_json,
    normalize,
    redact,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    EXACT_MIN_SESSIONS as _EXACT_MIN_SESSIONS,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    LINE_MIN_SESSIONS as _LINE_MIN_SESSIONS,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    MIN_LINE_CHARS as _MIN_LINE_CHARS,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    MIN_LINE_WORDS as _MIN_LINE_WORDS,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    MIN_PHRASE_LEN as _MIN_PHRASE_LEN,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    SLASH_ONLY as _SLASH_ONLY,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    STEM_MIN_SESSIONS as _STEM_MIN_SESSIONS,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    TOP as _TOP,
)
from shared.src.skills_traces.utility_skills_trace_state import (
    USER_QUERY_RE as _USER_QUERY_RE,
)

__all__ = ["SkillsTracesScan"]


class SkillsTracesScan(ISkillsTraceScanProtocol):
    """Scans sessions, builds skills-only usage, and mines repeated phrases."""

    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        days: int = 0,
        since_last: bool = False,
        min_turns: int = 1,
        limit: int = 0,
        include_headless: bool = False,
        include_subagents: bool = False,
    ) -> ScanResult:
        """Walk ``$GROK_HOME/sessions`` and return a compact scan outcome."""
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
        records: list[TraceSessionRecord] = []

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

            single = Counter(
                normalize(r["turns"][0]) for r in kept if r["human_turns"] == 1
            )
            for r in kept:
                r["repeated_single_turn"] = bool(
                    r["human_turns"] == 1 and single[normalize(r["turns"][0])] >= 3
                )

            kept = [r for r in kept if not r["repeated_single_turn"]]
            kept = [r for r in kept if not r["smoke_test"]]

            if limit > 0 and len(kept) > limit:
                dropped["beyond_limit"] += len(kept) - limit
                kept = kept[:limit]

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

    def build_usage(self, grok_home: GrokHome, run_dir: TraceRunDir) -> UsageReport:
        """Build the skills-only usage report from session records in ``run_dir``."""
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

    def build_phrases(self, grok_home: GrokHome, run_dir: TraceRunDir) -> PhrasesReport:
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

    def materialize(
        self, grok_home: GrokHome, run_dir: TraceRunDir
    ) -> tuple[UsageReport, PhrasesReport]:
        """Build usage + phrases for *run_dir*; write ``usage.json`` +
        ``phrases.json`` into it and return the two reports."""
        usage = self.build_usage(grok_home=grok_home, run_dir=run_dir)
        report = self.build_phrases(grok_home=grok_home, run_dir=run_dir)

        usage_path = os.path.join(run_dir, "usage.json")
        phrases_path = os.path.join(run_dir, "phrases.json")
        with open(usage_path, "w", encoding="utf-8") as f:
            json.dump(self._usage_to_json(usage), f, indent=1, ensure_ascii=False)
        with open(phrases_path, "w", encoding="utf-8") as f:
            json.dump(self._phrases_to_json(report), f, indent=1, ensure_ascii=False)

        return usage, report

    @staticmethod
    def _usage_to_json(usage: UsageReport) -> dict:
        """The skills-only usage.json shape the trace workflow reads."""
        return {
            "kept_sessions": usage.kept_sessions,
            "items": [
                {
                    "kind": "skill",
                    "name": it.name,
                    "source": it.source,
                    "path": it.path,
                    "loaded": it.loaded,
                    "count": it.count,
                    "sessions": list(it.sessions),
                    "last_used": it.last_used,
                    "in_slash_mru": it.in_slash_mru,
                }
                for it in usage.items
            ],
            "unused_loaded": list(usage.unused_loaded),
        }

    @staticmethod
    def _phrases_to_json(report: PhrasesReport) -> dict:
        """The legacy phrases.json shape (exact / stems / instruction lines)."""
        def rows(rows_: tuple[PhraseRow, ...]) -> list[dict]:
            return [
                {
                    "phrase": r.phrase,
                    "sessions": r.sessions,
                    "occurrences": r.occurrences,
                    "session_ids": list(r.session_ids),
                }
                for r in rows_
            ]

        return {
            "exact_prompts": rows(report.exact_prompts),
            "prompt_stems_12_words": rows(report.stems),
            "repeated_instruction_lines": rows(report.repeated_instruction_lines),
            "note": "counts are distinct sessions; single-turn sessions repeated 3+ times are excluded as likely automation",
        }

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


# ─── Module-level helpers used by the scan capability ──────────────


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
    found = [m.strip() for m in _USER_QUERY_RE.findall(txt)]
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
    """Load the user skill catalog: name -> {source, path, loaded, in_slash_mru}."""
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
