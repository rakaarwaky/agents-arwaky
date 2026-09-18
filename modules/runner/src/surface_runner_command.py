"""Tool surface — CLI adapter for the tool feature (aa tool / aa install|update|run)."""
from __future__ import annotations

import json as _json
import subprocess
import sys
import textwrap

from modules.shared.src.manifest import load_tools
from modules.shared.src.logging.utility_logging import BOLD, GREEN, CYAN, RESET, banner, err, info, ok, pad, table_widths, warn
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_aggregate import IToolAggregate
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_path
from modules.runner.src.agent_runner_orchestrator import ToolOrchestrator


def _term_width() -> int:
    import shutil
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


def _confirm(prompt: str, accepted: tuple[str, ...] = ("y", "yes")) -> bool:
    """TTY-aware confirmation; False in non-TTY without --yes (Plan2 P0)."""
    if not sys.stdin.isatty():
        return False
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in accepted


def cmd_list(args: list[str], orch: IToolAggregate) -> int:
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


def cmd_run(args: list[str], orch: IToolAggregate) -> int:
    """aa tool run <tool> [args...] — run the binary in-process."""
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
    exe = orch.executable_path(spec)
    if exe:
        import os
        import shutil

        tool_dir = repo_root() / spec.path
        if spec.category == "internal" and spec.runner == "cargo" and exe.name == "Cargo.toml":
            os.execvpe("cargo", ["cargo", "run", "--quiet", "--manifest-path", str(exe),
                                 "--bin", f"{spec.id}-arwaky-cli", "--", *tool_args], os.environ)
        if spec.category == "internal" and spec.runner in {"uv", "python"} and exe == tool_dir:
            if shutil.which("uv"):
                os.execvpe("uv", ["uv", "run", "--directory", str(tool_dir), spec.binary, *tool_args], os.environ)
            elif shutil.which("python3"):
                os.execvpe("python3", ["python3", "-m", spec.id, *tool_args], os.environ)
        os.execvpe(str(exe), [str(exe), *tool_args], os.environ)
    err(f"Binary '{spec.binary}' for tool '{spec.id}' is not installed or runnable.")
    print(f"Try running: {BOLD()}aa tool install {spec.id}{RESET()}")
    return 1


def cmd_install(args: list[str], orch: IToolAggregate) -> int:
    """aa tool install <tool|all> [--yes] — per-tool installers via the orchestrator."""
    from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_path
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
        from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator

        installer = getattr(orch, "_installer", None)
        if isinstance(installer, InstallerOrchestrator):
            results = installer.install_all()
        else:
            results = []
            for tool in orch.list_tools():
                spec = orch.resolve_spec(tool.id)
                if spec is not None:
                    results.append(orch.install(spec))
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


def cmd_update(args: list[str], orch: IToolAggregate) -> int:
    """aa tool update <tool|all> [--yes] — pull + reinstall."""
    from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_path
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
        for tool in load_tools():
            spec = orch.resolve_spec(tool.id)
            if spec is None:
                continue
            result = orch.update(spec)
            if not result.success:
                err(result.message)
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


def cmd_uninstall(args: list[str], orch: IToolAggregate) -> int:
    """aa tool uninstall <tool|--all> [--yes] — remove launchers + XDG artifacts."""
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
    if target in {"--all", "all"}:
        info("Uninstalling all tools...")
        failed = []
        for tool in load_tools():
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


def cmd_tool(args: list[str], orch: IToolAggregate) -> int:
    """aa tool <list|run|install|update|uninstall> [args]"""
    if not args:
        err("Missing subcommand.")
        print("Usage: aa tool <list|run|install|update|uninstall> [args]")
        return 1
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
