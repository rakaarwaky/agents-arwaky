"""Skill-pack pure helpers — manifest lookups, discovery, provision/remove (utility).

Stateless helpers shared by the skill capability (`SkillRegistry` /
`SkillPackProvisioner`) and the skill surface (`surface_skill_command`).
Extracted from `capabilities_skill_registry` so surface no longer imports
capabilities (AES201 surface rule). Also hosts provenance write / prune
(originally `utility_skill_pack`) so utility files never import each other.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import (
    PROVENANCE_FILE,
    PROVENANCE_VERSION,
    REPO_ROOT,
)
from modules.shared.src.taxonomy_skill_vo import (
    ensure_under,
    safe_child,
    safe_skill_name,
)

MANIFEST = REPO_ROOT / "config" / "manifest.json"
PACK_ROOT = REPO_ROOT / "skills"
# Companion dirs linked from SKILL.md; keep in sync with harness _ASSET_DIRS
# so relative references/ (etc.) resolve after project provisioning.
_ASSET_DIRS = ("scripts", "references", "resources", "examples", "templates", "assets")


def get_registered_tool_ids():
    """Return list of (tool_id, category, description) from manifest."""
    if not MANIFEST.exists():
        return []
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for t in data.get("tools", []):
        out.append((t.get("id", ""), t.get("category", ""), t.get("description", "")))
    return out


def normalize_tool_id(query):
    """Resolve alias -> canonical tool id. Returns None if unknown."""
    alias = {
        "lint-arwaky": "lint-arwaky", "lint": "lint-arwaky",
        "la": "lint-arwaky", "lac": "lint-arwaky",
        "ponytail": "ponytail", "ponytail-mcp": "ponytail",
        "context7": "context7", "context7-mcp": "context7",
        "codegraph": "codegraph", "codegraph-mcp": "codegraph",
        "anytype": "anytype", "anytype-mcp": "anytype", "anytype-daemon": "anytype",
        "fetch": "fetch", "fetch-mcp": "fetch",
        "vision-arwaky": "vision-arwaky", "vision": "vision-arwaky", "va": "vision-arwaky",
        "qwen-web-arwaky": "qwen-web-arwaky", "qwen-web": "qwen-web-arwaky",
        "qwa": "qwen-web-arwaky", "qwc": "qwen-web-arwaky",
        "blender-arwaky": "blender-arwaky", "blender": "blender-arwaky", "ba": "blender-arwaky",
        "skill": "skill", "skills": "skill", "skill-manager": "skill",
        "workspace": "workspace", "workspace-mcp": "workspace", "google-workspace": "workspace",
        "mnemosyne": "mnemosyne", "mnemosyne-memory": "mnemosyne", "mnemosyne-mcp": "mnemosyne",
    }
    if query in alias:
        return alias[query]
    for tid, _, _ in get_registered_tool_ids():
        if query == tid:
            return tid
    return None


def extract_description(skill_md):
    """Extract `description:` from SKILL.md frontmatter."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            d = re.search(r"^description:\s*[\"']?(.+?)[\"']?\s*$", m.group(1), re.MULTILINE)
            if d:
                return d.group(1).strip()
    except OSError:
        pass
    return "No description available"


def _find_skills(base: Path):
    """Iterate SKILL.md files under *base*, skipping common build dirs."""
    if not base.exists():
        return []
    out = []
    for p in sorted(base.rglob("SKILL.md")):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git"} for part in p.parts):
            continue
        out.append(p)
    return out


