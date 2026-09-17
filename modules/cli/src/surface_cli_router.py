"""CLI router — big dispatch table for the agents-arwaky CLI.

All command strings/aliases are kept identical to the original
tools/cli/arwaky.py ``main()`` dispatcher. Handlers are pulled from
``ctx`` (pre-built feature orchestrators/aggregates).
"""
from __future__ import annotations

from modules.shared.src.logging.utility_logging import err, ok, warn


def dispatch(argv: list[str], ctx: dict) -> int:
    """Route argv[0] to the right surface handler in *ctx*.

    *ctx* carries pre-built aggregates keyed by feature name:
    tool, daemon, service, mcp, skill, harness, backup, sync, check, doctor.
    """
    if not argv:
        return ctx["help"]([])
    cmd = argv[0]
    rest = argv[1:]

    dispatch_table: dict[str, object] = {
        # Meta / status
        "status": ctx["status"],
        "doctor": ctx["doctor"],
        "check": ctx["check"],
        "submodules": ctx.get("submodules", lambda r: err("submodules not wired yet (TODO)") or 1),
        "clean": ctx.get("clean", lambda r: err("clean not wired yet (TODO)") or 1),
        "reset": ctx.get("reset", lambda r: err("reset not wired yet (TODO)") or 1),
        "version": ctx.get("version", lambda r: 0),
        "help": ctx["help"],
        "-h": ctx["help"],
        "--help": ctx["help"],
        # Core noun-verb (canonical)
        "tool": ctx["tool"],
        "skill": ctx["skill"],
        "skills": ctx["skill"],
        "docs": ctx.get("docs", lambda r: err("docs not wired yet (TODO)") or 1),
        "connect": ctx["connect"],
        "disconnect": ctx["disconnect"],
        "mcp": ctx["mcp"],
        "sync": ctx["sync"],
        "completion": ctx.get("completion", lambda r: 0),
        # Daemons & services
        "anytype": ctx["anytype"],
        "9router": ctx["9router"],
        "service": ctx["service"],
        "backup": ctx["backup"],
        "restore": ctx["restore"],
        # Backward-compat aliases
        "install": ctx["install"],
        "update": ctx["update"],
        "uninstall": ctx["uninstall"],
        "list": ctx["list"],
        "ls": ctx["list"],
        "run": ctx["run"],
    }
    handler = dispatch_table.get(cmd)
    if handler is None:
        err(f"Unknown command: {cmd}")
        print()
        ctx["help"]([])
        return 1
    return handler(rest)
