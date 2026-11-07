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
#: ``taxonomy_skills_rule_vo.py`` consumes these.
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

__all__ = [
    "ARCHIVE_DIRNAME",
    "ASSETS_MARKER_FILENAME",
    "CATALOG_FILENAME",
    "CATEGORY_DESCRIPTION_FILENAME",
    "DRIFT_WARNING",
    "IGNORED_CATEGORY_DIRS",
    "MAX_DESCRIPTION_LEN",
    "NAME_MAX",
    "NAME_MIN",
    "NAME_RE",
    "PACK_MARKER_FILENAME",
]
