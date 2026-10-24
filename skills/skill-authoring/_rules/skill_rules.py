"""Deprecated shim: the rule SSOT now lives in the shared kernel.

``modules/shared/src/skills/taxonomy_skills_constant.py`` is the single
executable source of truth. This module re-exports it so in-pack imports
keep resolving during the shim window; it will be deleted with the
``scripts/`` directory once the shim has shipped for a release.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from modules.shared.src.skills.taxonomy_skills_constant import *  # noqa: F403
from modules.shared.src.utility_skills_markdown import (  # noqa: F401
    clean_one_line,
    md_escape,
    md_unescape,
    yaml_quote,
)
from modules.shared.src.skills.taxonomy_skills_constant import (  # noqa: F401
    ARCHIVE_DIRNAME,
    ASSETS_MARKER_FILENAME,
    CATEGORY_DESCRIPTION_FILENAME,
    CITATIONS,
    IGNORED_CATEGORY_DIRS,
    ISSUE_MESSAGES,
    MAX_DESCRIPTION_LEN,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
    PACK_MARKER_FILENAME,
    RULES,
    RULE_IDS,
    RULE_ONLY_ISSUE_TYPES,
    SUMMARIES,
    IssueType,
    Level,
    Rule,
    is_valid_skill_name,
    issue_message,
    rule,
)
