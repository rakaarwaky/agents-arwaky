"""Skill-update source discovery and pack merge (utility layer).

Pure helpers shared by the update capability (``SkillUpdateCapability``) and
the skill surface (``cmd_update``). Kept out of the capability so the surface
reaches discovery through the utility layer rather than importing a capability
(AES201).

Discovery is manifest-driven: every tool with ``category == "internal"`` is
probed at the language-layout skill homes, then the legacy ``.agents/skills/``.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    REPO_ROOT,
    SKILL_FILE,
    UPDATE_PROVENANCE_FILE,
    UPDATE_PROVENANCE_VERSION,
)
from modules.shared.src.taxonomy_common_vo import (
    PackFinding,
    Tool,
    skill_description,
    skill_name,
    utc_now_iso,
)
from modules.shared.src.taxonomy_skill_vo import sanitize_skill_name
from modules.shared.src.taxonomy_skill_update_vo import SourceSkillEntry

#: Manifest is the discovery driver; read it directly so a utility file never
#: imports another utility (AES201).
_MANIFEST = REPO_ROOT / "config" / "manifest.json"

#: Skill homes probed in order; the language layout folder wins over the legacy
#: ``.agents/skills/`` copy-nest, so a repo that has been refactored is read from
#: its canonical location.
SKILL_HOMES = (
    "crates/skills",
    "modules/skills",
    "packages/skills",
    ".agents/skills",
)

#: Pack category a brand-new skill from an internal tool lands in.
DEFAULT_INTERNAL_CATEGORY = "internal-tools"

#: Source-repo skill homes that map onto a specific existing pack category, so a
#: new upstream home never relocates skills a harness has already registered.
CATEGORY_OVERRIDES = {"crates/skills": "aes-architecture"}

#: Companion dirs copied next to a SKILL.md so relative links survive the merge.
_ASSET_DIRS = ("scripts", "references", "resources", "examples", "templates", "assets")

#: Finder-style duplicate folders: ``Foo copy`` and ``Foo copy 2``.
_COPY_SUFFIX = re.compile(r"\s+copy(\s+\d+)?$")

#: Files the pack adds to a merged skill, ignored when comparing it to its source
#: so a repeated update reports "already current" rather than re-merging.
_PACK_ONLY_FILES = (UPDATE_PROVENANCE_FILE,)


def skill_home(tool_path: Path) -> Path | None:
    """The first existing skill home under *tool_path*, or None when absent."""
    for relative in SKILL_HOMES:
        candidate = tool_path / relative
        if candidate.is_dir():
            return candidate
    return None


def iter_source_skill_dirs(home: Path, owned_names: frozenset[str] = frozenset()) -> list[Path]:
    """Skill directories directly under *home*, filtered by ownership.

    Finder-style duplicates (``Foo copy`` / ``Foo copy 2``) are skipped at
    discovery: their frontmatter still declares the original ``name:``, so a
    name-keyed merge would otherwise pick a stale duplicate over the real skill.

    Args:
        home: The skill home to scan.
        owned_names: When non-empty, only a directory whose frontmatter ``name:``
            is in this set is a source. The legacy ``.agents/skills/`` fallback
            passes the tool id and aliases, because that subtree is a *provisioned
            copy of the pack* — every skill in it is already a pack copy, except
            the tool's own guide.

    Returns:
        Skill directories, in sorted order.
    """
    if not home.is_dir():
        return []
    out: list[Path] = []
    for entry in sorted(home.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if _COPY_SUFFIX.search(entry.name):
            continue
        skill_md = entry / SKILL_FILE
        if not skill_md.is_file():
            continue
        if owned_names and sanitize_skill_name(skill_name(skill_md), entry.name) not in owned_names:
            continue
        out.append(entry)
    return out


def pack_category(
    pack_root: Path, name: str, default: str = DEFAULT_INTERNAL_CATEGORY
) -> str:
    """Category a skill named *name* already occupies in the pack, else *default*.

    Keeping an existing skill where it is means a harness that registered the
    category keeps loading it after the source home is renamed upstream.
    """
    for path in pack_root.glob(f"*/{name}/{SKILL_FILE}"):
        return path.parent.parent.name
    return default


def submodule_head(tool_path: Path) -> str:
    """Short commit SHA of the submodule at *tool_path*, or an empty string."""
    try:
        result = subprocess.run(
            ["git", "-C", str(tool_path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _load_manifest_tools() -> list[dict]:
    """Raw tool entries from config/manifest.json, in manifest order."""
    if not _MANIFEST.is_file():
        return []
    try:
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [t for t in data.get("tools", []) if isinstance(t, dict)]


def manifest_internal_tools() -> list[Tool]:
    """Manifest entries whose category is ``internal``, in manifest order."""
    return [
        Tool(
            id=str(t.get("id", "")),
            category=str(t.get("category", "")),
            binary=str(t.get("binary", "")),
            is_mcp=bool(t.get("isMcp", False)),
            description=str(t.get("description", "")),
            path=str(t.get("path", "")),
            alias=t.get("alias"),
            aliases=tuple(t.get("aliases") or []),
            mcp_binary=t.get("mcpBinary"),
        )
        for t in _load_manifest_tools()
        if str(t.get("category", "")) == "internal"
    ]


def _owned_names(tool: Tool) -> frozenset[str]:
    """Aliases of *tool* plus its id, lowercased so ``skill_name`` casing matches."""
    ids = {tool.id.lower()}
    if tool.alias:
        ids.add(tool.alias.lower())
    ids.update(a.lower() for a in (tool.aliases or ()))
    return frozenset(ids)


def is_legacy_home(home: Path) -> bool:
    """True when *home* is the ``.agents/skills/`` fallback rather than a layout home.

    A layout home is tool-owned content; the legacy one is a provisioned copy of
    the shared pack, so only the tool's own guide is treated as a source.
    """
    return home.name == "skills" and home.parent.name == ".agents"


def discover_skill_sources(
    pack_root: Path, repo_root: Path, tool_filter: str = ""
) -> list[SourceSkillEntry]:
    """Every skill the internal submodules expose, in manifest order.

    Args:
        pack_root: The shared pack root, consulted for existing categories.
        repo_root: Repository root the manifest ``path`` entries resolve against.
        tool_filter: Restrict discovery to one manifest tool id when non-empty.

    Returns:
        One entry per discoverable skill, each carrying the pack category the
        skill lands in.
    """
    entries: list[SourceSkillEntry] = []
    for tool in manifest_internal_tools():
        tool_id = tool.id
        if tool_filter and tool_id != tool_filter:
            continue
        tool_path = repo_root / tool.path
        if not tool_path.is_dir():
            continue
        home = skill_home(tool_path)
        if home is None:
            continue
        default = CATEGORY_OVERRIDES.get(
            home.relative_to(tool_path).as_posix(), DEFAULT_INTERNAL_CATEGORY
        )
        owned = _owned_names(tool) if is_legacy_home(home) else frozenset()
        for skill_dir in iter_source_skill_dirs(home, owned):
            skill_md = skill_dir / SKILL_FILE
            name = sanitize_skill_name(skill_name(skill_md), skill_dir.name)
            entries.append(SourceSkillEntry(
                tool_id=tool_id,
                source_path=str(skill_md),
                skill_name=name,
                category=pack_category(pack_root, name, default),
                description=skill_description(skill_md),
                relative_source=home.relative_to(tool_path).as_posix(),
            ))
    return entries


def find_pack_dir(pack_root: Path, entry: SourceSkillEntry) -> Path:
    """Where *entry* belongs inside the pack."""
    return pack_root / entry.category / entry.skill_name


def pack_matches_source(dest_dir: Path, src_dir: Path) -> bool:
    """True when the pack copy is byte-identical to its source skill dir.

    The pack adds :data:`UPDATE_PROVENANCE_FILE` after a merge; that file never
    lives in the source and must be ignored so a repeated run reports "already
    current" rather than re-merging.
    """
    for file in src_dir.rglob("*"):
        if file.is_dir() or "__pycache__" in file.parts:
            continue
        peer = dest_dir / file.relative_to(src_dir)
        if not peer.is_file() or peer.read_bytes() != file.read_bytes():
            return False
    return True


def _pack_has_current_provenance(dest_dir: Path, entry: SourceSkillEntry) -> bool:
    """True when the destination dir carries a valid provenance pointing at *entry*.

    This lets the merge re-run without re-copying the source while still
    reporting "unchanged" rather than "merged", keeping the output stable.
    """
    data = read_update_provenance(dest_dir)
    return (
        data.get("update_source") == _recorded_source(entry.source_path)
        and data.get("submodule") == entry.tool_id
    )


def read_update_provenance(dest_dir: Path) -> dict:
    """The update provenance sidecar for a pack skill, or an empty dict."""
    marker = dest_dir / UPDATE_PROVENANCE_FILE
    if not marker.is_file():
        return {}
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _source_priority(relative_source: str) -> int:
    """Preferred rank for a skill home relative path (lower = preferred)."""
    order = {
        "crates/skills": 0,
        "modules/skills": 1,
        "packages/skills": 2,
        ".agents/skills": 3,
    }
    return order.get(relative_source, 99)


def deduplicate_sources(
    entries: list[SourceSkillEntry],
) -> tuple[list[SourceSkillEntry], list[str]]:
    """Collapse multi-source collisions into winners, returning conflicts separately.

    When several internal tools expose the same skill name, the winner is the
    entry whose source home has the highest priority (``crates/skills`` >
    ``modules/skills`` > ``packages/skills`` > ``.agents/skills``). All losers
    are collected as conflicts.
    """
    by_name: dict[str, list[SourceSkillEntry]] = {}
    for entry in entries:
        by_name.setdefault(entry.skill_name, []).append(entry)
    winners: list[SourceSkillEntry] = []
    conflicts: list[str] = []
    for name, group in sorted(by_name.items()):
        if len(group) == 1:
            winners.append(group[0])
        else:
            group.sort(key=lambda e: _source_priority(e.relative_source))
            winners.append(group[0])
            losers = group[1:]
            conflicts.append(
                f"'{name}' exists in {len(group)} source(s): "
                + ", ".join(f"{e.tool_id}({e.relative_source})" for e in group)
            )
    return winners, conflicts


def iter_update_marked(pack_root: Path) -> list[Path]:
    """Pack skill directories carrying an update provenance sidecar."""
    return sorted(
        marker.parent
        for marker in pack_root.glob(f"*/*/{UPDATE_PROVENANCE_FILE}")
    )


def _recorded_source(source_path: str) -> str:
    """Normalize *source_path* to a repo-relative POSIX path for the sidecar.

    An absolute path would pin the record to one machine and one checkout, so
    a second clone or a git worktree would resolve the recorded source to a
    different (or missing) file and report false drift. Recording the path
    relative to :data:`REPO_ROOT` keeps the sidecar portable; the reader joins
    it back against the repo it is running in.
    """
    try:
        return Path(source_path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return source_path


def write_update_provenance(dest_dir: Path, entry: SourceSkillEntry) -> None:
    """Record which submodule a pack skill was pulled from.

    A different file from :data:`PROVENANCE_FILE` on purpose: that marker
    separates our provisioned copies from hand-written skills so a target
    workspace's ``--prune`` can act on them, while this one records upstream
    provenance. The two are independent, so a pack skill can carry both.
    """
    payload = {
        "version": UPDATE_PROVENANCE_VERSION,
        "update_source": _recorded_source(entry.source_path),
        "submodule": entry.tool_id,
        "submodule_home": entry.relative_source,
        "skill": entry.skill_name,
        "updated_at": utc_now_iso(),
    }
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / UPDATE_PROVENANCE_FILE).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def merge_skill_into_pack(
    entry: SourceSkillEntry, pack_root: Path, force: bool = False
) -> str:
    """Copy one submodule skill into the pack and stamp its provenance.

    Returns:
        ``"merged"`` when the pack copy was written, ``"unchanged"`` when it
        already matched the source, ``"conflict"`` when the bytes differ and
        *force* is off, and ``"error"`` when the copy failed.
    """
    src_md = Path(entry.source_path)
    if not src_md.is_file():
        return "error"
    src_dir = src_md.parent
    dest_dir = find_pack_dir(pack_root, entry)
    if dest_dir.is_dir() and _pack_has_current_provenance(dest_dir, entry):
        # Provenance points here but content may have drifted by hand; still
        # compare bytes so a manual edit surfaces as a conflict.
        if pack_matches_source(dest_dir, src_dir):
            return "unchanged"
        if not force:
            return "conflict"
    elif not force and dest_dir.is_dir() and not pack_matches_source(dest_dir, src_dir):
        return "conflict"
    try:
        for extra in _ASSET_DIRS:
            shutil.rmtree(dest_dir / extra, ignore_errors=True)
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_md, dest_dir / SKILL_FILE)
        for extra in _ASSET_DIRS:
            source = src_dir / extra
            if source.is_dir():
                shutil.copytree(source, dest_dir / extra)
    except OSError:
        return "error"
    write_update_provenance(dest_dir, entry)
    return "merged"


def _resolve_source(recorded: str, pack_root: Path) -> Path:
    """Join a repo-relative recorded source back to the repo it runs in.

    ``write_update_provenance`` stores :data:`update_source` as a
    ``REPO_ROOT``-relative POSIX path so the sidecar survives re-clones and
    git worktrees. ``audit_update_drift`` runs from a checkout whose own
    :data:`REPO_ROOT` may differ from the one that wrote the record, so the
    path is re-anchored to the *current* :data:`REPO_ROOT` before the
    byte comparison.
    """
    p = Path(recorded)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def audit_update_drift(
    pack_root: Path, sources: list[SourceSkillEntry]
) -> list[PackFinding]:
    """Report where the pack has drifted from the internal submodule sources.

    Both directions matter: a pack skill whose recorded source no longer matches
    on disk, and a submodule skill with no pack entry at all. Either way the
    pack is stale relative to the internal modules.
    """
    findings: list[PackFinding] = []
    for skill_dir in iter_update_marked(pack_root):
        data = read_update_provenance(skill_dir)
        recorded = str(data.get("update_source", ""))
        skill = str(data.get("skill", skill_dir.name))
        if not recorded:
            continue
        src_md = _resolve_source(recorded, pack_root)
        dest_md = skill_dir / SKILL_FILE
        if not src_md.is_file():
            findings.append(PackFinding(
                "update-source-missing",
                f"{skill} records update source {recorded}, which no longer exists",
                str(skill_dir.relative_to(pack_root)),
            ))
        elif not dest_md.is_file() or dest_md.read_bytes() != src_md.read_bytes():
            findings.append(PackFinding(
                "update-drift",
                f"{skill} differs from its update source {recorded}; "
                "run 'aa skill update --force'",
                str(skill_dir.relative_to(pack_root)),
            ))
    for entry in sorted(sources, key=lambda e: e.skill_name):
        dest_dir = find_pack_dir(pack_root, entry)
        if not (dest_dir / SKILL_FILE).is_file():
            findings.append(PackFinding(
                "update-missing",
                f"{entry.skill_name} exists in {entry.tool_id} but has no pack copy; "
                "run 'aa skill update'",
                entry.skill_name,
            ))
    return findings


__all__ = [
    "CATEGORY_OVERRIDES",
    "DEFAULT_INTERNAL_CATEGORY",
    "SKILL_HOMES",
    "audit_update_drift",
    "deduplicate_sources",
    "discover_skill_sources",
    "find_pack_dir",
    "iter_source_skill_dirs",
    "iter_update_marked",
    "manifest_internal_tools",
    "merge_skill_into_pack",
    "pack_category",
    "pack_matches_source",
    "read_update_provenance",
    "skill_home",
    "submodule_head",
    "write_update_provenance",
]
