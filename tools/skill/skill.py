#!/usr/bin/env python3
"""agents-arwaky Skill Manager (Python) — port of tools/skill/skill-manager.sh.

Commands:
    aa skill list [tool]
    aa skill check|audit
    aa skill install|copy|get|add <tool|skill|all> [--target DIR] [--dest PATH] [--force]
    aa skill uninstall|unskill|remove|delete <tool|skill|all> [--target DIR] [--dest PATH]
    aa skill show|cat|view <tool|skill>
    aa skill sync
"""
import json
import posixpath
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from skill_names import extract_skill_name, sanitize_skill_name, safe_skill_name, ensure_under  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
REPO_ROOT = repo_root()
MANIFEST = REPO_ROOT / "tools/config/manifest.json"

from ui import pad as _pad, table_widths as _table_widths  # type: ignore[import-not-found]

# --- tool registry ------------------------------------------------------------
def get_registered_tool_ids():
    """Return list of (tool_id, category, description) from manifest."""
    if not MANIFEST.exists():
        return []
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for t in data.get("tools", []):
        out.append((t.get("id", ""), t.get("category", ""), t.get("description", "")))
    return out


def normalize_tool_id(query):
    """Resolve alias -> canonical tool id. Returns None if unknown."""
    alias = {
        "lint": "lint", "lint-arwaky": "lint", "la": "lint", "lac": "lint",
        "9router": "9router",
        "ponytail": "ponytail", "ponytail-mcp": "ponytail",
        "context7": "context7", "context7-mcp": "context7",
        "codegraph": "codegraph", "codegraph-mcp": "codegraph",
        "anytype": "anytype", "anytype-mcp": "anytype", "anytype-daemon": "anytype",
        "fetch": "fetch", "fetch-mcp": "fetch",
        "vision": "vision", "vision-arwaky": "vision", "va": "vision",
        "qwen-web": "qwen-web", "qwen-web-arwaky": "qwen-web", "qwa": "qwen-web", "qwc": "qwen-web",
        "blender": "blender", "blender-arwaky": "blender", "ba": "blender",
        "skill": "skill", "skills": "skill", "skill-manager": "skill",
        "workspace": "workspace", "workspace-mcp": "workspace", "google-workspace": "workspace",
        "mnemosyne": "mnemosyne", "mnemosyne-memory": "mnemosyne", "mnemosyne-mcp": "mnemosyne",
    }
    if query in alias:
        return alias[query]
    for tid, _, _ in get_registered_tool_ids():
        if query == tid:
            return tid
    return None

# --- skill discovery -----------------------------------------------------------
# extract_skill_name, sanitize_skill_name, safe_skill_name, ensure_under
# are imported from lib/skill_names.py (single source of truth).


