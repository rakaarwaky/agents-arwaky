"""agents-arwaky Skill Manager — 1:1 verbatim port of tools/skill/skill.py.

Every function, constant, print, subprocess call, edge case and comment is
preserved exactly as written in the original script; the only differences are
the import swaps (tools/lib modules -> modules.shared.src):
  - paths.repo_root              -> modules.shared.src.common.utility_paths
  - skill_pack.*                 -> modules.shared.src.skill.capabilities_skill_pack
  - skill_names.*                -> modules.shared.src.common.utility_skill_names
  - ui.pad / ui.table_widths     -> modules.shared.src.logging.utility_logging

The ``if __name__ == "__main__"`` block from the original is dropped: the
CLI entry point in the AES tree is ``cmd_skill`` in
:mod:`modules.skill.src.surface_skill_command` (dispatch via
``modules.cli.src.root_cli_entry``).
"""
import json
import posixpath
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill.capabilities_skill_pack import (  # noqa: E402
    audit_pack,
    prune_provisioned,
    write_provenance,
)
from modules.shared.src.skill_names.utility_skill_names import (  # noqa: E402
    ensure_under,
    extract_skill_name,
    safe_child,
    safe_skill_name,
    sanitize_skill_name,
)
REPO_ROOT = repo_root()
MANIFEST = REPO_ROOT / "modules/shared/config/manifest.json"
PACK_ROOT = REPO_ROOT / "skills"

from modules.shared.src.logging.utility_logging import pad as _pad, table_widths as _table_widths  # type: ignore[import-not-found]

# --- tool registry ------------------------------------------------------------
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

    Harness provisioning (aa connect) does use links; see
    connect_shared.provision_skill_to_dir.
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


def cmd_uninstall(argv):
    target_name = ""
    target_dir = Path.cwd()
    custom_dest = ""
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--target", "-t"):
            target_dir = Path(argv[i + 1]); i += 2; continue
        if a in ("--dest", "-d"):
            custom_dest = argv[i + 1]; i += 2; continue
        if not target_name:
            target_name = a
        i += 1
    if not target_name:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill uninstall <tool-name|skill-name|all> [--target <dir>]")
        print()
        print("Note: Default target is the CURRENT WORKING DIRECTORY (.agents/skills/).")
        print("      This is different from 'aa disconnect' which removes skills from harness paths.")
        return 1

    # all tools
    if target_name == "all":
        print(f"Removing ALL provisioned skills from target workspace: {target_dir}")
        print("------------------------------------------------------------------")
        total = 0
        for tid, _, _ in get_registered_tool_ids():
            for sf in get_tool_skills(tid):
                if remove_single_skill(sf, target_dir, custom_dest):
                    total += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 All provisioned skills removed ({total} skill file(s) processed).")
        return 0

    # tool id
    tid = normalize_tool_id(target_name)
    if tid:
        uninstall_tool_skills(tid, target_dir, custom_dest)
        return 0

    # single skill
    sf = resolve_single_skill_file(target_name)
    if sf:
        print(f"Removing individual skill '{target_name}'...")
        remove_single_skill(sf, target_dir, custom_dest)
        return 0

    print(f"Error: Neither tool nor skill named '{target_name}' could be found.")
    print("Run 'aa skill list' to see all available tools and skills.")
    return 1

# --- install -------------------------------------------------------------------
def _provision_base(target_dir: Path, custom_dest: str) -> Path:
    """Where provisioned skill folders land, mirroring provision_single_skill."""
    if custom_dest and not custom_dest.endswith(".md"):
        return Path(custom_dest)
    return target_dir / ".agents" / "skills"


def _report_prune(base: Path) -> None:
    """Drop provisioned entries the pack no longer provides; leave foreign skills."""
    removed = prune_provisioned(base, PACK_ROOT)
    print("------------------------------------------------------------------")
    if not removed:
        print(f"Prune: nothing stale under {base}")
        return
    for name in removed:
        print(f"  - [PRUNE] {base / name}")
    print(f"Prune: removed {len(removed)} provisioned skill(s) the pack no longer provides.")


