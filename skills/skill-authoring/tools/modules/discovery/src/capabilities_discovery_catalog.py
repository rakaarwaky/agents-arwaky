"""Skills catalog capability (AES capabilities layer).

Owns everything that turns the live tree into ``catalog.json``: the JSON
serialization, the reader ``discover`` scores against, and the drift gate
(regenerate to a temporary file and diff the tracked artifact).

Drift contract: the tracked ``catalog.json`` is a checked artifact.
``check`` asserts the round-trip: an emitted catalog whose regenerated
bytes differ from the tracked artifact is hard, fail-closed drift, so an
operator cannot answer from a stale index. The read path is plain — it
hands back the tracked bytes (or ``""`` when the file is absent) and
lets the caller decide how to report it; staleness is ``check``'s job.
"""

from __future__ import annotations

import difflib
import json
import tempfile
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    CATALOG_FILENAME,
)
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.common.taxonomy_common_vo import (
    CatalogCheckResult,
    CatalogReport,
)
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import DiscoveryRoot
from shared.src.discovery.utility_discovery_core import (
    category_summaries,
    skill_entries,
)

__all__ = [
    "SkillsCatalog",
    "catalog_path",
]


# ─── Block 1: Module Declaration ──────────────
class SkillsCatalog(ISkillsCatalogProtocol):
    """Renders, rebuilds, checks, and reads the tracked catalog."""

# ─── Block 2: Module Contract ──────────────
    def rebuild(self, root: DiscoveryRoot) -> CatalogReport:
        """Walk the tree and rewrite the catalog; return the counts."""
        skills_root = Path(root)
        entries = skill_entries(skills_root)
        categories = category_summaries(entries, skills_root)
        path = catalog_path(skills_root)
        write_catalog_json(entries, categories, path)
        # Delete any legacy CATALOG.md so catalog.json is the sole artifact.
        (skills_root / "CATALOG.md").unlink(missing_ok=True)
        return CatalogReport(
            path=path,
            skills=len(entries),
            categories=len(categories),
        )

    def check(self, root: DiscoveryRoot) -> CatalogCheckResult:
        """Regenerate to a temp file and diff against the tracked artifact."""
        skills_root = Path(root)
        path = catalog_path(skills_root)

        if not path.exists():
            return CatalogCheckResult(
                in_sync=False,
                diff_lines=(),
                message=(
                    f"Catalog missing: {path} "
                    "(rebuild with the catalog subcommand)"
                ),
            )

        with tempfile.TemporaryDirectory(prefix="catalog-check-") as tmp:
            candidate = Path(tmp) / CATALOG_FILENAME
            entries = skill_entries(skills_root)
            categories = category_summaries(entries, skills_root)
            write_catalog_json(entries, categories, candidate)
            current = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            regenerated = candidate.read_text(encoding="utf-8-sig", errors="replace").splitlines()

        diff_lines = list(
            difflib.unified_diff(
                current,
                regenerated,
                fromfile=str(path),
                tofile=f"regenerated ({path})",
                lineterm="",
            )
        )

        if diff_lines:
            message = (
                f"Catalog drift detected: {path} does not match the live tree "
                f"({len(diff_lines)} diff line(s)); rebuild with the catalog subcommand"
            )
            return CatalogCheckResult(
                in_sync=False, diff_lines=tuple(diff_lines), message=message
            )

        return CatalogCheckResult(
            in_sync=True,
            diff_lines=(),
            message=f"Catalog in sync: {path}",
        )

    def read(self, root: DiscoveryRoot) -> str:
        """Return the raw tracked ``catalog.json`` text; ``""`` when missing."""
        path = catalog_path(Path(root))
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8-sig", errors="replace")

    def __repr__(self) -> str:
        return "SkillsCatalog()"


# ─── Block 3: Module Helpers ──────────────


def catalog_path(skills_root: Path) -> Path:
    """The catalog file for a skills root."""
    return skills_root / CATALOG_FILENAME


def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges.

    Catalog-local single-consumer string mechanic.
    """
    return " ".join(str(value).split()).strip()


def render_catalog_json(
    entries: list[SkillEntry],
    categories: list[CategorySummary],
) -> str:
    """Serialize the catalog as JSON: one object per skill with name,
    description, when_to_use, and category.

    ``categories`` is accepted for signature parity with the legacy
    markdown renderer but carries no weight in the JSON shape (categories
    are implicit in each skill's ``category`` field).
    """
    skills = [
        {
            "name": entry.skill,
            "description": clean_one_line(entry.description),
            "when_to_use": clean_one_line(entry.when_to_use),
            "category": entry.category,
        }
        for entry in sorted(entries, key=lambda item: (item.category, item.skill))
    ]
    return json.dumps({"skills": skills}, indent=2, ensure_ascii=False) + "\n"


def write_catalog_json(
    entries: list[SkillEntry],
    categories: list[CategorySummary],
    path: Path,
) -> None:
    """Write the JSON catalog to ``path`` (trailing newline included)."""
    path.write_text(
        render_catalog_json(entries, categories), encoding="utf-8"
    )
