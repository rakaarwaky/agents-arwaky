"""CLI entry point — 1:1 exact port of tools/cli/arwaky.py.

Every command-table entry, per-action validation message, help string, edge
case, the correlation-id + sentry blocks, the TOOL_RUNNERS run dispatch,
the manifest-driven tool listing, and the install/update/uninstall "all"
loops are preserved exactly as written in the original 876-line arwaky.py.
The only differences are the import swaps to the AES modules:
  - manifest        -> modules.shared.src.common.* (Tool, load_tools, find_tool)
  - ui              -> modules.shared.src.utility_logging
  - xdg             -> modules.shared.src.xdg.* (paths + atomic io)
  - tool_resolver.executable_path -> local executable_path() (original
                   body as-is: shutil.which + bin_home check)
  - tool_resolver.find_installer/find_updater/find_uninstaller -> local
                   _find_* helpers (original tools/lib/tool_resolver.py
                   bodies as-is, import-swapped)
  - doc_pack        -> modules.shared.src.utility_doc_pack
  - skill_pack      -> modules.skill.src.capabilities_skill_pack
  - paths.repo_root -> modules.shared.src.utility_paths

Delegated actions (skill/connect/disconnect/daemon/service/backup)
keep calling the module surface functions, which contain the
original bodies as-is (see the module surface docstrings).

The dispatch table and ``main`` entry point live in this module — the single
``aa`` binary entry point (sentry + correlation id + global-flag stripping +
dispatch-table routing + unknown-command fallback), ported as-is from the
original ``tools/cli/arwaky.py`` ``main()``.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import textwrap
from pathlib import Path

from modules.shared.src.utility_git_submodule import init_submodules
from modules.shared.src.utility_paths_resolver import repo_root
from modules.shared.src.utility_process_runner import run_cmd as _run_cmd_util

ROOT = repo_root()

from modules.shared.src.taxonomy_common_vo import (
    Tool,
    bin_home,
    cache_home,
    config_home,
    data_home,
    ensure_path,
)
from modules.shared.src.utility_logging_setup import (
    BLUE,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    banner,
    err,
    info,
    ok,
    set_color_mode,
    set_verbosity,
    warn,
)
from modules.shared.src.utility_logging_setup import (
    pad as _pad,
)
from modules.shared.src.utility_logging_setup import (
    table_widths as _table_widths,
)
from modules.shared.src.utility_manifest_reader import (
    find_tool,
    load_tools,
)

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# Runner map per tool (P5-P1: manifest-driven dispatch, avoid hardcoded IDs)
from modules.shared.src.taxonomy_common_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_common_vo import ToolSpec


# =============================================================================
# Helpers
# =============================================================================
def executable_path(binary: str, category: str = "", tool_id: str = "", runner: str = "") -> Path | None:
    """Port of tools/lib/tool_resolver.py executable_path() (shutil.which + bin_home check).

    For internal tools the runner candidates come from the runner module's
    ToolResolver (capabilities_runner), which is an exact port of the
    tool_resolver runner-candidate logic.
    """
    found = shutil.which(binary)
    if found:
        return Path(found)
    local = bin_home() / binary
    if local.exists() and os.access(local, os.X_OK):
        return local
    if category == "internal":
        from modules.shared.src.taxonomy_common_vo import ToolSpec
        from modules.tools.src.root_tools_container import create_tools_feature
        spec = ToolSpec(
            id=tool_id,
            category=category,
            binary=binary,
            is_mcp=False,
            description="",
            path="",
            alias=None,
            mcp_binary=None,
            runner=runner or TOOL_RUNNERS.get(tool_id, ""),
        )
        return create_tools_feature().executable_path(spec)
    return None


def run_cmd(cmd: list[str]) -> int:
    try:
        return _run_cmd_util(cmd).returncode
    except FileNotFoundError:
        err(f"Command not found: {cmd[0]}")
        return 127


def exec_python(script: Path, args: list[str]) -> int:
    if not script.exists():
        err(f"Python script not found: {script}")
        return 1
    os.execvpe(sys.executable, [sys.executable, str(script), *args], os.environ)
    return 1


def is_submodule_missing(path_str: str) -> bool:
    gitmodules = repo_root() / ".gitmodules"
    target = repo_root() / path_str
    if not gitmodules.exists():
        return False
    try:
        text = gitmodules.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if f"path = {path_str}" not in text:
        return False
    return not target.exists() or not (target / ".git").exists()


def remove_tool_state(tool: Tool) -> None:
    (bin_home() / tool.binary).unlink(missing_ok=True)
    shutil.rmtree(data_home() / tool.id, ignore_errors=True)
    shutil.rmtree(config_home() / tool.id, ignore_errors=True)
    ok(f"Removed state for {tool.id}")


# =============================================================================
# Commands
# =============================================================================
def cmd_version(argv: list[str]) -> int:
    """Print version (P1-D6). Reads config/version.txt if present."""
    vfile = repo_root() / "config" / "version.txt"
    version = "0.1.0"
    if vfile.exists():
        version = vfile.read_text(encoding="utf-8").strip()
    print(f"agents-arwaky {version}")
    return 0


def cmd_help(argv: list[str]) -> int:
    banner()
    print(f"{BOLD()}USAGE:{RESET()}")
    print("  aa <noun> <action> [arguments...]")
    print()
    print(f"{BOLD()}PRIMARY COMMANDS:{RESET()}")
    print(f"  {GREEN()}status{RESET()}                         Check health, submodule and binary installation status")
    print(f"  {GREEN()}doctor{RESET()}                         Diagnose runtime environment & toolchain")
    print(f"  {GREEN()}tool{RESET()} <cmd> [args]             Tool management (list|run|install|update|uninstall)")
    print(f"  {GREEN()}skill{RESET()} <cmd> [args]             Skill management (list|install|uninstall|show|check)")
    print(f"  {GREEN()}connect{RESET()} --<harness>|--all     Connect MCP, skills & env to harnesses")
    print(f"  {GREEN()}disconnect{RESET()} --<harness>|--all  Disconnect harnesses (use --all for all)")
    print(f"  {GREEN()}mcp{RESET()} [list|generate|show]       Manage MCP configuration")
    print(f"  {GREEN()}completion{RESET()} [bash|zsh]          Print shell completion script")
    print()
    print(f"{BOLD()}SERVICES & DAEMONS:{RESET()}")
    print(f"  {GREEN()}anytype{RESET()} <cmd>                  Anytype daemon (start|stop|status|auth-key|...)")
    print(f"  {GREEN()}9router{RESET()} <cmd>                  9Router daemon (start|stop|status|models|...)")
    print(f"  {GREEN()}service{RESET()} <cmd>                  Service manager (start|stop|restart|status|logs)")
    print()
    print(f"{BOLD()}DATA MANAGEMENT:{RESET()}")
    print(f"  {GREEN()}backup{RESET()} [args]                  Backup tool data (optionally to Google Drive)")
    print(f"  {GREEN()}restore{RESET()} [args]                 Restore tool data from archive")
    print()
    print(f"{BOLD()}MAINTENANCE:{RESET()}")
    print(f"  {GREEN()}check{RESET()} <scope> [args]          Repository verification (all|docs|skill; warnings gate)")
    print(f"  {CYAN()}submodules{RESET()}                     Initialize/update git submodules")
    print(f"  {CYAN()}clean{RESET()}                          Remove build artifacts & generated configs")
    print(f"  {CYAN()}reset{RESET()}                          Full factory reset = clean + uninstall + disconnect + unskill")
    print(f"  {CYAN()}help{RESET()}                           Show this help")
    print()
    print(f"{BOLD()}GLOBAL OPTIONS:{RESET()}")
    print(f"  {CYAN()}--no-color{RESET()} / {CYAN()}--plain{RESET()}         Disable ANSI colors")
    print(f"  {CYAN()}--force-color{RESET()}                  Force ANSI colors")
    print(f"  {CYAN()}-v{RESET()} / {CYAN()}--verbose{RESET()}              Enable debug logging")
    print(f"  {CYAN()}-q{RESET()} / {CYAN()}--quiet{RESET()}                Suppress info logs (warnings/errors only)")
    print()
    print(f"{BOLD()}EXAMPLES:{RESET()}")
    print(f"  {CYAN()}aa tool install lint{RESET()}           Install a single tool")
    print(f"  {CYAN()}aa tool update vision{RESET()}          Update a single tool (pull + reinstall)")
    print(f"  {CYAN()}aa tool update all{RESET()}             Update all tools")
    print(f"  {CYAN()}aa tool run lint check .{RESET()}       Run a tool (AES linter)")
    print(f"  {CYAN()}aa tool list{RESET()}                   List all registered tools")
    print(f"  {CYAN()}aa skill install --all{RESET()}         Provision all skills to CWD")
    print(f"  {CYAN()}aa check docs .{RESET()}               Audit PRD/ROADMAP/FRD/README/BACKLOG/AGENTS invariants")
    print(f"  {CYAN()}aa check skill{RESET()}                Audit skills/ pack loadability")
    print(f"  {CYAN()}aa skill uninstall --target .{RESET()}  Remove skills from CWD")
    print(f"  {CYAN()}aa connect --all{RESET()}               Connect all harnesses")
    print(f"  {CYAN()}aa disconnect --all{RESET()}            Disconnect all harnesses")
    print(f"  {CYAN()}aa backup all gdrive{RESET()}           Backup all tools to Google Drive")
    print()
    print(f"{BOLD()}BACKWARD COMPAT:{RESET()} {DIM()}('aa install', 'aa run' etc. still work){RESET()}")
    print()
    return 0


def cmd_status(argv: list[str]) -> int:
    ensure_path()
    if "--json" in argv:
        import json as _json
        out = []
        for tool in load_tools():
            if is_submodule_missing(tool.path):
                state = "submodule-missing"
            elif executable_path(tool.binary, category=tool.category, tool_id=tool.id):
                state = "installed"
            elif (bin_home() / tool.binary).exists():
                state = "ready"
            elif tool.category == "internal":
                state = "source-ready"
            else:
                state = "not-installed"
            out.append({"id": tool.id, "category": tool.category, "binary": tool.binary, "status": state})
        print(_json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    banner()
    print(f"{BOLD()}System & Tool Health Status:{RESET()}")
    # Terminal-width-aware column sizing
    try:
        import shutil
        term_w = shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        term_w = 80
    available = max(60, term_w - 2)
    w_tool, w_cat, w_bin, _w_status = _table_widths(available, [2, 1, 3, 4])
    sep = "-" * available
    print(sep)
    print(f"{BOLD()}{_pad('TOOL', w_tool)} {_pad('CATEGORY', w_cat)} {_pad('TARGET BINARY', w_bin)} STATUS{RESET()}")
    print(sep)
    for tool in load_tools():
        cat_color = GREEN() if tool.category == "internal" else CYAN()
        if is_submodule_missing(tool.path):
            status = f"{RED()}[FAIL] Submodule Missing{RESET()}"
        elif executable_path(tool.binary, category=tool.category, tool_id=tool.id):
            status = f"{GREEN()}[OK] Installed ({tool.binary}){RESET()}"
        elif (bin_home() / tool.binary).exists():
            status = f"{GREEN()}[OK] Ready ({bin_home()}){RESET()}"
        elif tool.category == "internal":
            status = f"{BLUE()}[OK] Source Ready (Internal){RESET()}"
        else:
            status = f"{YELLOW()}[WARN] Not Installed{RESET()}"
        print(f"{_pad(tool.id, w_tool)} {_pad(cat_color + tool.category + RESET(), w_cat)} {_pad(tool.binary, w_bin)} {status}")
    print(sep)
    return 0


def cmd_doctor(argv: list[str]) -> int:
    from modules.doctor.src.root_doctor_container import create_doctor_feature
    return create_doctor_feature().diagnose({"json": "--json" in argv})


def cmd_list(argv: list[str]) -> int:
    if "--json" in argv:
        import json as _json
        tools = [
            {"id": t.id, "category": t.category, "isMcp": t.is_mcp, "description": t.description, "binary": t.binary}
            for t in load_tools()
        ]
        print(_json.dumps(tools, indent=2, ensure_ascii=False))
        return 0
    banner()
    print(f"{BOLD()}Registered Tools in agents-arwaky:{RESET()}")
    try:
        import shutil
        term_w = shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        term_w = 80
    available = max(60, term_w - 2)
    w_id, w_cat, w_mcp, w_desc = _table_widths(available, [2, 1, 1, 6])
    sep = "-" * available
    print(sep)
    print(f"{BOLD()}{_pad('TOOL ID', w_id)} {_pad('CATEGORY', w_cat)} {_pad('MCP?', w_mcp)} {_pad('DESCRIPTION', w_desc)}{RESET()}")
    print(sep)
    for tool in load_tools():
        cat_color = GREEN() if tool.category == "internal" else CYAN()
        mcp_label = "Yes" if tool.is_mcp else "No"
        desc = textwrap.shorten(tool.description, width=w_desc, placeholder='...')
        print(
            f"{_pad(tool.id, w_id)} {_pad(cat_color + tool.category + RESET(), w_cat)} "
            f"{_pad(mcp_label, w_mcp)} {desc}"
        )
    print(sep)
    return 0


def cmd_run(argv: list[str]) -> int:
    """aa tool run <tool> [args...] — run the binary via the aggregate.

    Delegates entirely to IToolsAggregate.run(); exit-code fidelity,
    sentinel 126, and MCP stdio handling live in RunnerCapability.
    """
    if not argv:
        err("Missing tool name.")
        print("Usage: aa tool run <tool-name> [args...]")
        return 1
    tool = find_tool(argv[0])
    if tool is None:
        err(f"Tool '{argv[0]}' not found in manifest.")
        print("Run 'aa tool list' to see all available tools.")
        return 1
    from modules.tools.src.root_tools_container import create_tools_feature
    spec = _spec_from_tool(tool)
    orch = create_tools_feature()
    return orch.run(spec, argv[1:])


def _confirm(prompt: str, accepted: tuple = ("y", "yes")) -> bool:
    """Safe TTY-aware confirmation prompt. Returns False in non-TTY without --yes."""
    if not sys.stdin.isatty():
        return False
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in accepted


def _spec_from_tool(tool) -> ToolSpec:
    """Build a ToolSpec for the orchestrators from a manifest Tool."""
    from modules.shared.src.utility_manifest_reader import spec_from_tool
    return spec_from_tool(tool)


def cmd_install(argv: list[str]) -> int:
    ensure_path()
    target = argv[0] if argv else "all"
    has_yes = "--yes" in argv or "-y" in argv
    # Confirmation for install all (Plan2 P0)
    if target == "all" and not has_yes:
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        if not _confirm("Install ALL tools? [y/N]: "):
            warn("Aborted.")
            return 1
    print(f"{BOLD()}>>> Installing {target} using per-tool Python installers...{RESET()}")
    rc = init_submodules(repo_root(), ("vendor/", "internal/"))
    if rc != 0:
        err("Submodule init failed. Run 'aa submodules' manually and retry.")
        return rc
    tools = load_tools()
    if target != "all":
        tool = find_tool(target)
        if not tool:
            err(f"Tool '{target}' not found in manifest.")
            return 1
        tools = [tool]
    from modules.tools.src.root_tools_container import create_tools_feature
    installer = create_tools_feature()
    failed, skipped = [], []
    total = len(tools)
    for idx, tool in enumerate(tools, 1):
        spec = _spec_from_tool(tool)
        print(f"[{idx}/{total}] Installing {tool.id}", flush=True)
        result = installer.install(spec)
        if not result.success:
            failed.append(tool.id)
            err(f"{tool.id}: {result.message}")
        elif "skipped" in result.message.lower() or "already installed" in result.message.lower():
            skipped.append(tool.id)
            warn(f"{tool.id}: {result.message}")
    if target == "all":
        from modules.mcp.src.root_mcp_container import create_mcp_feature
        from modules.mcp.src.surface_mcp_command import cmd_mcp as _mcp
        info("Generating MCP configuration...")
        _mcp(["generate"], create_mcp_feature())
    if skipped:
        print()
        warn(f"Skipped: {', '.join(skipped)}")
    if failed:
        print()
        err(f"Failed: {', '.join(failed)}")
        return 1
    print()
    ok("Install finished.")
    return 0


def cmd_update(argv: list[str]) -> int:
    """Update tools: pull latest from remote + force reinstall."""
    ensure_path()
    target = argv[0] if argv else "all"
    has_yes = "--yes" in argv or "-y" in argv
    if target == "all" and not has_yes:
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        if not _confirm("Update ALL tools? [y/N]: "):
            warn("Aborted.")
            return 1
    print(f"{BOLD()}>>> Updating {target} (pull + reinstall)...{RESET()}")
    tools = load_tools()
    if target != "all":
        tool = find_tool(target)
        if not tool:
            err(f"Tool '{target}' not found in manifest.")
            return 1
        tools = [tool]
    from modules.tools.src.root_tools_container import create_tools_feature
    updater = create_tools_feature()
    failed, skipped = [], []
    total = len(tools)
    for idx, tool in enumerate(tools, 1):
        spec = _spec_from_tool(tool)
        print(f"[{idx}/{total}] Updating {tool.id}", flush=True)
        result = updater.update(spec)
        if not result.success:
            failed.append(tool.id)
            err(f"{tool.id}: {result.message}")
        elif "skipped" in result.message.lower() or "no updater" in result.message.lower():
            skipped.append(tool.id)
            warn(f"{tool.id}: {result.message}")
    if target == "all":
        from modules.mcp.src.root_mcp_container import create_mcp_feature
        from modules.mcp.src.surface_mcp_command import cmd_mcp as _mcp
        info("Regenerating MCP configuration...")
        _mcp(["generate"], create_mcp_feature())
    if skipped:
        print()
        warn(f"Skipped (no updater): {', '.join(skipped)}")
    if failed:
        print()
        err(f"Failed: {', '.join(failed)}")
        return 1
    print()
    ok("Update finished.")
    return 0


def cmd_mcp(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print("Usage: aa mcp <list|generate|show> [path|server_id] [--json]")
        print()
        print("  list                Enumerate MCP-enabled tools")
        print("  generate [path]     Rebuild mcp_servers.generated.json")
        print("  show [server_id]    Inspect the config, or probe one server")
        print("  list --json         Machine-readable server list")
        return 0
    action = argv[0]
    generated = repo_root() / "mcp_servers.generated.json"

    def _feature():
        from modules.mcp.src.root_mcp_container import create_mcp_feature
        return create_mcp_feature()

    def _generate(target: str | None = None) -> int:
        out = repo_root() / target if target else generated
        return _feature().generate(out)

    if action == "list":
        if "--json" in argv:
            import json as _json
            servers = [
                {"id": t.id, "category": t.category, "description": t.description}
                for t in load_tools()
                if t.is_mcp
            ]
            print(_json.dumps(servers, indent=2, ensure_ascii=False))
            return 0
        print(f"{BOLD()}MCP-Enabled Tools:{RESET()}")
        for tool in load_tools():
            if tool.is_mcp:
                print(f"  - {tool.id} [{tool.category}]: {tool.description}")
        return 0
    if action == "generate":
        target = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else None
        return _generate(target)
    if action in {"show", "path"}:
        raw = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else None
        if raw is not None:
            from modules.shared.src.taxonomy_mcp_vo import McpServerId

            return _feature().show_server(McpServerId(raw))
        if not generated.exists():
            warn("Configuration file not found. Generating now...")
            _generate()
        if generated.exists():
            print(f"{BOLD()}Path:{RESET()} {generated}")
            print()
            print(generated.read_text(encoding="utf-8"))
            return 0
        err("Failed to generate MCP configuration.")
        return 1
    err(f"Unknown MCP action: {action}")
    print("Valid actions: list, generate, show, alias, validate")
    return 1


def cmd_skill(argv: list[str]) -> int:
    from modules.skill.src.root_skill_container import create_skill_feature
    from modules.skill.src.surface_skill_command import main as _skill_surface
    return _skill_surface(argv, create_skill_feature())


def cmd_config(argv: list[str]) -> int:
    from modules.config.src.root_config_container import create_config_feature
    from modules.config.src.surface_config_command import cmd_config as _config_surface
    return _config_surface(list(argv), create_config_feature())


def cmd_connect(argv: list[str]) -> int:
    from modules.harness.src.root_harness_container import create_harness_feature
    from modules.harness.src.surface_harness_command import (
        cmd_connect as _harness_connect,
    )
    return _harness_connect(list(argv), create_harness_feature)


def cmd_disconnect(argv: list[str]) -> int:
    from modules.harness.src.root_harness_container import create_harness_feature
    from modules.harness.src.surface_harness_command import (
        cmd_disconnect as _harness_disconnect,
    )
    return _harness_disconnect(list(argv), create_harness_feature)


def cmd_completion(argv: list[str]) -> int:
    """Print a bash/zsh completion script for the aa CLI."""
    from modules.shared.src.utility_shell_completion import (
        bash_completion,
        zsh_completion,
    )

    shell = argv[0] if argv else "bash"
    if shell in ("-h", "--help", "help"):
        print("Usage: aa completion [bash|zsh]")
        print()
        print("  bash    Source in ~/.bashrc:  eval \"$(aa completion bash)\"")
        print("  zsh     Source in ~/.zshrc:   eval \"$(aa completion zsh)\"")
        return 0
    if shell == "bash":
        print(bash_completion())
        return 0
    if shell == "zsh":
        print(zsh_completion())
        return 0
    err(f"Unknown shell: {shell} (expected bash or zsh)")
    return 1


def cmd_tool(argv: list[str]) -> int:
    """Tool management: aa tool <list|run|install|update|uninstall> [args]

    Delegates to the module's CLI surface (surface_tools_command); this entry
    stays a thin router (AES506). The surface owns arg parsing + aggregate
    calls so the tool action lives in one place.
    """
    from modules.tools.src.surface_tools_command import cmd_tool as _tools_surface
    return _tools_surface(argv, _tool_orch())


def _tool_orch():
    from modules.tools.src.root_tools_container import create_tools_feature
    return create_tools_feature()


def _config_feature():
    from modules.config.src.root_config_container import config_modifier, config_writer
    return config_writer(), config_modifier()


def _doctor_feature():
    """Doctor feature aggregate (reachable composition root for AES502)."""
    from modules.doctor.src.root_doctor_container import create_doctor_feature
    return create_doctor_feature()


def _doctor_feature_compat():
    """Backward-compat shim for _doctor_feature() call sites."""
    return _doctor_feature()


def cmd_anytype(argv: list[str]) -> int:
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.daemon.src.surface_daemon_command import cmd_anytype as _daemon_anytype
    from modules.daemon.src.surface_daemon_command import (
        register_manager_factory as _reg_dm,
    )
    _c = DaemonContainer()
    _reg_dm("anytype", lambda: _c.anytype)
    return _daemon_anytype(argv)


def cmd_9router(argv: list[str]) -> int:
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.daemon.src.surface_daemon_command import (
        cmd_9router as _daemon_9router,
    )
    from modules.daemon.src.surface_daemon_command import (
        register_manager_factory as _reg_dm,
    )
    _c = DaemonContainer()
    _reg_dm("9router", lambda: _c.ninerouter)
    return _daemon_9router(argv)


def cmd_daemon(argv: list[str]) -> int:
    """aa daemon <id> <action> — list|status|start|… for a managed daemon."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature

    orch = create_daemon_feature()
    if not argv or argv[0] in ("-h", "--help", "help"):
        names = ", ".join(str(n) for n in orch.list_known())
        print("Usage: aa daemon <9router|anytype> <start|stop|restart|status|logs|help>")
        print(f"Known daemons: {names}")
        return 0
    daemon_id = argv[0]
    known = {str(n) for n in orch.list_known()}
    if daemon_id not in known:
        err(f"Unknown daemon: {daemon_id}")
        print(f"Known daemons: {', '.join(sorted(known))}")
        return 1
    action = argv[1] if len(argv) > 1 else "status"
    rest = argv[2:]
    if action in ("start", "stop", "restart", "logs", "help"):
        result = getattr(orch, action)(daemon_id)
        return int(result)
    if action == "status":
        from modules.daemon.src.root_daemon_container import DaemonContainer
        from modules.daemon.src.surface_daemon_command import (
            cmd_9router as _ni,
        )
        from modules.daemon.src.surface_daemon_command import (
            cmd_anytype as _any,
        )
        from modules.daemon.src.surface_daemon_command import (
            register_manager_factory as _reg_dm,
        )

        _c = DaemonContainer()
        _reg_dm("anytype", lambda: _c.anytype)
        _reg_dm("9router", lambda: _c.ninerouter)
        fn = _ni if daemon_id == "9router" else _any
        return fn(["status", *rest])
    err(f"Unknown daemon action: {action}")
    print("Valid actions: start, stop, restart, status, logs, help")
    return 1