def cmd_install(argv):
    target_name = ""
    target_dir = Path.cwd()
    custom_dest = ""
    force = False
    link = False
    prune = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--target", "-t"):
            target_dir = Path(argv[i + 1]); i += 2; continue
        if a in ("--dest", "-d"):
            custom_dest = argv[i + 1]; i += 2; continue
        if a in ("--force", "-f"):
            force = True; i += 1; continue
        if a == "--prune":
            prune = True; i += 1; continue
        if a in ("--copy", "--copy-skills"):
            link = False; i += 1; continue
        if a in ("--link", "--symlink"):
            link = True; i += 1; continue
        if not target_name:
            target_name = a
        i += 1

    if prune:
        # Prune first, then provision: the end state is the pack, exactly.
        # `--prune` without a target is a valid cleanup-only invocation.
        _report_prune(_provision_base(target_dir, custom_dest))
        if not target_name:
            return 0

    if not target_name:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill install <tool-name|skill-name|all> [--target <dir>] [--force] [--prune]")
        return 1

    if target_name == "all":
        print(f"Provisioning ALL skills for ALL tools into target workspace: {target_dir}")
        print("------------------------------------------------------------------")
        total = 0
        for tid, _, _ in get_registered_tool_ids():
            for sf in get_tool_skills(tid):
                if provision_single_skill(sf, target_dir, custom_dest, force, link):
                    total += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 All {total} ecosystem skills provisioned successfully.")
        return 0

    tid = normalize_tool_id(target_name)
    if tid:
        skills = get_tool_skills(tid)
        if not skills:
            print(f"Error: No skills found for tool '{tid}'.", file=sys.stderr)
            return 1
        print(f"Installing all {len(skills)} skills for tool '{tid}'...")
        print(f"Target Workspace: {target_dir}")
        print("------------------------------------------------------------------")
        ok = 0
        for sf in skills:
            if provision_single_skill(sf, target_dir, custom_dest, force, link):
                ok += 1
        print("------------------------------------------------------------------")
        print(f"\u2713 Successfully provisioned {ok} skill(s) for tool '{tid}'.")
        return 0

    sf = resolve_single_skill_file(target_name)
    if sf:
        print(f"Provisioning individual skill '{target_name}'...")
        provision_single_skill(sf, target_dir, custom_dest, force, link)
        return 0

    print(f"Error: Neither tool nor skill named '{target_name}' could be found.")
    print("Run 'aa skill list' to see all available tools and skills.")
    return 1


def _term_width():
    try:
        import shutil
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


# --- list ----------------------------------------------------------------------
def cmd_list(argv):
    tool_filter = argv[0] if argv else ""
    pack = get_tool_skills("all")  # satu pack user di tools/skills/
    total_unique = len(pack)
    term_w = _term_width()
    # Reserve space for inter-column separators (one space between each column)
    n_cols = 2 if (tool_filter and tool_filter != "--all") else 4
    available = max(40, term_w - 2 - (n_cols - 1))
    if tool_filter and tool_filter != "--all":
        tid = normalize_tool_id(tool_filter)
        if not tid:
            print(f"Error: Tool '{tool_filter}' not found in manifest.", file=sys.stderr)
            return 1
        w_name, w_desc = _table_widths(available, [3, 7])
        print(f"Skills available for tool '{tid}' (shared skill pack):")
        print("-" * available)
        print(f"{_pad('SKILL NAME', w_name)} {_pad('DESCRIPTION', w_desc)}")
        print("-" * available)
        for sf in pack:
            print(f"{_pad(extract_skill_name(sf), w_name)} {_pad(extract_description(sf), w_desc)}")
        print("-" * available)
        print(f"Total skill pack: {total_unique} | Install: 'aa skill install {tid}'")
        return 0

    w_id, w_cat, w_count, w_desc = _table_widths(available, [2, 1, 1, 6])
    print("Available Tools & Shared Skill Pack in agents-arwaky:")
    print("-" * available)
    print(f"{_pad('TOOL ID', w_id)} {_pad('CATEGORY', w_cat)} {_pad('SKILLS COUNT', w_count)} {_pad('DESCRIPTION', w_desc)}")
    print("-" * available)
    for tid, cat, desc in get_registered_tool_ids():
        print(f"{_pad(tid, w_id)} {_pad(cat, w_cat)} {_pad(str(total_unique), w_count)} {_pad(desc, w_desc)}")
    print("-" * available)
    print(f"Total Tools: {len(get_registered_tool_ids())} | Total Skill Pack (unique): {total_unique}")
    return 0


