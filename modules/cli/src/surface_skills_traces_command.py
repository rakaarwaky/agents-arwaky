"""Skills CLI surface — trace-lifecycle command handlers for ``aa skills traces``.

Extracted from ``surface_skills_command`` to keep both surface modules under
the AES301 line budget. The public entry point is ``cmd_traces`` (called by
the parent ``cmd_skills`` router); argv becomes a ``SkillsRequest`` whose
``traces_action`` flag selects the sub-action, the aggregate executes it, and
the text/JSON rendering comes back on ``SkillsResult``.

Exit codes for ``traces state wait`` are the legacy contract: 0 ready /
1 phase-stall / 3 report-stall / 2 deadline.
"""

from __future__ import annotations

import argparse
import json
import tempfile

from modules.shared.src.common.utility_logging_setup import err
from modules.shared.src.common.utility_paths_resolver import resolve_skills_root
from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillsExitCode,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
    TraceStateStatus,
)

_EXIT_USAGE = SkillsExitCode.USAGE_ERROR
_EXIT_WAIT_READY = SkillsExitCode.CLEAN
_EXIT_WAIT_PHASE_STALL = SkillsExitCode.ISSUES_FOUND
_EXIT_WAIT_REPORT_STALL = SkillsExitCode.CATALOG_DRIFT
_EXIT_WAIT_DEADLINE = SkillsExitCode.USAGE_ERROR


def _emit_json(payload: dict[str, object]) -> None:
    """Print a JSON payload with a stable key order and a trailing newline."""
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _split_root(args: list[str]) -> tuple[SkillsRoot | None, list[str]]:
    """Extract ``--skills-root PATH`` from *args*, leaving the rest intact.

    Mirrors the parent module's helper so this module stays self-contained;
    ``traces`` actions ignore the root, so the returned root is discarded.
    """
    root: SkillsRoot | None = None
    rest: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--skills-root" and index + 1 < len(args):  # nosec B105
            root = SkillsRoot(resolve_skills_root(args[index + 1]))
            index += 2
            continue
        if token.startswith("--skills-root="):
            root = SkillsRoot(resolve_skills_root(token.split("=", 1)[1]))
            index += 1
            continue
        rest.append(token)
        index += 1
    return root, rest