def cmd_service(argv: list[str]) -> int:
    from modules.service.src.root_service_container import create_service_feature
    from modules.service.src.surface_service_command import cmd_service as _service_cmd
    return _service_cmd(argv, create_service_feature())


def cmd_backup(argv: list[str]) -> int:
    from modules.backup.src.root_backup_container import create_backup_feature
    from modules.backup.src.surface_backup_command import cmd_backup as _backup_cmd
    return _backup_cmd(["backup", *argv], create_backup_feature())


def cmd_restore(argv: list[str]) -> int:
    from modules.backup.src.root_backup_container import create_backup_feature
    from modules.backup.src.surface_backup_command import cmd_restore as _restore_cmd
    return _restore_cmd(["restore", *argv], create_backup_feature())


def cmd_check(argv: list[str]) -> int:
    """aa check [all|docs|skill] [path] [--include-subtrees] [--json] — route through the check feature surface."""
    from modules.check.src.root_check_container import create_check_feature
    from modules.check.src.surface_check_command import cmd_check as _check_cmd
    return _check_cmd(argv, create_check_feature())


def cmd_submodules(argv: list[str]) -> int:
    info("Initializing and updating all submodules...")
    code = init_submodules(repo_root(), ("vendor/", "internal/"), recursive=True)
    if code == 0:
        ok("Submodules ready.")
    return code


