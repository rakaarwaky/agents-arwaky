"""Skill command surface — aa skill list|show|install|check|help|uninstall.

1:1 exact port of the action bodies from tools/skill/skill.py; pure helpers
live in :mod:`modules.shared.src.utility_skill_registry`.
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_vo import audit_pack
from modules.shared.src.taxonomy_skill_vo import (
    extract_skill_name,
)
from modules.shared.src.utility_logging_setup import (
    pad as _pad,
)
from modules.shared.src.utility_logging_setup import (
    table_widths as _table_widths,
)
from modules.shared.src.utility_skill_registry import (
    PACK_ROOT,
    _get_all_skills,
    _manifest_tools,
    extract_description,
    get_registered_tool_ids,
    get_tool_skills,
    normalize_tool_id,
    provision_single_skill,
    prune_provisioned,
    remove_single_skill,
    resolve_single_skill_file,
    resolve_tool_skills,
    uninstall_tool_skills,
)


def cmd_uninstall(argv):
    """Remove provisioned skills (by tool, skill, or all) from a target workspace."""
    target_name = ""
    target_dir = Path.cwd()
    custom_dest = ""
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--target", "-t"):
            target_dir = Path(argv[i + 1]); i += 2; continue
        if a in ("--dest", "-d"):
            custom_dest = argv[i + 1]; i += 2; continue
        if not target_name:
            target_name = a
        i += 1
    if not target_name:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill uninstall <tool-name|skill-name|all> [--target <dir>]")
        print()
        print("Note: Default target is the CURRENT WORKING DIRECTORY (.agents/skills/).")
        print("      This is different from 'aa disconnect' which removes skills from harness paths.")
        return 1

    # all tools
    if target_name == "all":
        print(f"Removing ALL provisioned skills from target workspace: {target_dir}")
        print("------------------------------------------------------------------")
        total = 0
        for tid, _, _ in get_registered_tool_ids():
            for sf in get_tool_skills(tid):
                if remove_single_skill(sf, target_dir, custom_dest):
                    total += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 All provisioned skills removed ({total} skill file(s) processed).")
        return 0

    # tool id
    tid = normalize_tool_id(target_name)
    if tid:
        uninstall_tool_skills(tid, target_dir, custom_dest)
        return 0

    # single skill
    sf = resolve_single_skill_file(target_name)
    if sf:
        print(f"Removing individual skill '{target_name}'...")
        remove_single_skill(sf, target_dir, custom_dest)
        return 0

    print(f"Error: Neither tool nor skill named '{target_name}' could be found.")
    print("Run 'aa skill list' to see all available tools and skills.")
    return 1

# --- install -------------------------------------------------------------------
def _provision_base(target_dir: Path, custom_dest: str) -> Path:
    """Where provisioned skill folders land, mirroring provision_single_skill."""
    if custom_dest and not custom_dest.endswith(".md"):
        return Path(custom_dest)
    return target_dir / ".agents" / "skills"


def _report_prune(base: Path) -> None:
    """Drop provisioned entries the pack no longer provides; leave foreign skills."""
    removed = prune_provisioned(base, PACK_ROOT)
    print("------------------------------------------------------------------")
    if not removed:
        print(f"Prune: nothing stale under {base}")
        return
    for name in removed:
        print(f"  - [PRUNE] {base / name}")
    print(f"Prune: removed {len(removed)} provisioned skill(s) the pack no longer provides.")


def cmd_install(argv):
    """Install skills (by tool, skill, or all) into a target workspace."""
    target_name = ""
    target_dir = Path.cwd()
    custom_dest = ""
    force = False
    link = False
    prune = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--target", "-t"):
            target_dir = Path(argv[i + 1]); i += 2; continue
        if a in ("--dest", "-d"):
            custom_dest = argv[i + 1]; i += 2; continue
        if a in ("--force", "-f"):
            force = True; i += 1; continue
        if a == "--prune":
            prune = True; i += 1; continue
        if a in ("--copy", "--copy-skills"):
            link = False; i += 1; continue
        if a in ("--link", "--symlink"):
            link = True; i += 1; continue
        if not target_name:
            target_name = a
        i += 1

    if prune:
        # Prune first, then provision: the end state is the pack, exactly.
        # `--prune` without a target is a valid cleanup-only invocation.
        _report_prune(_provision_base(target_dir, custom_dest))
        if not target_name:
            return 0

    if not target_name:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill install <tool-name|skill-name|all> [--target <dir>] [--force] [--prune]")
        return 1

    if target_name == "all":
        print(f"Provisioning ALL skills for ALL tools into target workspace: {target_dir}")
        print("------------------------------------------------------------------")
        total = 0
        for tid, _, _ in get_registered_tool_ids():
            for sf in get_tool_skills(tid):
                if provision_single_skill(sf, target_dir, custom_dest, force, link):
                    total += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 All {total} ecosystem skills provisioned successfully.")
        return 0

    tid = normalize_tool_id(target_name)
    if tid:
        skills = get_tool_skills(tid)
        if not skills:
            print(f"Error: No skills found for tool '{tid}'.", file=sys.stderr)
            return 1
        print(f"Installing all {len(skills)} skills for tool '{tid}'...")
        print(f"Target Workspace: {target_dir}")
        print("------------------------------------------------------------------")
        ok = 0
        for sf in skills:
            if provision_single_skill(sf, target_dir, custom_dest, force, link):
                ok += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 Successfully provisioned {ok} skill(s) for tool '{tid}'.")
        return 0

    sf = resolve_single_skill_file(target_name)
    if sf:
        print(f"Provisioning individual skill '{target_name}'...")
        provision_single_skill(sf, target_dir, custom_dest, force, link)
        return 0

    print(f"Error: Neither tool nor skill named '{target_name}' could be found.")
    print("Run 'aa skill list' to see all available tools and skills.")
    return 1


def _term_width():
    """Return the current terminal column width, defaulting to 80."""
    try:
        import shutil
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


# --- list ----------------------------------------------------------------------
def cmd_list(argv):
    """List tools and their available skills, optionally filtered by tool id."""
    tool_filter = argv[0] if argv else ""
    pack = get_tool_skills("all")  # satu pack user di tools/skills/
    total_unique = len(pack)
    term_w = _term_width()
    # Reserve space for inter-column separators (one space between each column)
    n_cols = 2 if (tool_filter and tool_filter != "--all") else 4
    available = max(40, term_w - 2 - (n_cols - 1))
    if tool_filter and tool_filter != "--all":
        tid = normalize_tool_id(tool_filter)
        if not tid:
            print(f"Error: Tool '{tool_filter}' not found in manifest.", file=sys.stderr)
            return 1
        w_name, w_desc = _table_widths(available, [3, 7])
        print(f"Skills available for tool '{tid}' (shared skill pack):")
        print("-" * available)
        print(f"{_pad('SKILL NAME', w_name)} {_pad('DESCRIPTION', w_desc)}")
        print("-" * available)
        for sf in pack:
            print(f"{_pad(extract_skill_name(sf), w_name)} {_pad(extract_description(sf), w_desc)}")
        print("-" * available)
        print(f"Total skill pack: {total_unique} | Install: 'aa skill install {tid}'")
        return 0

    w_id, w_cat, w_count, w_desc = _table_widths(available, [2, 1, 1, 6])
    print("Available Tools & Shared Skill Pack in agents-arwaky:")
    print("-" * available)
    print(f"{_pad('TOOL ID', w_id)} {_pad('CATEGORY', w_cat)} {_pad('SKILLS COUNT', w_count)} {_pad('DESCRIPTION', w_desc)}")
    print("-" * available)
    for tid, cat, desc in get_registered_tool_ids():
        print(f"{_pad(tid, w_id)} {_pad(cat, w_cat)} {_pad(str(total_unique), w_count)} {_pad(desc, w_desc)}")
    print("-" * available)
    print(f"Total Tools: {len(get_registered_tool_ids())} | Total Skill Pack (unique): {total_unique}")
    return 0


# --- check ---------------------------------------------------------------------
def cmd_check(argv=None):
    """Audit per-tool skill coverage and pack loadability; optional JSON output."""
    argv = list(argv or [])
    json_mode = "--json" in argv
    term_w = _term_width()
    n_cols = 5
    available = max(40, term_w - 2 - (n_cols - 1))
    w_id, w_cat, w_status, w_count, w_path = _table_widths(available, [2, 1, 1, 1, 5])
    tools = _manifest_tools()
    documented = shared_only = 0
    rows = []
    for tool in tools:
        tid = str(tool.get("id", ""))
        cat = str(tool.get("category", ""))
        dedicated = resolve_tool_skills(tool)
        sample = ""
        if dedicated:
            documented += 1
            status = "DOCUMENTED"
            sample = str(dedicated[0].relative_to(REPO_ROOT))
        else:
            shared_only += 1
            status = "SHARED-ONLY"
        source_path = str(tool.get("path", ""))
        if source_path and not (REPO_ROOT / source_path).exists():
            status = "PATH MISSING"
        rows.append({
            "id": tid,
            "category": cat,
            "status": status,
            "own_skills": len(dedicated),
            "sample": sample,
        })
    pack_size = len(_get_all_skills())
    findings = audit_pack(REPO_ROOT / "skills")
    if json_mode:
        import json as _json
        out = {
            "tools": rows,
            "totals": {
                "tools": len(tools),
                "documented": documented,
                "shared_only": shared_only,
                "pack_size": pack_size,
            },
            "loadability": [
                {"code": f.code, "message": f.message} for f in findings
            ],
            "ok": not findings,
        }
        print(_json.dumps(out, indent=2, ensure_ascii=False))
        return 1 if findings else 0
    print("Auditing the shared skill pack against manifest.json tools:")
    print("-" * available)
    print(f"{_pad('TOOL ID', w_id)} {_pad('CATEGORY', w_cat)} {_pad('STATUS', w_status)} {_pad('OWN SKILLS', w_count)} {_pad('SAMPLE PATH', w_path)}")
    print("-" * available)
    for row in rows:
        print(f"{_pad(row['id'], w_id)} {_pad(row['category'], w_cat)} {_pad(row['status'], w_status)} {_pad(str(row['own_skills']), w_count)} {_pad(row['sample'], w_path)}")
    print("-" * available)
    print(f"Total Tools: {len(tools)} | Documented: {documented} | Shared-only: {shared_only}")
    print(f"Shared pack: {pack_size} SKILL.md (provisioned to every tool; 'aa skill install <tool>' copies all of them)")
    if findings:
        print()
        print(f"Loadability findings ({len(findings)}):")
        for finding in findings:
            print(f"  ! {finding.code}: {finding.message}")
    else:
        print("Loadability: clean (layout, names, descriptions, budget)")
    return 1 if findings else 0


# --- show ----------------------------------------------------------------------
def cmd_show(argv):
    """Display the SKILL.md content for a tool or individual skill."""
    query = argv[0] if argv else ""
    if not query:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill show <tool-name|skill-name>")
        return 1
    tid = normalize_tool_id(query)
    if tid:
        skills = get_tool_skills(tid)
        if len(skills) > 1:
            print(f"Tool '{tid}' contains {len(skills)} skills.")
            print(f"Displaying primary canonical skill: {skills[0]}")
            print("-" * 66)
            print(skills[0].read_text(encoding="utf-8", errors="replace"))
            print("-" * 66)
            print(f"Other skills in '{tid}':")
            for sf in skills[1:]:
                print(f"  - {extract_skill_name(sf)}")
            print("\nView any specific skill using 'aa skill show <skill-name>'.")
            return 0
        if len(skills) == 1:
            print(f"Source: {skills[0]}")
            print("-" * 66)
            print(skills[0].read_text(encoding="utf-8", errors="replace"))
            return 0
    sf = resolve_single_skill_file(query)
    if sf:
        print(f"Source: {sf}")
        print("-" * 66)
        print(sf.read_text(encoding="utf-8", errors="replace"))
        return 0
    print(f"Error: Skill or tool '{query}' not found.", file=sys.stderr)
    return 1


# --- help & main ---------------------------------------------------------------
def cmd_help():
    """Print the top-level help screen for the skill subcommand."""
    print("agents-arwaky Skill Manager (aa skill)")
    print("Discover, inspect and provision AI agent skills.")
    print()
    print("COMMANDS:")
    print("  list, ls [tool]             List all tools and their associated skills")
    print("  install, get, copy <name>   Install ALL skills for a tool (or a specific skill)")
    print("  install all, sync           Provision ALL skills for ALL tools")
    print("  install --prune             Drop provisioned skills the pack no longer provides")
    print("  uninstall, unskill, remove  Remove provisioned skills from CURRENT WORKING DIRECTORY (.agents/skills/)")
    print("  show <name>                 Display the content of a skill's SKILL.md")
    print("  check [--json]              Audit per-tool skill coverage and pack loadability")
    print("  help                        Show this help screen")
    print()
    print("SUBCOMMAND HELP:")
    print("  aa skill list --help        Show list-specific options")
    print("  aa skill install --help     Show install-specific options")
    print("  aa skill uninstall --help   Show uninstall-specific options")
    print("  aa skill show --help        Show show-specific options")
    return 0


def cmd_list_help():
    """Print help for the 'aa skill list' subcommand."""
    print("Usage: aa skill list [tool]")
    print()
    print("List all registered tools and their associated skills, or filter by tool.")
    print()
    print("Options:")
    print("  tool              Optional tool ID to filter (e.g., 'lint-arwaky', 'vision-arwaky')")
    print("  --all             Show all tools (default behavior)")
    return 0


def cmd_install_help():
    """Print help for the 'aa skill install' subcommand."""
    print("Usage: aa skill install <tool|skill|all> [--target DIR] [--dest PATH] [--force] [--prune]")
    print()
    print("Install all skills for a tool, a specific skill, or all skills for all tools.")
    print()
    print("Skills are COPIED into the project workspace: it is meant to be committed")
    print("and pushed, and a symlink to the agents-arwaky checkout resolves to an")
    print("absolute path that breaks in anyone else's clone (--force refreshes an")
    print("existing copy from the pack). For harness-wide skill wiring that DOES")
    print("share self-improvements via symlinks, use 'aa connect <harness>'.")
    print()
    print("Options:")
    print("  <tool|skill|all>    Target tool ID, skill name, or 'all' for everything")
    print("  --target, -t DIR    Target workspace directory (default: current directory)")
    print("  --dest, -d PATH     Custom destination path")
    print("  --force, -f         Overwrite existing skills")
    print("  --link, --symlink   Symlink the skill dir to the pack (local only; do not commit)")
    print("  --copy              Explicitly request copies (the default)")
    print("  --prune             Also delete provisioned skills the pack no longer provides.")
    print("                      Only entries carrying .arwaky-skill.json, or links into the")
    print("                      pack, are removed — hand-written skills are never touched.")
    print("                      Alone ('aa skill install --prune') it prunes without installing.")
    return 0


def cmd_uninstall_help():
    """Print help for the 'aa skill uninstall' subcommand."""
    print("Usage: aa skill uninstall <tool|skill|all> [--target DIR] [--dest PATH]")
    print()
    print("Remove provisioned skills from the target workspace.")
    print()
    print("Options:")
    print("  <tool|skill|all>  Target tool ID, skill name, or 'all' for everything")
    print("  --target, -t DIR  Target workspace directory (default: current directory)")
    print("  --dest, -d PATH   Custom destination path")
    return 0


def cmd_show_help():
    """Print help for the 'aa skill show' subcommand."""
    print("Usage: aa skill show <tool|skill>")
    print()
    print("Display the content of a skill's SKILL.md file.")
    print()
    print("Arguments:")
    print("  <tool|skill>      Tool ID or skill name to display")
    return 0


def main(argv: list[str], orch: object | None = None) -> int:
    """Dispatch a top-level skill subcommand and return an exit code."""
    if not argv or argv[0] in ("-h", "--help", "help"):
        return cmd_help()
    action = argv[0]
    rest = argv[1:]
    # Per-subcommand --help support
    if rest and rest[0] in ("-h", "--help", "help"):
        if action in ("list", "ls"):
            return cmd_list_help()
        if action in ("install", "copy", "get", "add", "sync"):
            return cmd_install_help()
        if action in ("uninstall", "remove", "unskill", "delete"):
            return cmd_uninstall_help()
        if action in ("show", "cat", "view"):
            return cmd_show_help()
    if action in ("list", "ls"):
        return cmd_list(rest)
    if action in ("check", "audit"):
        return cmd_check(rest)
    if action in ("install", "copy", "get", "add"):
        return cmd_install(rest)
    if action in ("uninstall", "remove", "unskill", "delete"):
        return cmd_uninstall(rest)
    if action == "sync":
        return cmd_install(["all", *rest])
    if action in ("show", "cat", "view"):
        return cmd_show(rest)
    print(f"Unknown skill command: {action}")
    return cmd_help()


from modules.shared.src.contract_skill_protocol import ISkillRegistryProtocol
from modules.shared.src.taxonomy_skill_vo import ARGS_EMPTY, FILTER_EMPTY, QUERY_EMPTY, ExitCode, SkillArgs, ToolFilter


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillRegistryAdapter(ISkillRegistryProtocol):
    """ISkillRegistryProtocol implementation wrapping the module-level cmd_* functions.

    Lets the root composition layer inject a concrete registry object
    into :class:`modules.skill.src.agent_skill_orchestrator.SkillOrchestrator`
    without the agent importing the capabilities module (AES201 rule 8).
    """

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list(self, tool_filter: ToolFilter = FILTER_EMPTY) -> ExitCode:
        """List skills for tools, wrapping the module-level cmd_list."""
        return ExitCode(cmd_list([str(tool_filter)] if str(tool_filter) else []))

    def check(self) -> ExitCode:
        """Audit the shared skill pack loadability, wrapping cmd_check."""
        return ExitCode(cmd_check([]))

    def show(self, query: str = QUERY_EMPTY) -> ExitCode:
        """Display a skill's content, wrapping cmd_show."""
        return ExitCode(cmd_show([str(query)] if str(query) else []))

    def install(self, args: SkillArgs) -> ExitCode:
        """Provision skills into a target workspace, wrapping cmd_install."""
        return ExitCode(cmd_install(list(args)))

    def uninstall(self, args: SkillArgs) -> ExitCode:
        """Remove provisioned skills from a target workspace, wrapping cmd_uninstall."""
        return ExitCode(cmd_uninstall(list(args)))

    def sync(self, args: SkillArgs = ARGS_EMPTY) -> ExitCode:
        """Alias for installing all skills across all tools."""
        return ExitCode(cmd_install(["all", *list(args)]))
