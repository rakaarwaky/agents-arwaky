"""Skills CLI surface — command handlers for every ``aa skills`` verb.

Read-only discovery (``list``/``read``) plus the authoring commands
(``lint``, ``catalog``, ``discover``, ``move``, ``archive``,
``create``) and the trace lifecycle (``traces``).

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
from pathlib import Path

from modules.cli.src.surface_skills_traces_command import cmd_traces
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
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillQuery,
    SkillsExitCode,
    SkillsOp,
    SkillsRequest,
    SkillsResult,
    SkillsRoot,
)

_EXIT_USAGE = SkillsExitCode.USAGE_ERROR
_EXIT_DRIFT = SkillsExitCode.CATALOG_DRIFT

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
    if sub == "read":
        return _cmd_read(rest, aggregate)
    if sub in (
        "lint",
        "catalog",
        "discover",
        "move",
        "archive",
        "create",
    ):
        return _cmd_authoring(sub, rest, aggregate)
    if sub == "traces":
        return _cmd_traces(rest, aggregate)
    err(f"Unknown skills subcommand: {sub}")
    _print_usage()
    return _EXIT_USAGE


def _print_usage() -> None:
    banner()
    info(
        f"{BOLD()}aa skills list{RESET()}                  List all skills in the pack"
    )
    info(f"{BOLD()}aa skills read <name>{RESET()}           Print a skill's SKILL.md")
    info(f"{BOLD()}aa skills lint [--category NAME]{RESET()}  Full lint scan (validate + weed)")
    info(
        f"{BOLD()}aa skills catalog [--check]{RESET()}     Rebuild CATALOG.md (or test it)"
    )
    info(f"{BOLD()}aa skills discover <query>{RESET()}      Search the catalog")
    info(
        f"{BOLD()}aa skills move <skill> <cat>{RESET()}    Move a skill to another category"
    )
    info(
        f"{BOLD()}aa skills archive <skill>{RESET()}       Archive a skill into _archive/"
    )
    info(
        f"{BOLD()}aa skills create <skill|category> <name> [--category <cat>] "
        f"[--description <desc>] [--when-to-use <trigger>] [--argument-hint <hint>] "
        f"[--body <body>] [--force] [--apply]{RESET()}"
        f"  Create a skill or category in the pack"
    )
    info(f"{BOLD()}aa skills traces <action>[...]{RESET()}    Trace lifecycle: collect|usage|phrases|materialize|state")


# ─── Read-only surface ──────────────────────────────────────
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


def _cmd_read(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Print the raw SKILL.md for one skill."""
    root, rest = _split_root(args)
    if _has_help(rest) or not rest:
        info("Usage: aa skills read <name>")
        return 0
    name = rest[0]
    result = aggregate.execute(
        SkillsRequest(op=SkillsOp.READ, query=SkillQuery(name), root=root)
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

    sub = subparsers.add_parser("lint", help="Full lint scan (validate + weed)")
    add_common(sub)
    sub.add_argument(
        "--category",
        metavar="NAME",
        default=None,
        help="Only report issues in category NAME",
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
        "create", help="Create a skill or category (dry-run by default)"
    )
    add_common(sub)
    sub.add_argument("kind", choices=["skill", "category"], help="skill | category")
    sub.add_argument("name", help="Skill name or category name")
    sub.add_argument(
        "--category",
        metavar="CAT",
        default="",
        help="Target category folder (required for create skill)",
    )
    sub.add_argument(
        "--description",
        metavar="DESC",
        default="",
        help="Skill description or category description",
    )
    sub.add_argument(
        "--when-to-use",
        metavar="TRIGGER",
        default="",
        help="when-to-use trigger phrases (frontmatter when-to-use: key)",
    )
    sub.add_argument(
        "--argument-hint",
        metavar="HINT",
        default="",
        help="Slash-command argument hint (frontmatter argument-hint: key)",
    )
    sub.add_argument(
        "--body",
        metavar="BODY",
        default="",
        help="SKILL.md body content (markdown after the frontmatter)",
    )
    sub.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing DESCRIPTION.md (category create)",
    )
    sub.add_argument(
        "--apply",
        action="store_true",
        help="Write the skill/category (default is a preview)",
    )

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

    if sub == "lint":
        return _render_lint(result, request)
    if sub == "catalog":
        return _render_catalog(result, request)
    if sub == "discover":
        return _render_discover(result, request)
    if sub == "move":
        return _render_move(result, request)
    if sub == "archive":
        return _render_archive(result, request)
    if sub == "create":
        return _render_create(result, request)
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

    if command == "lint":
        return SkillsRequest(
            op=SkillsOp.LINT,
            flags={
                "category": namespace.category or "",
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
    if command == "create":
        kind = getattr(namespace, "kind", "skill")
        flags = {
            "kind": kind,
        }
        if kind == "skill":
            flags.update(
                {
                    "category": namespace.category or "",
                    "when_to_use": namespace.when_to_use or "",
                    "argument_hint": namespace.argument_hint or "",
                    "body": namespace.body or "",
                }
            )
        else:
            flags.update({"force": "1" if namespace.force else "0"})
        return SkillsRequest(
            op=SkillsOp.CREATE,
            query=SkillQuery(namespace.name),
            description=namespace.description or "",
            apply=namespace.apply,
            flags=flags,
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


def _lint_issue(issue: Issue) -> dict[str, object]:
    """Parse one lint issue into the JSON report shape."""
    payload: dict[str, object] = {"type": issue.type, "message": issue.message}
    if issue.path:
        payload["path"] = issue.path
    if issue.category:
        payload["category"] = issue.category
    return payload


def _lint_weed_issue(line: str) -> dict[str, str]:
    """Parse one weed line into the JSON report shape."""
    body = line.removeprefix("- ")
    kind, _, message = body.partition(": ")
    return {"type": kind, "message": message}


def _render_lint(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a lint report, narrowed by --category."""
    report = result.lint_report
    if report is None:
        err("Internal error: no lint report produced")
        return 1

    total = report.unfiltered_issue_count
    in_scope = report.issue_count
    root = _root_of(result)

    if request.json:
        _emit_json(
            {
                "skills_root": str(root),
                "category": request.flags.get("category") or None,
                "issue_count": in_scope,
                "total_issue_count": total,
                "issues": [_lint_issue(issue) for issue in report.issues],
                "weed_lines": [
                    _lint_weed_issue(line) for line in report.weed_lines
                ],
            }
        )
        return 1 if total else 0

    if request.flags.get("summary") == "1":
        print(report.summary())
        return 1 if total else 0

    if total == 0:
        print("No lint issues found.")
        return 0

    if request.flags.get("category"):
        category = request.flags["category"]
        print(
            f"{total} lint issue(s) found ({in_scope} in scope category={category}):"
        )
    else:
        print(f"{total} lint issue(s) found:")

    for issue in report.issues:
        print(f"- [{issue.type}] {issue.locator}: {issue.message}")
    for line in report.weed_lines:
        print(f"- {line}")
    return 1


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
        return _render_mutation_dry_run(
            "move",
            root,
            catalog,
            request,
            {
                "skills_root": str(root),
                "dry_run": True,
                "skill": request.query,
                "from": source,
                "to": destination,
                "note": _DRY_RUN_NOTE,
            },
            f"- move {source} -> {destination}",
        )

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
        return _render_mutation_dry_run(
            "archive",
            root,
            catalog,
            request,
            {
                "skills_root": str(root),
                "dry_run": True,
                "skill": request.query,
                "from": source,
                "to": destination,
                "note": _DRY_RUN_NOTE,
            },
            f"- move {source} -> {destination}\n"
            f"- rename {destination}/SKILL.md -> SKILL.md.archived",
        )

    print(f"Archived {source} -> {destination}")
    print(f"Rebuilt {catalog}")
    return 0


def _render_create(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a create preview or the applied report."""
    new_category = result.new_category
    if new_category is not None:
        return _render_create_category(result, request, new_category)

    plan = result.create_plan
    if plan is None:
        err("Internal error: no create plan produced")
        return 1
    root = _root_of(result)
    catalog = root / "CATALOG.md"

    if plan.already_exists:
        rel = relpath(plan.skill_md, root) if plan.skill_md else ""
        print(f"Skill already exists: {rel}")
        return 0

    rel_skill_md = relpath(plan.skill_md, root) if plan.skill_md else ""

    if not request.apply:
        return _render_mutation_dry_run(
            "create",
            root,
            catalog,
            request,
            {
                "skills_root": str(root),
                "dry_run": True,
                "skill": plan.skill,
                "category": plan.category,
                "would_create": rel_skill_md,
                "would_rebuild": str(catalog),
                "note": _DRY_RUN_NOTE,
            },
            f"- create {rel_skill_md}",
        )

    print(f"Created {rel_skill_md}")
    print(f"Rebuilt {catalog}")
    return 0


def _render_create_category(
    result: SkillsResult, request: SkillsRequest, plan
) -> int:
    """Render a category-creation preview or the applied report."""
    root = _root_of(result)
    catalog = root / "CATALOG.md"

    if not request.apply:
        return _render_mutation_dry_run(
            "create category",
            root,
            catalog,
            request,
            {
                "skills_root": str(root),
                "dry_run": True,
                "category": plan.name,
                "description": plan.description,
                "would_write_description": plan.will_write,
                "note": _DRY_RUN_NOTE,
            },
            f"- create {plan.name}/"
            + (
                f"\n- write {plan.name}/DESCRIPTION.md: {yaml_quote(plan.description)}"
                if plan.will_write
                else ""
            ),
        )

    print(f"Created category {plan.name}/")
    if plan.created:
        print(f"Wrote {plan.name}/DESCRIPTION.md")
    else:
        print(f"Kept existing {plan.name}/DESCRIPTION.md; use --force to overwrite")
    print(f"Rebuilt {catalog}")
    return 0


def _render_mutation_dry_run(
    verb: str,
    root: Path,
    catalog: Path,
    request: SkillsRequest,
    payload: dict,
    detail_lines: str,
) -> int:
    """Render the shared dry-run / JSON preview for a mutating command.

    Callers supply the full ordered payload dict (the legacy JSON key
    order is pinned by the contract test, so this helper does not
    reorder keys); this helper only decides JSON vs text output.
    """
    if request.json:
        _emit_json(payload)
        return 0
    print(f"Planned {verb} (dry-run — pass --apply to execute):")
    print(detail_lines)
    print(f"- rebuild {catalog}")
    return 0


# ─── Trace pipeline surface (traces collect / usage / phrases / materialize / state) ───
def _cmd_traces(args: list[str], aggregate: ISkillsAggregate) -> int:
    """Delegate to the extracted trace-surface module (AES301 line budget)."""
    return cmd_traces(args, aggregate)