def cmd_clean(argv: list[str]) -> int:
    info("Cleaning build artifacts and generated configs...")
    # Remove tool build caches (~/.cache/<tool>/)
    for tool in load_tools():
        cache_path = cache_home() / tool.id
        if cache_path.exists():
            shutil.rmtree(cache_path, ignore_errors=True)
            info(f"  Removed {cache_path}")
    # Remove generated MCP config
    (repo_root() / "mcp_servers.generated.json").unlink(missing_ok=True)
    ok("Build artifacts cleaned.")
    return 0


def uninstall_tool(tool: Tool) -> int:
    from modules.tools.src.root_tools_container import create_tools_feature
    uninstaller = create_tools_feature()
    spec = _spec_from_tool(tool)
    info(f"Uninstalling {tool.id}")
    result = uninstaller.uninstall(spec)
    if not result.success:
        err(f"{tool.id}: {result.message}")
        return 1
    return 0


def cmd_uninstall(argv: list[str]) -> int:
    target = argv[0] if argv else "--all"
    has_yes = "--yes" in argv or "-y" in argv
    # Confirmation for uninstall all (Plan2 P0)
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
            if uninstall_tool(tool) != 0:
                failed.append(tool.id)
        if failed:
            err(f"Failed: {', '.join(failed)}")
            return 1
        ok("All tools uninstalled.")
        return 0
    tool = find_tool(target)
    if not tool:
        err(f"Tool '{target}' not found in manifest.")
        return 1
    return uninstall_tool(tool)


