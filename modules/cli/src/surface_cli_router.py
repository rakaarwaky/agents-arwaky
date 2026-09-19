"""CLI router — dispatch table for the agents-arwaky CLI (surface layer).

Strict 1:1 verbatim port of the original ``tools/cli/arwaky.py`` dispatcher:
every command string / alias, the per-verb dispatch table, and the
unknown-command fallback (err + blank line + help) are preserved.

The `main()` entry point lives here (surface). It handles global flags
(--no-color / --force-color / -v / -q) and routes to the verb handlers
owned by `modules.root_cli_entry`.
"""
from __future__ import annotations

import sys

from modules.root_cli_entry import (
    cmd_9router,
    cmd_anytype,
    cmd_backup,
    cmd_check,
    cmd_clean,
    cmd_completion,
    cmd_connect,
    cmd_disconnect,
    cmd_docs,
    cmd_doctor,
    cmd_help,
    cmd_install,
    cmd_list,
    cmd_mcp,
    cmd_reset,
    cmd_restore,
    cmd_run,
    cmd_service,
    cmd_skill,
    cmd_status,
    cmd_submodules,
    cmd_tool,
    cmd_uninstall,
    cmd_update,
    cmd_version,
    _gen_correlation_id,
    _init_sentry,
)
from modules.shared.src.utility_logging_setup import err, set_color_mode, set_verbosity


def dispatch(argv: list[str], ctx: dict | None = None) -> int:
    """Route argv[0] to the right verb handler.

    *ctx* is accepted for backward compatibility with existing callers that
    pass a pre-built feature-container dict, but is not required.
    """
    if not argv:
        return cmd_help([])
    cmd = argv[0]
    rest = argv[1:]
    dispatch_table = {
        # Meta / status
        "status": cmd_status, "doctor": cmd_doctor,
        "check": cmd_check, "submodules": cmd_submodules, "clean": cmd_clean,
        "reset": cmd_reset, "version": cmd_version, "--version": cmd_version,
        "help": cmd_help, "-h": cmd_help, "--help": cmd_help,
        # Core noun-verb (canonical)
        "tool": cmd_tool, "skill": cmd_skill, "skills": cmd_skill,
        "docs": cmd_docs,
        "connect": cmd_connect, "disconnect": cmd_disconnect,
        "mcp": cmd_mcp, "completion": cmd_completion,
        # Daemons & services
        "anytype": cmd_anytype, "9router": cmd_9router, "service": cmd_service,
        "backup": cmd_backup, "restore": cmd_restore,
        # Backward compat aliases → noun verb (deprecated, prefer aa tool/aa skill)
        "install": cmd_install, "update": cmd_update, "uninstall": cmd_uninstall,
        "list": cmd_list, "ls": cmd_list, "run": cmd_run,
    }
    handler = dispatch_table.get(cmd)
    if not handler:
        err(f"Unknown command: {cmd}")
        print()
        cmd_help([])
        return 1
    return handler(rest)


def main(argv: list[str]) -> int:
    """Top-level CLI entry point: init sentry, parse global flags, dispatch."""
    _init_sentry()
    import os
    os.environ["ARWAKY_CORRELATION_ID"] = _gen_correlation_id()
    if not argv:
        return cmd_help([])
    # Global flag: --no-color / --plain
    if "--no-color" in argv or "--plain" in argv:
        set_color_mode(False)
        argv = [a for a in argv if a not in ("--no-color", "--plain")]
    if "--force-color" in argv:
        set_color_mode(True)
        argv = [a for a in argv if a != "--force-color"]
    # Global verbosity: -v / --verbose, -q / --quiet
    if "-v" in argv or "--verbose" in argv:
        set_verbosity("debug")
        argv = [a for a in argv if a not in ("-v", "--verbose")]
    if "-q" in argv or "--quiet" in argv:
        set_verbosity("warning")
        argv = [a for a in argv if a not in ("-q", "--quiet")]
    return dispatch(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
