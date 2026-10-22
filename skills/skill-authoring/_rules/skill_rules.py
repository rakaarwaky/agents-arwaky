"""SSOT for skill-library validation rules.

The single executable source of truth for what a valid skill is: the
``NAME_RE`` / budget / layout constants lifted verbatim from
``skill-librarian/scripts/librarian.py`` (lines 33-37), the escape helpers,
the layout invariants, and the issue taxonomy — the 13 issue-type strings
plus the exact message strings ``validate`` emits today.

Nothing in this module is re-derivable from elsewhere: every later consumer
(``scripts/validate.py``, ``librarian.py``, the PR-3 generated
``skill-rules.md``) must read these constants rather than restate them.

Import resolution (no packaging, see design doc §5.2 Alternative C): every
sibling module in this pack resolves this file relative to its own location
(``_rules/`` sits next to ``scripts/`` under the skill-authoring pack root),
so no ``sys.path`` patching or installed distribution is required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

# ── Naming budget (librarian.py:36-37) ──────────────────────────────────

#: Verbatim from ``librarian.py``: ``^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$``
NAME_RE: Final = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")

#: Verbatim from ``librarian.py``.
MAX_DESCRIPTION_LEN: Final = 1024

#: Inclusive bounds used by the validator (2-64 chars, no leading/trailing
#: hyphen, no double hyphen — all three conditions are checked by the
#: validator; ``NAME_RE`` alone enforces the character set and the
#: no-leading/trailing-hyphen rule).
NAME_MIN: Final = 2
NAME_MAX: Final = 64

# ── Layout invariants ──────────────────────────────────────────────────

#: Category description file name, verbatim from ``librarian.py``.
CATEGORY_DESCRIPTION_FILENAME: Final = "DESCRIPTION.md"

#: Category directories the walker skips, verbatim from ``librarian.py``.
IGNORED_CATEGORY_DIRS: Final = frozenset(
    {".git", ".hg", ".svn", "__pycache__", "_archive"}
)

# ── Escape rules (verbatim from librarian.py:52-60) ────────────────────

def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()


def md_escape(value: object) -> str:
    """Escape a value for Markdown table cells (pipes, newlines)."""
    return str(value).replace("|", "&#124;").replace("\n", " ").strip()


# ── Issue taxonomy ─────────────────────────────────────────────────────

#: Exactly the 13 strings ``librarian.py`` ``validate_library`` emits today
#: (lines 300-441). The ``validate`` CLI must keep emitting these verbatim
#: (risk R3 in the design doc), so they live here, not in two places.
class IssueType(str, Enum):
    NAME_MISMATCH = "name-mismatch"
    INVALID_SKILL_NAME = "invalid-skill-name"
    MISSING_DESCRIPTION = "missing-description"
    INVALID_DESCRIPTION_CHARACTERS = "invalid-description-characters"
    DESCRIPTION_TOO_LONG = "description-too-long"
    NESTED_SKILL_MD = "nested-skill-md"
    INVALID_PLACEMENT = "invalid-placement"
    TOO_DEEP = "too-deep"
    DUPLICATE_SKILL_NAME = "duplicate-skill-name"
    DUPLICATE_DESCRIPTION = "duplicate-description"
    MISSING_CATEGORY_DESCRIPTION = "missing-category-description"
    EMPTY_CATEGORY_DESCRIPTION = "empty-category-description"
    EMPTY_CATEGORY = "empty-category"


#: Verbatim message templates. Fields are exactly the ones
#: ``librarian.py`` interpolates today; ``{}`` are bound by keyword by the
#: same callsite shape as the original code so messages stay byte-identical.
ISSUE_MESSAGES: Final = {
    IssueType.NAME_MISMATCH: (
        "Frontmatter name '{name}' does not match directory '{dir}'."
    ),
    IssueType.INVALID_SKILL_NAME: (
        "Directory name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
        "no leading/trailing hyphen or double hyphen."
    ),
    IssueType.MISSING_DESCRIPTION: "SKILL.md description is missing.",
    IssueType.INVALID_DESCRIPTION_CHARACTERS: (
        "Description contains <, >, or double quote characters."
    ),
    IssueType.DESCRIPTION_TOO_LONG: (
        "Description is {length} chars; max is {max_len}."
    ),
    IssueType.NESTED_SKILL_MD: "Nested SKILL.md files found: {paths}",
    IssueType.INVALID_PLACEMENT: (
        "SKILL.md is directly under a category; expected category/skill/SKILL.md."
    ),
    IssueType.TOO_DEEP: (
        "SKILL.md is nested deeper than category/skill/SKILL.md."
    ),
    IssueType.DUPLICATE_SKILL_NAME: "Skill name '{name}' appears in: {paths}.",
    IssueType.DUPLICATE_DESCRIPTION: "Identical description appears in: {paths}.",
    IssueType.MISSING_CATEGORY_DESCRIPTION: "DESCRIPTION.md is missing.",
    IssueType.EMPTY_CATEGORY_DESCRIPTION: "DESCRIPTION.md has no description.",
    IssueType.EMPTY_CATEGORY: "Category has no skills.",
}


@dataclass(frozen=True)
class Rule:
    """One named rule from the executable SSOT.

    ``message`` is the verbatim template ``validate`` emits for ``issue``;
    ``check`` is a short human label for ``--markdown`` rendering (PR-3).
    """

    issue: IssueType
    message: str
    check: str


#: The typed Rule/IssueType taxonomy: one Rule per IssueType, message
#: templates lifted verbatim from ``librarian.py`` (see line numbers in
#: ``ISSUE_MESSAGES`` docstring above).
RULES: Final = tuple(Rule(t, ISSUE_MESSAGES[t], t.value.replace("-", " ")) for t in IssueType)


def is_valid_skill_name(name: str) -> bool:
    """The name-format predicate the validator applies to directory names.

    Verbatim compound condition from ``librarian.py``: ``NAME_RE`` match AND
    no double hyphen AND 2-64 chars.
    """
    return bool(NAME_RE.match(name)) and "--" not in name and NAME_MIN <= len(name) <= NAME_MAX


def issue_message(issue_type: IssueType, **fields: Any) -> str:
    """Render the verbatim message for an issue type with the given fields."""
    return ISSUE_MESSAGES[issue_type].format(**fields)


__all__ = [
    "CATEGORY_DESCRIPTION_FILENAME",
    "IGNORED_CATEGORY_DIRS",
    "ISSUE_MESSAGES",
    "MAX_DESCRIPTION_LEN",
    "NAME_MAX",
    "NAME_MIN",
    "NAME_RE",
    "RULES",
    "IssueType",
    "Rule",
    "clean_one_line",
    "is_valid_skill_name",
    "issue_message",
    "md_escape",
]
