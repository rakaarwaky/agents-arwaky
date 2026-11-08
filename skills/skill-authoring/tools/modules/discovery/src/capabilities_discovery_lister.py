"""Skills lister capability (AES capabilities layer).

Implements ``ISkillsListerProtocol``: read-only listing of the skill pack,
sorted by name, plus the global-skill JSON list seam. The pack-walking
helpers live in ``utility_skill_pack`` (shared kernel), so this capability
depends on contract + taxonomy + utility only — never on a sibling.
"""
from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_common_vo import (
    SkillContent,
    SkillRecord,
    SkillsJsonPayload,
)
from shared.src.discovery.contract_discovery_protocol import ISkillsListerProtocol
from shared.src.discovery.taxonomy_discovery_request import DiscoveryRoot
from shared.src.storage.utility_skill_pack import (
    default_pack_root,
    iter_skill_mds,
    parse_skill_frontmatter,
)

__all__ = ["SkillsLister", "default_pack_root"]

# ─── Block 1: Module Declaration ──────────────
class SkillsLister(ISkillsListerProtocol):
    """Read-only listing of the skill pack, sorted by name."""

    def __init__(self, pack_root: Path | None = None) -> None:
        self._root = pack_root or default_pack_root()

    # ─── Block 2: Module Contract ─────────────

    def list_skills(self, root: DiscoveryRoot | None = None):
        """Return one record per skill, sorted by name.

        ``root`` overrides the capability's construction-time pack root
        (explicit beats derived); ``None`` keeps it.
        """
        pack_root = Path(root) if root is not None else self._root
        records = [
            (parse_skill_frontmatter(md), md) for md in iter_skill_mds(pack_root)
        ]
        out: list[SkillRecord] = []
        for (name, description), md in records:
            out.append(
                SkillRecord(
                    name=name or md.parent.name,
                    description=SkillContent(description) if description else None,
                    path=md,
                )
            )
        out.sort(key=lambda r: r.name)
        return tuple(out)

    def list_skills_json(self, root: DiscoveryRoot | None = None) -> SkillsJsonPayload:
        """Return the global-skill JSON list as a pure-data dict."""
        skills_root = Path(root) if root is not None else self._root
        records = self.list_skills(DiscoveryRoot(skills_root) if root is not None else None)
        return {
            "skills": [
                {
                    "name": record.name,
                    "source": str(self._root),
                    "path": str(record.path),
                    "loaded": True,
                }
                for record in records
            ]
        }

    # ─── Block 3: Module Helpers ───

    def __repr__(self) -> str:
        return "SkillsLister()"
