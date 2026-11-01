"""Skills CLI surface — command handlers for every ``aa skills`` verb.

Read-only discovery (``list``/``show``) plus the authoring commands
(``validate``, ``catalog``, ``discover``, ``weed``, ``repair``, ``move``,
``archive``, ``new-category``, ``merge-plan``).

The aggregate is injected by the caller (the root CLI), never imported
here, so no root→surface coupling exists (AES205). Argv becomes a
``SkillsRequest``; the rendered text/JSON comes back on ``SkillsResult``.
Exit codes are the legacy contract: 0 clean / 1 issues / 2 usage /
3 catalog drift.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from modules.shared.src.common.utility_logging_setup import (
    BOLD,
    CYAN,
    RESET,
    banner,
    err,
    info,
)
from modules.shared.src.common.utility_paths_resolver import resolve_skills_root
from modules.shared.src.common.utility_skills_markdown import md_escape, yaml_quote
from modules.shared.src.common.utility_skills_tree import relpath
from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.taxonomy_skills_entity import Issue
from modules.shared.src.skills.taxonomy_skills_error import SkillsUsageError
from modules.shared.src.skills.taxonomy_skills_rule_vo import (
    RULE_ONLY_ISSUE_TYPES,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsResult,
    SkillsRoot,
    TraceStateStatus,
)

_EXIT_USAGE = 2
_EXIT_DRIFT = 3
_EXIT_WAIT_READY = 0
_EXIT_WAIT_PHASE_STALL = 4
_EXIT_WAIT_REPORT_STALL = 3
_EXIT_WAIT_DEADLINE = 2

#: The results table header/separator and empty-result line, verbatim from
#: the legacy command (presentation strings, owned by the surface).
_SCORE_TABLE_HEADER = "| Skill | Category | Description | Path | Score |"
_SCORE_TABLE_SEPARATOR = "|---|---|---|---|---|"
_NO_MATCH_LINE = "No matching skills found in CATALOG.md."

#: The dry-run footer every mutating preview prints.
_DRY_RUN_NOTE = "no changes made (dry-run default; pass --apply to execute)"


def cmd_skills(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Route ``aa skills <sub>`` to the aggregate; render; return the exit code."""
    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        return 0

    sub = args[0]
    rest = args[1:]

    if sub in ("list", "ls"):
        return _cmd_list(rest, aggregate)
    if sub == "show":
        return _cmd_show(rest, aggregate)
    if sub in (
        "validate",
        "catalog",
        "discover",
        "weed",
        "repair",
        "move",
        "archive",
        "new-category",
        "merge-plan",
    ):
        return _cmd_authoring(sub, rest, aggregate)
    if sub in ("trace-collect", "trace-usage", "trace-phrases", "trace-state"):
        return _cmd_trace(sub, rest, aggregate)

    err(f"Unknown skills subcommand: {sub}")
    _print_usage()
    return _EXIT_USAGE


def _print_usage() -> None:
    banner()
    info(
        f"{BOLD()}aa skills list{RESET()}                  List all skills in the pack"
    )
    info(f"{BOLD()}aa skills show <name>{RESET()}           Print a skill's SKILL.md")
    info(f"{BOLD()}aa skills validate{RESET()}              Report validation issues")
    info(
        f"{BOLD()}aa skills catalog [--check]{RESET()}     Rebuild CATALOG.md (or test it)"
    )
    info(f"{BOLD()}aa skills discover <query>{RESET()}      Search the catalog")
    info(
        f"{BOLD()}aa skills weed{RESET()}                  Report duplicates and empty categories"
    )
    info(
        f"{BOLD()}aa skills repair [--apply]{RESET()}      Apply safe mechanical repairs"
    )
    info(
        f"{BOLD()}aa skills move <skill> <cat>{RESET()}    Move a skill to another category"
    )
    info(
        f"{BOLD()}aa skills archive <skill>{RESET()}       Archive a skill into _archive/"
    )
    info(f"{BOLD()}aa skills new-category <name>{RESET()}    Create a category")
    info(
        f"{BOLD()}aa skills merge-plan <a> <b>{RESET()}    Emit the read-only merge plan"
    )
    info(f"{BOLD()}aa skills trace-collect[...]{RESET()}    Scan sessions → build usage (run dir + kept/seen counts)")
    info(f"{BOLD()}aa skills trace-usage[...]{RESET()}      Read last run's usage (skills-only table, unused_loaded)")
    info(f"{BOLD()}aa skills trace-phrases[...]{RESET()}    Mine repeated prompts + instruction lines")
    info(f"{BOLD()}aa skills trace-state <action>[...]{RESET()}  Trace lifecycle: get|set|clear|trash|restrict|decide|wait")


