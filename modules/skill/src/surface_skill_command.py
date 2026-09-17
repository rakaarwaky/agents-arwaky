"""Skill surface — CLI adapter for aa skill (list|check|install|uninstall|show|sync)."""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.logging.utility_logging import BOLD, CYAN, GREEN, RESET, banner, err, info, ok, warn
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.skill_names.utility_skill_names import extract_skill_name
from modules.shared.src.skill_pack.capabilities_skill_pack import (
    DESCRIPTION_BUDGET_BYTES,
    get_all_skill_files,
    iter_skill_files,
)

HELP = """agents-arwaky Skill Manager (aa skill)
Discover, inspect and provision AI agent skills.

COMMANDS:
  list, ls [tool]             List all tools and their associated skills
  install, get, copy <name>   Install ALL skills for a tool (or a specific skill)
  install all, sync           Provision ALL skills for ALL tools
  install --prune             Drop provisioned skills the pack no longer provides
  uninstall, unskill, remove  Remove provisioned skills from CURRENT WORKING DIRECTORY (.agents/skills/)
  show <name>                 Display the content of a skill's SKILL.md
  check                       Audit per-tool skill coverage and pack loadability
  help                        Show this help screen"""

_INSTALL_HELP = """Usage: aa skill install <tool|skill|all> [--target DIR] [--dest PATH] [--force] [--prune]

Options:
  <tool|skill|all>    Target tool ID, skill name, or 'all' for everything
  --target, -t DIR    Target workspace directory (default: current directory)
  --dest, -d PATH     Custom destination path
  --force, -f         Overwrite existing skills
  --link, --symlink   Symlink the skill dir to the pack (local only; do not commit)
  --copy              Explicitly request copies (the default)
  --prune             Also delete provisioned skills the pack no longer provides."""


def parse_skill_args(args: list[str]) -> dict[str, object]:
    """Shared arg parsing for install/uninstall verbs (ported from skill.py)."""
    parsed: dict[str, object] = {
        "target_name": "",
        "target": Path.cwd(),
        "dest": "",
        "force": False,
        "link": False,
        "prune": False,
    }
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--target", "-t"):
            parsed["target"] = Path(args[i + 1]); i += 2; continue
        if a in ("--dest", "-d"):
            parsed["dest"] = args[i + 1]; i += 2; continue
        if a in ("--force", "-f"):
            parsed["force"] = True; i += 1; continue
        if a == "--prune":
            parsed["prune"] = True; i += 1; continue
        if a in ("--copy", "--copy-skills"):
            parsed["link"] = False; i += 1; continue
        if a in ("--link", "--symlink"):
            parsed["link"] = True; i += 1; continue
        if not parsed["target_name"]:
            parsed["target_name"] = a
        i += 1
    return parsed


def _term_width() -> int:
    import shutil
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


def cmd_skill(args: list[str], orch: ISkillAggregate) -> int:
    """aa skill <list|check|install|uninstall|show|sync|help> [args]."""
    if not args or args[0] in ("-h", "--help", "help"):
        print(HELP)
        return 0
    action = args[0]
    rest = args[1:]
    if rest and rest[0] in ("-h", "--help", "help"):
        if action in ("list", "ls"):
            print("Usage: aa skill list [tool]")
            return 0
        if action in ("install", "copy", "get", "add", "sync"):
            print(_INSTALL_HELP)
            return 0
        if action in ("uninstall", "remove", "unskill", "delete"):
            print("Usage: aa skill uninstall <tool|skill|all> [--target DIR] [--dest PATH]")
            return 0
        if action in ("show", "cat", "view"):
            print("Usage: aa skill show <tool|skill>")
            return 0
    if action in ("list", "ls"):
        return _cmd_list(rest, orch)
    if action in ("check", "audit"):
        return orch.check_skills()
    if action in ("install", "copy", "get", "add"):
        return orch.install_skills(rest)
    if action in ("uninstall", "remove", "unskill", "delete"):
        return orch.uninstall_skills(rest)
    if action == "sync":
        return orch.sync_skills(rest)
    if action in ("show", "cat", "view"):
        return _cmd_show(rest, orch)
    print(f"Unknown skill command: {action}")
    return cmd_skill([], orch)


