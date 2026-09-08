#!/usr/bin/env python3
"""agents-arwaky Unified Tool Orchestrator (Python) — pengganti arwaky-cli.sh."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from manifest import Tool, find_tool, load_tools, repo_root  # noqa: E402
from ui import (  # noqa: E402
    BOLD, BLUE, CYAN, DIM, GREEN, RED, RESET, YELLOW,
    banner, err, info, ok, sub, warn,
)
from xdg import bin_home, config_home, data_home, ensure_path  # noqa: E402


# =============================================================================
# Helpers
# =============================================================================
def run_cmd(cmd: list[str]) -> int:
    try:
        return subprocess.run(cmd).returncode
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


def executable_path(binary: str):
    found = shutil.which(binary)
    if found:
        return Path(found)
    local = bin_home() / binary
    if local.exists() and os.access(local, os.X_OK):
        return local
    return None


def install_dir_candidates(tool: Tool) -> list[Path]:
    overrides = {"workspace": "google-workspace-mcp", "fetch": "fetch-mcp", "anytype": "anytype-mcp"}
    names = []
    if tool.id in overrides:
        names.append(overrides[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    return [repo_root() / "tools/install" / f"install_{n.replace(chr(45), chr(95))}.py" for n in names if n]


def find_installer(tool: Tool):
    for candidate in install_dir_candidates(tool):
        if candidate.exists():
            return candidate
    return None


def uninstall_dir_candidates(tool: Tool) -> list[Path]:
    overrides = {"workspace": "google-workspace-mcp", "fetch": "fetch-mcp", "anytype": "anytype-mcp"}
    names = []
    if tool.id in overrides:
        names.append(overrides[tool.id])
    names.append(tool.id)
    names.append(f"{tool.id}-mcp")
    return [repo_root() / "tools/uninstall" / f"uninstall_{n.replace(chr(45), chr(95))}.py" for n in names if n]


def find_uninstaller(tool: Tool):
    for candidate in uninstall_dir_candidates(tool):
        if candidate.exists():
            return candidate
    return None


def remove_tool_state(tool: Tool) -> None:
    (bin_home() / tool.binary).unlink(missing_ok=True)
    shutil.rmtree(data_home() / tool.id, ignore_errors=True)
    shutil.rmtree(config_home() / tool.id, ignore_errors=True)
    ok(f"Removed state for {tool.id}")


# =============================================================================
# Commands
# =============================================================================
def cmd_help(argv: list[str]) -> int:
    banner()
    print(f"{BOLD}USAGE:{RESET}")
    print("  aa <command> [arguments...]")
    print()
    print(f"{BOLD}PRIMARY COMMANDS:{RESET}")
    print(f"  {GREEN}status{RESET}                         Check health, submodule and binary installation status")
    print(f"  {GREEN}doctor{RESET}                         Diagnose runtime environment & toolchain")
    print(f"  {GREEN}list{RESET}                           List all registered tools")
    print(f"  {GREEN}run{RESET} <tool> [args]              Execute registered tool")
    print(f"  {GREEN}install{RESET} [tool]                 Install tools using per-tool install.py")
    print(f"  {GREEN}mcp{RESET} [list|generate|show]       Manage MCP configuration")
    print(f"  {GREEN}skill{RESET} [args]                   Skill manager")
    print(f"  {GREEN}connect{RESET} [args]                 Harness connector")
    print(f"  {GREEN}disconnect{RESET} [args]              Harness disconnector")
    print(f"  {GREEN}unconnect{RESET}                      Remove agents-arwaky from all harnesses")
    print(f"  {GREEN}unskill{RESET}                        Remove provisioned skills from current workspace")
    print(f"  {GREEN}anytype{RESET} [args]                 Anytype daemon manager")
    print(f"  {GREEN}9router{RESET} [args]                 9Router daemon manager")
    print(f"  {GREEN}service{RESET} [args]                 Service manager")
    print(f"  {GREEN}backup{RESET} [args]                  Backup manager")
    print(f"  {GREEN}restore{RESET} [args]                 Restore manager")
    print()
    print(f"{BOLD}MAINTENANCE:{RESET}")
    print(f"  {CYAN}check{RESET}                          Run repository verification (JSON + Python compile)")
    print(f"  {CYAN}submodules{RESET}                     Initialize/update git submodules")
    print(f"  {CYAN}clean{RESET}                          Remove generated artifacts")
    print(f"  {CYAN}uninstall{RESET} [tool|--all]         Remove installed binaries/data (per-tool uninstall.py)")
    print(f"  {CYAN}reset{RESET}                          Full factory reset = clean + uninstall + unconnect + unskill")
    print(f"  {CYAN}help{RESET}                           Show this help")
    print()
    return 0


def cmd_status(argv: list[str]) -> int:
    ensure_path()
    banner()
    print(f"{BOLD}System & Tool Health Status:{RESET}")
    print("--------------------------------------------------------------------------------")
    print(f"{BOLD}{'TOOL':<14} {'CATEGORY':<10} {'TARGET BINARY':<20} STATUS{RESET}")
    print("--------------------------------------------------------------------------------")
    for tool in load_tools():
        cat_color = GREEN if tool.category == "internal" else CYAN
        if is_submodule_missing(tool.path):
            status = f"{RED}Submodule Missing{RESET}"
        elif executable_path(tool.binary):
            status = f"{GREEN}Installed ({tool.binary}){RESET}"
        elif (bin_home() / tool.binary).exists():
            status = f"{GREEN}Ready ({bin_home()}){RESET}"
        elif tool.category == "internal":
            status = f"{BLUE}Source Ready (Internal){RESET}"
        else:
            status = f"{YELLOW}Not Installed{RESET}"
        print(f"{tool.id:<14} {cat_color}{tool.category:<10}{RESET} {tool.binary:<20} {status}")
    print("--------------------------------------------------------------------------------")
    return 0


def cmd_doctor(argv: list[str]) -> int:
    ensure_path()
    banner()
    print(f"{BOLD}Running Environment Diagnostics...{RESET}")
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
            print(f"  {DIM}[SKIP]{RESET} {util} not installed (optional)")
    engine = shutil.which("podman") or shutil.which("docker")
    if engine:
        ok(f"Container engine: {engine}")
    else:
        warn("Podman/Docker not found (only needed for 9router & anytype daemons)")
    print("------------------------------------------------------")
    print(f"{GREEN}Diagnostics complete.{RESET}")
    return 0


def cmd_list(argv: list[str]) -> int:
    banner()
    print(f"{BOLD}Registered Tools in agents-arwaky:{RESET}")
    print("--------------------------------------------------------------------------------")
    print(f"{BOLD}{'TOOL ID':<14} {'CATEGORY':<10} {'MCP?':<8} {'DESCRIPTION':<45}{RESET}")
    print("--------------------------------------------------------------------------------")
    for tool in load_tools():
        cat_color = GREEN if tool.category == "internal" else CYAN
        mcp_label = "Yes" if tool.is_mcp else "No"
        print(f"{tool.id:<14} {cat_color}{tool.category:<10}{RESET} {mcp_label:<8} {tool.description:<45}")
    print("--------------------------------------------------------------------------------")
    return 0


def cmd_run(argv: list[str]) -> int:
    if not argv:
        err("Missing tool name.")
        print("Usage: aa run <tool-name> [args...]")
        return 1
    tool = find_tool(argv[0])
    if not tool:
        err(f"Tool '{argv[0]}' not found in manifest.")
        print("Run 'aa list' to see all available tools.")
        return 1
    tool_args = argv[1:]
    exe = executable_path(tool.binary)
    if exe:
        os.execvpe(str(exe), [str(exe), *tool_args], os.environ)
    tool_dir = repo_root() / tool.path
    if tool.category == "internal":
        if tool.id == "lint" and shutil.which("cargo"):
            os.execvpe("cargo", ["cargo", "run", "--quiet", "--manifest-path",
                                 str(tool_dir / "Cargo.toml"), "--bin", "lint-arwaky-cli", "--", *tool_args], os.environ)
        if tool.id in {"vision", "qwen-web", "blender"} and shutil.which("uv"):
            os.execvpe("uv", ["uv", "run", "--directory", str(tool_dir), tool.binary, *tool_args], os.environ)
    err(f"Binary '{tool.binary}' for tool '{tool.id}' is not installed or runnable.")
    print(f"Try running: {BOLD}aa install {tool.id}{RESET} or {BOLD}aa install{RESET}")
    return 1


def cmd_install(argv: list[str]) -> int:
    ensure_path()
    target = argv[0] if argv else "all"
    # Konfirmasi untuk install all (Plan2 P0)
    if target == "all" and "--yes" not in argv and "-y" not in argv:
        answer = input(f"Install ALL tools? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            warn("Aborted.")
            return 1
    print(f"{BOLD}>>> Installing {target} using per-tool Python installers...{RESET}")
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
    failed, skipped = [], []
    for tool in tools:
        installer = find_installer(tool)
        if not installer:
            skipped.append(tool.id)
            warn(f"No install.py found for {tool.id}")
            continue
        info(f"Installing {tool.id} -> {installer}")
        if run_cmd([sys.executable, str(installer)]) != 0:
            failed.append(tool.id)
    if target == "all":
        gen = repo_root() / "tools" / "mcp" / "generate_config.py"
        if gen.exists():
            info("Generating MCP configuration...")
            run_cmd([sys.executable, str(gen)])
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


def cmd_mcp(argv: list[str]) -> int:
    action = argv[0] if argv else "list"
    generated = repo_root() / "mcp_servers.generated.json"
    generator = repo_root() / "tools" / "mcp" / "generate_config.py"
    if action == "list":
        print(f"{BOLD}MCP-Enabled Tools:{RESET}")
        for tool in load_tools():
            if tool.is_mcp:
                print(f"  - {tool.id} [{tool.category}]: {tool.description}")
        return 0
    if action == "generate":
        if generator.exists():
            return run_cmd([sys.executable, str(generator), *argv[1:]])
        err("tools/mcp/generate_config.py not found.")
        return 1
    if action in {"show", "path"}:
        if not generated.exists():
            warn("Configuration file not found. Generating now...")
            run_cmd([sys.executable, str(generator)])
        if generated.exists():
            print(f"{BOLD}Path:{RESET} {generated}")
            print()
            print(generated.read_text(encoding="utf-8"))
            return 0
        err("Failed to generate MCP configuration.")
        return 1
    err(f"Unknown MCP action: {action}")
    print("Valid actions: list, generate, show")
    return 1


def cmd_skill(argv: list[str]) -> int:
    return exec_python(repo_root() / "tools" / "skill" / "skill.py", argv)


def cmd_connect(argv: list[str]) -> int:
    script = repo_root() / "tools" / "connect" / "connect.py"
    if not script.exists():
        err("tools/connect/connect.py not found.")
        return 1
    return run_cmd([sys.executable, str(script), "connect", *argv])


def cmd_disconnect(argv: list[str]) -> int:
    script = repo_root() / "tools" / "connect" / "connect.py"
    if not script.exists():
        err("tools/connect/connect.py not found.")
        return 1
    return run_cmd([sys.executable, str(script), "disconnect", *argv])


def cmd_unconnect(argv: list[str]) -> int:
    script = repo_root() / "tools" / "connect" / "connect.py"
    if not script.exists():
        err("tools/connect/connect.py not found.")
        return 1
    info("Unconnecting agents-arwaky from all harnesses...")
    code = run_cmd([sys.executable, str(script), "disconnect", "--all"])
    if code != 0:
        return code
    print()
    info("Cleaning legacy lean-ctx remnants...")
    return run_cmd([sys.executable, str(script), "disconnect", "--lean-ctx"])


def cmd_unskill(argv: list[str]) -> int:
    script = repo_root() / "tools" / "skill" / "skill.py"
    if not script.exists():
        err("tools/skill/skill.py not found.")
        return 1
    info("Removing provisioned skills from current working directory...")
    return run_cmd([sys.executable, str(script), "uninstall", "all", "--target", os.getcwd()])


def cmd_anytype(argv: list[str]) -> int:
    return exec_python(repo_root() / "tools/daemons/anytype_daemon.py", argv)


def cmd_9router(argv: list[str]) -> int:
    return exec_python(repo_root() / "tools/daemons/ninerouter_daemon.py", argv)


def cmd_service(argv: list[str]) -> int:
    return exec_python(repo_root() / "tools/service/service_manager.py", argv)


def cmd_backup(argv: list[str]) -> int:
    return exec_python(repo_root() / "tools/backup/backup_manager.py", ["backup", *argv])


def cmd_restore(argv: list[str]) -> int:
    return exec_python(repo_root() / "tools/backup/backup_manager.py", ["restore", *argv])


def cmd_check(argv: list[str]) -> int:
    import py_compile
    banner()
    info("Running Python-based repository verification...")
    errors = 0
    print()
    print("[1/2] Validating JSON files...")
    for json_file in (repo_root() / "tools").rglob("*.json"):
        if "node_modules" in json_file.parts:
            continue
        try:
            json.loads(json_file.read_text(encoding="utf-8"))
            ok(str(json_file.relative_to(repo_root())))
        except Exception as e:
            err(f"Invalid JSON: {json_file}: {e}")
            errors += 1
    print()
    print("[2/2] Compiling Python files...")
    for py_file in (repo_root() / "tools").rglob("*.py"):
        if "node_modules" in py_file.parts:
            continue
        try:
            py_compile.compile(str(py_file), doraise=True)
            ok(str(py_file.relative_to(repo_root())))
        except Exception as e:
            err(f"Python compile error: {py_file}: {e}")
            errors += 1
    print()
    # Shellcheck untuk .sh milik kita (exclude tools/skills = salinan submodule upstream)
    sh_files = [
        f for f in (repo_root() / "tools").rglob("*.sh")
        if "node_modules" not in f.parts and "tools/skills" not in f.relative_to(repo_root()).as_posix()
    ]
    if sh_files:
        if shutil.which("shellcheck"):
            print("[3/3] Running shellcheck...", flush=True)
            for f in sh_files:
                try:
                    res = subprocess.run(
                        ["shellcheck", "-x", str(f)],
                        capture_output=True, text=True, input="", timeout=15,
                    )
                except subprocess.TimeoutExpired:
                    err(f"shellcheck timeout: {f}")
                    errors += 1
                    continue
                if res.returncode != 0:
                    # tampilkan ringkas (baris pertama saja)
                    first = res.stdout.strip().splitlines()[:3]
                    for line in first:
                        err(f"shellcheck {f}: {line}")
                    errors += 1
        else:
            warn("shellcheck not installed; skipping .sh lint")
    print()
    if errors:
        err(f"Verification FAILED with {errors} errors.")
        return 1
    ok("All verifications PASSED.")
    return 0


def cmd_submodules(argv: list[str]) -> int:
    info("Initializing and updating all submodules...")
    code = run_cmd(["git", "-C", str(repo_root()), "submodule", "update", "--init", "--recursive", "vendor/", "internal/"])
    if code == 0:
        ok("Submodules ready.")
    return code


def cmd_clean(argv: list[str]) -> int:
    info("Cleaning build artifacts and generated configs...")
    for dist_dir in (repo_root() / "tools").glob("*/dist"):
        shutil.rmtree(dist_dir, ignore_errors=True)
    (repo_root() / "mcp_servers.generated.json").unlink(missing_ok=True)
    ok("Build artifacts cleaned.")
    return 0


def uninstall_tool(tool: Tool) -> int:
    uninstaller = find_uninstaller(tool)
    if uninstaller:
        info(f"Uninstalling {tool.id} using {uninstaller}")
        return run_cmd([sys.executable, str(uninstaller)])
    warn(f"No uninstall.py found for {tool.id}, removing default state")
    remove_tool_state(tool)
    return 0


def cmd_uninstall(argv: list[str]) -> int:
    target = argv[0] if argv else "--all"
    # Konfirmasi untuk uninstall all (Plan2 P0)
    if target in {"--all", "all"} and "--yes" not in argv and "-y" not in argv:
        warn("WARNING: This will remove ALL installed tool binaries, data and config.")
        answer = input("Type 'uninstall' to continue: ").strip()
        if answer.lower() != "uninstall":
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
    if "--yes" not in argv:
        warn("WARNING: This will wipe installed tool state and reset the repository.")
        warn("This action cannot be undone.")
        answer = input("Type RESET to continue: ").strip()
        if answer != "RESET":
            warn("Aborted.")
            return 1
    warn("WARNING: This will wipe installed tool state and reset the repository.")
    warn("This action cannot be undone.")
    print()
    info("[1/4] clean")
    cmd_clean([])
    print()
    info("[2/4] uninstall --all")
    cmd_uninstall(["--all"])
    print()
    info("[3/4] unconnect")
    cmd_unconnect([])
    print()
    info("[4/4] unskill")
    cmd_unskill([])
    print()
    info("Resetting submodules...")
    run_cmd(["git", "-C", str(repo_root()), "submodule", "foreach", "--recursive", "git clean -fd && git checkout ."])
    ok("Factory reset complete.")
    return 0


def cmd_completion(argv):
    script = repo_root() / "tools/completion/completion.py"
    if not script.exists():
        err("tools/completion/completion.py not found.")
        return 1
    return run_cmd([sys.executable, str(script), *argv])


def cmd_sync(argv):
    script = repo_root() / "tools/sync/sync_all.py"
    if not script.exists():
        err("tools/sync/sync_all.py not found.")
        return 1
    return run_cmd([sys.executable, str(script), *argv])


# =============================================================================
# Main dispatcher
# =============================================================================
def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        return cmd_help([])
    cmd = argv[0]
    rest = argv[1:]
    dispatch = {
        "status": cmd_status, "doctor": cmd_doctor, "list": cmd_list, "ls": cmd_list,
        "run": cmd_run, "install": cmd_install, "mcp": cmd_mcp,
        "skill": cmd_skill, "skills": cmd_skill,
        "connect": cmd_connect, "disconnect": cmd_disconnect,
        "unconnect": cmd_unconnect, "unskill": cmd_unskill,
        "anytype": cmd_anytype, "9router": cmd_9router, "service": cmd_service,
        "backup": cmd_backup, "restore": cmd_restore,
        "completion": cmd_completion, "sync": cmd_sync,
        "check": cmd_check, "submodules": cmd_submodules, "clean": cmd_clean,
        "uninstall": cmd_uninstall, "reset": cmd_reset,
        "help": cmd_help, "-h": cmd_help, "--help": cmd_help,
    }
    handler = dispatch.get(cmd)
    if not handler:
        err(f"Unknown command: {cmd}")
        print()
        cmd_help([])
        return 1
    return handler(rest)


if __name__ == "__main__":
    raise SystemExit(main())