def cmd_reset(argv: list[str]) -> int:
    has_yes = "--yes" in argv or "-y" in argv
    warn("WARNING: This will wipe installed tool state and reset the repository.")
    warn("This action cannot be undone.")
    if not has_yes:
        if not sys.stdin.isatty():
            err("Non-interactive mode detected. Use --yes to skip confirmation.")
            return 1
        if not _confirm("Type 'RESET' to continue: ", accepted=("reset",)):
            warn("Aborted.")
            return 1
    print()
    info("[1/4] clean")
    cmd_clean([])
    print()
    info("[2/4] uninstall --all")
    uninstall_rc = cmd_uninstall(["--all", "--yes"])
    if uninstall_rc != 0:
        err("Uninstall step failed during reset.")
        return uninstall_rc
    print()
    info("[3/4] disconnect --all")
    cmd_disconnect(["--all"])
    print()
    info("[4/4] skill uninstall (CWD)")
    cmd_skill(["uninstall", "all", "--target", os.getcwd()])
    print()
    info("Resetting submodules...")
    run_cmd(["git", "-C", str(repo_root()), "submodule", "foreach", "--recursive", "git clean -fd && git checkout ."])
    ok("Factory reset complete.")
    return 0


# =============================================================================
# Tool resolver (original tools/lib/tool_resolver.py bodies, import-swapped)
# =============================================================================
# The original find_installer/find_updater/find_uninstaller returned a
# tools/{install,update,uninstall}/install_<name>.py script path. Those
# script directories were deleted by the AES refactor; their per-tool logic
def _installer_registry_ids() -> set:
    """Tool ids that have a registered per-tool installer capability."""
    from modules.tools.src.root_tools_container import TOOLS_REGISTRY

    return set(TOOLS_REGISTRY)