# ─── Read-only surface (historical behavior preserved) ────────────────
def _has_help(args: list[str]) -> bool:
    return any(a in ("-h", "--help") for a in args)


def _split_root(args: list[str]) -> tuple[SkillsRoot | None, list[str]]:
    """Extract ``--skills-root PATH`` from *args*, leaving the rest intact."""
    root: SkillsRoot | None = None
    rest: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--skills-root" and index + 1 < len(args):  # nosec B105
            root = SkillsRoot(resolve_skills_root(args[index + 1]))
            index += 2
            continue
        if token.startswith("--skills-root="):
            root = SkillsRoot(resolve_skills_root(token.split("=", 1)[1]))
            index += 1
            continue
        rest.append(token)
        index += 1
    return root, rest


def _cmd_list(args: list[str], aggregate: ISkillsAggregate) -> int:
    """List every skill in the pack as a compact table."""
    root, rest = _split_root(args)
    if _has_help(rest):
        info("Usage: aa skills list — list all skills in the pack")
        return 0
    result = aggregate.execute(SkillsRequest(op=SkillsOp.LIST, root=root))
    rows = list(result.records)
    if not result.ok or not rows:
        if result.exit_code == _EXIT_USAGE and result.message:
            print(f"ERROR: {result.message}", file=sys.stderr)
            return _EXIT_USAGE
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
    root, rest = _split_root(args)
    if _has_help(rest) or not rest:
        info("Usage: aa skills show <name>")
        return 0
    name = rest[0]
    result = aggregate.execute(
        SkillsRequest(op=SkillsOp.SHOW, query=SkillQuery(name), root=root)
    )
    if not result.ok or result.content is None:
        err("Skill not found")
        return 1
    print(result.content)
    return 0


# ─── Authoring parser ────────────────────────────────────────────────
def _authoring_parser() -> argparse.ArgumentParser:
    """Construct the authoring CLI; exported so tests can drive it directly."""
    parser = argparse.ArgumentParser(
        prog="aa skills",
        description="Skill-pack tooling: validate, catalog, discover, and mutations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--skills-root",
            metavar="PATH",
            default=None,
            help="Skills root (default: the repository's skills/ pack)",
        )
        sub.add_argument("--json", action="store_true", help="Emit the report as JSON")

    sub = subparsers.add_parser("validate", help="Report validation issues")
    add_common(sub)
    sub.add_argument(
        "--category",
        metavar="NAME",
        default=None,
        help="Only report issues in category NAME",
    )
    sub.add_argument(
        "--rules-only",
        action="store_true",
        help="Only report the rule checks (skip library-wide duplicates)",
    )
    sub.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Print the 'N issues / M skills / K categories' observability line "
            "instead of the per-issue listing; --json wins when both are passed"
        ),
    )

    sub = subparsers.add_parser(
        "catalog", help="Rebuild CATALOG.md (or check for drift)"
    )
    add_common(sub)
    sub.add_argument(
        "--check",
        action="store_true",
        help="Regenerate to a temp file and diff (drift gate; exit 3 on drift)",
    )

    sub = subparsers.add_parser("discover", help="Search CATALOG.md")
    add_common(sub)
    sub.add_argument("query", help="Search query")
    sub.add_argument("--limit", type=int, default=20, help="Maximum results")

    sub = subparsers.add_parser("weed", help="Report duplicates and empty categories")
    add_common(sub)

    sub = subparsers.add_parser(
        "repair", help="Apply safe mechanical repairs (dry-run by default)"
    )
    add_common(sub)
    sub.add_argument(
        "--apply",
        action="store_true",
        help="Execute the repairs (default is a preview)",
    )

    sub = subparsers.add_parser("move", help="Move a skill to a target category")
    add_common(sub)
    sub.add_argument("skill", help="Skill reference, e.g. category/skill-name")
    sub.add_argument("target_category", help="Target category folder")
    sub.add_argument(
        "--apply", action="store_true", help="Execute the move (default is a preview)"
    )

    sub = subparsers.add_parser("archive", help="Archive a skill (dry-run by default)")
    add_common(sub)
    sub.add_argument("skill", help="Skill reference, e.g. category/skill-name")
    sub.add_argument(
        "--apply",
        action="store_true",
        help="Execute the archive (default is a preview)",
    )

    sub = subparsers.add_parser(
        "new-category", help="Create category and DESCRIPTION.md"
    )
    add_common(sub)
    sub.add_argument("name", help="Category folder name")
    sub.add_argument(
        "description", nargs="?", default=None, help="Category description"
    )
    sub.add_argument("--force", action="store_true", help="Overwrite DESCRIPTION.md")
    sub.add_argument(
        "--apply",
        action="store_true",
        help="Execute the creation (default is a preview)",
    )

    sub = subparsers.add_parser(
        "merge-plan",
        help="Emit the merge plan for two skills (read-only; skill-lifecycle executes it)",
    )
    add_common(sub)
    sub.add_argument("skill_a", help="First skill reference, category/skill")
    sub.add_argument("skill_b", help="Second skill reference, category/skill")

    return parser


