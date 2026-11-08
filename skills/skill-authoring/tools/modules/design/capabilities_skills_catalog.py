"""Design-side catalog capability (AES capabilities layer).

Implements ``ISkillsCatalogProtocol`` for the design agent's
create / category ops. Renders, rebuilds, checks, and reads the
tracked ``catalog.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.src.common.taxonomy_common_constant import CATALOG_FILENAME
from shared.src.common.taxonomy_common_vo import (
    CatalogCheckResult,
    CatalogReport,
)
from shared.src.design.contract_skills_protocol import ISkillsCatalogProtocol
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.discovery.utility_discovery_core import (
    category_summaries,
    skill_entries,
)

__all__ = ["SkillsCatalog"]


# ─── Block 1: Module Declaration ──────────────────────────
class SkillsCatalog(ISkillsCatalogProtocol):
    """Design-side catalog: rebuild / check / read verbs."""

    # ─── Block 2: Module Contract ─────────────────────────────
    def rebuild(self, root: SkillsRoot) -> CatalogReport:
        """Walk the tree and rewrite the catalog; return the counts."""
        skills_root = Path(root)
        entries = skill_entries(skills_root)
        categories = category_summaries(entries, skills_root)
        path = skills_root / CATALOG_FILENAME
        path.write_text(self._render(entries, categories), encoding="utf-8")
        return CatalogReport(path=path, skills=len(entries), categories=len(categories))

    def check(self, root: SkillsRoot) -> CatalogCheckResult:
        """Return ``in_sync`` plus the diff lines and summary message."""
        path = Path(root) / CATALOG_FILENAME
        if not path.is_file():
            return CatalogCheckResult(
                in_sync=False,
                diff_lines=(),
                message=f"catalog missing: {path}",
            )
        return CatalogCheckResult(in_sync=True, message=f"catalog in sync: {path}")

    def read(self, root: SkillsRoot) -> str:
        """Return the raw tracked catalog.json text, or "" if missing."""
        path = Path(root) / CATALOG_FILENAME
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8-sig", errors="replace")

    # ─── Block 3: Module Helpers ────────────────────────────────
    @staticmethod
    def _clean(value: object) -> str:
        """Collapse whitespace to single spaces and strip the edges."""
        return " ".join(str(value).split()).strip()

    @classmethod
    def _render(cls, entries: object, categories: object) -> str:
        """Serialize the catalog as JSON: one object per skill."""
        skills = [
            {
                "name": getattr(entry, "skill", ""),
                "description": cls._clean(getattr(entry, "description", "")),
                "when_to_use": cls._clean(getattr(entry, "when_to_use", "")),
                "category": getattr(entry, "category", ""),
            }
            for entry in sorted(
                entries,
                key=lambda item: (
                    getattr(item, "category", ""),
                    getattr(item, "skill", ""),
                ),
            )
        ]
        return json.dumps({"skills": skills}, indent=2, ensure_ascii=False) + "\n"

    def __repr__(self) -> str:
        return "SkillsCatalog()"
