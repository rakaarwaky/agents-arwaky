"""SSOT for skill-library validation rules (AES taxonomy layer).

The single executable source of truth for what a valid skill is: the
budget / layout constants, the escape helpers' rule text, the layout
invariants, and the issue taxonomy — the 13 issue-type strings plus the
exact message strings ``validate`` emits.

Lifted verbatim from ``librarian.py``. Nothing in this module
is re-derivable from elsewhere: every consumer (the validator
capability and the skill-rules reference doc) must read these constants
rather than restate them.
"""

from __future__ import annotations

import re
from typing import Final

# Verbatim from ``librarian.py``.
MAX_DESCRIPTION_LEN: Final = 1024

# ─── Naming budget ─────────────────────────────────────────────────────

#: Naming budget. ``is_valid_skill_name`` in
#: ``taxonomy_skills_vo.py`` consumes these.
NAME_MIN: Final = 2
NAME_MAX: Final = 64
NAME_RE: Final = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")

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

#: The loud drift warning: the catalog failed its drift gate, so the
#: answer comes from a live tree scan. Named repair: ``catalog --check``.
DRIFT_WARNING: Final = (
    "WARNING: catalog drift detected — answering from a live tree scan. "
    "Run `catalog --check` to repair catalog.json."
)

#: The catalog file name (tracked artifact name).
CATALOG_FILENAME: Final = "catalog.json"

# ── Discovery scoring ────────────────────────────────────────────────

#: Score scale factor: float BM25F score * scale → int legacy projection.
#: Lived in ``capabilities_skills_discover`` (AES403 CapabilityLocalConstant:
#: module-level constants in capability files are flagged); taxonomy is the
#: SSOT home for shared numeric constants.
BM25F_SCORE_SCALE: Final = 100

# ── Rule documentation ───────────────────────────────────────────────

#: One-line summaries for the skill-rules reference doc headings.
#: Short imperatives; the full constraint text is the verbatim
#: ``ISSUE_MESSAGES`` template in ``taxonomy_skills_vo.py``.
SUMMARIES: Final = {
    "name-mismatch": "Frontmatter `name:` equals the skill directory name",
    "name-format": "Skill names are lowercase letters, digits, and hyphens",
    "description-present": "Every skill carries a `description:`",
    "description-characters": "Descriptions contain no `<`, `>`, or `\"`",
    "description-length": "Descriptions are at most 1024 characters",
    "skill-placement": "`SKILL.md` lives at `<category>/<skill>/SKILL.md`",
    "category-depth": "No nesting deeper than `<category>/<skill>/`",
    "unique-skill-name": "Each skill name is used by one folder only",
    "unique-description": "No two skills share one description",
    "category-description-present": "Every category has a `DESCRIPTION.md`",
    "category-description-nonempty": "Category `DESCRIPTION.md` describes the category",
    "category-nonempty": "Every category holds at least one skill",
    "references-linked": "Every file in `references/` is linked from `SKILL.md`",
}

#: Loader citations: the file each constraint was first read from. Empty
#: where no real citation exists — provenance that cannot be traced to a
#: source is left to the skill-rules reference doc to discuss, never invented here.
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
    "references-linked": (
        "`SKILL.md` body or Routing table must name every `references/` file"
    ),
}

# ── Lifecycle ────────────────────────────────────────────────────────

#: Lifecycle states a skill can hold.
LIFECYCLE_STATES: Final = ("active", "stale", "archived")

#: Lifecycle config file name, read from the pack root.
CONFIG_FILENAME: Final = ".lifecycle_config.json"

__all__ = [
    "ARCHIVE_DIRNAME",
    "ASSETS_MARKER_FILENAME",
    "BM25F_SCORE_SCALE",
    "CATALOG_FILENAME",
    "CATEGORY_DESCRIPTION_FILENAME",
    "CITATIONS",
    "CONFIG_FILENAME",
    "DRIFT_WARNING",
    "IGNORED_CATEGORY_DIRS",
    "LIFECYCLE_STATES",
    "MAX_DESCRIPTION_LEN",
    "NAME_MAX",
    "NAME_MIN",
    "NAME_RE",
    "PACK_MARKER_FILENAME",
    "SUMMARIES",
]