def _cmd_authoring(sub: str, rest: list[str], aggregate: ISkillsAggregate) -> int:
    """Parse an authoring subcommand and render its result."""
    try:
        namespace = _authoring_parser().parse_args([sub, *rest])
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    request = _build_request(namespace)
    result = aggregate.execute(request)

    if not result.ok and result.exit_code == _EXIT_USAGE:
        # The legacy ``fail()`` channel prints the ERROR line verbatim on
        # stderr (no banner prefix); callers and older tests parse it.
        print(f"ERROR: {result.message}", file=sys.stderr)
        return result.exit_code

    if sub == "validate":
        return _render_validate(result, request)
    if sub == "catalog":
        return _render_catalog(result, request)
    if sub == "discover":
        return _render_discover(result, request)
    if sub == "weed":
        return _render_weed(result, request)
    if sub == "repair":
        return _render_repair(result, request)
    if sub == "move":
        return _render_move(result, request)
    if sub == "archive":
        return _render_archive(result, request)
    if sub == "new-category":
        return _render_new_category(result, request)
    if sub == "merge-plan":
        return _render_merge_plan(result, request)
    raise SkillsUsageError(f"Unknown skills subcommand: {sub}")


def _build_request(namespace: argparse.Namespace) -> SkillsRequest:
    """Map parsed argv onto the request the domain understands."""
    command = namespace.command
    root_value: SkillsRoot | None = (
        SkillsRoot(resolve_skills_root(namespace.skills_root))
        if namespace.skills_root
        else None
    )
    json_value = bool(getattr(namespace, "json", False))

    if command == "validate":
        return SkillsRequest(
            op=SkillsOp.VALIDATE,
            flags={
                "category": namespace.category or "",
                "rules_only": "1" if namespace.rules_only else "0",
                "summary": "1" if namespace.summary else "0",
            },
            root=root_value,
            json=json_value,
        )
    if command == "catalog":
        return SkillsRequest(
            op=SkillsOp.CATALOG,
            flags={"check": "1" if namespace.check else "0"},
            root=root_value,
            json=json_value,
        )
    if command == "discover":
        return SkillsRequest(
            op=SkillsOp.DISCOVER,
            query=SkillQuery(namespace.query),
            flags={"limit": str(namespace.limit)},
            root=root_value,
            json=json_value,
        )
    if command == "weed":
        return SkillsRequest(op=SkillsOp.WEED, root=root_value, json=json_value)
    if command == "repair":
        return SkillsRequest(
            op=SkillsOp.REPAIR,
            apply=namespace.apply,
            root=root_value,
            json=json_value,
        )
    if command == "move":
        return SkillsRequest(
            op=SkillsOp.MOVE,
            query=SkillQuery(namespace.skill),
            apply=namespace.apply,
            flags={"target": namespace.target_category},
            root=root_value,
            json=json_value,
        )
    if command == "archive":
        return SkillsRequest(
            op=SkillsOp.ARCHIVE,
            query=SkillQuery(namespace.skill),
            apply=namespace.apply,
            root=root_value,
            json=json_value,
        )
    if command == "new-category":
        return SkillsRequest(
            op=SkillsOp.NEW_CATEGORY,
            query=SkillQuery(namespace.name),
            description=namespace.description or "",
            apply=namespace.apply,
            flags={"force": "1" if namespace.force else "0"},
            root=root_value,
            json=json_value,
        )
    if command == "merge-plan":
        return SkillsRequest(
            op=SkillsOp.MERGE_PLAN,
            query=SkillQuery(namespace.skill_a),
            flags={"target": namespace.skill_b},
            root=root_value,
            json=json_value,
        )
    raise SkillsUsageError(f"Unknown skills subcommand: {command}")