def extract_description(skill_md):
    """Extract `description:` from SKILL.md frontmatter."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            d = re.search(r"^description:\s*[\"']?(.+?)[\"']?\s*$", m.group(1), re.MULTILINE)
            if d:
                return d.group(1).strip()
    except OSError:
        pass
    return "No description available"


def _find_skills(base: Path):
    if not base.exists():
        return []
    out = []
    for p in sorted(base.rglob("SKILL.md")):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git"} for part in p.parts):
            continue
        out.append(p)
    return out


@lru_cache(maxsize=1)
def _get_all_skills():
    """Shared skill discovery — cached once per process (no per-tool eviction)."""
    base = REPO_ROOT / "skills"
    if not base.is_dir():
        return ()
    return tuple(sorted(
        f for f in base.rglob("SKILL.md")
        if not any(part in {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"} for part in f.parts)
    ))


def get_tool_skills(tool_id):
    """Return sorted list of SKILL.md paths for a tool.

    User-managed skill pack: ALL skills live in tools/skills/ and are shared
    across every tool. internal/ and vendor/ submodules are no longer read.
    """
    return _get_all_skills()


def resolve_single_skill_file(query):
    """Find a SKILL.md by exact tool/skill name or alias (shared pack only)."""
    base = REPO_ROOT / "skills"
    if not base.is_dir():
        return None
    for p in sorted(base.rglob("SKILL.md")):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"} for part in p.parts):
            continue
        if query in p.parent.name or query in p.parent.parent.name:
            return p
    return None


def copy_single_skill(source_file, target_dir, custom_dest="", force=False):
    """Copy one SKILL.md into target workspace (with path containment)."""
    if not source_file.is_file():
        print(f"  \u2717 Error: Source file not found: {source_file}", file=sys.stderr)
        return False
    name = safe_skill_name(source_file)
    if custom_dest:
        if custom_dest.endswith(".md"):
            dest = Path(custom_dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest = ensure_under(REPO_ROOT, dest)
            except ValueError as exc:
                print(f"  \u2717 {exc}", file=sys.stderr)
                return False
        else:
            # user-supplied --dest dir is intentionally arbitrary; no containment
            dest = Path(custom_dest) / name / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and not force:
            print(f"  \u21b7 [SKIP] Already exists: {dest} (use --force to overwrite)")
            return False
        shutil.copy2(source_file, dest)
        print(f"  \u2713 [OK] Provisioned: {dest}")
        return True
    skills_base = target_dir / ".agents" / "skills"
    try:
        dest_dir = ensure_under(skills_base, skills_base / name)
    except ValueError as exc:
        print(f"  \u2717 {exc}", file=sys.stderr)
        return False
    dest = dest_dir / "SKILL.md"
    dest_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        print(f"  \u21b7 [SKIP] Already exists: {dest}")
        return False
    shutil.copy2(source_file, dest)
    print(f"  \u2713 [OK] Provisioned: {dest}")
    return True

# --- uninstall (unskill) --------------------------------------------------------
def remove_single_skill(source_file, target_dir, custom_dest=""):
    """Remove one provisioned skill (with path containment)."""
    if not source_file.is_file():
        return False
    name = safe_skill_name(source_file)
    if custom_dest:
        if custom_dest.endswith(".md"):
            p = Path(custom_dest)
            if p.exists():
                p.unlink(missing_ok=True)
                print(f"  \u2713 [OK] Removed: {p}")
            else:
                print(f"  \u21b7 [SKIP] Not found: {p}")
            return True
        d = Path(custom_dest) / name
        if d.is_dir():
            shutil.rmtree(d)
            print(f"  \u2713 [OK] Removed: {d}")
        else:
            print(f"  \u21b7 [SKIP] Not found: {d}")
        return True
    skills_base = target_dir / ".agents" / "skills"
    try:
        d = ensure_under(skills_base, skills_base / name)
    except ValueError as exc:
        print(f"  \u2717 {exc}", file=sys.stderr)
        return False
    if d.is_dir():
        shutil.rmtree(d)
        print(f"  \u2713 [OK] Removed: {d}")
    else:
        print(f"  \u21b7 [SKIP] Not found: {d}")
    return True


def uninstall_tool_skills(tool_id, target_dir, custom_dest=""):
    skills = get_tool_skills(tool_id)
    total = len(skills)
    if total == 0:
        print(f"  \u26a0 No skills registered for tool '{tool_id}'.", file=sys.stderr)
        return 0
    print(f"Removing {total} skill(s) for tool '{tool_id}'...")
    print(f"Target Workspace: {target_dir}")
    print("------------------------------------------------------------------")
    removed = 0
    for sf in skills:
        if remove_single_skill(sf, target_dir, custom_dest):
            removed += 1
    print("------------------------------------------------------------------")
    print(f"\u2713 Successfully removed {removed} skill(s) for tool '{tool_id}'.")
    return removed


def cmd_uninstall(argv):
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
def cmd_install(argv):
    target_name = ""
    target_dir = Path.cwd()
    custom_dest = ""
    force = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--target", "-t"):
            target_dir = Path(argv[i + 1]); i += 2; continue
        if a in ("--dest", "-d"):
            custom_dest = argv[i + 1]; i += 2; continue
        if a in ("--force", "-f"):
            force = True; i += 1; continue
        if not target_name:
            target_name = a
        i += 1
    if not target_name:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill install <tool-name|skill-name|all> [--target <dir>] [--force]")
        return 1

    if target_name == "all":
        print(f"Provisioning ALL skills for ALL tools into target workspace: {target_dir}")
        print("------------------------------------------------------------------")
        total = 0
        for tid, _, _ in get_registered_tool_ids():
            for sf in get_tool_skills(tid):
                if copy_single_skill(sf, target_dir, custom_dest, force):
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
            if copy_single_skill(sf, target_dir, custom_dest, force):
                ok += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 Successfully provisioned {ok} skill(s) for tool '{tid}'.")
        return 0

    sf = resolve_single_skill_file(target_name)
    if sf:
        print(f"Provisioning individual skill '{target_name}'...")
        copy_single_skill(sf, target_dir, custom_dest, force)
        return 0

    print(f"Error: Neither tool nor skill named '{target_name}' could be found.")
    print("Run 'aa skill list' to see all available tools and skills.")
    return 1


def _term_width():
    try:
        import shutil
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


# --- list ----------------------------------------------------------------------
def cmd_list(argv):
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
def cmd_check():
    term_w = _term_width()
    n_cols = 5
    available = max(40, term_w - 2 - (n_cols - 1))
    w_id, w_cat, w_status, w_count, w_path = _table_widths(available, [2, 1, 1, 1, 5])
    print("Auditing SKILL.md Readiness across Registered Tools:")
    print("-" * available)
    print(f"{_pad('TOOL ID', w_id)} {_pad('CATEGORY', w_cat)} {_pad('STATUS', w_status)} {_pad('SKILLS COUNT', w_count)} {_pad('SAMPLE PATH', w_path)}")
    print("-" * available)
    total_tools = ready = missing = total_skills = 0
    for tid, cat, _ in get_registered_tool_ids():
        total_tools += 1
        skills = get_tool_skills(tid)
        total_skills += len(skills)
        if skills:
            ready += 1
            sample = str(skills[0]).replace(str(REPO_ROOT) + "/", "")
            print(f"{_pad(tid, w_id)} {_pad(cat, w_cat)} {_pad('FOUND', w_status)} {_pad(str(len(skills)), w_count)} {_pad(sample, w_path)}")
        else:
            missing += 1
            print(f"{_pad(tid, w_id)} {_pad(cat, w_cat)} {_pad('MISSING', w_status)} {_pad('0 skills', w_count)} {_pad('None', w_path)}")
    print("-" * available)
    print(f"Total Tools: {total_tools} | Ready: {ready} | Missing: {missing} | Total Skills: {total_skills}")
    return 0


# --- show ----------------------------------------------------------------------
def cmd_show(argv):
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
    print("agents-arwaky Skill Manager (aa skill)")
    print("Discover, inspect and provision AI agent skills.")
    print()
    print("COMMANDS:")
    print("  list, ls [tool]             List all tools and their associated skills")
    print("  install, get, copy <name>   Install ALL skills for a tool (or a specific skill)")
    print("  install all, sync           Provision ALL skills for ALL tools")
    print("  uninstall, unskill, remove  Remove provisioned skills from CURRENT WORKING DIRECTORY (.agents/skills/)")
    print("  show <name>                 Display the content of a skill's SKILL.md")
    print("  check                       Audit SKILL.md coverage across all registered tools")
    print("  help                        Show this help screen")
    print()
    print("SUBCOMMAND HELP:")
    print("  aa skill list --help        Show list-specific options")
    print("  aa skill install --help     Show install-specific options")
    print("  aa skill uninstall --help   Show uninstall-specific options")
    print("  aa skill show --help        Show show-specific options")
    return 0


def cmd_list_help():
    print("Usage: aa skill list [tool]")
    print()
    print("List all registered tools and their associated skills, or filter by tool.")
    print()
    print("Options:")
    print("  tool              Optional tool ID to filter (e.g., 'lint', 'vision')")
    print("  --all             Show all tools (default behavior)")
    return 0


def cmd_install_help():
    print("Usage: aa skill install <tool|skill|all> [--target DIR] [--dest PATH] [--force]")
    print()
    print("Install all skills for a tool, a specific skill, or all skills for all tools.")
    print()
    print("Options:")
    print("  <tool|skill|all>  Target tool ID, skill name, or 'all' for everything")
    print("  --target, -t DIR  Target workspace directory (default: current directory)")
    print("  --dest, -d PATH   Custom destination path")
    print("  --force, -f       Overwrite existing skills")
    return 0


def cmd_uninstall_help():
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
    print("Usage: aa skill show <tool|skill>")
    print()
    print("Display the content of a skill's SKILL.md file.")
    print()
    print("Arguments:")
    print("  <tool|skill>      Tool ID or skill name to display")
    return 0


def main(argv):
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
        return cmd_check()
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
