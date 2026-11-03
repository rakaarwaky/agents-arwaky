"""Skills CLI surface — command handlers for the ``aa skills`` verbs.

Five agent-oriented commands: read-only discovery (``list``/``read``),
the lint scan (``lint``), the catalog builder/reader (``catalog``), and
the search (``discover``). The pack root is always the repository's
``skills/`` pack; there is no ``--skills-root`` override and no JSON
export — output is a terminal listing consumed by the agent.

The aggregate is injected by the caller (the root CLI), never imported
here, so no root→surface coupling exists (AES205). Argv becomes a
``SkillsRequest``; the rendered text comes back on ``SkillsResult``.
Exit codes are the legacy contract: 0 clean / 1 issues / 2 usage /
3 catalog drift.
"""

from __future__ import annotations

import argparse
import sys

from modules.shared.src.common.utility_logging_setup import (
    BOLD,
    CYAN,
    RESET,
    banner,
    err,
    info,
)
from modules.shared.src.common.utility_skills_markdown import md_escape
from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.taxonomy_skills_error import SkillsUsageError
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillQuery,
    SkillsExitCode,
    SkillsOp,
    SkillsRequest,
    SkillsResult,
)

_EXIT_USAGE = SkillsExitCode.USAGE_ERROR
_EXIT_DRIFT = SkillsExitCode.CATALOG_DRIFT

#: The results table header/separator and empty-result line, verbatim from
#: the legacy command (presentation strings, owned by the surface).
_SCORE_TABLE_HEADER = "| Skill | Category | Description | Path | Score |"
_SCORE_TABLE_SEPARATOR = "|---|---|---|---|---|"
_NO_MATCH_LINE = "No matching skills found in CATALOG.md."


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
    if sub in ("lint", "catalog", "discover"):
        return _cmd_authoring(sub, rest, aggregate)
    err(f"Unknown skills subcommand: {sub}")
    _print_usage()
    return _EXIT_USAGE


def _print_usage() -> None:
    banner()
    info(
        f"{BOLD()}aa skills list{RESET()}                  List all skills in the pack"
    )
    info(f"{BOLD()}aa skills read <name>{RESET()}           Print a skill's SKILL.md")
    info(f"{BOLD()}aa skills lint [--category NAME]{RESET()}  Lint scan all skills (optionally filter by category)")
    info(
        f"{BOLD()}aa skills catalog [--build] [--read]{RESET()}  Build and/or print CATALOG.md"
    )
    info(f"{BOLD()}aa skills discover <query>{RESET()}      Search the catalog")


# ─── Read-only surface ──────────────────────────────────────
def _has_help(args: list[str]) -> bool:
    return any(a in ("-h", "--help") for a in args)


def _cmd_list(args: list[str], aggregate: ISkillsAggregate) -> int:
    """List every skill in the pack as a compact table."""
    if _has_help(args):
        info("Usage: aa skills list — list all skills in the pack")
        return 0
    result = aggregate.execute(SkillsRequest(op=SkillsOp.LIST))
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
    if _has_help(args) or not args:
        info("Usage: aa skills read <name>")
        return 0
    name = args[0]
    result = aggregate.execute(
        SkillsRequest(op=SkillsOp.READ, query=SkillQuery(name))
    )
    if not result.ok or result.content is None:
        err("Skill not found")
        return 1
    print(result.content)
    return 0


