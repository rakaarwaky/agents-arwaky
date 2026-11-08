"""Skills CLI surface — command handlers for the ``sac`` verbs.

Agent-oriented commands: read-only discovery (``list``/``read``), the lint
scan (``lint``), the catalog builder/reader (``catalog``), the search
(``discover``), the mutation verbs (``move``/``archive``/``create``), and the
lifecycle verbs (``status``/``usage``/``run``/``pause``/``resume``/
``pin``/``unpin``/``lock``/``unlock``/``restore``/``list-unmanaged``/
``list-archived``/``prune``/``purge``/``adopt``/``backup``/``rollback``/
``ledger``).

The pack root is always the repository's ``skills/`` pack; there is no
``--skills-root`` override and no JSON export — output is a terminal
listing consumed by the agent.

The aggregate is injected by the caller (the root CLI), never imported
here, so no root→surface coupling exists (AES205). Argv becomes a
``SkillsRequest``; the rendered text comes back on ``SkillsResult``.

Exit-code contract (primary agent-readable state signal — 0 clean /
1 issues found / 2 usage error / 3 catalog drift):
  0 clean      lint passed, listing built, read/mutation applied
  1 issues     lint issues found, or a non-usage runtime failure
  2 usage      bad argv, unknown skill/verb, missing required arg
  3 drift      catalog drift or corrupt (agent-level check; not
               exposed as a CLI flag)

Status-prefix vocabulary (agent-readable; color never carries
meaning, so the textual prefix is the entire signal):
  [OK]      success
  [FAIL]    error (stderr)
  [WARN]    warning
  [DRY-RUN] mutation plan (no write)
  [APPLIED] mutation write performed
Data rows carry no prefix; status lines always do.
"""

from __future__ import annotations

import argparse
import sys

from shared.src.observability.utility_logging_setup import (
    BOLD,
    CYAN,
    RESET,
    banner,
    err,
    info,
)
from shared.src.design.contract_skills_aggregate import ISkillsAggregate
from shared.src.common.taxonomy_common_error import SkillsUsageError
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)

_EXIT_USAGE = SkillsExitCode.USAGE_ERROR
_EXIT_DRIFT = SkillsExitCode.CATALOG_DRIFT

#: Lifecycle verbs mapped to SkillsOp values — flat top-level commands.
_LIFECYCLE_OPS = {
    "status": SkillsOp.STATUS,
    "usage": SkillsOp.USAGE,
    "run": SkillsOp.RUN,
    "pause": SkillsOp.PAUSE,
    "resume": SkillsOp.RESUME,
    "pin": SkillsOp.PIN,
    "unpin": SkillsOp.UNPIN,
    "lock": SkillsOp.LOCK,
    "unlock": SkillsOp.UNLOCK,
    "restore": SkillsOp.RESTORE,
    "list-unmanaged": SkillsOp.LIST_UNMANAGED,
    "list-archived": SkillsOp.LIST_ARCHIVED,
    "prune": SkillsOp.PRUNE,
    "purge": SkillsOp.PURGE,
    "adopt": SkillsOp.ADOPT,
    "backup": SkillsOp.BACKUP,
    "rollback": SkillsOp.ROLLBACK,
    "ledger": SkillsOp.LEDGER,
}

#: The results table header/separator and empty-result line, verbatim from
#: the legacy command (presentation strings, owned by the surface).
_NO_MATCH_LINE = "No matching skills found in catalog.json."


