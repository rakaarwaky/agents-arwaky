"""SSOT for skill-library validation rules (AES taxonomy layer).

The single executable source of truth for what a valid skill is: the
naming / budget / layout constants, the escape helpers' rule text, the
layout invariants, and the issue taxonomy — the 13 issue-type strings
plus the exact message strings ``validate`` emits.

Lifted verbatim from ``skills/skill-authoring/_rules/skill_rules.py``
(which itself was lifted from ``librarian.py``). Nothing in this module
is re-derivable from elsewhere: every consumer (the validator
capability, the rules renderer, and the generated
``_rules/skill-rules.md``) must read these constants rather than
restate them. ``Rule`` is the published shape — ``id``, ``level``,
``summary``, ``detail_md`` (the verbatim message template), ``why``
(loader citation) — and ``rule(rule_id)`` is the lookup both the
checkers and the docs generator read through.

``IssueType``/``Level``/``Rule`` are defined here rather than in
``taxonomy_skills_vo`` because ``RULES`` is a compile-time constant
table keyed by them; ``taxonomy_skills_vo`` re-exports every symbol so
consumers can import the published shape from either module. This keeps
the taxonomy dependency acyclic (constant imports nothing).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

# ── Naming budget ─────────────────────────────────────────────────────

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

# ── Layout invariants ─────────────────────────────────────────────────

#: Category description file name, verbatim from ``librarian.py``.
CATEGORY_DESCRIPTION_FILENAME: Final = "DESCRIPTION.md"

#: Category directories the walker skips, verbatim from ``librarian.py``.
IGNORED_CATEGORY_DIRS: Final = frozenset(
    {".git", ".hg", ".svn", "__pycache__", "_archive"}
)

#: Archive directory the ``archive`` mutation moves skills into; the
#: walker skips it (it is in ``IGNORED_CATEGORY_DIRS``).
ARCHIVE_DIRNAME: Final = "_archive"

# ── DM1 / DM2 markers ────────────────────────────────────────────────

#: The DM2 asset-container marker file. A category directory that carries
#: it (with frontmatter ``kind: assets``) declares itself a cross-skill
#: asset container, not a category of skills: ``validate`` and the weed
#: report skip its ``empty-category`` / ``missing-category-description``
#: checks. Declared file, not a directory-name heuristic.
ASSETS_MARKER_FILENAME: Final = "ASSETS.md"

#: The DM1 nested-pack marker file. A subdirectory of a category that
#: holds its own ``SKILL.md`` files one level deeper than the loader's
#: two-level walk declares itself a nested pack by carrying this marker:
#: ``validate`` skips the ``too-deep`` error for those files. Opt-in
#: only — without the marker, depth violations are unchanged.
PACK_MARKER_FILENAME: Final = "pack.toml"

# ── Issue taxonomy ─────────────────────────────────────────────────────

#: Exactly the 13 strings ``librarian.py`` ``validate_library`` emits.
#: The ``validate`` command must keep emitting these verbatim, so they
#: live here, not in two places.
class IssueType(str, Enum):
    """The closed set of validation issue types."""

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


#: Rule IDs are stable identifiers the skill bodies and the generated
#: ``skill-rules.md`` link against; only the member order of this mapping
#: defines the doc's section order.
RULE_IDS: Final = {
    "name-mismatch": IssueType.NAME_MISMATCH,
    "name-format": IssueType.INVALID_SKILL_NAME,
    "description-present": IssueType.MISSING_DESCRIPTION,
    "description-characters": IssueType.INVALID_DESCRIPTION_CHARACTERS,
    "description-length": IssueType.DESCRIPTION_TOO_LONG,
    "skill-md-nesting": IssueType.NESTED_SKILL_MD,
    "skill-placement": IssueType.INVALID_PLACEMENT,
    "category-depth": IssueType.TOO_DEEP,
    "unique-skill-name": IssueType.DUPLICATE_SKILL_NAME,
    "unique-description": IssueType.DUPLICATE_DESCRIPTION,
    "category-description-present": IssueType.MISSING_CATEGORY_DESCRIPTION,
    "category-description-nonempty": IssueType.EMPTY_CATEGORY_DESCRIPTION,
    "category-nonempty": IssueType.EMPTY_CATEGORY,
}

#: One-line summaries for ``aa skills rules`` and the generated doc headings.
#: Short imperatives; the full constraint text is the verbatim
#: ``ISSUE_MESSAGES`` template below.
SUMMARIES: Final = {
    "name-mismatch": "Frontmatter `name:` equals the skill directory name",
    "name-format": "Skill names are lowercase letters, digits, and hyphens",
    "description-present": "Every skill carries a `description:`",
    "description-characters": "Descriptions contain no `<`, `>`, or `\"`",
    "description-length": "Descriptions are at most 1024 characters",
    "skill-md-nesting": "A skill directory holds exactly one `SKILL.md`",
    "skill-placement": "`SKILL.md` lives at `<category>/<skill>/SKILL.md`",
    "category-depth": "No nesting deeper than `<category>/<skill>/`",
    "unique-skill-name": "Each skill name is used by one folder only",
    "unique-description": "No two skills share one description",
    "category-description-present": "Every category has a `DESCRIPTION.md`",
    "category-description-nonempty": "Category `DESCRIPTION.md` describes the category",
    "category-nonempty": "Every category holds at least one skill",
}

#: Loader citations: the file each constraint was first read from. Empty
#: where no real citation exists — provenance that cannot be traced to a
#: source is left to ``_rules/RULES.md`` to discuss, never invented here.
CITATIONS: Final = {
    "name-mismatch": "`create-skills/SKILL.md` (name must equal the directory)",
    "name-format": (
        "`create-skills/SKILL.md` and `create-skills/references/"
        "validation-criteria.md` (both stated the name alphabet)"
    ),
    "description-present": "`create-skills/SKILL.md` (required frontmatter shape)",
    "description-characters": (
        "`create-skills/SKILL.md` (Grok Build embeds the value in "
        "`<skill description=\"...\">`)"
    ),
    "description-length": (
        "`create-skills/SKILL.md` and `validation-criteria.md` "
        "(both stated the 1,024-char ceiling)"
    ),
    "skill-md-nesting": (
        "`create-skills/SKILL.md` (structure section: nested `SKILL.md` "
        "is rejected on upload)"
    ),
    "skill-placement": (
        "`create-skills/SKILL.md` (placement rule) and "
        "`skill-librarian/references/category-rules.md` (folder shape)"
    ),
    "category-depth": (
        "`create-skills/SKILL.md` (loaders walk one level) and "
        "`category-rules.md` (no nested subcategories)"
    ),
    "unique-skill-name": "",
    "unique-description": "",
    "category-description-present": (
        "`skill-librarian/references/category-rules.md` (DESCRIPTION.md section)"
    ),
    "category-description-nonempty": (
        "`skill-librarian/references/category-rules.md` "
        "(the description decides where skills belong)"
    ),
    "category-nonempty": "",
}

#: Verbatim message templates. Fields are exactly the ones
#: ``librarian.py`` interpolates; ``{}`` are bound by keyword by the same
#: callsite shape as the original code so messages stay byte-identical.
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


#: Severity of a rule. Every check the validator performs today fails the
#: skill outright, so all 13 rules are ERROR; the WARN level exists for
#: future soft rules and is part of the published interface so the docs
#: renderer does not need to change when the first soft rule lands.
class Level(str, Enum):
    """Rule severity."""

    ERROR = "error"
    WARN = "warn"


@dataclass(frozen=True)
class Rule:
    """One named constraint from the executable SSOT.

    ``id`` is the kebab-case identifier the rest of the pack links to
    (``rule("name-format")`` is how ``validate`` and the docs generator
    both read the detail); ``level`` is the severity; ``summary`` is the
    one-line form shown by ``aa skills rules``; ``detail_md`` is the
    verbatim message template the validator emits, so the generated
    ``skill-rules.md`` cannot disagree with the executable rule;
    ``why`` is the loader citation (empty when no real citation exists).
    """

    id: str
    issue: IssueType
    level: Level
    summary: str
    detail_md: str
    why: str


#: The typed Rule/IssueType taxonomy: one Rule per IssueType. ``detail_md``
#: is the verbatim template from ``ISSUE_MESSAGES`` (the two maps can never
#: diverge: ``issue_message`` and the docs renderer both read it through
#: here), and ``why`` cites the loader file each constraint was first read
#: from. Rules whose constraint was inferred from the validator's own
#: behavior rather than from a written source carry an empty ``why``
#: rather than an invented citation.
RULES: Final = tuple(
    Rule(
        id=rule_id,
        issue=issue_type,
        level=Level.ERROR,
        summary=SUMMARIES[rule_id],
        detail_md=ISSUE_MESSAGES[issue_type],
        why=CITATIONS[rule_id],
    )
    for rule_id, issue_type in RULE_IDS.items()
)

_RULES_BY_ID: Final = {r.id: r for r in RULES}

#: The issue types ``validate --rules-only`` keeps. The other checks
#: (duplicate names/descriptions, category emptiness) are library hygiene
#: rather than per-rule frontmatter constraints, so the flag filters them
#: out without changing which issues are found.
RULE_ONLY_ISSUE_TYPES: Final = frozenset(
    {
        IssueType.INVALID_SKILL_NAME.value,
        IssueType.NAME_MISMATCH.value,
        IssueType.MISSING_DESCRIPTION.value,
        IssueType.INVALID_DESCRIPTION_CHARACTERS.value,
        IssueType.DESCRIPTION_TOO_LONG.value,
        IssueType.NESTED_SKILL_MD.value,
        IssueType.INVALID_PLACEMENT.value,
        IssueType.TOO_DEEP.value,
        IssueType.MISSING_CATEGORY_DESCRIPTION.value,
        IssueType.EMPTY_CATEGORY_DESCRIPTION.value,
    }
)


def rule(rule_id: str) -> Rule:
    """The lookup: ``rule("name-format").detail_md`` is the message
    ``validate`` emits. A typo'd id fails loudly (KeyError) rather than
    silently falling back to a generic message."""
    return _RULES_BY_ID[rule_id]


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
    "ARCHIVE_DIRNAME",
    "ASSETS_MARKER_FILENAME",
    "CATEGORY_DESCRIPTION_FILENAME",
    "CITATIONS",
    "IGNORED_CATEGORY_DIRS",
    "ISSUE_MESSAGES",
    "MAX_DESCRIPTION_LEN",
    "NAME_MAX",
    "NAME_MIN",
    "NAME_RE",
    "PACK_MARKER_FILENAME",
    "RULES",
    "RULE_IDS",
    "RULE_ONLY_ISSUE_TYPES",
    "SUMMARIES",
    "IssueType",
    "Level",
    "Rule",
    "is_valid_skill_name",
    "issue_message",
    "rule",
]