def cmd_traces(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Route a ``traces`` sub-action to its handler."""
    _, rest = _split_root(args)
    if not rest:
        err("Usage: aa skills traces <collect|usage|phrases|materialize|state> [flags]")
        return _EXIT_USAGE
    action = rest[0]

    if action == "collect":
        return _cmd_traces_collect(rest[1:], aggregate)
    if action == "usage":
        return _cmd_traces_usage(rest[1:], aggregate)
    if action == "phrases":
        return _cmd_traces_phrases(rest[1:], aggregate)
    if action == "materialize":
        return _cmd_traces_materialize(rest[1:], aggregate)
    if action == "state":
        # No sub-action: default to "get" — route through the typed state parser.
        return _cmd_traces_state(rest[1:] or ["get"], aggregate)
    err(f"Unknown traces action: {action}")
    return _EXIT_USAGE


def _trace_collect_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills traces collect",
        description="Scan sessions and build the skills-only usage material.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME to scan")
    parser.add_argument(
        "--out",
        metavar="DIR",
        default="",
        help="Run dir for output records (default: a scratch skills-trace-* temp dir)",
    )
    parser.add_argument("--days", type=int, default=0, help="Only sessions updated within N days")
    parser.add_argument("--since-last", action="store_true", help="Since the last completed run")
    parser.add_argument("--min-turns", type=int, default=1, help="Minimum human turns per session")
    parser.add_argument("--limit", type=int, default=0, help="Max sessions to keep")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_traces_collect(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_collect_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    run_dir = ns.out or tempfile.mkdtemp(prefix="skills-trace-")
    request = SkillsRequest(
        op=SkillsOp.TRACES,
        flags={
            "traces_action": "collect",
            "grok_home": ns.grok_home,
            "run_dir": run_dir,
            "days": str(ns.days),
            "since_last": "1" if ns.since_last else "0",
            "min_turns": str(ns.min_turns),
            "limit": str(ns.limit),
        },
        json=ns.json,
    )
    result = aggregate.execute(request)

    if not result.ok:
        err(result.message)
        return result.exit_code

    if ns.json:
        _emit_json(
            {
                "run_dir": run_dir,
                "kept": len(result.usage.items) if result.usage else 0,
                "seen": result.collect_summary.sessions_seen if result.collect_summary else 0,
                "dropped": dict(result.collect_summary.dropped) if result.collect_summary else {},
            }
        )
        return 0
    print(result.message or f"Trace collect → {run_dir}")
    return 0


def _trace_usage_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills traces usage",
        description="Read the last run's skills-only usage report.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME to read")
    parser.add_argument("--run-dir", metavar="DIR", default="", help="Run dir to read usage from")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_traces_usage(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_usage_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    request = SkillsRequest(
        op=SkillsOp.TRACES,
        flags={
            "traces_action": "usage",
            "grok_home": ns.grok_home,
            "run_dir": ns.run_dir,
        },
        json=ns.json,
    )
    result = aggregate.execute(request)

    if ns.json:
        _emit_json(
            {
                "kept_sessions": result.usage.kept_sessions if result.usage else 0,
                "items": [
                    {
                        "name": it.name,
                        "source": it.source,
                        "path": it.path,
                        "loaded": it.loaded,
                        "count": it.count,
                        "sessions": list(it.sessions),
                        "last_used": it.last_used,
                        "in_slash_mru": it.in_slash_mru,
                    }
                    for it in (result.usage.items or [])
                ],
                "unused_loaded": list(result.usage.unused_loaded or []),
            }
        )
        return 0

    usage = result.usage
    if usage is None:
        err("Internal error: no usage report produced")
        return 1
    print(f"Kept sessions: {usage.kept_sessions}")
    print(f"{'Skill':<28} {'Loaded':<7} {'Count':<6} {'Last used':<20} {'In slash MRU'}")
    print("-" * 28 + " " + "-" * 7 + " " + "-" * 6 + " " + "-" * 20 + " " + "-" * 12)
    for it in usage.items:
        print(
            f"{it.name:<28} {it.loaded!s:<7} {it.count:<6} "
            f"{it.last_used!s:<20} {it.in_slash_mru!s}"
        )
    print(f"\nUnused loaded: {', '.join(usage.unused_loaded) or '(none)'}")
    return 1 if usage.unused_loaded else 0


def _trace_phrases_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills traces phrases",
        description="Mine repeated prompts and instruction lines from session records.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME (unused by phrases, kept for symmetry)")
    parser.add_argument("--run-dir", metavar="DIR", default="", help="Run dir holding session records")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_traces_phrases(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_phrases_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    request = SkillsRequest(
        op=SkillsOp.TRACES,
        flags={
            "traces_action": "phrases",
            "grok_home": ns.grok_home,
            "run_dir": ns.run_dir,
        },
        json=ns.json,
    )
    result = aggregate.execute(request)

    if ns.json:
        _emit_json(
            {
                "exact_prompts": [
                    {
                        "phrase": row.phrase,
                        "sessions": row.sessions,
                        "occurrences": row.occurrences,
                        "session_ids": list(row.session_ids),
                    }
                    for row in (result.phrases.exact_prompts or [])
                ],
                "stems": [
                    {
                        "phrase": row.phrase,
                        "sessions": row.sessions,
                        "occurrences": row.occurrences,
                        "session_ids": list(row.session_ids),
                    }
                    for row in (result.phrases.stems or [])
                ],
                "repeated_instruction_lines": [
                    {
                        "phrase": row.phrase,
                        "sessions": row.sessions,
                        "occurrences": row.occurrences,
                        "session_ids": list(row.session_ids),
                    }
                    for row in (result.phrases.repeated_instruction_lines or [])
                ],
            }
        )
        return 0

    phrases = result.phrases
    if phrases is None:
        err("Internal error: no phrases report produced")
        return 1
    if phrases.exact_prompts:
        print("Repeated exact prompts:")
        for row in phrases.exact_prompts:
            print(f"  [{row.sessions} sessions] {row.phrase}")
    if phrases.stems:
        print("Repeated prompt stems:")
        for row in phrases.stems:
            print(f"  [{row.sessions} sessions] {row.phrase}")
    if phrases.repeated_instruction_lines:
        print("Repeated instruction lines:")
        for row in phrases.repeated_instruction_lines:
            print(f"  [{row.sessions} sessions] {row.phrase}")
    if not any((phrases.exact_prompts, phrases.stems, phrases.repeated_instruction_lines)):
        print("No repeated phrases found.")
    return 0


def _trace_materialize_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills traces materialize",
        description="Write usage.json + phrases.json into a run dir for the trace workflow.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME to read")
    parser.add_argument("--run-dir", metavar="DIR", default="", help="Run dir to write into (required)")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_traces_materialize(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_materialize_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    if not ns.run_dir:
        err("--run-dir is required")
        return 2

    request = SkillsRequest(
        op=SkillsOp.TRACES,
        flags={
            "traces_action": "materialize",
            "grok_home": ns.grok_home,
            "run_dir": ns.run_dir,
        },
        json=ns.json,
    )
    result = aggregate.execute(request)
    if not result.ok:
        err(result.message or "Materialize failed")
        return int(result.exit_code or 1)

    if ns.json:
        _emit_json(
            {
                "run_dir": ns.run_dir,
                "usage_items": len(result.usage.items) if result.usage else 0,
                "unused_loaded": list(result.usage.unused_loaded) if result.usage else [],
                "phrases": {
                    "exact_prompts": len(result.phrases.exact_prompts) if result.phrases else 0,
                    "stems": len(result.phrases.stems) if result.phrases else 0,
                    "instruction_lines": len(result.phrases.repeated_instruction_lines) if result.phrases else 0,
                },
            }
        )
        return 0
    print(result.message or f"Materialized usage.json + phrases.json → {ns.run_dir}")
    return 0


def _trace_state_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills traces state",
        description="Drive the trace-learning lifecycle (status, trash, decisions, wait).",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    p_get = subparsers.add_parser("get", help="Show the pending run status")
    p_get.add_argument("--grok-home", metavar="P", default="")

    p_set = subparsers.add_parser("set", help="Set the pending run status")
    p_set.add_argument("--grok-home", metavar="P", default="")
    p_set.add_argument("--run-dir", metavar="DIR", default="")
    p_set.add_argument("--status", required=True, help="collected|running|report_ready|curating|done")

    p_clear = subparsers.add_parser("clear", help="Clear the pending run")
    p_clear.add_argument("--grok-home", metavar="P", default="")
    p_clear.add_argument("--run-dir", metavar="DIR", default="")

    p_trash = subparsers.add_parser("trash", help="Move validated paths into learn/trash/<run_name>")
    p_trash.add_argument("--grok-home", metavar="P", default="")
    p_trash.add_argument("--run-name", required=True, help="Trash sub-dir name (single path component)")
    p_trash.add_argument("paths", nargs="*", help="Paths to trash")

    p_restrict = subparsers.add_parser("restrict", help="chmod 0600 on the given paths")
    p_restrict.add_argument("paths", nargs="*", help="Paths to restrict")

    p_decide = subparsers.add_parser("decide", help="Append a decision line to learn/decisions.jsonl")
    p_decide.add_argument("--grok-home", metavar="P", default="")
    p_decide.add_argument("--run-dir", metavar="DIR", default="")
    p_decide.add_argument("--id", required=True, help="Decision id")
    p_decide.add_argument("--kind", required=True, help="skill|workflow|hook")
    p_decide.add_argument(
        "--action", required=True, dest="decide_action", help="create|update|delete|reject|..."
    )
    p_decide.add_argument("--target", required=True, help="Skill/target name")
    p_decide.add_argument("--path", required=True, help="Target path")
    p_decide.add_argument("--decision", required=True, help="applied|rejected|...")
    p_decide.add_argument("--date", default="", help="Decision date (ISO)")
    p_decide.add_argument("--undo", default=None, help="Undo path")

    p_wait = subparsers.add_parser("wait", help="Wait for report.md + actions.json in the run dir")
    p_wait.add_argument("--grok-home", metavar="P", default="")
    p_wait.add_argument("--run-dir", required=True, help="Run dir to watch")
    p_wait.add_argument("--timeout-min", type=int, default=90, help="Max minutes to wait")
    return parser


def _cmd_traces_state(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_state_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    action = ns.action
    flags = {
        "traces_action": "state",
        "state_action": action,
        "grok_home": getattr(ns, "grok_home", ""),
        "run_dir": getattr(ns, "run_dir", ""),
    }

    if action == "set":
        flags["status"] = ns.status
    elif action == "trash":
        flags["run_name"] = ns.run_name
        flags["trash_paths"] = ",".join(ns.paths)
    elif action == "restrict":
        flags["restrict_paths"] = ",".join(ns.paths)
    elif action == "decide":
        flags["id"] = ns.id
        flags["kind"] = ns.kind
        flags["decide_action"] = ns.decide_action
        flags["target"] = ns.target
        flags["path"] = ns.path
        flags["decision"] = ns.decision
        flags["date"] = getattr(ns, "date", "")
        flags["undo"] = getattr(ns, "undo", "") or ""
    elif action == "wait":
        flags["timeout_min"] = str(getattr(ns, "timeout_min", 90))

    request = SkillsRequest(op=SkillsOp.TRACES, flags=flags)
    result = aggregate.execute(request)

    if action == "get":
        status = result.state
        if status in (
            TraceStateStatus.COLLECTED,
            TraceStateStatus.RUNNING,
        ):
            # "exit 3 while a run is pending" domain signal
            return 3
        print(f"Pending status: {status}")
        return 0

    if action == "set":
        print(f"Status set: {result.state}")
        return 0

    if action == "clear":
        print(f"Pending cleared: {result.state}")
        return 0

    if action == "trash":
        for line in result.lines or ():
            print(line)
        return 0

    if action == "restrict":
        for line in result.lines or ():
            print(line)
        return 0

    if action == "decide":
        for line in result.lines or ():
            print(line)
        return 0

    if action == "wait":
        status = result.state_status
        if status == TraceStateStatus.REPORT_READY:
            return _EXIT_WAIT_READY
        if status == TraceStateStatus.PHASE_STALL:
            return _EXIT_WAIT_PHASE_STALL
        if status == TraceStateStatus.REPORT_STALL:
            return _EXIT_WAIT_REPORT_STALL
        if status == TraceStateStatus.DEADLINE:
            return _EXIT_WAIT_DEADLINE
        print(f"Wait ended: {status}")
        return 0

    return 0


__all__ = [
    "cmd_traces",
]
