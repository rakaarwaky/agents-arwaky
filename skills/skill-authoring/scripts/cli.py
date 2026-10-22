#!/usr/bin/env python3
"""Path-invocable CLI for the skill-authoring script package.

Canonical invocation (design doc §6.1; the pack directory contains a
hyphen, so ``python3 -m`` cannot target it)::

    python3 skills/skill-authoring/scripts/cli.py validate

``validate`` runs the 13 checks from ``validate.py`` against the skills
root resolved from this file's location (the same layout invariant as
``librarian.py``: the script package sits directly under the pack
directory) and prints the identical report the old
``librarian.py validate`` command prints today.

More subcommands (catalog/discover/mutate/rules) land in PR-4; this
PR ships ``validate`` only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()

if len(SCRIPT.parents) < 3:
    print(
        "ERROR: skill-authoring CLI must be installed as "
        "<skills-root>/<pack>/scripts/cli.py",
        file=sys.stderr,
    )
    sys.exit(1)

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

from validate import validate_library


def cmd_validate(args: argparse.Namespace) -> None:
    """Report validation issues — byte-identical to the old command."""
    del args
    report = validate_library(SKILLS_ROOT)

    if report["issue_count"] == 0:
        print("No validation issues found.")
        return

    print(f"{report['issue_count']} validation issue(s) found:")

    for issue in report["issues"]:
        locator = issue.get("path") or issue.get("category") or "library"
        print(f"- [{issue['type']}] {locator}: {issue['message']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Skill-authoring pack tooling (PR-2: validate only).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Report validation issues")

    args = parser.parse_args()

    commands = {
        "validate": cmd_validate,
    }

    commands[args.command](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
