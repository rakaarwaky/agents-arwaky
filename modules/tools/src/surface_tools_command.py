"""Tool CLI surface — command handlers for `aa tool` / `aa install|update|uninstall`.

Ported from the runner verb surface; surface files use the AES `command`
suffix (AES102). All side effects are delegated to the IToolsAggregate.
"""
from __future__ import annotations

import json as _json
import sys
import textwrap

from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.utility_logging_setup import (
    BOLD,
    CYAN,
    GREEN,
    RESET,
    banner,
    err,
    info,
    ok,
    pad,
    table_widths,
    warn,
)
from modules.shared.src.utility_paths_resolver import repo_root


def _term_width() -> int:
    import shutil
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


def _has_help(args: list[str]) -> bool:
    """A2: intercept -h/--help before target resolution in every subcommand."""
    return any(a in ("-h", "--help") for a in args)


def _confirm(prompt: str, accepted: tuple[str, ...] = ("y", "yes")) -> bool:
    """TTY-aware confirmation; False in non-TTY without --yes."""
    if not sys.stdin.isatty():
        return False
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in accepted


def cmd_list(args: list[str], orch: IToolsAggregate) -> int:
    """aa tool list [tool] — registered tools, table or --json."""
    if "--json" in args:
        tools = [
            {"id": t.id, "category": t.category, "isMcp": t.is_mcp, "description": t.description, "binary": t.binary}
            for t in orch.list_tools()
        ]
        print(_json.dumps(tools, indent=2, ensure_ascii=False))
        return 0
    banner()
    print(f"{BOLD()}Registered Tools in agents-arwaky:{RESET()}")
    term_w = _term_width()
    available = max(60, term_w - 2)
    w_id, w_cat, w_mcp, w_desc = table_widths(available, [2, 1, 1, 6])
    sep = "-" * available
    print(sep)
    print(f"{BOLD()}{pad('TOOL ID', w_id)} {pad('CATEGORY', w_cat)} {pad('MCP?', w_mcp)} {pad('DESCRIPTION', w_desc)}{RESET()}")
    print(sep)
    for tool in orch.list_tools():
        cat_color = GREEN() if tool.category == "internal" else CYAN()
        mcp_label = "Yes" if tool.is_mcp else "No"
        desc = textwrap.shorten(tool.description, width=w_desc, placeholder="...")
        print(f"{pad(tool.id, w_id)} {pad(cat_color + tool.category + RESET(), w_cat)} "
              f"{pad(mcp_label, w_mcp)} {desc}")
    print(sep)
    return 0


def cmd_run(args: list[str], orch: IToolsAggregate) -> int:
    """aa tool run <tool> [args...] — run the binary via the aggregate.

    P0-3: delegates entirely to orch.run_tool(); the duplicated
    cargo/uv/python os.execvpe dispatch (and its uncaught-OSError
    crash path) is removed. Exit-code fidelity, sentinel 126, and
    MCP stdio handling live in RunnerCapability.
    """
    if _has_help(args):
        print("Usage: aa tool run <tool-name> [args...]")
        return 0
    if not args:
        err("Missing tool name.")
        print("Usage: aa tool run <tool-name> [args...]")
        return 1
    spec = orch.resolve_spec(args[0])
    if spec is None:
        err(f"Tool '{args[0]}' not found in manifest.")
        print("Run 'aa tool list' to see all available tools.")
        return 1
    tool_args = args[1:]
    # All dispatch/exec/error semantics live in RunnerCapability:
    # discovery order, sentinel 126, MCP stdio, child exit-code passthrough.
    return orch.run_tool(spec, tool_args)


def cmd_install(args: list[str], orch: IToolsAggregate) -> int:
    """aa tool install <tool|all> [--yes] — per-tool installers via the orchestrator."""
    if _has_help(args):
        print("Usage: aa tool install <tool|all> [--yes]")
        return 0
    from modules.shared.src.taxonomy_common_vo import ensure_path
    ensure_path()
    target = args[0] if args and args[0] not in ("--yes", "-y") else "all"
    has_yes = "--yes" in args or "-y" in args
    if target == "all" and not has_yes:
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        if not _confirm("Install ALL tools? [y/N]: "):
            warn("Aborted.")
            return 1
    print(f"{BOLD()}>>> Installing {target} using per-tool Python installers...{RESET()}")
    import subprocess
    rc = subprocess.run(
        ["git", "-C", str(repo_root()), "submodule", "update", "--init", "vendor/", "internal/"],
        check=False,
    ).returncode
    if rc != 0:
        err("Submodule init failed. Run 'aa submodules' manually and retry.")
        return rc
    if target == "all":
        results = [
            orch.install(orch.resolve_spec(tool.id))
            for tool in orch.list_tools()
            if orch.resolve_spec(tool.id) is not None
        ]
        failed = [r.tool_id for r in results if not r.success]
        if failed:
            err(f"Failed: {', '.join(failed)}")
            return 1
        ok("Install finished.")
        return 0
    spec = orch.resolve_spec(target)
    if spec is None:
        err(f"Tool '{target}' not found in manifest.")
        return 1
    result = orch.install(spec)
    if not result.success:
        err(result.message)
        return 1
    ok(result.message)
    return 0