@lru_cache(maxsize=1)
def get_all_skills():
    """Shared skill discovery — cached once per process (no per-tool eviction)."""
    base = REPO_ROOT / "skills"
    if not base.is_dir():
        return ()
    return tuple(sorted(
        f for f in base.rglob("SKILL.md")
        if not any(part in {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"} for part in f.parts)
    ))


# Back-compat private alias used by surface_skill_command.
_get_all_skills = get_all_skills


def get_tool_skills(tool_id):
    """Return sorted list of SKILL.md paths for a tool.

    User-managed skill pack: ALL skills live in tools/skills/ and are shared
    across every tool. internal/ and vendor/ submodules are no longer read.
    """
    return get_all_skills()


def manifest_tools():
    """Raw tool entries from manifest.json, in manifest order."""
    if not MANIFEST.exists():
        return []
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [t for t in data.get("tools", []) if isinstance(t, dict)]


_manifest_tools = manifest_tools


def tool_names(tool):
    """Every handle a manifest tool answers to: id, alias, binaries."""
    names = set()
    for key in ("id", "alias", "binary", "mcpBinary"):
        value = str(tool.get(key) or "").strip().lower()
        if value:
            names.add(value)
    return {n for n in names if len(n) > 2}


def resolve_tool_skills(tool):
    """The subset of the shared pack that documents THIS manifest tool.

    The pack is shared on purpose (one skill tree, every harness), so "skills for
    a tool" can only mean skills whose name or trigger text points at that tool.
    """
    handles = tool_names(tool)
    patterns = [re.compile(rf"(?<!\w){re.escape(h)}(?!\w)", re.IGNORECASE) for h in handles]
    dedicated = []
    for path in get_all_skills():
        haystack = f"{path.parent.name} {extract_description(path)}"
        if any(p.search(haystack) for p in patterns):
            dedicated.append(path)
    return dedicated


def resolve_single_skill_file(query):
    """Find a SKILL.md by exact tool/skill name or alias (shared pack only)."""
    base = REPO_ROOT / "skills"
    if not base.is_dir():
        return None
    for p in sorted(base.rglob("SKILL.md")):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"} for part in p.parts):
            continue
        if query in p.parent.name or query in p.parent.parent.name:
            return p
    return None


def provision_single_skill(source_file, target_dir, custom_dest="", force=False, link=False):
    """Provision one skill into a PROJECT workspace as a copy of SKILL.md.

    Copy is the default here on purpose: a project workspace gets committed and
    pushed, and a symlink to the agents-arwaky checkout is meaningless anywhere
    else — git stores it as mode 120000 with an absolute target, so a clone on
    another machine (or Windows with core.symlinks=false) gets a dead link or a
    plain text file containing a path. Use --link only for local, uncommitted
    workspaces where live tracking of the pack is worth more than portability.

    Harness provisioning (aa connect) uses links; see
    `_link_skills_root` / `_provision_skill` in the harness skills capability.
    """
    if not source_file.is_file():
        print(f"  \u2717 Error: Source file not found: {source_file}", file=sys.stderr)
        return False
    name = safe_skill_name(source_file)
    src_dir = source_file.parent
    if custom_dest:
        if custom_dest.endswith(".md"):
            # explicit single-file target: a directory link would not match
            # what the user asked for, so this branch always copies
            dest = Path(custom_dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest = ensure_under(REPO_ROOT, dest)
            except ValueError as exc:
                print(f"  \u2717 {exc}", file=sys.stderr)
                return False
            if dest.exists() and not force:
                print(f"  \u21b7 [SKIP] Already exists: {dest} (use --force to overwrite)")
                return False
            shutil.copy2(source_file, dest)
            print(f"  \u2713 [OK] Provisioned: {dest}")
            return True
        dest_dir = Path(custom_dest) / name
        base = Path(custom_dest)
    else:
        base = target_dir / ".agents" / "skills"
        dest_dir = base / name
    dest_file = dest_dir / "SKILL.md"

    if link and dest_dir.is_symlink():
        if dest_dir.resolve() == src_dir.resolve():
            print(f"  \u21b7 [SKIP] Already linked: {dest_dir}")
            return False
        if not force:
            print(f"  \u21b7 [SKIP] {dest_dir} is a link to {dest_dir.resolve()} (use --force to replace)")
            return False
        dest_dir.unlink()

    if link and dest_dir.resolve() == src_dir.resolve():
        # linking the pack into itself would create a self-referential loop
        print(f"  \u21b7 [SKIP] Target {dest_dir} is the pack source itself")
        return False

    if dest_dir.is_dir() and not dest_dir.is_symlink():
        if not link:
            if dest_file.exists() and not force:
                _copy_skill_assets(src_dir, dest_dir)
                print(f"  ↷ [SKIP] Already exists: {dest_file} (use --force to overwrite)")
                return False
        elif not _dir_is_empty(dest_dir) and not copy_matches_pack(dest_dir, src_dir) and not force:
            print(f"  \u26a0 {dest_dir} differs from the pack; left as a copy (not relinked). "
                  f"Use --force to replace it with a link to the pack.")
            return False
        else:
            shutil.rmtree(dest_dir)

    if link:
        base.mkdir(parents=True, exist_ok=True)
        dest_dir.symlink_to(src_dir, target_is_directory=True)
        try:
            shown = src_dir.relative_to(REPO_ROOT)
        except ValueError:
            shown = src_dir
        print(f"  \u2713 [OK] Linked: {dest_dir} -> {shown}")
        return True

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, dest_file)
    _copy_skill_assets(src_dir, dest_dir)
    # Provenance is what makes `--prune` safe: it separates our copies from
    # hand-written skills. Links need none — the link already points at the pack.
    write_provenance(dest_dir, source_file, PACK_ROOT)
    print(f"  ✓ [OK] Provisioned: {dest_file}")
    return True


def _copy_skill_assets(src_dir: Path, dest_dir: Path) -> None:
    """Copy pack companion dirs so relative SKILL.md links resolve in the copy."""
    for extra in _ASSET_DIRS:
        e = src_dir / extra
        if not e.is_dir():
            continue
        shutil.rmtree(dest_dir / extra, ignore_errors=True)
        shutil.copytree(e, dest_dir / extra)


def _dir_is_empty(d: Path) -> bool:
    try:
        return not any(d.iterdir())
    except OSError:
        return False


def copy_matches_pack(dest_dir: Path, src_dir: Path) -> bool:
    """True when a provisioned copy is still byte-identical to its pack source."""
    for f in src_dir.rglob("*"):
        if f.is_dir() or "__pycache__" in f.parts:
            continue
        peer = dest_dir / f.relative_to(src_dir)
        if not peer.is_file() or peer.read_bytes() != f.read_bytes():
            return False
    return True


_copy_matches_pack = copy_matches_pack


def copy_single_skill(source_file, target_dir, custom_dest="", force=False, link=True):
    """Backwards-compatible alias for provision_single_skill."""
    return provision_single_skill(source_file, target_dir, custom_dest, force, link)


def remove_single_skill(source_file, target_dir, custom_dest=""):
    """Remove one provisioned skill (with path containment).

    A linked skill is removed by unlinking the link only — the pack source
    under skills/ is what the link points at and must survive.
    """
    if not source_file.is_file():
        return False
    name = safe_skill_name(source_file)
    if custom_dest:
        if custom_dest.endswith(".md"):
            p = Path(custom_dest)
            if p.exists():
                p.unlink(missing_ok=True)
                print(f"  \u2713 [OK] Removed: {p}")
            else:
                print(f"  \u21b7 [SKIP] Not found: {p}")
            return True
        d = Path(custom_dest) / name
        return _remove_skill_dir(d)
    skills_base = target_dir / ".agents" / "skills"
    try:
        d = ensure_under(skills_base, skills_base / name)
    except ValueError:
        # a provisioned link resolves back into the pack, which trips
        # containment; fall back to the lexical path and remove the link
        d = safe_child(skills_base, name)
        if d.is_symlink():
            return _remove_skill_dir(d)
        print(f"  \u2717 Refusing path outside target directory: {d}", file=sys.stderr)
        return False
    return _remove_skill_dir(d)


def _remove_skill_dir(d: Path) -> bool:
    """Remove a provisioned skill directory (symlink or real dir)."""
    if d.is_symlink():
        d.unlink()
        print(f"  \u2713 [OK] Unlinked: {d} (pack source intact)")
        return True
    if d.is_dir():
        shutil.rmtree(d)
        print(f"  \u2713 [OK] Removed: {d}")
        return True
    print(f"  \u21b7 [SKIP] Not found: {d}")
    return False


def uninstall_tool_skills(tool_id, target_dir, custom_dest=""):
    """Remove all provisioned skills for *tool_id*; returns the count removed."""
    skills = get_tool_skills(tool_id)
    total = len(skills)
    if total == 0:
        print(f"  \u26a0 No skills registered for tool '{tool_id}'.", file=sys.stderr)
        return 0
    print(f"Removing {total} skill(s) for tool '{tool_id}'...")
    print(f"Target Workspace: {target_dir}")
    print("------------------------------------------------------------------")
    removed = 0
    for sf in skills:
        if remove_single_skill(sf, target_dir, custom_dest):
            removed += 1
    print("------------------------------------------------------------------")
    print(f"\u2713 Successfully removed {removed} skill(s) for tool '{tool_id}'.")
    return removed


def write_provenance(dest_dir: Path, source_md: Path, pack_root: Path) -> bool:
    """Record where a provisioned copy came from. Never writes into the pack itself."""
    try:
        source = str(source_md.resolve().relative_to(pack_root.resolve()))
    except (OSError, ValueError):
        return False
    payload = {
        "version": PROVENANCE_VERSION,
        "pack_root": str(pack_root),
        "source_skill": source,
    }
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / PROVENANCE_FILE).write_text(json.dumps(payload, indent=2))
        return True
    except OSError:
        return False


def _skills_root(target_dir: Path) -> Path:
    """Resolve the skills root a target workspace is pruned from.

    Callers pass either a workspace root (the historical contract, where the
    helper appends ``.agents/skills``) or an already-resolved skills root, which
    is what the surface and provisioner hand over. Treating the latter as a
    workspace root made prune scan ``.agents/skills/.agents/skills`` and always
    report nothing stale.
    """
    if target_dir.name == "skills" and target_dir.parent.name == ".agents":
        return target_dir
    return target_dir / ".agents" / "skills"


def _pack_skill_names(pack_root: Path) -> set[str]:
    """Names of every skill the pack currently provides, flat and <category>/ forms."""
    if not pack_root.is_dir():
        return set()
    names = set()
    for skill_file in pack_root.rglob("SKILL.md"):
        if any(p in {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"}
               for p in skill_file.parts):
            continue
        names.add(safe_skill_name(skill_file))
    return names


def prune_provisioned(
    target_dir: Path,
    pack_root: Path,
    *,
    names: list[str] | None = None,
) -> int:
    """Remove provisioned skill copies under *target_dir* the pack no longer provides.

    Returns the count of entries removed, appending the name of each removed
    entry relative to the skills root to *names* when one is supplied, so a
    caller can report exactly what it deleted.

    An entry is removed only when BOTH hold: it carries the
    :data:`PROVENANCE_FILE` marker (so it was provisioned, not hand-written),
    and the pack no longer provides a skill of that name. Without the second
    check a prune would delete every provisioned copy in the workspace,
    including the ones the pack still ships. Symlinks pointing outside the pack
    are never touched.

    Two layouts are in play. :func:`provision_single_skill` lands a copy FLAT at
    ``.agents/skills/<skill>/``, because a harness scans one level below the
    skills root. A category may also be present — ``.agents/skills/<category>/``
    — holding either a nested ``<skill>/`` copy or a hand-written skill of its
    own. So each direct child is first tested as a skill itself, and only a
    child that is not a skill is descended into as a possible category.
    """
    skills_root = _skills_root(target_dir)
    if not skills_root.is_dir():
        return 0
    pack_resolved = pack_root.resolve()

    provided = _pack_skill_names(pack_root)

    def _drop(entry: Path, label: str) -> None:
        """Remove one provisioned entry the pack no longer provides."""
        nonlocal removed
        if entry.is_symlink():
            if not entry.resolve().is_relative_to(pack_resolved):
                return
            entry.unlink()
        else:
            # Still in the pack -> this copy is current, keep it.
            if entry.name in provided:
                return
            shutil.rmtree(entry, ignore_errors=True)
        removed += 1
        if names is not None:
            names.append(label)

    removed = 0
    for child in sorted(skills_root.iterdir()):
        if child.is_symlink():
            _drop(child, child.name)
            continue
        if not child.is_dir():
            continue
        if (child / PROVENANCE_FILE).is_file():
            _drop(child, child.name)
            continue
        if (child / "SKILL.md").is_file():
            # A hand-written skill in its own right, not a category folder.
            continue
        for nested in sorted(child.iterdir()):
            if nested.is_symlink():
                _drop(nested, f"{child.name}/{nested.name}")
            elif nested.is_dir() and (nested / PROVENANCE_FILE).is_file():
                _drop(nested, f"{child.name}/{nested.name}")
    return removed


def provision_base(target_dir: Path, custom_dest: str) -> Path:
    """Where provisioned skill folders land, mirroring provision_single_skill."""
    if custom_dest and not custom_dest.endswith(".md"):
        return Path(custom_dest)
    return target_dir / ".agents" / "skills"


_provision_base = provision_base


__all__ = [
    "MANIFEST",
    "PACK_ROOT",
    "copy_matches_pack",
    "copy_single_skill",
    "extract_description",
    "get_all_skills",
    "get_registered_tool_ids",
    "get_tool_skills",
    "manifest_tools",
    "normalize_tool_id",
    "provision_base",
    "provision_single_skill",
    "prune_provisioned",
    "remove_single_skill",
    "resolve_single_skill_file",
    "resolve_tool_skills",
    "tool_names",
    "uninstall_tool_skills",
    "write_provenance",
]