# ─── Authoring parser ────────────────────────────────────────────────
class _TriFlag(argparse.Action):
    """argparse action: unset stays None, set → True.

    ``store_true`` coerces a ``None`` default to ``False``, which would
    hide the "flag absent" state the surface needs to resolve the
    default (neither ``--build`` nor ``--read`` → both).
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | None,
        option_string: str | None = None,
    ) -> None:
        setattr(namespace, self.dest, True)


def _authoring_parser() -> argparse.ArgumentParser:
    """Construct the authoring CLI; exported so tests can drive it directly."""
    parser = argparse.ArgumentParser(
        prog="aa skills",
        description="Skill-pack tooling: lint, catalog, discover.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("lint", help="Lint scan all skills (optionally filter by category)")
    sub.add_argument(
        "--category",
        metavar="NAME",
        default=None,
        help="Only report issues in category NAME",
    )

    sub = subparsers.add_parser("catalog", help="Build and/or print CATALOG.md")
    sub.add_argument(
        "--build",
        action=_TriFlag,
        nargs=0,
        default=None,
        help="Rebuild CATALOG.md from the live tree",
    )
    sub.add_argument(
        "--read",
        action=_TriFlag,
        nargs=0,
        default=None,
        help="Print the current CATALOG.md content",
    )

    sub = subparsers.add_parser("discover", help="Search CATALOG.md")
    sub.add_argument("query", help="Search query")
    sub.add_argument("--limit", type=int, default=20, help="Maximum results")

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
    raise SkillsUsageError(f"Unknown skills subcommand: {sub}")


def _build_request(namespace: argparse.Namespace) -> SkillsRequest:
    """Map parsed argv onto the request the domain understands."""
    command = namespace.command

    if command == "lint":
        return SkillsRequest(
            op=SkillsOp.LINT,
            flags={"category": namespace.category or ""},
        )

    if command == "catalog":
        # Tri-state: no flag at all → both (the convenient agent default:
        # build then print). An explicit flag pins its value; the other
        # flag defaults to False.
        if namespace.build is None and namespace.read is None:
            build, read = True, True
        elif namespace.build is None:
            build, read = False, True  # --read only
        elif namespace.read is None:
            build, read = True, False  # --build only
        else:
            build, read = namespace.build, namespace.read  # both explicit
        return SkillsRequest(
            op=SkillsOp.CATALOG,
            flags={
                "build": "1" if build else "0",
                "read": "1" if read else "0",
            },
        )

    if command == "discover":
        return SkillsRequest(
            op=SkillsOp.DISCOVER,
            query=SkillQuery(namespace.query),
            flags={"limit": str(namespace.limit)},
        )

    raise SkillsUsageError(f"Unknown skills subcommand: {command}")


# ─── Renderers ───────────────────────────────────────────────────────
def _render_catalog(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the catalog build / read output."""
    build = request.flags.get("build", "1") == "1"
    read = request.flags.get("read", "1") == "1"

    if build:
        report = result.catalog
        if report is None:
            err("Internal error: no catalog report produced")
            return 1
        print(f"Rebuilt {report.path}")
        print(f"Categories: {report.categories}; skills: {report.skills}")

    if read:
        text = result.catalog_text
        if not text:
            if result.message:
                err(result.message)
            else:
                err("CATALOG.md not found — run with --build first")
            return result.exit_code or 1
        print(text)

    return 0


def _render_discover(result: SkillsResult, request: SkillsRequest) -> int:
    """Render the scored matches (or the legacy no-match line)."""
    if result.warning:
        print(result.warning, file=sys.stderr)
        if result.message:
            print(f"  reason: {result.message}", file=sys.stderr)

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


def _render_lint(result: SkillsResult, request: SkillsRequest) -> int:
    """Render a lint report, narrowed by --category."""
    report = result.lint_report
    if report is None:
        err("Internal error: no lint report produced")
        return 1

    total = report.unfiltered_issue_count
    in_scope = report.issue_count

    if total == 0:
        print("No lint issues found.")
        return 0

    if request.flags.get("category"):
        category = request.flags["category"]
        print(f"{total} lint issue(s) found ({in_scope} in scope category={category}):")
    else:
        print(f"{total} lint issue(s) found:")

    for issue in report.issues:
        print(f"- [{issue.type}] {issue.locator}: {issue.message}")
    for line in report.weed_lines:
        print(f"- {line}")
    return 1