# --- check ---------------------------------------------------------------------
def cmd_check():
    term_w = _term_width()
    n_cols = 5
    available = max(40, term_w - 2 - (n_cols - 1))
    w_id, w_cat, w_status, w_count, w_path = _table_widths(available, [2, 1, 1, 1, 5])
    print("Auditing the shared skill pack against manifest.json tools:")
    print("-" * available)
    print(f"{_pad('TOOL ID', w_id)} {_pad('CATEGORY', w_cat)} {_pad('STATUS', w_status)} {_pad('OWN SKILLS', w_count)} {_pad('SAMPLE PATH', w_path)}")
    print("-" * available)
    tools = _manifest_tools()
    documented = shared_only = 0
    for tool in tools:
        tid = str(tool.get("id", ""))
        cat = str(tool.get("category", ""))
        dedicated = resolve_tool_skills(tool)
        sample = ""
        if dedicated:
            documented += 1
            status = "DOCUMENTED"
            sample = str(dedicated[0].relative_to(REPO_ROOT))
        else:
            shared_only += 1
            status = "SHARED-ONLY"
        source_path = str(tool.get("path", ""))
        if source_path and not (REPO_ROOT / source_path).exists():
            status = "PATH MISSING"
        print(f"{_pad(tid, w_id)} {_pad(cat, w_cat)} {_pad(status, w_status)} {_pad(str(len(dedicated)), w_count)} {_pad(sample, w_path)}")
    print("-" * available)
    pack_size = len(_get_all_skills())
    print(f"Total Tools: {len(tools)} | Documented: {documented} | Shared-only: {shared_only}")
    print(f"Shared pack: {pack_size} SKILL.md (provisioned to every tool; 'aa skill install <tool>' copies all of them)")
    findings = audit_pack(REPO_ROOT / "skills")
    if findings:
        print()
        print(f"Loadability findings ({len(findings)}):")
        for finding in findings:
            print(f"  ! {finding.code}: {finding.message}")
    else:
        print("Loadability: clean (layout, names, descriptions, budget)")
    return 1 if findings else 0


# --- show ----------------------------------------------------------------------
def cmd_show(argv):
    query = argv[0] if argv else ""
    if not query:
        print("Error: Missing tool or skill name.")
        print("Usage: aa skill show <tool-name|skill-name>")
        return 1
    tid = normalize_tool_id(query)
    if tid:
        skills = get_tool_skills(tid)
        if len(skills) > 1:
            print(f"Tool '{tid}' contains {len(skills)} skills.")
            print(f"Displaying primary canonical skill: {skills[0]}")
            print("-" * 66)
            print(skills[0].read_text(encoding="utf-8", errors="replace"))
            print("-" * 66)
            print(f"Other skills in '{tid}':")
            for sf in skills[1:]:
                print(f"  - {extract_skill_name(sf)}")
            print("\nView any specific skill using 'aa skill show <skill-name>'.")
            return 0
        if len(skills) == 1:
            print(f"Source: {skills[0]}")
            print("-" * 66)
            print(skills[0].read_text(encoding="utf-8", errors="replace"))
            return 0
    sf = resolve_single_skill_file(query)
    if sf:
        print(f"Source: {sf}")
        print("-" * 66)
        print(sf.read_text(encoding="utf-8", errors="replace"))
        return 0
    print(f"Error: Skill or tool '{query}' not found.", file=sys.stderr)
    return 1


