"""Skill surface — CLI adapter for aa skill (list|check|install|uninstall|show|sync).

Dispatch logic and per-subcommand --help are the original ``main()`` from
tools/skill/skill.py, verbatim.
"""
from __future__ import annotations

from modules.skill.contract.contract_skill_aggregate import ISkillAggregate

from modules.skill.src import capabilities_skill_registry as _reg


def cmd_skill(args: list[str], orch: ISkillAggregate) -> int:
    """aa skill <list|check|install|uninstall|show|sync|help> [args]."""
    if not args or args[0] in ("-h", "--help", "help"):
        _reg.cmd_help()
        return 0
    action = args[0]
    rest = args[1:]
    # Per-subcommand --help support
    if rest and rest[0] in ("-h", "--help", "help"):
        if action in ("list", "ls"):
            _reg.cmd_list_help()
            return 0
        if action in ("install", "copy", "get", "add", "sync"):
            _reg.cmd_install_help()
            return 0
        if action in ("uninstall", "remove", "unskill", "delete"):
            _reg.cmd_uninstall_help()
            return 0
        if action in ("show", "cat", "view"):
            _reg.cmd_show_help()
            return 0
    if action in ("list", "ls"):
        return orch.list_skills(rest[0] if rest else "")
    if action in ("check", "audit"):
        return orch.check_skills()
    if action in ("install", "copy", "get", "add"):
        return orch.install_skills(rest)
    if action in ("uninstall", "remove", "unskill", "delete"):
        return orch.uninstall_skills(rest)
    if action == "sync":
        return orch.sync_skills(rest)
    if action in ("show", "cat", "view"):
        return orch.show_skill(rest[0] if rest else "")
    print(f"Unknown skill command: {action}")
    _reg.cmd_help()
    return 0
