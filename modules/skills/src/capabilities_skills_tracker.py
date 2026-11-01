"""Skills tracker capability (AES capabilities layer).

Ports the session-scanning, redaction, and usage-building business logic out
of the retired ``skills/skill-authoring/_trace-pipeline/scripts/collect_sessions.py``
into the ``ITrackerProtocol`` seam.

Skills-only: plugin / MCP / workflow / slash-mru usage tracking is dropped;
skill hit counts, ``unused_loaded``, per-session records, and phrases are kept.

The capability writes its records into ``run_dir`` (``manifest.json`` and
``sessions/NNNN-<id>.json``) and returns the same data as VOs. ``build_usage``
reads those session records back out of the run dir.

No capability-to-capability imports: depends only on ``modules.shared``
contract + taxonomy + utilities. I/O is limited to reading
``$GROK_HOME/sessions`` files and writing the run dir — that is this
capability's job, not a layer violation.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

from modules.shared.src.common.utility_skill_pack import (
    SLASH_RE,
    WORD_RE,
    parse_skill_frontmatter,
)
from modules.shared.src.skills.contract_skills_protocol import ITrackerProtocol
from modules.shared.src.skills.taxonomy_skills_authoring_vo import UsageReport
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillUsageItem,
    TraceSessionRecord,
)

__all__ = [
    "SECRET_RES",
    "TURN_CAP",
    "SkillsTracker",
    "normalize",
    "redact",
]

TURN_CAP = 2000
"""Max characters kept per human prompt (longer prompts are truncated)."""

USER_QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
SUBAGENT_KINDS = {"subagent", "subagent_resume", "subagent_fork"}
DEFAULT_EXCLUDE_SUBSTR = ["grok-e2e"]
SKILL_PATH_RE = re.compile(r"[/\\]skills[/\\]([^/\\]+)[/\\]SKILL\.md$")
# a slash command, not a path segment (~/x, ./x, a/b) and not followed by more path
DEFAULT_DROP_PATTERNS = [r"^the user invoked `/feedback`"]

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


class SkillsTracker(ITrackerProtocol):
    """Scans sessions and builds the skills-only usage material."""

    # ── ITrackerProtocol ──────────────────────────────────────────

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
    ) -> tuple[TraceSessionRecord, ...]:
        """Walk ``$GROK_HOME/sessions`` and return compact per-session records.

        Applies the subagent/headless/temp-cwd/grok-e2e/window/min-turns
        filters, redacts secrets verbatim, caps prompts at ``TURN_CAP`` chars,
        drops smoke-test sessions, writes ``manifest.json`` +
        ``sessions/NNNN-<id>.json`` into ``run_dir``, and returns the kept
        records as VOs.
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

        _write_manifest(grok_home, run_dir, records, kept, seen, dropped, days, since_last, min_turns, limit)
        return tuple(records)

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


# ── internal helpers ────────────────────────────────────────────────


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