# =============================================================================
# Main dispatcher (original main() body, as-is)
# =============================================================================
def _dispatch(argv: list[str], ctx: dict | None = None) -> int:
    """Route argv[0] to the right action handler (1:1 port of the surface table)."""
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
        # Core noun-action (canonical)
        "tool": cmd_tool, "skill": cmd_skill, "skills": cmd_skill,
        "config": cmd_config,
        "connect": cmd_connect, "disconnect": cmd_disconnect,
        "mcp": cmd_mcp, "completion": cmd_completion,
        # Daemons & services
        "anytype": cmd_anytype, "9router": cmd_9router, "service": cmd_service,
        "daemon": cmd_daemon,
        "backup": cmd_backup, "restore": cmd_restore,
        # Backward compat aliases → noun action (deprecated, prefer aa tool/aa skill)
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


def _gen_correlation_id() -> str:
    """Generate short correlation ID (P1-O4) for multi-step ops."""
    import uuid
    return uuid.uuid4().hex[:8]


def _init_sentry():
    """Opt-in Sentry error tracking (P1-O2), controlled by ARWAKY_SENTRY_DSN."""
    dsn = os.environ.get("ARWAKY_SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)
    except ImportError:
        pass


def main(argv: list[str]) -> int:
    _init_sentry()
    os.environ["ARWAKY_CORRELATION_ID"] = _gen_correlation_id()
    if not argv:
        return cmd_help([])
    # Global flag: --no-color / --plain (P2-P1)
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
    return _dispatch(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
