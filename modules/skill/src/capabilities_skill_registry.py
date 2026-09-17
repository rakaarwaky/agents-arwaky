"""Skill registry capability — tool id/alias resolution (port of skill/skill.py)."""
from __future__ import annotations

import functools

import json

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill.taxonomy_skill_vo import SkillInfo

_ALIASES = {
    "lint": "lint", "lint-arwaky": "lint", "la": "lint", "lac": "lint",
    "9router": "9router",
    "ponytail": "ponytail", "ponytail-mcp": "ponytail",
    "context7": "context7", "context7-mcp": "context7",
    "codegraph": "codegraph", "codegraph-mcp": "codegraph",
    "anytype": "anytype", "anytype-mcp": "anytype", "anytype-daemon": "anytype",
    "fetch": "fetch", "fetch-mcp": "fetch",
    "vision": "vision", "vision-arwaky": "vision", "va": "vision",
    "qwen-web": "qwen-web", "qwen-web-arwaky": "qwen-web", "qwa": "qwen-web", "qwc": "qwen-web",
    "blender": "blender", "blender-arwaky": "blender", "ba": "blender",
    "skill": "skill", "skills": "skill", "skill-manager": "skill",
    "workspace": "workspace", "workspace-mcp": "workspace", "google-workspace": "workspace",
    "mnemosyne": "mnemosyne", "mnemosyne-memory": "mnemosyne", "mnemosyne-mcp": "mnemosyne",
}


class SkillRegistry:
    """Tool registry: registered tool ids + alias normalization.

    # Block 1: Constructor (manifest location)
    # Block 2: Registration reads
    # Block 3: Alias normalization
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self) -> None:
        self._manifest = repo_root() / "tools/config/manifest.json"

    # -- Block 2: Registration reads ----------------------------------------------
    def get_registered_tool_ids(self) -> list[SkillInfo]:
        """(tool_id, category, description) rows from the manifest."""
        if not self._manifest.exists():
            return []
        try:
            data = json.loads(self._manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return [
            SkillInfo(t.get("id", ""), t.get("category", ""), t.get("description", ""))
            for t in data.get("tools", [])
        ]

    def manifest_tools(self) -> list[dict[str, object]]:
        """Raw tool entries from the manifest, in manifest order."""
        if not self._manifest.exists():
            return []
        try:
            data = json.loads(self._manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return [t for t in data.get("tools", []) if isinstance(t, dict)]

    # -- Block 3: Alias normalization ------------------------------------------------
    def normalize_tool_id(self, query: str) -> str | None:
        """Resolve alias -> canonical tool id; None when unknown."""
        if query in _ALIASES:
            return _ALIASES[query]
        for info in self.get_registered_tool_ids():
            if query == info.tool_id:
                return info.tool_id
        return None


# --- module-level API (kept for test/CLI compatibility) ----------------------
REPO_ROOT = repo_root()
PACK_ROOT = REPO_ROOT / "skills"


@functools.lru_cache(maxsize=1)
def _get_all_skills() -> tuple[Path, ...]:
    """All SKILL.md files under the pack, cached per process."""
    return tuple(sorted(PACK_ROOT.rglob("SKILL.md")) if PACK_ROOT.is_dir() else ())


def provision_single_skill(
    src_md: Path,
    ws: Path,
    link: bool = False,
) -> bool:
    """Provision one skill into a project's .agents/skills/ dir."""
    from modules.harness.src.capabilities_harness_shared import (
        provision_skill_to_dir,
    )
    from modules.shared.src.skill_pack.capabilities_skill_pack import (
        write_provenance,
    )
    dest_base = ws / ".agents" / "skills"
    ok = provision_skill_to_dir(src_md, dest_base, link=link)
    if ok and not link:
        try:
            skill_name = src_md.parent.name
            dest_dir = dest_base / skill_name
            write_provenance(dest_dir, src_md, PACK_ROOT)
        except (OSError, ValueError):
            pass
    return ok


def remove_single_skill(src_md: Path, ws: Path) -> bool:
    """Remove one skill from a project's .agents/skills/ dir."""
    import shutil
    from modules.shared.src.skill_names.utility_skill_names import safe_skill_name
    name = safe_skill_name(src_md)
    dest = ws / ".agents" / "skills" / name
    if not name or not dest.exists():
        return False
    if dest.is_symlink():
        dest.unlink()
        return True
    shutil.rmtree(dest)
    return True


def resolve_tool_skills(tool: dict) -> list[Path]:
    """Return skill files whose handle matches the tool id or alias."""
    tool_id = tool.get("id", "")
    alias = tool.get("alias", "")
    hits = []
    for sf in _get_all_skills():
        name = sf.parent.name
        if name == tool_id or name == alias:
            hits.append(sf)
        # Also match <tool>-arwaky and <tool> patterns
        if name.startswith(f"{tool_id}-") or name == f"{tool_id}":
            if sf not in hits:
                hits.append(sf)
    return hits
