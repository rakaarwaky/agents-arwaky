"""CLI entry point — builds every feature container, assembles ctx, dispatches.

Kept alongside the legacy tools/cli/arwaky.py entry point; the old script
will later be thinned down to a thin re-export of this module.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from modules.shared.src.logging.utility_logging import set_verbosity

# --- per-feature surface handlers (imported lazily to keep module import light)
from modules.check.src.surface_check_command import cmd_check
from modules.cli.src.surface_cli_router import dispatch as _dispatch
from modules.completion.src.surface_completion_command import cmd_completion
from modules.daemon.src.surface_daemon_command import cmd_9router, cmd_anytype
from modules.doctor.src.surface_doctor_command import cmd_doctor, cmd_status
from modules.harness.src.surface_harness_command import cmd_connect, cmd_disconnect
from modules.mcp.src.surface_mcp_command import cmd_mcp
from modules.service.src.surface_service_command import cmd_service
from modules.skill.src.surface_skill_command import cmd_skill
from modules.sync.src.surface_sync_command import cmd_sync
from modules.tool.src.surface_tool_command import cmd_install, cmd_list, cmd_run, cmd_tool, cmd_uninstall, cmd_update

HELP_DOC = """agents-arwaky — Unified Tool Orchestrator
Usage: aa <noun> <verb> [arguments...]

PRIMARY COMMANDS:
  status  doctor  tool  skill  docs  connect  disconnect  mcp
  anytype  9router  service  backup  restore

MAINTENANCE:
  check  submodules  clean  reset  sync  completion  help

GLOBAL OPTIONS:
  --no-color / --plain   Disable ANSI colors
  --force-color          Force ANSI colors
  -v / --verbose         Enable debug logging
  -q / --quiet           Suppress info logs