def cmd_skills(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Route ``sac <sub>`` to the aggregate; render; return the exit code."""
    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        return 0

    sub = args[0]
    rest = args[1:]

    if sub == "skills":
        err("Remove the legacy 'skills' subcommand: use 'sac list' instead of 'sac skills list'")
        return _EXIT_USAGE
    if sub in ("list", "ls"):
        return _cmd_list(rest, aggregate)
    if sub == "read":
        return _cmd_read(rest, aggregate)
    if sub in ("lint", "catalog", "discover", "move", "archive", "create"):
        return _cmd_authoring(sub, rest, aggregate)
    if sub == "phrases":
        return _cmd_phrases(rest, aggregate)
    if sub in _LIFECYCLE_OPS:
        return _cmd_lifecycle(sub, rest, aggregate)
    err(f"Unknown skills subcommand: {sub}")
    _print_usage()
    return _EXIT_USAGE


def _cmd_lifecycle(sub: str, rest: list[str], aggregate: ISkillsAggregate) -> int:
    """Route a flat lifecycle verb to the aggregate; render; return exit code."""
    op = _LIFECYCLE_OPS[sub]
    parser = _lifecycle_verb_parser(sub)
    try:
        namespace = parser.parse_args(rest)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    query = getattr(namespace, "query", "") or ""
    flags: dict[str, object] = {}
    for key in ("days", "dry_run", "apply", "compact", "id"):
        if hasattr(namespace, key):
            value = getattr(namespace, key)
            if value is not None:
                if key == "compact":
                    flags[key] = "1" if value else "0"
                else:
                    flags[key] = value

    request = SkillsRequest(op=op, query=query, flags=flags, apply=bool(flags.get("apply", False)))
    result = aggregate.execute(request)

    return _render_lifecycle(sub, op, result)


def _cmd_phrases(rest: list[str], aggregate: ISkillsAggregate) -> int:
    """Route ``sac phrases`` to the traces agent; render repeated phrases."""
    parser = argparse.ArgumentParser(prog="sac phrases", add_help=True)
    parser.add_argument("--grok-home", metavar="DIR", default="", help="$GROK_HOME directory")
    parser.add_argument("--run-dir", metavar="DIR", default="", help="Run dir to write session records into")
    parser.add_argument("--days", type=str, default="0", help="Only keep sessions within N days")
    parser.add_argument("--since-last", action="store_true", default=False, help="Skip sessions processed in a prior run")
    parser.add_argument("--min-turns", type=str, default="1", help="Minimum human turns per kept session")
    parser.add_argument("--limit", type=str, default="0", help="Max sessions to keep")
    parser.add_argument("--min-sessions", type=str, default="2", help="Minimum distinct sessions for a phrase to count")
    parser.add_argument("--json", action="store_true", default=False, help="Emit JSON")
    try:
        namespace = parser.parse_args(rest)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    run_dir = getattr(namespace, "run_dir", "") or ""
    flags: dict[str, object] = {
        "traces_action": "phrases",
        "grok_home": getattr(namespace, "grok_home", "") or "",
        "run_dir": run_dir,
        "days": str(getattr(namespace, "days", "0") or "0"),
        "since_last": "1" if getattr(namespace, "since_last", False) else "0",
        "min_turns": str(getattr(namespace, "min_turns", "1") or "1"),
        "limit": str(getattr(namespace, "limit", "0") or "0"),
        "min_sessions": str(getattr(namespace, "min_sessions", "2") or "2"),
    }
    request = SkillsRequest(op=SkillsOp.TRACES, flags=flags)
    result = aggregate.execute(request)

    return _render_phrases(result, getattr(namespace, "json", False), run_dir)


def _render_phrases(result: SkillsResult, json_mode: bool, run_dir: str) -> int:
    """Render a phrases result and return its exit code."""
    if not result.ok:
        err(result.message)
        return result.exit_code if result.exit_code != 0 else _EXIT_USAGE

    exact = result.phrases_exact or ()
    stems = result.phrases_stems or ()
    lines = result.phrases_lines or ()

    if json_mode:
        import json as _json

        print(
            _json.dumps(
                {
                    "run_dir": run_dir,
                    "exact_prompts": [
                        {
                            "phrase": r.phrase,
                            "sessions": r.sessions,
                            "occurrences": r.occurrences,
                            "session_ids": list(r.session_ids),
                        }
                        for r in exact
                    ],
                    "prompt_stems_12_words": [
                        {
                            "phrase": r.phrase,
                            "sessions": r.sessions,
                            "occurrences": r.occurrences,
                            "session_ids": list(r.session_ids),
                        }
                        for r in stems
                    ],
                    "repeated_instruction_lines": [
                        {
                            "phrase": r.phrase,
                            "sessions": r.sessions,
                            "occurrences": r.occurrences,
                            "session_ids": list(r.session_ids),
                        }
                        for r in lines
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    info(f"[OK] phrases — {result.message}")
    if exact:
        info(f"{len(exact)} repeated exact prompt(s):")
        for r in exact:
            info(f"  [{r.sessions} sessions / {r.occurrences} occurrences] {r.phrase}")
    if stems:
        info(f"{len(stems)} repeated prompt stem(s):")
        for r in stems:
            info(f"  [{r.sessions} sessions / {r.occurrences} occurrences] {r.phrase}")
    if lines:
        info(f"{len(lines)} repeated instruction line(s):")
        for r in lines:
            info(f"  [{r.sessions} sessions / {r.occurrences} occurrences] {r.phrase}")
    if not exact and not stems and not lines:
        info("  No repeated phrases found.")
    return 0


def _lifecycle_verb_parser(sub: str) -> argparse.ArgumentParser:
    """Build the argparse parser for one lifecycle verb."""
    parser = argparse.ArgumentParser(prog=f"sac {sub}", add_help=True)
    if sub in ("pin", "unpin", "lock", "unlock", "restore", "adopt"):
        parser.add_argument("query")
        parser.add_argument("--apply", action="store_true", default=False)
    elif sub == "archive":
        parser.add_argument("query")
        parser.add_argument("--apply", action="store_true", default=False)
    elif sub == "prune":
        parser.add_argument("--days", type=str, default=None)
        parser.add_argument("--dry-run", action="store_true", default=False)
        parser.add_argument("--apply", action="store_true", default=False)
    elif sub == "purge":
        parser.add_argument("--days", type=str, default=None)
        parser.add_argument("--dry-run", action="store_true", default=False)
        parser.add_argument("--apply", action="store_true", default=False)
    elif sub == "rollback":
        parser.add_argument("--id", type=str, default=None)
    elif sub == "ledger":
        parser.add_argument("--compact", action="store_true", default=False)
    return parser


def _render_lifecycle(sub: str, op: SkillsOp, result: SkillsResult) -> int:
    """Render a lifecycle result and return its exit code."""
    if not result.ok:
        err(f"{result.message}")
        return result.exit_code if result.exit_code != 0 else _EXIT_USAGE

    exit_code = result.exit_code

    if sub == "status":
        return _render_status(result)
    if sub == "usage":
        return _render_usage(result)
    if sub == "run":
        return _render_run(result)
    if sub in ("pause", "resume"):
        return _render_pause_resume(op, result)
    if sub in ("pin", "unpin", "lock", "unlock", "adopt"):
        return _render_bool(sub, result)
    if sub == "restore":
        return _render_archive_restore(op, result)
    if sub == "list-unmanaged":
        return _render_list_unmanaged(result)
    if sub == "list-archived":
        return _render_list_archived(result)
    if sub == "prune":
        return _render_prune(result)
    if sub == "purge":
        return _render_purge(result)
    if sub == "backup":
        return _render_backup(result)
    if sub == "rollback":
        return _render_rollback(result)
    if sub == "ledger":
        return _render_ledger(result)

    return exit_code


def _render_status(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] status — {len(records)} state row(s)")
    if records:
        for rec in records:
            info(f"  {rec}")
    return 0


def _render_usage(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] usage — {len(records)} skill row(s)")
    if records:
        for rec in records:
            info(f"  {rec}")
    return 0


def _render_run(result: SkillsResult) -> int:
    info(f"[OK] run — {result.message}")
    return 0


def _render_pause_resume(op: SkillsOp, result: SkillsResult) -> int:
    action = "paused" if op == SkillsOp.PAUSE else "resumed"
    info(f"[OK] lifecycle {action}")
    return 0


def _render_bool(sub: str, result: SkillsResult) -> int:
    info(f"[OK] {sub} — {result.message}")
    return 0


def _render_archive_restore(op: SkillsOp, result: SkillsResult) -> int:
    if result.exit_code == SkillsExitCode.CLEAN:
        info(f"[APPLIED] archive/restore — {result.message}")
    else:
        info(f"[OK] archive/restore — {result.message}")
    return 0


def _render_list_unmanaged(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] list-unmanaged — {len(records)} unmanaged skill(s)")
    for rec in records:
        info(f"  {rec}")
    return 0


def _render_list_archived(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] list-archived — {len(records)} archived skill(s)")
    for rec in records:
        info(f"  {rec}")
    return 0


def _render_prune(result: SkillsResult) -> int:
    pruned = result.records or ()
    dry_run = False
    if "'dry_run': True" in str(result.message) or '"dry_run": true' in str(result.message):
        dry_run = True
    prefix = "[DRY-RUN]" if dry_run else "[OK]"
    info(f"{prefix} prune — {len(pruned)} pruned; {result.message}")
    return 0


def _render_purge(result: SkillsResult) -> int:
    info(f"[OK] purge — {result.message}")
    return 0


def _render_backup(result: SkillsResult) -> int:
    info(f"[OK] backup — {result.content or result.message}")
    return 0


def _render_rollback(result: SkillsResult) -> int:
    info(f"[OK] rollback — {result.message}")
    return 0


def _render_ledger(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] ledger — {len(records)} record(s)")
    for rec in records:
        info(f"  {rec}")
    return 0


def _print_usage() -> None:
    banner()
    info(f"{BOLD()}Modes (agent-level):{RESET()}")
    info("  --create  ->  sac create skill|category")
    info("  --improve ->  sac lint -> sac read -> edit -> sac catalog")
    info("  --prune   ->  sac discover -> sac move|archive")
    print()
    info(f"{BOLD()}Discovery:{RESET()}")
    info(f"{BOLD()}sac list{RESET()}                          List all skills in the pack")
    info(f"{BOLD()}sac read <name>{RESET()}                   Print a skill's SKILL.md")
    info(f"{BOLD()}sac lint [--category NAME]{RESET()}        Lint scan all skills (optionally filter by category)")
    info(f"{BOLD()}sac catalog [--build] [--read]{RESET()}    Build and/or print catalog.json")
    info(f"{BOLD()}sac discover <query>{RESET()}             Search the catalog")
    print()
    info(f"{BOLD()}Observation:{RESET()}")
    info(f"{BOLD()}sac phrases [--grok-home DIR] [--run-dir DIR] [--days N]{RESET()}  "
         "Mine repeated user prompts from session traces")
    info(f"{BOLD()}sac phrases [--since-last] [--min-turns N] [--limit N]{RESET()}      "
         "[--min-sessions N] [--json]")
    print()
    info(f"{BOLD()}Mutations:{RESET()}")
    info(f"{BOLD()}sac move <name> <category> [--apply]{RESET()}  Move a skill to a category")
    info(f"{BOLD()}sac archive <name> [--apply]{RESET()}     Archive a skill into _archive/")
    info(f"{BOLD()}sac create <kind> <name> [--category C] [--apply]{RESET()}  "
         "Create a skill or category")
    print()
    info(f"{BOLD()}Lifecycle:{RESET()}")
    info(f"{BOLD()}sac status{RESET()}                        Show per-skill lifecycle states")
    info(f"{BOLD()}sac usage{RESET()}                         Show usage telemetry rows")
    info(f"{BOLD()}sac run{RESET()}                           Run automated state transitions")
    info(f"{BOLD()}sac pause{RESET()}                         Pause automatic transitions")
    info(f"{BOLD()}sac resume{RESET()}                        Resume automatic transitions")
    info(f"{BOLD()}sac pin <skill>{RESET()}                   Pin a skill in active state")
    info(f"{BOLD()}sac unpin <skill>{RESET()}                 Unpin a skill")
    info(f"{BOLD()}sac lock <skill>{RESET()}                  Lock a skill from mutation")
    info(f"{BOLD()}sac unlock <skill>{RESET()}                Unlock a skill")
    info(f"{BOLD()}sac adopt <skill>{RESET()}                 Mark skill as agent-managed")
    print()
    info(f"{BOLD()}Archive & Restore:{RESET()}")
    info(f"{BOLD()}sac restore <skill>{RESET()}               Restore an archived skill")
    info(f"{BOLD()}sac list-unmanaged{RESET()}                List skills without telemetry")
    info(f"{BOLD()}sac list-archived{RESET()}                 List archived skills")
    info(f"{BOLD()}sac prune [--days N] [--apply]{RESET()}    Bulk archive idle skills")
    info(f"{BOLD()}sac purge [--days N] [--apply]{RESET()}    Permanently remove archived skills")
    print()
    info(f"{BOLD()}Backup & Rollback:{RESET()}")
    info(f"{BOLD()}sac backup{RESET()}                        Create a snapshot of skills pack")
    info(f"{BOLD()}sac rollback [--id ID]{RESET()}            Restore from snapshot")
    info(f"{BOLD()}sac ledger [--compact]{RESET()}            View or compact audit ledger")
    print()
    info(f"{BOLD()}Note:{RESET()} move/archive/create are dry-run by default; pass --apply to write.")
    info(
        f"{BOLD()}Exit codes:{RESET()} 0 clean | 1 issues found | 2 usage error | 3 catalog drift"
    )


# ─── Read-only surface ──────────────────────────────────────
def _has_help(args: list[str]) -> bool:
    return any(a in ("-h", "--help") for a in args)


def _cmd_list(args: list[str], aggregate: ISkillsAggregate) -> int:
    """List every skill in the pack as a compact table."""
    if _has_help(args):
        info("Usage: sac list — list all skills in the pack")
        return 0
    result = aggregate.execute(SkillsRequest(op=SkillsOp.LIST))
    rows = list(result.records)
    if not result.ok or not rows:
        if result.exit_code == _EXIT_USAGE and result.message:
            print(f"ERROR: {result.message}", file=sys.stderr)
            return _EXIT_USAGE
        # Empty pack is a valid empty state (new user/agent, no skills
        # yet) — exit 0 with onboarding guidance, not an error.
        info("No skills in the pack yet.")
        info("Create one: sac create skill <name> --category <cat> --apply")
        return 0
    print(f"{CYAN()}SKILL{RESET()}".ljust(28) + "DESCRIPTION")
    print("-" * 28 + " " + "-" * 60)
    truncated = False
    for record in rows:
        desc = (record.description or "").replace("\n", " ")
        if len(desc) > 70:
            desc = desc[:69] + "…"
            truncated = True
        print(record.name.ljust(28) + " " + desc)
    if truncated:
        print("Tip: sac read <name> for full content")
    print(f"\n{BOLD()}{len(rows)}{RESET()} skills in the pack.")
    return 0


def _cmd_read(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Print the raw SKILL.md for one skill."""
    if _has_help(args) or not args:
        info("Usage: sac read <name>")
        return 0
    name = args[0]
    result = aggregate.execute(
        SkillsRequest(op=SkillsOp.READ, query=SkillQuery(name))
    )
    if not result.ok or result.content is None:
        err("Skill not found")
        return 1
    print(result.content)
    return 0


# ─── Authoring parser ────────────────────────────────────────────────
class _TriFlag(argparse.Action):
    """argparse action: unset stays None, set → True.

    ``store_true`` coerces a ``None`` default to ``False``, which would
    hide the "flag absent" state the surface needs to resolve the
    default (neither ``--build`` nor ``--read`` → both).
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | None,
        option_string: str | None = None,
    ) -> None:
        setattr(namespace, self.dest, True)


def _authoring_parser() -> argparse.ArgumentParser:
    """Construct the authoring CLI; exported so tests can drive it directly."""
    parser = argparse.ArgumentParser(
        prog="sac",
        description="Skill-pack tooling: lint, catalog, discover.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("lint", help="Lint scan all skills (optionally filter by category)")
    sub.add_argument(
        "--category",
        metavar="NAME",
        default=None,
        help="Only report issues in category NAME",
    )

    sub = subparsers.add_parser("catalog", help="Build and/or read catalog.json")
    sub.add_argument(
        "--build",
        action=_TriFlag,
        nargs=0,
        default=None,
        help="Rebuild catalog.json from the live tree",
    )
    sub.add_argument(
        "--read",
        action=_TriFlag,
        nargs=0,
        default=None,
        help="Print the current catalog.json content",
    )
    sub.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Verify catalog.json matches the live tree (drift gate; never writes)",
    )

    sub = subparsers.add_parser("discover", help="Search catalog.json")
    sub.add_argument("query", help="Search query")
    sub.add_argument("--limit", type=int, default=20, help="Maximum results")

    sub = subparsers.add_parser("move", help="Move a skill to a category")
    sub.add_argument("skill", help="Skill name to move")
    sub.add_argument("category", help="Target category")
    sub.add_argument("--apply", action="store_true", help="Apply the move")

    sub = subparsers.add_parser("archive", help="Archive a skill into _archive/")
    sub.add_argument("skill", help="Skill name to archive")
    sub.add_argument("--apply", action="store_true", help="Apply the archive")

    sub = subparsers.add_parser("create", help="Create a skill or category")
    sub.add_argument("kind", choices=["skill", "category"], help="Kind to create")
    sub.add_argument("name", help="Name of the skill or category")
    sub.add_argument("--category", metavar="CAT", help="Target category (skill only)")
    sub.add_argument("--description", default="", help="Description")
    sub.add_argument("--force", action="store_true", help="Force (category only)")
    sub.add_argument("--apply", action="store_true", help="Apply the create")

    return parser


def _cmd_authoring(sub: str, rest: list[str], aggregate: ISkillsAggregate) -> int:
    """Parse an authoring subcommand and render its result."""
    try:
        namespace = _authoring_parser().parse_args([sub, *rest])
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    request = _build_request(namespace)
    result = aggregate.execute(request)

    if not result.ok and result.exit_code == _EXIT_USAGE:
        # The legacy ``fail()`` channel prints the ERROR line verbatim on
        # stderr (no banner prefix); callers and older tests parse it.
        print(f"ERROR: {result.message}", file=sys.stderr)
        return result.exit_code

    if sub == "lint":
        return _render_lint(result, request)
    if sub == "catalog":
        return _render_catalog(result, request)
    if sub == "discover":
        return _render_discover(result, request)
    if sub in ("move", "archive", "create"):
        return _render_mutation(sub, result, request)
    raise SkillsUsageError(f"Unknown skills subcommand: {sub}")


def _build_request(namespace: argparse.Namespace) -> SkillsRequest:
    """Map parsed argv onto the request the domain understands."""
    command = namespace.command

    if command == "lint":
        return SkillsRequest(
            op=SkillsOp.LINT,
            flags={"category": namespace.category or ""},
        )

    if command == "catalog":
        if namespace.check:
            return SkillsRequest(
                op=SkillsOp.CATALOG,
                flags={"check": "1"},
            )
        # Tri-state: no flag at all → both (the convenient agent default:
        # build then print). An explicit flag pins its value; the other
        # flag defaults to False.
        if namespace.build is None and namespace.read is None:
            build, read = True, True
        elif namespace.build is None:
            build, read = False, True  # --read only
        elif namespace.read is None:
            build, read = True, False  # --build only
        else:
            build, read = namespace.build, namespace.read  # both explicit
        return SkillsRequest(
            op=SkillsOp.CATALOG,
            flags={
                "build": "1" if build else "0",
                "read": "1" if read else "0",
            },
        )

    if command == "discover":
        return SkillsRequest(
            op=SkillsOp.DISCOVER,
            query=SkillQuery(namespace.query),
            flags={"limit": str(namespace.limit)},
        )

    if command == "move":
        return SkillsRequest(
            op=SkillsOp.MOVE,
            query=SkillQuery(namespace.skill),
            apply=namespace.apply,
            flags={"target": namespace.category},
        )

    if command == "archive":
        return SkillsRequest(
            op=SkillsOp.ARCHIVE,
            query=SkillQuery(namespace.skill),
            apply=namespace.apply,
        )

    if command == "create":
        if namespace.kind == "skill":
            flags = {"kind": "skill"}
            if namespace.category:
                flags["category"] = namespace.category
        else:
            flags = {"kind": "category"}
            if namespace.force:
                flags["force"] = "1"
        return SkillsRequest(
            op=SkillsOp.CREATE,
            query=SkillQuery(namespace.name),
            description=namespace.description,
            apply=namespace.apply,
            flags=flags,
        )

    raise SkillsUsageError(f"Unknown skills subcommand: {command}")


# ─── Renderers ───────────────────────────────────────────────────────
def _render_catalog(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the catalog build / read output."""
    if request.flags.get("check") == "1":
        check = result.check
        if check is None:
            err("Internal error: no catalog check produced")
            return 1
        if check.in_sync:
            print(f"[OK] catalog.json is in sync with the live tree")
            return result.exit_code
        err(check.message or "catalog.json drifted from the live tree")
        return result.exit_code or 3

    build = request.flags.get("build", "1") == "1"
    read = request.flags.get("read", "1") == "1"

    if build:
        report = result.catalog
        if report is None:
            err("Internal error: no catalog report produced")
            return 1
        print(f"Rebuilt {report.path}")
        print(f"Categories: {report.categories}; skills: {report.skills}")

    if read:
        text = result.catalog_text
        if not text:
            if result.message:
                err(result.message)
            else:
                err("catalog.json not found — run with --build first")
            info("Tip: sac catalog --build to generate catalog.json")
            return result.exit_code or 1
        print(text)

    return 0


def _render_discover(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the scored matches as a compact agent-oriented list.

    One line per skill: ``<name>  <when-to-use (truncated)>``.
    No category, no score column, no path — just the ranked skill
    names the agent needs to pick from, with the actionable reason
    inlined.
    """
    if result.warning:
        print(result.warning, file=sys.stderr)
        if result.message:
            print(f"  reason: {result.message}", file=sys.stderr)

    if not result.matches:
        print(_NO_MATCH_LINE)
        return 0

    for match in result.matches:
        desc = match.when_to_use or match.description
        if len(desc) > 100:
            desc = desc[:97] + "…"
        print(f"{match.skill:28s} {desc}")
    return 0


def _render_lint(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a lint report, narrowed by --category."""
    report = result.lint_report
    if report is None:
        err("Internal error: no lint report produced")
        return 1

    total = report.unfiltered_issue_count
    in_scope = report.issue_count

    if total == 0:
        print("No lint issues found.")
        return 0

    if request.flags.get("category"):
        category = request.flags["category"]
        if in_scope == 0 and total > 0:
            print(f"No issues in category '{category}'. {total} issue(s) in other categories:")
        else:
            print(f"{total} lint issue(s) found ({in_scope} in scope category={category}):")
    else:
        print(f"{total} lint issue(s) found:")

    for issue in report.issues:
        print(f"- [{issue.type}] {issue.locator}: {issue.message}")
    for line in report.weed_lines:
        print(f"- {line}")
    return 1


def _render_mutation(sub: str, result: SkillsResult, request: SkillsRequest) -> int:
    """Render a move / archive / create result (plan or applied outcome)."""
    if not result.ok:
        if result.message:
            err(result.message)
        return result.exit_code or 1

    # Plan (default, no --apply): show the plan and stop.
    if not request.apply:
        plan = result.plan or result.create_plan or result.new_category
        if plan is not None:
            _print_mutation_plan(sub, plan)
            print("No files were modified. Pass --apply to execute.")
        elif result.message:
            print(result.message)
            print("No files were modified. Pass --apply to execute.")
        return 0

    # Applied: show the outcome.
    outcome = result.outcome
    if outcome is not None:
        print(f"[APPLIED] {sub.capitalize()} applied:")
        for line in outcome.applied:
            print(f"  [APPLIED] {line}")
        if outcome.message:
            print(f"  [APPLIED] {outcome.message}")
    elif result.message:
        print(result.message)
    else:
        print(f"[APPLIED] {sub.capitalize()} applied.")
    print("Files written.")
    return 0


def _print_mutation_plan(sub: str, plan: object) -> None:
    """Print a dry-run mutation plan (no write) from its real VO fields."""
    print(f"[DRY-RUN] Plan ({sub.capitalize()}) — pass --apply to write:")

    # SkillCreatePlan
    if hasattr(plan, "already_exists"):
        print(f"[DRY-RUN] skill: {plan.skill}")
        print(f"[DRY-RUN] category: {plan.category}")
        if getattr(plan, "already_exists", False):
            print("[DRY-RUN] already exists — nothing to do")
        return

    # NewCategoryPlan
    if hasattr(plan, "will_write"):
        print(f"[DRY-RUN] name: {plan.name}")
        if plan.description:
            print(f"[DRY-RUN] description: {plan.description}")
        if not plan.will_write:
            print("[DRY-RUN] DESCRIPTION.md already present — kept (use --force to overwrite)")
        return

    # MutationPlan (move / archive)
    if hasattr(plan, "already_in_category"):
        if getattr(plan, "already_in_category", False):
            print("[DRY-RUN] already in category — nothing to do")
        if getattr(plan, "source", None):
            print(f"[DRY-RUN] source: {plan.source}")
        if getattr(plan, "destination", None):
            print(f"[DRY-RUN] destination: {plan.destination}")
        for step in getattr(plan, "lines", ()):
            print(f"[DRY-RUN] {step}")
        return

    # Fallback: print whatever is available.
    for attr in ("kind", "source", "destination", "lines"):
        value = getattr(plan, attr, None)
        if value not in (None, "", False, ()):
            print(f"[DRY-RUN] {attr}: {value}")