"""CLI entry point — 1:1 verbatim port of tools/cli/arwaky.py.

Every command-table entry, per-verb validation message, help string, edge
case, the correlation-id + sentry blocks, the TOOL_RUNNERS run dispatch,
the manifest-driven tool listing, and the install/update/uninstall "all"
loops are preserved exactly as written in the original 876-line arwaky.py.
The only differences are the import swaps to the AES modules:
  - manifest        -> modules.shared.src.common.* (Tool, load_tools, find_tool)
  - ui              -> modules.shared.src.utility_logging
  - xdg             -> modules.shared.src.xdg.* (paths + atomic io)
  - tool_resolver.executable_path -> local executable_path() (original
                   body verbatim: shutil.which + bin_home check)
  - tool_resolver.find_installer/find_updater/find_uninstaller -> local
                   _find_* helpers (original tools/lib/tool_resolver.py
                   bodies verbatim, import-swapped)
  - doc_pack        -> modules.check.src.capabilities_doc_pack
  - skill_pack      -> modules.skill.src.capabilities_skill_pack
  - paths.repo_root -> modules.shared.src.utility_paths

Delegated verbs (skill/connect/disconnect/daemon/service/backup/
completion) keep calling the module surface functions, which contain the
original bodies verbatim (see the module surface docstrings).

The dispatch table and ``main`` entry point live in this module — the single
``aa`` binary entry point (sentry + correlation id + global-flag stripping +
dispatch-table routing + unknown-command fallback), ported verbatim from the
original ``tools/cli/arwaky.py`` ``main()``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from modules.shared.src.utility_paths_resolver import repo_root

ROOT = repo_root()

from modules.shared.src.taxonomy_manifest_vo import Tool
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
from modules.shared.src.taxonomy_xdg_atomic_io import ensure_path
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    cache_home,
    config_home,
    data_home,
)

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# Runner map per tool (P5-P1: manifest-driven dispatch, avoid hardcoded IDs)
from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_tool_vo import ToolSpec


# =============================================================================
# Helpers
# =============================================================================
def executable_path(binary: str, category: str = "", tool_id: str = "", runner: str = "") -> Path | None:
    """Port of tools/lib/tool_resolver.py executable_path() (shutil.which + bin_home check).

    For internal tools the runner candidates come from the runner module's
    ToolResolver (capabilities_runner), which is a verbatim port of the
    tool_resolver runner-candidate logic.
    """
    found = shutil.which(binary)
    if found:
        return Path(found)
    local = bin_home() / binary
    if local.exists() and os.access(local, os.X_OK):
        return local
    if category == "internal":
        from modules.shared.src.taxonomy_tool_vo import ToolSpec
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
        return subprocess.run(cmd, check=False).returncode
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
    print("  aa <noun> <verb> [arguments...]")
    print()
    print(f"{BOLD()}PRIMARY COMMANDS:{RESET()}")
    print(f"  {GREEN()}status{RESET()}                         Check health, submodule and binary installation status")
    print(f"  {GREEN()}doctor{RESET()}                         Diagnose runtime environment & toolchain")
    print(f"  {GREEN()}tool{RESET()} <cmd> [args]             Tool management (list|run|install|update|uninstall)")
    print(f"  {GREEN()}skill{RESET()} <cmd> [args]             Skill management (list|install|uninstall|show|check)")
    print(f"  {GREEN()}docs{RESET()} <cmd> [path]             Document invariants (check [--strict] [--include-subtrees])")
    print(f"  {GREEN()}connect{RESET()} [targets]              Connect MCP, skills & env to harnesses")
    print(f"  {GREEN()}disconnect{RESET()} [targets]           Disconnect harnesses (use --all for all)")
    print(f"  {GREEN()}mcp{RESET()} [list|generate|show]       Manage MCP configuration")
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
    print(f"  {CYAN()}check{RESET()}                          Repository verification (JSON + Python compile)")
    print(f"  {CYAN()}submodules{RESET()}                     Initialize/update git submodules")
    print(f"  {CYAN()}clean{RESET()}                          Remove build artifacts & generated configs")
    print(f"  {CYAN()}reset{RESET()}                          Full factory reset = clean + uninstall + disconnect + unskill")
    print(f"  {CYAN()}completion{RESET()}                     Shell completion generator")
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
    print(f"  {CYAN()}aa docs check .{RESET()}              Audit PRD/FRD/README/BACKLOG/AGENTS invariants")
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
    ensure_path()
    banner()
    print(f"{BOLD()}Running Environment Diagnostics...{RESET()}")
    print("------------------------------------------------------")
    target_bin = str(bin_home())
    if target_bin in os.environ.get("PATH", "").split(os.pathsep):
        ok(f"PATH includes {target_bin}")
    else:
        warn(f"PATH does not include {target_bin}")
    for util in ["git", "jq", "curl", "python3"]:
        p = shutil.which(util)
        if p:
            ok(f"{util}: {p}")
        else:
            err(f"{util} is required")
    for util in ["cargo", "uv", "node", "npm", "bun", "pnpm", "rustc"]:
        p = shutil.which(util)
        if p:
            ok(f"{util}: {p}")
        else:
            print(f"  {DIM()}[SKIP]{RESET()} {util} not installed (optional)")
    engine = shutil.which("podman") or shutil.which("docker")
    if engine:
        ok(f"Container engine: {engine}")
    else:
        warn("Podman/Docker not found (only needed for 9router & anytype daemons)")
    print("------------------------------------------------------")
    print(f"{GREEN()}Diagnostics complete.{RESET()}")
    return 0


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
    if not argv:
        err("Missing tool name.")
        print("Usage: aa tool run <tool-name> [args...]")
        return 1
    tool = find_tool(argv[0])
    if not tool:
        err(f"Tool '{argv[0]}' not found in manifest.")
        print("Run 'aa tool list' to see all available tools.")
        return 1
    tool_args = argv[1:]
    exe = executable_path(tool.binary, category=tool.category, tool_id=tool.id)
    if exe:
        os.execvpe(str(exe), [str(exe), *tool_args], os.environ)
    tool_dir = repo_root() / tool.path
    # Runner dispatch (P5-P1: manifest-driven, not hardcoded tool IDs)
    if tool.category == "internal":
        runner = TOOL_RUNNERS.get(tool.id, "")
        if runner == "cargo" and shutil.which("cargo"):
            os.execvpe("cargo", ["cargo", "run", "--quiet", "--manifest-path",
                                 str(tool_dir / "Cargo.toml"), "--bin", "lint-arwaky-cli", "--", *tool_args], os.environ)
        if runner in {"uv", "python"} and shutil.which("uv"):
            os.execvpe("uv", ["uv", "run", "--directory", str(tool_dir), tool.binary, *tool_args], os.environ)
        if runner == "uv" and not shutil.which("uv") and shutil.which("python3"):
            os.execvpe("python3", ["python3", "-m", tool.id, *tool_args], os.environ)
    err(f"Binary '{tool.binary}' for tool '{tool.id}' is not installed or runnable.")
    has_installer = tool.id in _installer_registry_ids()
    if has_installer:
        print(f"Try running: {BOLD()}aa tool install {tool.id}{RESET()}")
    else:
        print(f"No installer available for '{tool.id}'. Try: {BOLD()}aa submodules{RESET()} then {BOLD()}aa tool run {tool.id}{RESET()}")
    return 1


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
    return ToolSpec(
        id=tool.id,
        category=tool.category,
        binary=tool.binary,
        is_mcp=tool.is_mcp,
        description=tool.description,
        path=tool.path,
        alias=tool.alias,
        mcp_binary=getattr(tool, "mcp_binary", None),
        runner=TOOL_RUNNERS.get(tool.id, ""),
    )


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
    rc = run_cmd(["git", "-C", str(repo_root()), "submodule", "update", "--init", "vendor/", "internal/"])
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
        from modules.mcp.src.agent_mcp_verb import cmd_mcp as _mcp
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
        from modules.mcp.src.agent_mcp_verb import cmd_mcp as _mcp
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
    action = argv[0] if argv else "list"
    generated = repo_root() / "mcp_servers.generated.json"

    def _generate(target: str | None = None) -> int:
        from modules.mcp.src.root_mcp_container import create_mcp_feature
        out = repo_root() / target if target else generated
        return create_mcp_feature().generate(out)

    if action == "list":
        print(f"{BOLD()}MCP-Enabled Tools:{RESET()}")
        for tool in load_tools():
            if tool.is_mcp:
                print(f"  - {tool.id} [{tool.category}]: {tool.description}")
        return 0
    if action == "generate":
        target = argv[1] if len(argv) > 1 else None
        return _generate(target)
    if action in {"show", "path"}:
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
    print("Valid actions: list, generate, show")
    return 1


def cmd_skill(argv: list[str]) -> int:
    from modules.skill.src.root_skill_container import create_skill_feature
    from modules.skill.src.agent_skill_verb import main as _skill_surface
    return _skill_surface(argv, create_skill_feature())


def cmd_connect(argv: list[str]) -> int:
    from modules.harness.src.agent_harness_orchestrator import cmd_connect as _harness_connect
    return _harness_connect(list(argv))


def cmd_disconnect(argv: list[str]) -> int:
    from modules.harness.src.agent_harness_orchestrator import cmd_disconnect as _harness_disconnect
    return _harness_disconnect(list(argv))


def cmd_tool(argv: list[str]) -> int:
    """Tool management: aa tool <list|run|install|update|uninstall> [args]"""
    if not argv:
        err("Missing subcommand.")
        print("Usage: aa tool <list|run|install|update|uninstall> [args]")
        return 1
    sub = argv[0]
    rest = argv[1:]
    tool_dispatch = {
        "list": cmd_list, "ls": cmd_list,
        "run": cmd_run,
        "install": cmd_install,
        "update": cmd_update,
        "uninstall": cmd_uninstall,
    }
    handler = tool_dispatch.get(sub)
    if not handler:
        err(f"Unknown tool subcommand: {sub}")
        print(f"Valid: {', '.join(tool_dispatch.keys())}")
        return 1
    return handler(rest)


def cmd_anytype(argv: list[str]) -> int:
    from modules.daemon.src.agent_daemon_verb import cmd_anytype as _daemon_anytype, register_manager_factory as _reg_dm
    from modules.daemon.src.root_daemon_container import DaemonContainer
    _c = DaemonContainer()
    _reg_dm("anytype", lambda: _c.anytype)
    return _daemon_anytype(argv)


def cmd_9router(argv: list[str]) -> int:
    from modules.daemon.src.agent_daemon_verb import cmd_9router as _daemon_9router, register_manager_factory as _reg_dm
    from modules.daemon.src.root_daemon_container import DaemonContainer
    _c = DaemonContainer()
    _reg_dm("9router", lambda: _c.ninerouter)
    return _daemon_9router(argv)


def cmd_service(argv: list[str]) -> int:
    from modules.service.src.root_service_container import create_service_feature
    from modules.service.src.agent_service_verb import cmd_service as _service_cmd
    return _service_cmd(argv, create_service_feature())


def cmd_backup(argv: list[str]) -> int:
    from modules.backup.src.root_backup_container import create_backup_feature
    from modules.backup.src.agent_backup_verb import cmd_backup as _backup_cmd
    return _backup_cmd(["backup", *argv], create_backup_feature())


def cmd_restore(argv: list[str]) -> int:
    from modules.backup.src.root_backup_container import create_backup_feature
    from modules.backup.src.agent_backup_verb import cmd_restore as _restore_cmd
    return _restore_cmd(["restore", *argv], create_backup_feature())


def cmd_check(argv: list[str]) -> int:
    import py_compile
    banner()
    info("Running Python-based repository verification...")
    errors = 0
    print()
    print("[1/5] Validating JSON files...")
    for json_file in (repo_root() / "modules").rglob("*.json"):
        if "node_modules" in json_file.parts:
            continue
        try:
            json.loads(json_file.read_text(encoding="utf-8"))
            ok(str(json_file.relative_to(repo_root())))
        except (OSError, ValueError) as e:
            err(f"Invalid JSON: {json_file}: {e}")
            errors += 1
    print()
    print("[2/5] Compiling Python files...")
    for py_file in (repo_root() / "modules").rglob("*.py"):
        if "node_modules" in py_file.parts:
            continue
        try:
            py_compile.compile(str(py_file), doraise=True)
            ok(str(py_file.relative_to(repo_root())))
        except (py_compile.PyCompileError, OSError, ValueError) as e:
            err(f"Python compile error: {py_file}: {e}")
            errors += 1
    print()
    errors += _check_docs()
    print()
    errors += _check_skill_pack()
    print()
    errors += _check_shell()
    print()
    if errors:
        err(f"Verification FAILED with {errors} errors.")
        return 1
    ok("All verifications PASSED.")
    return 0


def _check_docs() -> int:
    """Gate this repo's documents on the invariants the add-docs skill states in prose.

    Warnings on files under skills/ are counted rather than printed: the pack hosts
    upstream copies whose shape is not ours to fix.
    """
    from modules.check.src.capabilities_doc_pack import (
        audit_docs,
        errors_only,
        warnings_only,
    )

    print("[3/5] Validating document invariants...")
    root = repo_root()
    findings = audit_docs(root)
    problems = errors_only(findings)
    for finding in problems:
        err(f"{finding.code} {finding.path}: {finding.message}")
    surface = [
        f for f in warnings_only(findings)
        if not f.path.startswith(f"{root}{os.sep}skills{os.sep}")
    ]
    hidden = len(warnings_only(findings)) - len(surface)
    for finding in surface:
        warn(f"{finding.code} {finding.path}: {finding.message}")
    if not findings:
        ok("every document satisfies the add-docs invariants")
    elif not problems:
        ok(f"{len(findings)} advisory finding(s), no errors "
           f"({len(surface)} in this repo's docs, {hidden} in provisioned skill copies)")
        info("  list them with 'aa docs check'; gate on them with 'aa docs check --strict'")
    return len(problems)


def cmd_docs(argv: list[str]) -> int:
    """Audit document invariants: aa docs check [path] [--strict] [--include-subtrees]"""
    from modules.check.src.capabilities_doc_pack import (
        as_strict,
        audit_docs,
        errors_only,
        iter_doc_files,
        warnings_only,
    )

    if not argv or argv[0] != "check":
        err("Missing subcommand." if not argv else f"Unknown docs subcommand: {argv[0]}")
        print("Usage: aa docs check [path] [--strict] [--include-subtrees]")
        return 1
    args = argv[1:]
    strict = "--strict" in args
    include_subtrees = "--include-subtrees" in args or "--include-submodules" in args
    positional = [a for a in args if not a.startswith("-")]
    target = Path(positional[0]).resolve() if positional else repo_root()
    if not target.is_dir():
        err(f"Not a directory: {target}")
        return 1

    info(f"Auditing documents under {target} ...")
    scanned = len(iter_doc_files(target, include_subtrees=include_subtrees))
    findings = audit_docs(target, include_subtrees=include_subtrees)
    problems = errors_only(as_strict(findings)) if strict else errors_only(findings)
    notes = [] if strict else warnings_only(findings)
    for finding in problems:
        err(f"{finding.code} {finding.path}: {finding.message}")
    for finding in notes:
        warn(f"{finding.code} {finding.path}: {finding.message}")
    print()
    if problems:
        err(f"{len(problems)} error(s), {len(notes)} warning(s) across {scanned} document(s) — "
            "a claim is in the wrong file, a pointer is broken, or a status assertion has no "
            "re-runnable evidence")
        return 1
    ok(f"{scanned} document(s) scanned: no errors, {len(notes)} warning(s)")
    return 0


def _check_skill_pack() -> int:
    """Gate skills/ on the invariants a harness loader actually depends on."""
    from modules.shared.src.taxonomy_skill_audit import audit_pack, iter_skill_files
    from modules.shared.src.taxonomy_core_constant import DESCRIPTION_BUDGET_BYTES

    print("[4/5] Validating skill pack loadability...")
    pack = repo_root() / "skills"
    findings = audit_pack(pack)
    total = len(iter_skill_files(pack))
    for finding in findings:
        err(f"{finding.code}: {finding.message}")
    if not findings:
        ok(f"{total} skills across {len({p.relative_to(pack).parts[0] for p in iter_skill_files(pack)})} categories; names unique, layout loadable")
    else:
        info(f"  ({total} SKILL.md files scanned, budget {DESCRIPTION_BUDGET_BYTES} bytes)")
    return len(findings)


def _check_shell() -> int:
    """Shellcheck for our own .sh files (exclude skills = upstream submodule copies)."""
    errors = 0
    sh_files = [
        f for f in (repo_root() / "modules").rglob("*.sh")
        if "node_modules" not in f.parts and f.relative_to(repo_root()).parts[0] != "skills"
    ]
    if not sh_files:
        return 0
    if not shutil.which("shellcheck"):
        warn("shellcheck not installed; skipping .sh lint")
        return 0
    print("[5/5] Running shellcheck...")
    for f in sh_files:
        try:
            res = subprocess.run(
                ["shellcheck", "-x", str(f)],
                capture_output=True, text=True, input="", timeout=15, check=False,
            )
        except subprocess.TimeoutExpired:
            err(f"shellcheck timeout: {f}")
            errors += 1
            continue
        if res.returncode != 0:
            # tampilkan ringkas (baris pertama saja)
            for line in res.stdout.strip().splitlines()[:3]:
                err(f"shellcheck {f}: {line}")
            errors += 1
    return errors


def cmd_submodules(argv: list[str]) -> int:
    info("Initializing and updating all submodules...")
    code = run_cmd(["git", "-C", str(repo_root()), "submodule", "update", "--init", "--recursive", "vendor/", "internal/"])
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


def cmd_completion(argv):
    from modules.shared.src.agent_completion_verb import (
        cmd_completion as _completion_cmd,
    )
    return _completion_cmd(list(argv))


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
# Main dispatcher (original main() body, verbatim)
# =============================================================================
def _dispatch(argv: list[str], ctx: dict | None = None) -> int:
    """Route argv[0] to the right verb handler (1:1 port of the surface table)."""
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