def cmd_update(args: list[str], orch: IToolsAggregate) -> int:
    """aa tool update <tool|all> [--yes] — pull + reinstall."""
    if _has_help(args):
        print("Usage: aa tool update <tool|all> [--yes]")
        return 0
    from modules.shared.src.taxonomy_common_vo import ensure_path
    ensure_path()
    target = args[0] if args and args[0] not in ("--yes", "-y") else "all"
    has_yes = "--yes" in args or "-y" in args
    if target == "all" and not has_yes:
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        if not _confirm("Update ALL tools? [y/N]: "):
            warn("Aborted.")
            return 1
    print(f"{BOLD()}>>> Updating {target} (pull + reinstall)...{RESET()}")
    if target == "all":
        failed: list[str] = []
        for tool in orch.list_tools():
            spec = orch.resolve_spec(tool.id)
            if spec is None:
                continue
            result = orch.update(spec)
            if not result.success:
                err(result.message)
                failed.append(tool.id)
        if failed:
            err(f"Update failed for: {', '.join(failed)}")
            return 1
        ok("Update finished.")
        return 0
    spec = orch.resolve_spec(target)
    if spec is None:
        err(f"Tool '{target}' not found in manifest.")
        return 1
    result = orch.update(spec)
    if not result.success:
        err(result.message)
        return 1
    ok(result.message)
    return 0


def cmd_uninstall(args: list[str], orch: IToolsAggregate) -> int:
    """aa tool uninstall <tool|--all> [--yes] — remove launchers + XDG artifacts."""
    if _has_help(args):
        print("Usage: aa tool uninstall <tool|--all> [--yes]")
        return 0
    target = args[0] if args and args[0] not in ("--yes", "-y") else "--all"
    has_yes = "--yes" in args or "-y" in args
    if target in {"--all", "all"} and not has_yes:
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        warn("WARNING: This will remove ALL installed tool binaries, data and config.")
        if not _confirm("Type 'uninstall' to continue: ", accepted=("uninstall",)):
            warn("Aborted.")
            return 1
    elif target not in {"--all", "all"} and not has_yes:
        # P1-14: single-tool uninstall gets the same TTY/--yes guard as --all.
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        if not _confirm(f"Uninstall '{target}'? [y/N]: "):
            warn("Aborted.")
            return 1
    if target in {"--all", "all"}:
        info("Uninstalling all tools...")
        failed = []
        for tool in orch.list_tools():
            spec = orch.resolve_spec(tool.id)
            if spec is None:
                continue
            result = orch.uninstall(spec)
            if not result.success:
                failed.append(tool.id)
        if failed:
            err(f"Failed: {', '.join(failed)}")
            return 1
        ok("All tools uninstalled.")
        return 0
    spec = orch.resolve_spec(target)
    if spec is None:
        err(f"Tool '{target}' not found in manifest.")
        return 1
    result = orch.uninstall(spec)
    if not result.success:
        err(result.message)
        return 1
    ok(result.message)
    return 0


def cmd_tool(args: list[str], orch: IToolsAggregate) -> int:
    """aa tool <list|run|install|update|uninstall> [args]"""
    if not args or args[0] in ("-h", "--help", "help"):
        print("Usage: aa tool <list|run|install|update|uninstall> [args]")
        print()
        print("  list, ls [tool]     List registered tools (add --json for machine output)")
        print("  run <tool> [args]   Execute a registered tool")
        print("  install <tool|all> [--yes]")
        print("  update <tool|all> [--yes]")
        print("  uninstall <tool|--all> [--yes]")
        return 0
    sub_cmd = args[0]
    rest = args[1:]
    dispatch = {
        "list": lambda r: cmd_list(r, orch),
        "ls": lambda r: cmd_list(r, orch),
        "run": lambda r: cmd_run(r, orch),
        "install": lambda r: cmd_install(r, orch),
        "update": lambda r: cmd_update(r, orch),
        "uninstall": lambda r: cmd_uninstall(r, orch),
    }
    handler = dispatch.get(sub_cmd)
    if not handler:
        err(f"Unknown tool subcommand: {sub_cmd}")
        print(f"Valid: {', '.join(dispatch.keys())}")
        return 1
    return handler(rest)


__all__ = [
    "cmd_install",
    "cmd_list",
    "cmd_run",
    "cmd_tool",
    "cmd_uninstall",
    "cmd_update",
]
