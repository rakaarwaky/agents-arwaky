"""Lifecycle CLI surface — command group for skill lifecycle management.

Nested subparser group with one subparser per lifecycle verb (status, usage,
run, pause, resume, pin, unpin, lock, unlock, archive, restore, list-unmanaged,
list-archived, prune, purge, adopt, backup, rollback, ledger). Each handler
builds a ``SkillsRequest`` routed to the injected aggregate and renders
the ``SkillsResult`` with status-prefix vocabulary from the skills CLI
([OK] / [FAIL] / [WARN] / [DRY-RUN] / [APPLIED]) and the exit-code contract.

The aggregate is injected by the caller (the root CLI), never imported
here, so no root→surface coupling exists (AES205).

Exit-code contract:
  0 clean   verb applied successfully
  1 issues  runtime failure / verb could not complete
  2 usage   bad argv, unknown skill, missing required arg
"""

from __future__ import annotations

import argparse

from shared.src.common.utility_logging_setup import BOLD, RESET, banner, err, info
from shared.src.skills_design.contract_skills_aggregate import ISkillsAggregate
from shared.src.skills_design.taxonomy_skills_request import SkillsOp, SkillsRequest
from shared.src.skills_design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)

_EXIT_USAGE = SkillsExitCode.USAGE_ERROR
_EXIT_ISSUES = SkillsExitCode.ISSUES_FOUND

#: Lifecycle verbs mapped to SkillsOp values.
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
    "archive": SkillsOp.ARCHIVE,
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


def cmd_skills_lifecycle(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Route ``lifecycle <verb> [args]`` to the aggregate; render; return exit code."""
    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        return 0

    sub = args[0]
    rest = args[1:]

    if sub not in _LIFECYCLE_OPS:
        err(f"Unknown lifecycle subcommand: {sub}")
        _print_usage()
        return _EXIT_USAGE

    op = _LIFECYCLE_OPS[sub]
    parser = _verb_parser(sub)
    try:
        namespace = parser.parse_args(rest)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    query = getattr(namespace, "query", "") or ""
    flags = {}
    for key in ("days", "dry_run", "apply", "compact", "id"):
        if hasattr(namespace, key):
            value = getattr(namespace, key)
            if value is not None:
                if key == "compact":
                    flags[key] = "1" if value else "0"
                else:
                    flags[key] = value

    request = SkillsRequest(op=op, query=query, flags=flags)
    result = aggregate.execute(request)

    return _render(sub, op, result)


def _verb_parser(sub: str) -> argparse.ArgumentParser:
    """Build the argparse parser for one lifecycle verb."""
    parser = argparse.ArgumentParser(prog=f"lifecycle {sub}", add_help=False)
    if sub in ("pin", "unpin", "lock", "unlock", "archive", "restore", "adopt"):
        parser.add_argument("query")
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


def _render(sub: str, op: SkillsOp, result: SkillsResult) -> int:
    """Render a lifecycle result and return its exit code."""
    if not result.ok:
        err(f"{result.message}")
        return result.exit_code if result.exit_code != 0 else _EXIT_ISSUES

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
    if sub in ("archive", "restore"):
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
    info(f"{BOLD()}sdc lifecycle <verb> [args]{RESET()}    Skill lifecycle management")
    print()
    info(f"{BOLD()}Status & Usage:{RESET()}")
    info("  sdc lifecycle status            Show per-skill lifecycle states")
    info("  sdc lifecycle usage             Show usage telemetry rows")
    info("  sdc lifecycle list-unmanaged    List skills without telemetry")
    info("  sdc lifecycle list-archived     List archived skills")
    print()
    info(f"{BOLD()}Controls:{RESET()}")
    info("  sdc lifecycle run               Run automated state transitions")
    info("  sdc lifecycle pause             Pause automatic transitions")
    info("  sdc lifecycle resume            Resume automatic transitions")
    info("  sdc lifecycle pin <skill>       Pin a skill in active state")
    info("  sdc lifecycle unpin <skill>     Unpin a skill")
    info("  sdc lifecycle lock <skill>      Lock a skill from mutation")
    info("  sdc lifecycle unlock <skill>    Unlock a skill")
    info("  sdc lifecycle adopt <skill>     Mark skill as agent-managed")
    print()
    info(f"{BOLD()}Archive & Restore:{RESET()}")
    info("  sdc lifecycle archive <skill>   Archive a skill")
    info("  sdc lifecycle restore <skill>   Restore an archived skill")
    info("  sdc lifecycle prune [--days N]  Bulk archive idle skills")
    info("  sdc lifecycle purge [--days N]  Permanently remove archived skills")
    print()
    info(f"{BOLD()}Backup & Rollback:{RESET()}")
    info("  sdc lifecycle backup            Create a snapshot of skills pack")
    info("  sdc lifecycle rollback [--id ID] Restore from snapshot")
    info("  sdc lifecycle ledger [--compact] View or compact audit ledger")
    print()
