"""Skills CLI surface — command handlers for `aa skills list` and `aa skills show`.

Read-only discovery and inspection of the agents-arwaky skill pack.
The aggregate is injected by the caller (the root CLI), never imported here,
so no root→surface coupling exists (AES205).
"""
from __future__ import annotations

from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery, SkillsRequest
from modules.shared.src.utility_logging_setup import (
    BOLD,
    CYAN,
    RESET,
    banner,
    err,
    info,
)


def cmd_skills(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Route ``aa skills <sub>`` to list/show handlers."""
    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        return 0

    sub = args[0]
    rest = args[1:]

    if sub in ("list", "ls"):
        return _cmd_list(rest, aggregate)
    if sub == "show":
        return _cmd_show(rest, aggregate)
    err(f"Unknown skills subcommand: {sub}")
    _print_usage()
    return 1


def _print_usage() -> None:
    banner()
    info(f"{BOLD()}aa skills list{RESET()}                  List all skills in the pack")
    info(f"{BOLD()}aa skills show <name>{RESET()}           Print a skill's SKILL.md")


def _has_help(args: list[str]) -> bool:
    return any(a in ("-h", "--help") for a in args)


def _cmd_list(args: list[str], aggregate: ISkillsAggregate) -> int:
    """List every skill in the pack as a compact table."""
    if _has_help(args):
        info("Usage: aa skills list — list all skills in the pack")
        return 0
    result = aggregate.execute(SkillsRequest(op="list"))
    rows = list(result.records)
    if not result.ok or not rows:
        err("No skills found — is the agents-arwaky pack present?")
        return 1
    print(f"{CYAN()}SKILL{RESET()}".ljust(28) + "DESCRIPTION")
    print("-" * 28 + " " + "-" * 60)
    for record in rows:
        desc = (record.description or "").replace("\n", " ")[:70]
        print(record.name.ljust(28) + " " + desc)
    print(f"\n{BOLD()}{len(rows)}{RESET()} skills in the pack.")
    return 0


def _cmd_show(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Print the raw SKILL.md for one skill."""
    if _has_help(args) or not args:
        info("Usage: aa skills show <name>")
        return 0
    name = args[0]
    result = aggregate.execute(SkillsRequest(op="show", query=SkillQuery(name)))
    if not result.ok or result.content is None:
        err(f"Skill not found: {name}")
        return 1
    print(result.content)
    return 0
