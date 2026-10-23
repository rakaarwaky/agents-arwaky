#!/usr/bin/env python3
"""Path-invocable CLI for the skill-authoring script package.

Canonical invocation (design doc §6.1; the pack directory contains a
hyphen, so ``python3 -m`` cannot target it)::

    python3 skills/skill-authoring/scripts/cli.py validate

The old path keeps working through a back-compat shim
(``skill-librarian/scripts/librarian.py``) that delegates here, so every
read-only subcommand prints the same report through both entrypoints.

Layout invariant: this file lives at
``<skills-root>/<pack>/scripts/cli.py``, so ``parents[2]`` is the skills
root — the same resolution ``librarian.py`` always used. ``--skills-root``
overrides it (explicit beats derived; the flag exists precisely for trees
whose layout does not match the script's own placement).

Contract (design §6.1):
- exit 0 clean · 1 issues found · 2 usage error · 3 catalog drift
- every subcommand accepts ``--json`` and ``--skills-root PATH``
- mutating subcommands (``repair``, ``move``, ``archive``, ``new-category``)
  default to dry-run and execute only with ``--apply`` (§5.5)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()

if len(SCRIPT.parents) < 3:
    print(
        "ERROR: skill-authoring CLI must be installed as "
        "<skills-root>/<pack>/scripts/cli.py",
        file=sys.stderr,
    )
    sys.exit(2)

# Expected layout: <skills-root>/<category>/<pack>/scripts/cli.py
# The script package sits directly under the pack directory, so
# parents[2] is the skills root:
#   parents[0]=scripts  parents[1]=pack  parents[2]=skills-root
SKILLS_ROOT = SCRIPT.parents[2]

# Running this file by path puts its own directory on sys.path, so the
# sibling modules resolve by name; the _rules/ SSOT needs one more entry.
_RULES_DIR = SCRIPT.parent.parent / "_rules"
if str(_RULES_DIR) not in sys.path:
    sys.path.insert(0, str(_RULES_DIR))

import catalog
import discover as discover_mod
import mergeplan
import mutate
from docs import render_rules_markdown, render_rules_summary
from mutate import fail
from validate import validate_library, validate_summary

_EXIT_USAGE = 2
_EXIT_DRIFT = 3

#: The rule IDs whose issues ``validate --rules-only`` keeps. The other
#: checks (duplicate names/descriptions, category emptiness) are library
#: hygiene rather than per-rule frontmatter constraints, so the flag
#: filters them out without changing which issues are found.
_RULE_IDS = {
    "invalid-skill-name",
    "name-mismatch",
    "missing-description",
    "invalid-description-characters",
    "description-too-long",
    "nested-skill-md",
    "invalid-placement",
    "too-deep",
    "missing-category-description",
    "empty-category-description",
}


def _emit(lines: list[str]) -> None:
    """Print the report, one line per row, newline-terminated."""
    for line in lines:
        print(line)


def _emit_json(payload: dict) -> None:
    """Print a JSON payload with a stable key order and a trailing newline."""
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _validate_report(
    skills_root: Path, category: str | None, rules_only: bool
) -> tuple[dict, list[dict]]:
    """Run the validator and apply the filters, keeping discovery order.

    The filters only narrow the report: ``validate_library`` still finds
    every issue, so the flag pair cannot hide a regression in a check.
    """
    report = validate_library(skills_root)
    issues = report["issues"]

    if category:
        issues = [i for i in issues if i.get("category") == category or i.get("path", "").startswith(f"{category}/")]
    if rules_only:
        issues = [i for i in issues if i["type"] in _RULE_IDS]

    return report, issues


def cmd_validate(args: argparse.Namespace) -> int:
    """Report validation issues — byte-identical to the old command.

    ``--category``/``--rules-only`` narrow what is listed but never what
    is found: the count line states the unfiltered total, and the exit
    code tracks it, so a scoped view cannot report the library as clean
    while issues exist outside the scope.

    ``--summary`` prints a single observability line (design §10.1) with
    the live counts — issues / loader-visible skills / categories — and
    suppresses the per-issue listing; it is orthogonal to the report
    filters. It takes no precedence on its own: when ``--json`` is
    passed, the JSON report wins and ``--summary`` is ignored.
    """
    skills_root = _skills_root(args)
    report, issues = _validate_report(skills_root, args.category, args.rules_only)
    total = report["issue_count"]
    scope_note = _filter_note(args.category, args.rules_only)

    if args.json:
        _emit_json(
            {
                "skills_root": str(skills_root),
                "category": args.category,
                "rules_only": args.rules_only,
                "issue_count": len(issues),
                "total_issue_count": total,
                "issues": issues,
            }
        )
        return 1 if total else 0

    if args.summary:
        print(validate_summary(skills_root))
        return 1 if total else 0

    if total == 0:
        print("No validation issues found.")
        return 0

    if scope_note:
        print(f"{total} validation issue(s) found ({len(issues)} in scope {scope_note}):")
    else:
        print(f"{total} validation issue(s) found:")

    for issue in issues:
        locator = issue.get("path") or issue.get("category") or "library"
        print(f"- [{issue['type']}] {locator}: {issue['message']}")

    if not issues:
        print("(none in scope)")
    return 1


def _filter_note(category: str | None, rules_only: bool) -> str:
    """The parenthetical that names the active filter(s)."""
    bits = []
    if category:
        bits.append(f"category={category}")
    if rules_only:
        bits.append("rules-only")
    return "; ".join(bits)


def cmd_catalog(args: argparse.Namespace) -> int:
    """Rebuild ``CATALOG.md`` — or, with ``--check``, only test for drift."""
    skills_root = _skills_root(args)

    if args.check:
        in_sync, summary, diff_lines = catalog.check_catalog(skills_root)
        if args.json:
            _emit_json(
                {
                    "skills_root": str(skills_root),
                    "in_sync": in_sync,
                    "catalog": str(catalog.catalog_path(skills_root)),
                    "diff": diff_lines,
                }
            )
        else:
            print(summary)
            for line in diff_lines:
                print(line)
        return 0 if in_sync else _EXIT_DRIFT

    path = catalog.catalog_path(skills_root)
    entries, categories = catalog.rebuild_catalog(skills_root)
    if args.json:
        _emit_json(
            {
                "skills_root": str(skills_root),
                "catalog": str(path),
                "rebuilt": True,
                "categories": len(categories),
                "skills": len(entries),
            }
        )
    else:
        print(f"Rebuilt {path}")
        print(f"Categories: {len(categories)}; skills: {len(entries)}")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    """Search the catalog and rank matches.

    §5.6: when the catalog fails its drift gate, the result carries a
    ``warning`` field (JSON) / a stderr warning (text) naming
    ``catalog --check`` as the repair, and the answer comes from a
    read-only tree scan. Exit stays 0 — a successful search is a
    successful search; drift is ``catalog --check``'s exit 3.
    """
    skills_root = _skills_root(args)
    lines, results, warning = discover_mod.discover(args.query, skills_root, limit=args.limit)

    if args.json:
        payload: dict = {
            "skills_root": str(skills_root),
            "query": args.query,
            "limit": args.limit,
            "match_count": len(results),
            "matches": results,
        }
        if warning is not None:
            payload["warning"] = warning
        _emit_json(payload)
    else:
        _emit(lines)
    return 0


def cmd_weed(args: argparse.Namespace) -> int:
    """Report duplicates, empty categories, and missing category descriptions."""
    skills_root = _skills_root(args)
    lines = mutate.weed_report(skills_root)

    if args.json:
        issues = [_weed_issue(line) for line in lines]
        _emit_json(
            {
                "skills_root": str(skills_root),
                "issue_count": len(issues),
                "issues": issues,
            }
        )
    else:
        print("Weeding report:")
        if lines:
            _emit(lines)
        else:
            print("No obvious weeds found.")
    return 1 if lines else 0


def _weed_issue(line: str) -> dict[str, str]:
    """Parse one weed line into the JSON report shape.

    The weed report is the one command whose text form has no structured
    source yet (it is computed directly from the model), so the line is
    parsed back into ``type``/``message`` for the JSON consumers rather
    than duplicated at the computation site.
    """
    body = line.removeprefix("- ")
    kind, _, message = body.partition(": ")
    return {"type": kind, "message": message}


def cmd_repair(args: argparse.Namespace) -> int:
    """Apply safe mechanical repairs — preview by default, apply with ``--apply``."""
    skills_root = _skills_root(args)
    planned = mutate.repair_plan(skills_root)

    if not args.apply:
        if args.json:
            _emit_json(
                {
                    "skills_root": str(skills_root),
                    "dry_run": True,
                    "planned": planned,
                    "plan_count": len(planned),
                    "note": "no changes made (dry-run default; pass --apply to execute)",
                }
            )
        else:
            print("Planned repairs (dry-run — pass --apply to execute):")
            if planned:
                for item in planned:
                    print(f"- {item}")
            else:
                print("- (none)")
            print(f"Would rebuild {catalog.catalog_path(skills_root)}")
        return 0

    applied = mutate.apply_repairs(skills_root)
    catalog.rebuild_catalog(skills_root)

    if applied:
        print("Repairs applied:")
        for item in applied:
            print(f"- {item}")
    else:
        print("No mechanical repairs needed.")

    print(f"Rebuilt {catalog.catalog_path(skills_root)}")
    return 0


def cmd_move(args: argparse.Namespace) -> int:
    """Move a skill folder to another category — preview by default."""
    skills_root = _skills_root(args)
    source, dest = mutate.move_plan(args.skill, args.target_category, skills_root)

    if source.parent == (skills_root / args.target_category):
        print(f"Skill already in category: {args.target_category}")
        return 0

    if not args.apply:
        if args.json:
            _emit_json(
                {
                    "skills_root": str(skills_root),
                    "dry_run": True,
                    "skill": args.skill,
                    "from": mutate.relpath(source, skills_root),
                    "to": mutate.relpath(dest, skills_root),
                    "note": "no changes made (dry-run default; pass --apply to execute)",
                }
            )
        else:
            print("Planned move (dry-run — pass --apply to execute):")
            print(f"- move {mutate.relpath(source, skills_root)} -> {mutate.relpath(dest, skills_root)}")
            print(f"- rebuild {catalog.catalog_path(skills_root)}")
        return 0

    mutate.apply_move(source, dest)
    catalog.rebuild_catalog(skills_root)

    print(f"Moved {mutate.relpath(source, skills_root)} -> {mutate.relpath(dest, skills_root)}")
    print(f"Rebuilt {catalog.catalog_path(skills_root)}")
    return 0


def cmd_archive(args: argparse.Namespace) -> int:
    """Move a skill into ``_archive/`` and disable its ``SKILL.md``."""
    skills_root = _skills_root(args)
    source, dest = mutate.archive_plan(args.skill, skills_root)

    if not args.apply:
        if args.json:
            _emit_json(
                {
                    "skills_root": str(skills_root),
                    "dry_run": True,
                    "skill": args.skill,
                    "from": mutate.relpath(source, skills_root),
                    "to": mutate.relpath(dest, skills_root),
                    "note": "no changes made (dry-run default; pass --apply to execute)",
                }
            )
        else:
            print("Planned archive (dry-run — pass --apply to execute):")
            print(f"- move {mutate.relpath(source, skills_root)} -> {mutate.relpath(dest, skills_root)}")
            print(f"- rename {mutate.relpath(dest, skills_root)}/SKILL.md -> SKILL.md.archived")
            print(f"- rebuild {catalog.catalog_path(skills_root)}")
        return 0

    mutate.apply_archive(source, dest)
    catalog.rebuild_catalog(skills_root)

    print(f"Archived {mutate.relpath(source, skills_root)} -> {mutate.relpath(dest, skills_root)}")
    print(f"Rebuilt {catalog.catalog_path(skills_root)}")
    return 0


def cmd_new_category(args: argparse.Namespace) -> int:
    """Create a category folder and write its ``DESCRIPTION.md``."""
    skills_root = _skills_root(args)
    category, description, will_write = mutate.new_category_plan(
        args.name, args.description, skills_root, force=args.force
    )

    if not args.apply:
        if args.json:
            _emit_json(
                {
                    "skills_root": str(skills_root),
                    "dry_run": True,
                    "category": args.name,
                    "description": description,
                    "would_write_description": will_write,
                    "note": "no changes made (dry-run default; pass --apply to execute)",
                }
            )
        else:
            print("Planned new-category (dry-run — pass --apply to execute):")
            print(f"- create {mutate.relpath(category, skills_root)}/")
            if will_write:
                print(f"- write {args.name}/DESCRIPTION.md: {mutate.yaml_quote(description)}")
            else:
                print(f"- keep existing {args.name}/DESCRIPTION.md; use --force to overwrite")
            print(f"- rebuild {catalog.catalog_path(skills_root)}")
        return 0

    wrote = mutate.apply_new_category(category, description, force=args.force)
    catalog.rebuild_catalog(skills_root)

    if wrote:
        print(f"Wrote {args.name}/DESCRIPTION.md")
    else:
        print(f"Kept existing {args.name}/DESCRIPTION.md; use --force to overwrite")

    print(f"Rebuilt {catalog.catalog_path(skills_root)}")
    return 0


def cmd_merge_plan(args: argparse.Namespace) -> int:
    """Emit the merge plan ``prune-skills`` executes (read-only)."""
    skills_root = _skills_root(args)
    plan = mergeplan.merge_plan(args.skill_a, args.skill_b, skills_root)

    if args.json:
        _emit_json(
            {
                "skills_root": str(skills_root),
                "survivor": plan["survivor"],
                "absorbed": plan["absorbed"],
                "survival_reason": plan["survival_reason"],
                "moves": [
                    {"from": src, "to": dst} for src, dst in plan["moves"]
                ],
                "rewrites": plan["rewrites"],
                "category_after": plan["category_after"],
                "empty_category_after": plan["empty_category_after"],
            }
        )
    else:
        _emit(mergeplan.render_merge_plan(plan))
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    """Render the SSOT — one line per rule, or the full markdown doc.

    ``--markdown`` writes the exact bytes of the committed artifact (no
    extra trailing newline), so a shell redirect reproduces it exactly.
    """
    if args.markdown:
        sys.stdout.write(render_rules_markdown())
    else:
        print(render_rules_summary())

    return 0


def _skills_root(args: argparse.Namespace) -> Path:
    """Resolve the skills root: ``--skills-root`` wins, else derive from this file.

    Deriving from the script path is what makes the bare invocation work
    from anywhere; the explicit flag is what makes crafted trees (tests,
    CI on relocated layouts) work. Whichever wins, a root that is not a
    directory fails fast with the legacy ``ERROR:`` line and exit 2.
    """
    if args.skills_root:
        root = Path(args.skills_root).expanduser().resolve()
        if not root.is_dir():
            fail(f"Skills root does not exist: {root}")
        return root

    return SKILLS_ROOT


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI; exported so tests can drive the parser directly."""
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Skill-authoring pack tooling: validate, catalog, discover, and mutations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--skills-root",
            metavar="PATH",
            default=None,
            help="Skills root (default: derived from this script's location)",
        )
        sub.add_argument("--json", action="store_true", help="Emit the report as JSON")

    p = subparsers.add_parser("validate", help="Report validation issues")
    add_common(p)
    p.add_argument("--category", metavar="NAME", default=None,
                   help="Only report issues in category NAME")
    p.add_argument("--rules-only", action="store_true",
                   help="Only report the rule checks (skip library-wide duplicates)")
    p.add_argument("--summary", action="store_true",
                   help="Print the 'N issues / M skills / K categories' observability line "
                        "instead of the per-issue listing; exit code tracks the unfiltered "
                        "issue total as usual. If --json is also passed, JSON wins and "
                        "--summary is ignored")

    p = subparsers.add_parser("catalog", help="Rebuild CATALOG.md (or check for drift)")
    add_common(p)
    p.add_argument("--check", action="store_true",
                   help="Regenerate to a temp file and diff against CATALOG.md (drift gate; exit 3 on drift)")

    p = subparsers.add_parser("discover", help="Search CATALOG.md")
    add_common(p)
    p.add_argument("query", help="Search query")
    p.add_argument("--limit", type=int, default=20, help="Maximum results")

    p = subparsers.add_parser("weed", help="Report duplicates and empty categories")
    add_common(p)

    p = subparsers.add_parser("repair", help="Apply safe mechanical repairs (dry-run by default)")
    add_common(p)
    p.add_argument("--apply", action="store_true", help="Execute the repairs (default is a preview)")

    p = subparsers.add_parser("move", help="Move a skill to a target category")
    add_common(p)
    p.add_argument("skill", help="Skill reference, e.g. category/skill-name")
    p.add_argument("target_category", help="Target category folder")
    p.add_argument("--apply", action="store_true", help="Execute the move (default is a preview)")

    p = subparsers.add_parser("archive", help="Archive a skill (dry-run by default)")
    add_common(p)
    p.add_argument("skill", help="Skill reference, e.g. category/skill-name")
    p.add_argument("--apply", action="store_true", help="Execute the archive (default is a preview)")

    p = subparsers.add_parser("new-category", help="Create category and DESCRIPTION.md")
    add_common(p)
    p.add_argument("name", help="Category folder name")
    p.add_argument("description", nargs="?", default=None, help="Category description")
    p.add_argument("--force", action="store_true", help="Overwrite DESCRIPTION.md")
    p.add_argument("--apply", action="store_true", help="Execute the creation (default is a preview)")

    p = subparsers.add_parser(
        "merge-plan", help="Emit the merge plan for two skills (read-only; prune-skills executes it)"
    )
    add_common(p)
    p.add_argument("skill_a", help="First skill reference, category/skill")
    p.add_argument("skill_b", help="Second skill reference, category/skill")

    p = subparsers.add_parser(
        "rules", help="Render the SSOT rules (add --markdown for the full doc)"
    )
    add_common(p)
    p.add_argument(
        "--markdown",
        action="store_true",
        help="Print the full rules document (redirect into _rules/skill-rules.md)",
    )

    return parser


#: Success/failure mapping for the CLI's own exit codes, documented for
#: callers that interpret them (skill bodies and CI gates).
EXIT_CODES = {
    "clean": 0,
    "issues_found": 1,
    "usage_error": _EXIT_USAGE,
    "catalog_drift": _EXIT_DRIFT,
}


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` (``sys.argv[1:]`` by default) and run the subcommand."""
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "validate": cmd_validate,
        "catalog": cmd_catalog,
        "discover": cmd_discover,
        "weed": cmd_weed,
        "repair": cmd_repair,
        "move": cmd_move,
        "archive": cmd_archive,
        "new-category": cmd_new_category,
        "merge-plan": cmd_merge_plan,
        "rules": cmd_rules,
    }

    try:
        return commands[args.command](args)
    except SystemExit as exit_exc:
        # ``fail`` prints the legacy ERROR line and exits 1; a nonexistent
        # skill or a bad category name is a caller-input problem, which the
        # §6.1 contract classes as usage (2) rather than a found issue (1).
        if exit_exc.code == 1:
            return _EXIT_USAGE
        if exit_exc.code not in (0, None):
            return int(exit_exc.code)
        return 0


if __name__ == "__main__":
    sys.exit(main())
