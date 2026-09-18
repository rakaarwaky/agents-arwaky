"""CLI router — big dispatch table for the agents-arwaky CLI.

Strict 1:1 verbatim port of the original tools/cli/arwaky.py ``main()``
dispatcher: every command string / alias, the per-verb dispatch table, the
unknown-command fallback (err + blank line + help), and the handler(rest)
return are preserved exactly as written in the original. Handlers are the
module-level verb functions in :mod:`modules.cli.src.root_cli_entry`
(local bodies where the original had them; thin delegation to the module
surface functions for verbs whose original body now lives in a module
feature).
"""
from __future__ import annotations

from modules.root_cli_entry import (
    cmd_check,
    cmd_clean,
    cmd_completion,
    cmd_connect,
    cmd_disconnect,
    cmd_docs,
    cmd_doctor,
    cmd_help,
    cmd_9router,
    cmd_install,
    cmd_list,
    cmd_mcp,
    cmd_reset,
    cmd_backup,
    cmd_restore,
    cmd_run,
    cmd_service,
    cmd_skill,
    cmd_status,
    cmd_submodules,
    cmd_sync,
    cmd_tool,
    cmd_uninstall,
    cmd_update,
    cmd_version,
    cmd_anytype,
)
from modules.shared.src.utility_logging import err


def dispatch(argv: list[str], ctx: dict | None = None) -> int:
    """Route argv[0] to the right verb handler.

    *ctx* is accepted for backward compatibility with existing callers that
    pass a pre-built feature-container dict, but is not required: the
    original arwaky.py dispatcher routed by direct function reference and
    is reproduced here verbatim.
    """
    if not argv:
        return cmd_help([])
    cmd = argv[0]
    rest = argv[1:]
    dispatch = {
        # Meta / status
        "status": cmd_status, "doctor": cmd_doctor,
        "check": cmd_check, "submodules": cmd_submodules, "clean": cmd_clean,
        "reset": cmd_reset, "version": cmd_version, "--version": cmd_version,
        "help": cmd_help, "-h": cmd_help, "--help": cmd_help,
        # Core noun-verb (canonical)
        "tool": cmd_tool, "skill": cmd_skill, "skills": cmd_skill,
        "docs": cmd_docs,
        "connect": cmd_connect, "disconnect": cmd_disconnect,
        "mcp": cmd_mcp, "sync": cmd_sync, "completion": cmd_completion,
        # Daemons & services
        "anytype": cmd_anytype, "9router": cmd_9router, "service": cmd_service,
        "backup": cmd_backup, "restore": cmd_restore,
        # Backward compat aliases → noun verb (deprecated, prefer aa tool/aa skill)
        "install": cmd_install, "update": cmd_update, "uninstall": cmd_uninstall,
        "list": cmd_list, "ls": cmd_list, "run": cmd_run,
    }
    handler = dispatch.get(cmd)
    if not handler:
        err(f"Unknown command: {cmd}")
        print()
        cmd_help([])
        return 1
    return handler(rest)