# --- help & main ---------------------------------------------------------------
def cmd_help():
    print("agents-arwaky Skill Manager (aa skill)")
    print("Discover, inspect and provision AI agent skills.")
    print()
    print("COMMANDS:")
    print("  list, ls [tool]             List all tools and their associated skills")
    print("  install, get, copy <name>   Install ALL skills for a tool (or a specific skill)")
    print("  install all, sync           Provision ALL skills for ALL tools")
    print("  install --prune             Drop provisioned skills the pack no longer provides")
    print("  uninstall, unskill, remove  Remove provisioned skills from CURRENT WORKING DIRECTORY (.agents/skills/)")
    print("  show <name>                 Display the content of a skill's SKILL.md")
    print("  check                       Audit per-tool skill coverage and pack loadability")
    print("  help                        Show this help screen")
    print()
    print("SUBCOMMAND HELP:")
    print("  aa skill list --help        Show list-specific options")
    print("  aa skill install --help     Show install-specific options")
    print("  aa skill uninstall --help   Show uninstall-specific options")
    print("  aa skill show --help        Show show-specific options")
    return 0


def cmd_list_help():
    print("Usage: aa skill list [tool]")
    print()
    print("List all registered tools and their associated skills, or filter by tool.")
    print()
    print("Options:")
    print("  tool              Optional tool ID to filter (e.g., 'lint', 'vision')")
    print("  --all             Show all tools (default behavior)")
    return 0


def cmd_install_help():
    print("Usage: aa skill install <tool|skill|all> [--target DIR] [--dest PATH] [--force] [--prune]")
    print()
    print("Install all skills for a tool, a specific skill, or all skills for all tools.")
    print()
    print("Skills are COPIED into the project workspace: it is meant to be committed")
    print("and pushed, and a symlink to the agents-arwaky checkout resolves to an")
    print("absolute path that breaks in anyone else's clone (--force refreshes an")
    print("existing copy from the pack). For harness-wide skill wiring that DOES")
    print("share self-improvements via symlinks, use 'aa connect <harness>'.")
    print()
    print("Options:")
    print("  <tool|skill|all>    Target tool ID, skill name, or 'all' for everything")
    print("  --target, -t DIR    Target workspace directory (default: current directory)")
    print("  --dest, -d PATH     Custom destination path")
    print("  --force, -f         Overwrite existing skills")
    print("  --link, --symlink   Symlink the skill dir to the pack (local only; do not commit)")
    print("  --copy              Explicitly request copies (the default)")
    print("  --prune             Also delete provisioned skills the pack no longer provides.")
    print("                      Only entries carrying .arwaky-skill.json, or links into the")
    print("                      pack, are removed — hand-written skills are never touched.")
    print("                      Alone ('aa skill install --prune') it prunes without installing.")
    return 0


def cmd_uninstall_help():
    print("Usage: aa skill uninstall <tool|skill|all> [--target DIR] [--dest PATH]")
    print()
    print("Remove provisioned skills from the target workspace.")
    print()
    print("Options:")
    print("  <tool|skill|all>  Target tool ID, skill name, or 'all' for everything")
    print("  --target, -t DIR  Target workspace directory (default: current directory)")
    print("  --dest, -d PATH   Custom destination path")
    return 0


def cmd_show_help():
    print("Usage: aa skill show <tool|skill>")
    print()
    print("Display the content of a skill's SKILL.md file.")
    print()
    print("Arguments:")
    print("  <tool|skill>      Tool ID or skill name to display")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        return cmd_help()
    action = argv[0]
    rest = argv[1:]
    # Per-subcommand --help support
    if rest and rest[0] in ("-h", "--help", "help"):
        if action in ("list", "ls"):
            return cmd_list_help()
        if action in ("install", "copy", "get", "add", "sync"):
            return cmd_install_help()
        if action in ("uninstall", "remove", "unskill", "delete"):
            return cmd_uninstall_help()
        if action in ("show", "cat", "view"):
            return cmd_show_help()
    if action in ("list", "ls"):
        return cmd_list(rest)
    if action in ("check", "audit"):
        return cmd_check()
    if action in ("install", "copy", "get", "add"):
        return cmd_install(rest)
    if action in ("uninstall", "remove", "unskill", "delete"):
        return cmd_uninstall(rest)
    if action == "sync":
        return cmd_install(["all", *rest])
    if action in ("show", "cat", "view"):
        return cmd_show(rest)
    print(f"Unknown skill command: {action}")
    return cmd_help()