# ─── Renderers ───────────────────────────────────────────────────────
def _emit_json(payload: dict[str, object]) -> None:
    """Print a JSON payload with a stable key order and a trailing newline."""
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _root_of(result: SkillsResult) -> Path:
    """The resolved skills root a result was produced from."""
    return result.root or Path()


def _issue_payload(issue: Issue) -> dict[str, object]:
    """The legacy issue projection (key order: type, message, path, category)."""
    payload: dict[str, object] = {"type": issue.type, "message": issue.message}
    if issue.path:
        payload["path"] = issue.path
    if issue.category:
        payload["category"] = issue.category
    return payload


def _render_validate(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a validation report, narrowed by --category/--rules-only."""
    report = result.report
    if report is None:
        err("Internal error: no validation report produced")
        return 1
    total = report.issue_count
    issues = list(report.issues)

    if request.flags.get("category"):
        category = request.flags["category"]
        issues = [
            issue
            for issue in issues
            if issue.category == category
            or (issue.path or "").startswith(f"{category}/")
        ]
    if request.flags.get("rules_only") == "1":
        issues = [issue for issue in issues if issue.type in RULE_ONLY_ISSUE_TYPES]

    root = _root_of(result)

    if request.json:
        _emit_json(
            {
                "skills_root": str(root),
                "category": request.flags.get("category") or None,
                "rules_only": request.flags.get("rules_only") == "1",
                "issue_count": len(issues),
                "total_issue_count": total,
                "issues": [_issue_payload(issue) for issue in issues],
            }
        )
        return 1 if total else 0

    if request.flags.get("summary") == "1":
        print(report.summary())
        return 1 if total else 0

    if total == 0:
        print("No validation issues found.")
        return 0

    scope_note = _filter_note(
        request.flags.get("category"), request.flags.get("rules_only")
    )
    if scope_note:
        print(
            f"{total} validation issue(s) found ({len(issues)} in scope {scope_note}):"
        )
    else:
        print(f"{total} validation issue(s) found:")

    for issue in issues:
        print(f"- [{issue.type}] {issue.locator}: {issue.message}")

    if not issues:
        print("(none in scope)")
    return 1


def _filter_note(category: str | None, rules_only: str | None) -> str:
    """The parenthetical that names the active filter(s)."""
    bits = []
    if category:
        bits.append(f"category={category}")
    if rules_only == "1":
        bits.append("rules-only")
    return "; ".join(bits)


def _render_catalog(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the rebuild result or the drift gate."""
    root = _root_of(result)
    catalog = root / "CATALOG.md"

    if request.flags.get("check") == "1":
        check = result.check
        if check is None:
            err("Internal error: no catalog check result produced")
            return 1
        if request.json:
            _emit_json(
                {
                    "skills_root": str(root),
                    "in_sync": check.in_sync,
                    "catalog": str(catalog),
                    "diff": list(check.diff_lines),
                }
            )
        else:
            print(check.message)
            for line in check.diff_lines:
                print(line)
        return 0 if check.in_sync else _EXIT_DRIFT

    report = result.catalog
    if report is None:
        err("Internal error: no catalog report produced")
        return 1
    if request.json:
        _emit_json(
            {
                "skills_root": str(root),
                "catalog": str(report.path),
                "rebuilt": True,
                "categories": report.categories,
                "skills": report.skills,
            }
        )
    else:
        print(f"Rebuilt {report.path}")
        print(f"Categories: {report.categories}; skills: {report.skills}")
    return 0


def _render_discover(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the scored matches (or the legacy no-match line)."""
    root = _root_of(result)
    if result.warning:
        print(result.warning, file=sys.stderr)
        if result.message:
            print(f"  reason: {result.message}", file=sys.stderr)

    if request.json:
        payload: dict[str, object] = {
            "skills_root": str(root),
            "query": request.query,
            "limit": request.flags.get("limit"),
            "match_count": len(result.matches),
            "matches": [match.as_dict() for match in result.matches],
        }
        if result.warning is not None:
            payload["warning"] = result.warning
        _emit_json(payload)
        return 0

    if not result.matches:
        print(_NO_MATCH_LINE)
        return 0

    print(_SCORE_TABLE_HEADER)
    print(_SCORE_TABLE_SEPARATOR)
    for match in result.matches:
        print(
            f"| {md_escape(match.skill)} "
            f"| {md_escape(match.category)} "
            f"| {md_escape(match.description)} "
            f"| {md_escape(match.path)} "
            f"| {match.score} |"
        )
    return 0


def _weed_issue(line: str) -> dict[str, str]:
    """Parse one weed line into the JSON report shape."""
    body = line.removeprefix("- ")
    kind, _, message = body.partition(": ")
    return {"type": kind, "message": message}


def _render_weed(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the weeding report; any weed line means exit 1."""
    plan = result.plan
    if plan is None:
        err("Internal error: no weed plan produced")
        return 1
    lines = list(plan.lines)
    root = _root_of(result)

    if request.json:
        _emit_json(
            {
                "skills_root": str(root),
                "issue_count": len(lines),
                "issues": [_weed_issue(line) for line in lines],
            }
        )
    else:
        print("Weeding report:")
        if lines:
            for line in lines:
                print(line)
        else:
            print("No obvious weeds found.")
    return 1 if lines else 0


def _render_repair(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a repair preview or the applied report."""
    plan = result.plan
    if plan is None:
        err("Internal error: no repair plan produced")
        return 1
    root = _root_of(result)
    catalog = root / "CATALOG.md"

    if not request.apply:
        if request.json:
            _emit_json(
                {
                    "skills_root": str(root),
                    "dry_run": True,
                    "planned": list(plan.lines),
                    "plan_count": len(plan.lines),
                    "note": _DRY_RUN_NOTE,
                }
            )
        else:
            print("Planned repairs (dry-run — pass --apply to execute):")
            if plan.lines:
                for item in plan.lines:
                    print(f"- {item}")
            else:
                print("- (none)")
            print(f"Would rebuild {catalog}")
        return 0

    applied = list(result.outcome.applied) if result.outcome else []
    if applied:
        print("Repairs applied:")
        for item in applied:
            print(f"- {item}")
    else:
        print("No mechanical repairs needed.")
    print(f"Rebuilt {catalog}")
    return 0


def _render_move(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a move preview, the applied report, or the already-there case."""
    plan = result.plan
    if plan is None:
        err("Internal error: no move plan produced")
        return 1
    root = _root_of(result)
    catalog = root / "CATALOG.md"

    if plan.already_in_category:
        print(f"Skill already in category: {request.flags.get('target')}")
        return 0

    source = relpath(plan.source, root) if plan.source else ""
    destination = relpath(plan.destination, root) if plan.destination else ""

    if not request.apply:
        if request.json:
            _emit_json(
                {
                    "skills_root": str(root),
                    "dry_run": True,
                    "skill": request.query,
                    "from": source,
                    "to": destination,
                    "note": _DRY_RUN_NOTE,
                }
            )
        else:
            print("Planned move (dry-run — pass --apply to execute):")
            print(f"- move {source} -> {destination}")
            print(f"- rebuild {catalog}")
        return 0

    print(f"Moved {source} -> {destination}")
    print(f"Rebuilt {catalog}")
    return 0


def _render_archive(result: SkillsResult, request: SkillsRequest) -> int:
    """Render an archive preview or the applied report."""
    plan = result.plan
    if plan is None:
        err("Internal error: no archive plan produced")
        return 1
    root = _root_of(result)
    catalog = root / "CATALOG.md"
    source = relpath(plan.source, root) if plan.source else ""
    destination = relpath(plan.destination, root) if plan.destination else ""

    if not request.apply:
        if request.json:
            _emit_json(
                {
                    "skills_root": str(root),
                    "dry_run": True,
                    "skill": request.query,
                    "from": source,
                    "to": destination,
                    "note": _DRY_RUN_NOTE,
                }
            )
        else:
            print("Planned archive (dry-run — pass --apply to execute):")
            print(f"- move {source} -> {destination}")
            print(f"- rename {destination}/SKILL.md -> SKILL.md.archived")
            print(f"- rebuild {catalog}")
        return 0

    print(f"Archived {source} -> {destination}")
    print(f"Rebuilt {catalog}")
    return 0


def _render_new_category(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a category-creation preview or the applied report."""
    plan = result.new_category
    if plan is None:
        err("Internal error: no new-category plan produced")
        return 1
    root = _root_of(result)
    catalog = root / "CATALOG.md"

    if not request.apply:
        if request.json:
            _emit_json(
                {
                    "skills_root": str(root),
                    "dry_run": True,
                    "category": plan.name,
                    "description": plan.description,
                    "would_write_description": plan.will_write,
                    "note": _DRY_RUN_NOTE,
                }
            )
        else:
            print("Planned new-category (dry-run — pass --apply to execute):")
            print(f"- create {plan.name}/")
            if plan.will_write:
                print(
                    f"- write {plan.name}/DESCRIPTION.md: "
                    f"{yaml_quote(plan.description)}"
                )
            else:
                print(
                    f"- keep existing {plan.name}/DESCRIPTION.md; "
                    "use --force to overwrite"
                )
            print(f"- rebuild {catalog}")
        return 0

    if plan.created:
        print(f"Wrote {plan.name}/DESCRIPTION.md")
    else:
        print(f"Kept existing {plan.name}/DESCRIPTION.md; use --force to overwrite")
    print(f"Rebuilt {catalog}")
    return 0


def _render_merge_plan(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the merge plan (JSON projections keep the legacy key order)."""
    plan = result.merge
    if plan is None:
        err("Internal error: no merge plan produced")
        return 1
    root = _root_of(result)

    if request.json:
        _emit_json(
            {
                "skills_root": str(root),
                "survivor": plan.survivor,
                "absorbed": plan.absorbed,
                "survival_reason": plan.survival_reason,
                "moves": [
                    {"from": source, "to": destination}
                    for source, destination in plan.moves
                ],
                "rewrites": list(plan.rewrites),
                "category_after": plan.category_after,
                "empty_category_after": plan.empty_category_after,
            }
        )
        return 0

    for line in result.lines:
        print(line)
    return 0


# ─── Trace pipeline surface (trace-collect / trace-usage / trace-phrases / trace-state) ───
def _cmd_trace(
    sub: str, args: list[str], aggregate: ISkillsAggregate
) -> int:
    """Route a trace subcommand to its handler."""
    # strip --skills-root (trace verbs use --grok-home, not the skills pack root)
    _, rest = _split_root(args)
    if sub == "trace-collect":
        return _cmd_trace_collect(rest, aggregate)
    if sub == "trace-usage":
        return _cmd_trace_usage(rest, aggregate)
    if sub == "trace-phrases":
        return _cmd_trace_phrases(rest, aggregate)
    if sub == "trace-state":
        return _cmd_trace_state(rest, aggregate)
    err(f"Unknown trace subcommand: {sub}")
    return _EXIT_USAGE


def _trace_collect_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills trace-collect",
        description="Scan sessions and build the skills-only usage material.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME to scan")
    parser.add_argument(
        "--out",
        metavar="DIR",
        default="",
        help="Run dir for output records (default: a scratch skills-trace-* temp dir)",
    )
    parser.add_argument("--days", type=int, default=0, help="Only sessions updated within N days")
    parser.add_argument("--since-last", action="store_true", help="Since the last completed run")
    parser.add_argument("--min-turns", type=int, default=1, help="Minimum human turns per session")
    parser.add_argument("--limit", type=int, default=0, help="Max sessions to keep")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_trace_collect(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_collect_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    run_dir = ns.out or tempfile.mkdtemp(prefix="skills-trace-")
    request = SkillsRequest(
        op=SkillsOp.TRACE_COLLECT,
        flags={
            "grok_home": ns.grok_home,
            "run_dir": run_dir,
            "days": str(ns.days),
            "since_last": "1" if ns.since_last else "0",
            "min_turns": str(ns.min_turns),
            "limit": str(ns.limit),
        },
        json=ns.json,
    )
    result = aggregate.execute(request)

    if ns.json:
        _emit_json(
            {
                "run_dir": run_dir,
                "kept": len(result.usage.items) if result.usage else 0,
                "seen": result.collect_summary.sessions_seen if result.collect_summary else 0,
                "dropped": dict(result.collect_summary.dropped) if result.collect_summary else {},
            }
        )
        return 0
    print(result.message or f"Trace collect → {run_dir}")
    return 0


def _trace_usage_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills trace-usage",
        description="Read the last run's skills-only usage report.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME to read")
    parser.add_argument("--run-dir", metavar="DIR", default="", help="Run dir to read usage from")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_trace_usage(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_usage_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    request = SkillsRequest(
        op=SkillsOp.TRACE_USAGE,
        flags={
            "grok_home": ns.grok_home,
            "run_dir": ns.run_dir,
        },
        json=ns.json,
    )
    result = aggregate.execute(request)

    if ns.json:
        _emit_json(
            {
                "kept_sessions": result.usage.kept_sessions if result.usage else 0,
                "items": [
                    {
                        "name": it.name,
                        "source": it.source,
                        "path": it.path,
                        "loaded": it.loaded,
                        "count": it.count,
                        "sessions": list(it.sessions),
                        "last_used": it.last_used,
                        "in_slash_mru": it.in_slash_mru,
                    }
                    for it in (result.usage.items or [])
                ],
                "unused_loaded": list(result.usage.unused_loaded or []),
            }
        )
        return 0

    usage = result.usage
    if usage is None:
        err("Internal error: no usage report produced")
        return 1
    print(f"Kept sessions: {usage.kept_sessions}")
    print(f"{'Skill':<28} {'Loaded':<7} {'Count':<6} {'Last used':<20} {'In slash MRU'}")
    print("-" * 28 + " " + "-" * 7 + " " + "-" * 6 + " " + "-" * 20 + " " + "-" * 12)
    for it in usage.items:
        print(
            f"{it.name:<28} {it.loaded!s:<7} {it.count:<6} "
            f"{it.last_used!s:<20} {it.in_slash_mru!s}"
        )
    print(f"\nUnused loaded: {', '.join(usage.unused_loaded) or '(none)'}")
    return 1 if usage.unused_loaded else 0


def _trace_phrases_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills trace-phrases",
        description="Mine repeated prompts and instruction lines from session records.",
    )
    parser.add_argument("--grok-home", metavar="P", default="", help="$GROK_HOME (unused by phrases, kept for symmetry)")
    parser.add_argument("--run-dir", metavar="DIR", default="", help="Run dir holding session records")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def _cmd_trace_phrases(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_phrases_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    request = SkillsRequest(
        op=SkillsOp.TRACE_PHRASES,
        flags={
            "grok_home": ns.grok_home,
            "run_dir": ns.run_dir,
        },
        json=ns.json,
    )
    result = aggregate.execute(request)

    if ns.json:
        _emit_json(
            {
                "exact_prompts": [
                    {
                        "phrase": row.phrase,
                        "sessions": row.sessions,
                        "occurrences": row.occurrences,
                        "session_ids": list(row.session_ids),
                    }
                    for row in (result.phrases.exact_prompts or [])
                ],
                "stems": [
                    {
                        "phrase": row.phrase,
                        "sessions": row.sessions,
                        "occurrences": row.occurrences,
                        "session_ids": list(row.session_ids),
                    }
                    for row in (result.phrases.stems or [])
                ],
                "repeated_instruction_lines": [
                    {
                        "phrase": row.phrase,
                        "sessions": row.sessions,
                        "occurrences": row.occurrences,
                        "session_ids": list(row.session_ids),
                    }
                    for row in (result.phrases.repeated_instruction_lines or [])
                ],
            }
        )
        return 0

    phrases = result.phrases
    if phrases is None:
        err("Internal error: no phrases report produced")
        return 1
    if phrases.exact_prompts:
        print("Repeated exact prompts:")
        for row in phrases.exact_prompts:
            print(f"  [{row.sessions} sessions] {row.phrase}")
    if phrases.stems:
        print("Repeated prompt stems:")
        for row in phrases.stems:
            print(f"  [{row.sessions} sessions] {row.phrase}")
    if phrases.repeated_instruction_lines:
        print("Repeated instruction lines:")
        for row in phrases.repeated_instruction_lines:
            print(f"  [{row.sessions} sessions] {row.phrase}")
    if not any((phrases.exact_prompts, phrases.stems, phrases.repeated_instruction_lines)):
        print("No repeated phrases found.")
    return 0


def _trace_state_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aa skills trace-state",
        description="Drive the trace-learning lifecycle (status, trash, decisions, wait).",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    p_get = subparsers.add_parser("get", help="Show the pending run status")
    p_get.add_argument("--grok-home", metavar="P", default="")

    p_set = subparsers.add_parser("set", help="Set the pending run status")
    p_set.add_argument("--grok-home", metavar="P", default="")
    p_set.add_argument("--run-dir", metavar="DIR", default="")
    p_set.add_argument("--status", required=True, help="collected|running|report_ready|curating|done")

    p_clear = subparsers.add_parser("clear", help="Clear the pending run")
    p_clear.add_argument("--grok-home", metavar="P", default="")
    p_clear.add_argument("--run-dir", metavar="DIR", default="")

    p_trash = subparsers.add_parser("trash", help="Move validated paths into learn/trash/<run_name>")
    p_trash.add_argument("--grok-home", metavar="P", default="")
    p_trash.add_argument("--run-name", required=True, help="Trash sub-dir name (single path component)")
    p_trash.add_argument("paths", nargs="*", help="Paths to trash")

    p_restrict = subparsers.add_parser("restrict", help="chmod 0600 on the given paths")
    p_restrict.add_argument("paths", nargs="*", help="Paths to restrict")

    p_decide = subparsers.add_parser("decide", help="Append a decision line to learn/decisions.jsonl")
    p_decide.add_argument("--grok-home", metavar="P", default="")
    p_decide.add_argument("--run-dir", metavar="DIR", default="")
    p_decide.add_argument("--id", required=True, help="Decision id")
    p_decide.add_argument("--kind", required=True, help="skill|workflow|hook")
    p_decide.add_argument(
        "--action", required=True, dest="decide_action", help="create|update|delete|reject|..."
    )
    p_decide.add_argument("--target", required=True, help="Skill/target name")
    p_decide.add_argument("--path", required=True, help="Target path")
    p_decide.add_argument("--decision", required=True, help="applied|rejected|...")
    p_decide.add_argument("--date", default="", help="Decision date (ISO)")
    p_decide.add_argument("--undo", default=None, help="Undo path")

    p_wait = subparsers.add_parser("wait", help="Wait for report.md + actions.json in the run dir")
    p_wait.add_argument("--grok-home", metavar="P", default="")
    p_wait.add_argument("--run-dir", required=True, help="Run dir to watch")
    p_wait.add_argument("--timeout-min", type=int, default=90, help="Max minutes to wait")
    return parser


def _cmd_trace_state(args: list[str], aggregate: ISkillsAggregate) -> int:
    try:
        ns = _trace_state_parser().parse_args(args)
    except SystemExit as exit_exc:
        return int(exit_exc.code or 0)

    action = ns.action
    flags = {
        "state_action": action,
        "grok_home": getattr(ns, "grok_home", ""),
        "run_dir": getattr(ns, "run_dir", ""),
    }

    if action == "set":
        flags["status"] = ns.status
    elif action == "trash":
        flags["run_name"] = ns.run_name
        flags["trash_paths"] = ",".join(ns.paths)
    elif action == "restrict":
        flags["restrict_paths"] = ",".join(ns.paths)
    elif action == "decide":
        flags["id"] = ns.id
        flags["kind"] = ns.kind
        flags["decide_action"] = ns.decide_action
        flags["target"] = ns.target
        flags["path"] = ns.path
        flags["decision"] = ns.decision
        flags["date"] = getattr(ns, "date", "")
        flags["undo"] = getattr(ns, "undo", "") or ""
    elif action == "wait":
        flags["timeout_min"] = str(getattr(ns, "timeout_min", 90))

    request = SkillsRequest(op=SkillsOp.TRACE_STATE, flags=flags)
    result = aggregate.execute(request)

    if action == "get":
        status = result.state
        if status in (
            TraceStateStatus.COLLECTED,
            TraceStateStatus.RUNNING,
        ):
            # "exit 3 while a run is pending" domain signal
            return 3
        print(f"Pending status: {status}")
        return 0

    if action == "set":
        print(f"Status set: {result.state}")
        return 0

    if action == "clear":
        print(f"Pending cleared: {result.state}")
        return 0

    if action == "trash":
        for line in result.lines or ():
            print(line)
        return 0

    if action == "restrict":
        for line in result.lines or ():
            print(line)
        return 0

    if action == "decide":
        for line in result.lines or ():
            print(line)
        return 0

    if action == "wait":
        status = result.state_status
        if status == TraceStateStatus.REPORT_READY:
            return _EXIT_WAIT_READY
        if status == TraceStateStatus.PHASE_STALL:
            return _EXIT_WAIT_PHASE_STALL
        if status == TraceStateStatus.REPORT_STALL:
            return _EXIT_WAIT_REPORT_STALL
        if status == TraceStateStatus.DEADLINE:
            return _EXIT_WAIT_DEADLINE
        print(f"Wait ended: {status}")
        return 0

    return 0
