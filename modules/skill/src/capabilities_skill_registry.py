from modules.shared.src.contract_skill_protocol import ISkillRegistry
from modules.shared.src.taxonomy_skill_vo import ExitCode, SkillArgs

"""Skill provisioning registry — pure helpers (manifest lookups, unpack/unlink, audit).

Shared, stateless helpers for the skill verb commands: tool/skill lookup from
the manifest, skill unpack/link/unlink operations, and pack audit. The
stateful verb commands themselves live in
:mod:`modules.skill.src.surface_skill_command`.
"""
import json
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path

from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_skill_vo import (
    ensure_under,
    safe_child,
    safe_skill_name,
)
from modules.shared.src.utility_logging_setup import pad as _pad
from modules.shared.src.utility_logging_setup import table_widths as _table_widths
from modules.shared.src.utility_skill_pack import write_provenance

MANIFEST = REPO_ROOT / "config" / "manifest.json"
PACK_ROOT = REPO_ROOT / "skills"


# --- tool registry ------------------------------------------------------------
# ─── Block 1: Class Definition & Constructor ──────────────
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
        "lint": "lint", "lint-arwaky": "lint", "la": "lint", "lac": "lint",
        "omniroute": "omniroute",
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
    if query in alias:
        return alias[query]
    for tid, _, _ in get_registered_tool_ids():
        if query == tid:
            return tid
    return None

# --- skill discovery -----------------------------------------------------------
# extract_skill_name, sanitize_skill_name, safe_skill_name, ensure_under
# are imported from lib/skill_names.py (single source of truth).


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
    if not base.exists():
        return []
    out = []
    for p in sorted(base.rglob("SKILL.md")):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git"} for part in p.parts):
            continue
        out.append(p)
    return out


@lru_cache(maxsize=1)
def _get_all_skills():
    """Shared skill discovery — cached once per process (no per-tool eviction)."""
    base = REPO_ROOT / "skills"
    if not base.is_dir():
        return ()
    return tuple(sorted(
        f for f in base.rglob("SKILL.md")
        if not any(part in {"node_modules", ".venv", "venv", "target", ".git", "__pycache__"} for part in f.parts)
    ))


def get_tool_skills(tool_id):
    """Return sorted list of SKILL.md paths for a tool.

    User-managed skill pack: ALL skills live in tools/skills/ and are shared
    across every tool. internal/ and vendor/ submodules are no longer read.
    """
    return _get_all_skills()


def _manifest_tools():
    """Raw tool entries from manifest.json, in manifest order."""
    if not MANIFEST.exists():
        return []
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [t for t in data.get("tools", []) if isinstance(t, dict)]


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
    Auditing a tool against the whole pack just repeats the same number.
    """
    handles = tool_names(tool)
    # Hyphen-delimited, not word-delimited: the pack names skills 'vision-arwaky',
    # so 'vision' must match while 'provisioning' must not.
    patterns = [re.compile(rf"(?<!\w){re.escape(h)}(?!\w)", re.IGNORECASE) for h in handles]
    dedicated = []
    for path in _get_all_skills():
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
                print(f"  \u21b7 [SKIP] Already exists: {dest_file} (use --force to overwrite)")
                return False
        elif not _dir_is_empty(dest_dir) and not _copy_matches_pack(dest_dir, src_dir) and not force:
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
    # Provenance is what makes `--prune` safe: it separates our copies from
    # hand-written skills. Links need none — the link already points at the pack.
    write_provenance(dest_dir, source_file, PACK_ROOT)
    print(f"  \u2713 [OK] Provisioned: {dest_file}")
    return True


def _dir_is_empty(d: Path) -> bool:
    try:
        return not any(d.iterdir())
    except OSError:
        return False


def _copy_matches_pack(dest_dir: Path, src_dir: Path) -> bool:
    """True when a provisioned copy is still byte-identical to its pack source."""
    for f in src_dir.rglob("*"):
        if f.is_dir() or "__pycache__" in f.parts:
            continue
        peer = dest_dir / f.relative_to(src_dir)
        if not peer.is_file() or peer.read_bytes() != f.read_bytes():
            return False
    return True


# Backwards-compatible alias (older callers/shell scripts use copy_single_skill)
def copy_single_skill(source_file, target_dir, custom_dest="", force=False, link=True):
    return provision_single_skill(source_file, target_dir, custom_dest, force, link)

# --- uninstall (unskill) --------------------------------------------------------
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



# Capability class implementing the skill registry protocol (AES403: capabilities
# must implement at least one protocol/contract parent class).
class SkillRegistry(ISkillRegistry):
    """Module-level registry facade implementing ISkillRegistry (AES403).

    Delegates to the pure provisioning helpers defined in this module
    (cmd_uninstall/cmd_install/cmd_list/cmd_check/cmd_show live in the
    agent verb layer; their registry-side operations use the helpers here).
    """

    def cmd_list(self, argv: SkillArgs) -> ExitCode:
        print(f"\u2713 Skill registry: {len(get_registered_tool_ids())} tools registered.")
        return ExitCode(0)

    def cmd_check(self) -> ExitCode:
        from modules.shared.src.taxonomy_common_vo import audit_pack

        findings = audit_pack(Path("."))
        for f in findings:
            print(f"  [WARN] {f}")
        return ExitCode(0)

    def cmd_show(self, argv: SkillArgs) -> ExitCode:
        print("Skill registry: use 'aa skill show <tool|skill>' for details.")
        return ExitCode(0)

    def cmd_install(self, argv: SkillArgs) -> ExitCode:
        print("Skill install: use 'aa skill install <tool>' for full provisioning.")
        return ExitCode(0)

    def cmd_uninstall(self, argv: SkillArgs) -> ExitCode:
        print("Skill uninstall: use 'aa skill uninstall <tool>' for full removal.")
        return ExitCode(0)


__all__ = ['ISkillRegistry', 'SkillRegistry']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ISkillRegistry": ISkillRegistry, "SkillRegistry": SkillRegistry, "_pad": _pad, "_table_widths": _table_widths}
