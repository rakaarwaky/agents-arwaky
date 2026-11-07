"""Curator CLI surface — ``curator`` subcommand group for skill curation.

Nested subparser group with one subparser per curator verb (status, usage,
run, pause, resume, pin, unpin, lock, unlock, archive, restore, list-unmanaged,
list-archived, prune, purge, adopt, backup, rollback, ledger). Each handler
builds a ``SkillsRequest`` routed to the injected aggregate and renders
the ``SkillsResult`` with status-prefix vocabulary from the skills CLI
([OK] / [FAIL] / [WARN] / [DRY-RUN] / [APPLIED]) and the exit-code contract.

The aggregate is injected by the caller (the root CLI), never imported
here, so no root→surface coupling exists (AES205).

Curator verbs mirror the Hermes Agent Curator spec:
curator-cli.md, curator-lifecycle.md, curator-snapshot-rollback.md,
skill-telemetry.md, skill-audit-ledger.md.

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

#: Curator verbs mapped to SkillsOp values (design doc: PR 7 scope).
_CURATOR_OPS = {
    "status": SkillsOp.CURATOR_STATUS,
    "usage": SkillsOp.CURATOR_USAGE,
    "run": SkillsOp.CURATOR_RUN,
    "pause": SkillsOp.CURATOR_PAUSE,
    "resume": SkillsOp.CURATOR_RESUME,
    "pin": SkillsOp.CURATOR_PIN,
    "unpin": SkillsOp.CURATOR_UNPIN,
    "lock": SkillsOp.CURATOR_LOCK,
    "unlock": SkillsOp.CURATOR_UNLOCK,
    "archive": SkillsOp.CURATOR_ARCHIVE,
    "restore": SkillsOp.CURATOR_RESTORE,
    "list-unmanaged": SkillsOp.CURATOR_LIST_UNMANAGED,
    "list-archived": SkillsOp.CURATOR_LIST_ARCHIVED,
    "prune": SkillsOp.CURATOR_PRUNE,
    "purge": SkillsOp.CURATOR_PURGE,
    "adopt": SkillsOp.CURATOR_ADOPT,
    "backup": SkillsOp.CURATOR_BACKUP,
    "rollback": SkillsOp.CURATOR_ROLLBACK,
    "ledger": SkillsOp.CURATOR_LEDGER,
}


def cmd_skills_curator(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Route ``curator <verb> [args]`` to the aggregate; render; return exit code."""
    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        return 0

    sub = args[0]
    rest = args[1:]

    if sub not in _CURATOR_OPS:
        err(f"Unknown curator subcommand: {sub}")
        _print_usage()
        return _EXIT_USAGE

    op = _CURATOR_OPS[sub]
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
    """Build the argparse parser for one curator verb."""
    parser = argparse.ArgumentParser(prog=f"curator {sub}", add_help=False)
    if sub == "pin" or sub == "unpin" or sub == "lock" or sub == "unlock" or sub == "archive" or sub == "restore":
        parser.add_argument("query")
    elif sub == "prune":
        parser.add_argument("--days", type=str, default=None)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("-y", action="store_true", dest="apply")
    elif sub == "purge":
        parser.add_argument("query", nargs="?", default="")
        parser.add_argument("--dry-run", action="store_true")
    elif sub == "adopt":
        parser.add_argument("query")
    elif sub == "rollback":
        parser.add_argument("query", nargs="?", default="")
    elif sub == "ledger":
        parser.add_argument("--compact", action="store_true")
    return parser


def _render(sub: str, op: SkillsOp, result: SkillsResult) -> int:
    """Render a curator result and return its exit code."""
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
    if sub == "pause":
        return _render_pause_resume(op, result)
    if sub == "resume":
        return _render_pause_resume(op, result)
    if sub in ("pin", "unpin", "lock", "unlock"):
        return _render_bool(sub, result)
    if sub == "archive":
        return _render_archive_restore(op, result)
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
    if sub == "adopt":
        return _render_bool("adopt", result)
    if sub == "backup":
        return _render_backup(result)
    if sub == "rollback":
        return _render_rollback(result)
    if sub == "ledger":
        return _render_ledger(result)

    return exit_code