"""


def _gen_correlation_id() -> str:
    return uuid.uuid4().hex[:8]


def _init_sentry() -> None:
    """Opt-in Sentry error tracking (P1-O2), controlled by ARWAKY_SENTRY_DSN."""
    dsn = os.environ.get("ARWAKY_SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk  # type: ignore[import-not-found]
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)
    except ImportError:
        pass


def _build_ctx() -> dict:
    """Build every feature container + surface handler dict for dispatch."""
    from modules.backup.src.root_backup_container import BackupContainer
    from modules.check.src.root_check_container import CheckContainer
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.doctor.src.root_doctor_container import DoctorContainer
    from modules.harness.src.root_harness_container import HarnessContainer
    from modules.mcp.src.root_mcp_container import McpContainer
    from modules.service.src.root_service_container import ServiceContainer
    from modules.skill.src.root_skill_container import SkillContainer
    from modules.sync.src.root_sync_container import SyncContainer
    from modules.tool.src.root_tool_container import ToolContainer

    tool_container = ToolContainer()
    daemon_container = DaemonContainer()
    service_container = ServiceContainer()
    mcp_container = McpContainer()
    skill_container = SkillContainer()
    harness_container = HarnessContainer()
    backup_container = BackupContainer()
    sync_container = SyncContainer()
    check_container = CheckContainer()
    doctor_container = DoctorContainer()

    def _cmd_version(rest: list[str]) -> int:
        vfile = Path(__file__).resolve().parents[4] / "tools/config/version.txt"
        version = "0.1.0"
        if vfile.exists():
            version = vfile.read_text(encoding="utf-8").strip()
        print(f"agents-arwaky {version}")
        return 0

    def _cmd_help(rest: list[str]) -> int:
        print(HELP_DOC)
        return 0

    return {
        "help": _cmd_help,
        "version": _cmd_version,
        "status": lambda r: cmd_status(r, doctor_container.aggregate),
        "doctor": lambda r: cmd_doctor(r, doctor_container.aggregate),
        "check": lambda r: cmd_check(r, check_container.aggregate),
        "tool": lambda r: cmd_tool(r, tool_container.aggregate),
        "list": lambda r: _cmd_tool_list(r, tool_container.aggregate),
        "ls": lambda r: _cmd_tool_list(r, tool_container.aggregate),
        "run": lambda r: _cmd_tool_run(r, tool_container.aggregate),
        "install": lambda r: _cmd_tool_install(r, tool_container.aggregate),
        "update": lambda r: _cmd_tool_update(r, tool_container.aggregate),
        "uninstall": lambda r: _cmd_tool_uninstall(r, tool_container.aggregate),
        "skill": lambda r: cmd_skill(r, skill_container.aggregate),
        "mcp": lambda r: cmd_mcp(r, mcp_container.aggregate),
        "connect": lambda r: cmd_connect(r, harness_container.aggregate),
        "disconnect": lambda r: cmd_disconnect(r, harness_container.aggregate),
        "sync": lambda r: cmd_sync(r, sync_container.aggregate),
        "completion": lambda r: cmd_completion(r),
        "anytype": lambda r: cmd_anytype(r, daemon_container),
        "9router": lambda r: cmd_9router(r, daemon_container),
        "service": lambda r: cmd_service(r, service_container.aggregate),
        "backup": lambda r: _cmd_backup(r, backup_container.aggregate),
        "restore": lambda r: _cmd_restore(r, backup_container.aggregate),
        "submodules": lambda r: _cmd_submodules(r),
        "clean": lambda r: _cmd_clean(r),
        "reset": lambda r: _cmd_reset(r),
        "docs": lambda r: _cmd_docs(r),
    }


def _cmd_tool_list(args, orch) -> int:
    from modules.tool.src.surface_tool_command import cmd_list
    return cmd_list(args, orch)

def _cmd_tool_run(args, orch) -> int:
    from modules.tool.src.surface_tool_command import cmd_run
    return cmd_run(args, orch)

def _cmd_tool_install(args, orch) -> int:
    from modules.tool.src.surface_tool_command import cmd_install
    return cmd_install(args, orch)

def _cmd_tool_update(args, orch) -> int:
    from modules.tool.src.surface_tool_command import cmd_update
    return cmd_update(args, orch)

def _cmd_tool_uninstall(args, orch) -> int:
    from modules.tool.src.surface_tool_command import cmd_uninstall
    return cmd_uninstall(args, orch)

def _cmd_anytype(args, daemon_container) -> int:
    return cmd_anytype(args, manager=daemon_container.anytype)

def _cmd_9router(args, daemon_container) -> int:
    return cmd_9router(args, manager=daemon_container.ninerouter)

def _cmd_backup(args, orch) -> int:
    from modules.backup.src.surface_backup_command import cmd_backup
    return cmd_backup(args, orch)

def _cmd_restore(args, orch) -> int:
    from modules.backup.src.surface_backup_command import cmd_restore
    return cmd_restore(args, orch)

def _cmd_submodules(args: list[str]) -> int:
    # TODO(AES-CLI): inline git submodule init for now; move to a capability.
    import subprocess
    from modules.shared.src.paths.utility_paths import repo_root
    from modules.shared.src.logging.utility_logging import info, ok
    info("Initializing and updating all submodules...")
    code = subprocess.run(
        ["git", "-C", str(repo_root()), "submodule", "update", "--init", "--recursive", "vendor/", "internal/"],
        check=False,
    ).returncode
    if code == 0:
        ok("Submodules ready.")
    return code

def _cmd_clean(args: list[str]) -> int:
    # TODO(AES-CLI): inline artifact removal; move to a maintenance capability.
    import shutil
    from modules.shared.src.paths.utility_paths import repo_root
    from modules.shared.src.logging.utility_logging import info, ok
    from modules.shared.src.xdg.utility_xdg_paths import cache_home
    from modules.shared.src.manifest.capabilities_manifest_reader import load_tools

    info("Cleaning build artifacts and generated configs...")
    for tool in load_tools():
        cache_path = cache_home() / tool.id
        if cache_path.exists():
            shutil.rmtree(cache_path, ignore_errors=True)
            info(f"  Removed {cache_path}")
    (repo_root() / "mcp_servers.generated.json").unlink(missing_ok=True)
    ok("Build artifacts cleaned.")
    return 0

def _cmd_reset(args: list[str]) -> int:
    # TODO(AES-CLI): full factory reset = clean + uninstall + disconnect + skill unskill.
    from modules.shared.src.logging.utility_logging import err, info
    err("reset is not yet fully wired in the AES CLI; run 'aa clean', 'aa tool uninstall --all', 'aa disconnect --all' manually.")
    return 1

def _cmd_docs(args: list[str]) -> int:
    # TODO(AES-CLI): port cmd_docs from tools/cli/arwaky.py (delegates to shared doc_pack).
    from modules.shared.src.logging.utility_logging import err, info
    from modules.shared.src.doc_pack.capabilities_doc_pack import audit_docs, errors_only, as_strict, warnings_only
    from modules.shared.src.paths.utility_paths import repo_root

    if not args or args[0] != "check":
        err("Missing subcommand." if not args else f"Unknown docs subcommand: {args[0]}")
        print("Usage: aa docs check [path] [--strict] [--include-subtrees]")
        return 1
    rest = args[1:]
    strict = "--strict" in rest
    include_subtrees = "--include-subtrees" in rest or "--include-submodules" in rest
    positional = [a for a in rest if not a.startswith("-")]
    target = Path(positional[0]).resolve() if positional else repo_root()
    if not target.is_dir():
        err(f"Not a directory: {target}")
        return 1
    info(f"Auditing documents under {target} ...")
    findings = audit_docs(target, include_subtrees=include_subtrees)
    problems = errors_only(as_strict(findings)) if strict else errors_only(findings)
    notes = [] if strict else warnings_only(findings)
    for finding in problems:
        err(f"{finding.code} {finding.path}: {finding.message}")
    for finding in notes:
        err(f"{finding.code} {finding.path}: {finding.message}")
    print()
    if problems:
        err(f"{len(problems)} error(s), {len(notes)} warning(s) — a claim is in the wrong file, "
            "a pointer is broken, or a status assertion has no re-runnable evidence")
        return 1
    from modules.shared.src.logging.utility_logging import ok
    ok(f"No errors, {len(notes)} warning(s)")
    return 0


def main(argv: list[str]) -> int:
    """Build all feature containers, assemble ctx, dispatch argv."""
    _init_sentry()
    os.environ["ARWAKY_CORRELATION_ID"] = _gen_correlation_id()

    if "--no-color" in argv or "--plain" in argv:
        argv = [a for a in argv if a not in ("--no-color", "--plain")]
    if "--force-color" in argv:
        argv = [a for a in argv if a != "--force-color"]
    if "-v" in argv or "--verbose" in argv:
        set_verbosity("debug")
        argv = [a for a in argv if a not in ("-v", "--verbose")]
    if "-q" in argv or "--quiet" in argv:
        set_verbosity("warning")
        argv = [a for a in argv if a not in ("-q", "--quiet")]

    ctx = _build_ctx()
    return _dispatch(argv, ctx)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