def _cmd_list(args: list[str], orch: ISkillAggregate) -> int:
    """Port of skill.py cmd_list: tools table + per-tool skill listing."""
    tool_filter = args[0] if args else ""
    pack = get_all_skill_files()
    total_unique = len(pack)
    from modules.shared.src.logging.utility_logging import pad, table_widths
    term_w = _term_width()
    n_cols = 2 if (tool_filter and tool_filter != "--all") else 4
    available = max(40, term_w - 2 - (n_cols - 1))
    if tool_filter and tool_filter != "--all":
        from modules.skill.src.capabilities_skill_registry import SkillRegistry
        tid = SkillRegistry().normalize_tool_id(tool_filter)
        if not tid:
            err(f"Tool '{tool_filter}' not found in manifest.")
            return 1
        w_name, w_desc = table_widths(available, [3, 7])
        print(f"Skills available for tool '{tid}' (shared skill pack):")
        print("-" * available)
        print(f"{pad('SKILL NAME', w_name)} {pad('DESCRIPTION', w_desc)}")
        print("-" * available)
        for skill_md in pack:
            print(f"{pad(extract_skill_name(skill_md), w_name)} {pad(_description_of(skill_md), w_desc)}")
        print("-" * available)
        print(f"Total skill pack: {total_unique} | Install: 'aa skill install {tid}'")
        return 0
    w_id, w_cat, w_count, w_desc = table_widths(available, [2, 1, 1, 6])
    print("Available Tools & Shared Skill Pack in agents-arwaky:")
    print("-" * available)
    print(f"{pad('TOOL ID', w_id)} {pad('CATEGORY', w_cat)} {pad('SKILLS COUNT', w_count)} {pad('DESCRIPTION', w_desc)}")
    print("-" * available)
    from modules.skill.src.capabilities_skill_registry import SkillRegistry
    for info in SkillRegistry().get_registered_tool_ids():
        print(f"{pad(info.tool_id, w_id)} {pad(info.category, w_cat)} {pad(str(total_unique), w_count)} {pad(info.description, w_desc)}")
    print("-" * available)
    print(f"Total Tools: {len(SkillRegistry().get_registered_tool_ids())} | Total Skill Pack (unique): {total_unique}")
    return 0


def _description_of(skill_md: Path) -> str:
    import re
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


def _cmd_show(args: list[str], orch: ISkillAggregate) -> int:
    """Port of skill.py cmd_show: display the SKILL.md content."""
    query = args[0] if args else ""
    if not query:
        err("Missing tool or skill name.")
        print("Usage: aa skill show <tool-name|skill-name>")
        return 1
    from modules.skill.src.capabilities_skill_registry import SkillRegistry
    base = repo_root() / "skills"
    if SkillRegistry().normalize_tool_id(query):
        skills = [p for p in get_all_skill_files() if query in p.parent.name or query in p.parent.parent.name]
        if not skills:
            print(f"Tool '{query}' has no dedicated skills in the shared pack.")
            return 0
        print(f"Source: {skills[0]}")
        print("-" * 66)
        print(skills[0].read_text(encoding="utf-8", errors="replace"))
        if len(skills) > 1:
            print(f"\nOther matching skills: {', '.join(extract_skill_name(s) for s in skills[1:])}")
        return 0
    for p in get_all_skill_files():
        if query in p.parent.name or query in p.parent.parent.name:
            print(f"Source: {p}")
            print("-" * 66)
            print(p.read_text(encoding="utf-8", errors="replace"))
            return 0
    print(f"Error: Skill or tool '{query}' not found.", file=sys.stderr)
    return 1