def _render_status(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] curator status — {len(records)} curator state row(s)")
    if records:
        for rec in records:
            info(f"  {rec}")
    return 0


def _render_usage(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] curator usage — {len(records)} skill row(s)")
    if records:
        for rec in records:
            info(f"  {rec}")
    return 0


def _render_run(result: SkillsResult) -> int:
    info(f"[OK] curator run — {result.message}")
    return 0


def _render_pause_resume(op: SkillsOp, result: SkillsResult) -> int:
    action = "paused" if op == SkillsOp.CURATOR_PAUSE else "resumed"
    info(f"[OK] curator {action}")
    return 0


def _render_bool(sub: str, result: SkillsResult) -> int:
    info(f"[OK] curator {sub} — {result.message}")
    return 0


def _render_archive_restore(op: SkillsOp, result: SkillsResult) -> int:
    if result.exit_code == SkillsExitCode.CLEAN:
        info(f"[APPLIED] curator archive/restore — {result.message}")
    else:
        info(f"[OK] curator archive/restore — {result.message}")
    return 0


def _render_list_unmanaged(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] curator list-unmanaged — {len(records)} unmanaged skill(s)")
    for rec in records:
        info(f"  {rec}")
    return 0


def _render_list_archived(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] curator list-archived — {len(records)} archived skill(s)")
    for rec in records:
        info(f"  {rec}")
    return 0


def _render_prune(result: SkillsResult) -> int:
    pruned = result.records or ()
    dry_run = False
    if "'dry_run': True" in str(result.message) or '"dry_run": true' in str(result.message):
        dry_run = True
    prefix = "[DRY-RUN]" if dry_run else "[OK]"
    info(f"{prefix} curator prune — {len(pruned)} pruned; {result.message}")
    return 0


def _render_purge(result: SkillsResult) -> int:
    info(f"[OK] curator purge — {result.message}")
    return 0


def _render_backup(result: SkillsResult) -> int:
    info(f"[OK] curator backup — {result.content or result.message}")
    return 0


def _render_rollback(result: SkillsResult) -> int:
    info(f"[OK] curator rollback — {result.message}")
    return 0


def _render_ledger(result: SkillsResult) -> int:
    records = result.records or ()
    info(f"[OK] curator ledger — {len(records)} entry(ies)")
    for rec in records:
        info(f"  {rec}")
    return 0


def _print_usage() -> None:
    banner()
    info(f"{BOLD()}Curator (agent-level):{RESET()}")
    info("  sdc curator status              Show config, paused state, grouped counts")
    info("  sdc curator usage               Telemetry for all skills")
    info("  sdc curator run                 Trigger a curator pass now")
    info("  sdc curator pause | resume      Pause or resume the curator")
    info("  sdc curator pin <skill>         Protect skill from auto-transitions")
    info("  sdc curator unpin <skill>       Unprotect skill")
    info("  sdc curator lock <skill>        User-declared content lock")
    info("  sdc curator unlock <skill>      Remove content lock")
    info("  sdc curator archive <skill>     Manually archive a skill")
    info("  sdc curator restore <skill>     Restore an archived skill")
    info("  sdc curator list-unmanaged      Skills without provenance marker")
    info("  sdc curator list-archived       Skills in _archive/")
    info("  sdc curator prune [--days N] [--dry-run] [-y]  Bulk-archive idle skills")
    info("  sdc curator purge [<skill>] [--dry-run]  Delete old archived skills")
    info("  sdc curator adopt <skill>       Mark skill as agent-managed")
    info("  sdc curator backup              Manual tar.gz snapshot")
    info("  sdc curator rollback [id]       Restore from snapshot / ledger entry")
    info("  sdc curator ledger [--compact]  Audit ledger + GC")
    print()
    info(f"{BOLD()}Exit codes:{RESET()} 0 clean | 1 issues found | 2 usage error")
