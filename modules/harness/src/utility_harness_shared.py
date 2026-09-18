"""Shared harness-connection infrastructure — capabilities layer (P4-A2).

Engine bridge, skill provisioning helpers, env injection and server
registry shared by all per-harness adapters.
"""
from __future__ import annotations

import functools
import json as _json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_skill_vo import (
    extract_skill_name,
    safe_child,
    safe_skill_name,
)

REPO_ROOT = repo_root
HOME = Path.home()

from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)


# --- logging helpers ---------------------------------------------------------
def log_header(msg): print(f"==> {msg}")
def log_sub(msg):    print(f"  -> {msg}")
def log_ok(msg):     print(f"  \u2713 {msg}")
def log_skip(msg):   print(f"  \u21b7 {msg}")
def log_warn(msg):   print(f"  \u26a0 {msg}")
def log_err(msg):    print(f"  \u2717 {msg}", file=sys.stderr)


# --- engine bridge -----------------------------------------------------------
def engine(*args):
    """Run the AES config engine (python3 -m modules.config.src.capabilities_config_engine)
    and return stdout lines.

    Raises RuntimeError on non-zero exit so config failures are not hidden (E2).
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m",
             "modules.config.src.capabilities_config_engine", *args],
            capture_output=True, text=True, timeout=30, check=False,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"engine.py timed out after 30s: {args[:2]}")
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or f"engine.py exited {proc.returncode}"
        raise RuntimeError(f"engine.py: {err_msg}")
    return proc.stdout.splitlines()


_server_names_cache: list | None = None


def arwaky_server_names():
    """Return agents-arwaky server names, cached once per process run (P1)."""
    global _server_names_cache
    if _server_names_cache is None:
        _server_names_cache = engine("arwaky-server-names", str(REPO_ROOT))
    return _server_names_cache


def remove_mcp_servers(file: Path, dry_run: bool = False):
    """Remove agents-arwaky servers from a JSON/JSONC/YAML MCP config."""
    if not file.exists():
        return []
    servers = arwaky_server_names()
    args = ["remove-mcp-servers", str(file), *servers]
    if dry_run:
        args.append("--dry-run")
    try:
        return engine(*args)
    except RuntimeError as exc:
        log_err(str(exc))
        return []


def remove_env_keys(file: Path, keys, dry_run: bool = False):
    if not file.exists():
        return []
    args = ["remove-env-keys", str(file), *keys]
    if dry_run:
        args.append("--dry-run")
    try:
        return engine(*args)
    except RuntimeError as exc:
        log_err(str(exc))
        return []


# --- skills ------------------------------------------------------------------
# extract_skill_name, sanitize_skill_name, safe_skill_name, ensure_under
# are imported from modules/shared/src/utility_skill_names (single source of truth).


def hermes_targets(h: Path):
    targets = [("Main Profile", h)]
    profiles = h / "profiles"
    if profiles.is_dir():
        targets.extend((f"Profile: {p.name}", p) for p in sorted(profiles.iterdir()) if p.is_dir())
    return targets


@functools.lru_cache(maxsize=1)
def get_all_skill_files():
    """All SKILL.md files owned by the user-managed skill pack (tools/skills/).

    Source of truth is ONLY tools/skills/ — internal/ and vendor/ submodules
    are no longer scanned directly. Materialized as a tuple so the cache
    does not return an exhausted generator to later callers.
    """
    seen = set()
    base = REPO_ROOT / "skills"
    if not base.is_dir():
        return ()
    result = []
    for p in base.rglob("SKILL.md"):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git"} for part in p.parts):
            continue
        name = extract_skill_name(p)
        if name and name not in seen:
            seen.add(name)
            result.append(p)
    return tuple(result)


def discover_skill_roots():
    """Directories that directly hold skill folders inside the pack.

    A harness that scans exactly ONE level below each skills root cannot see
    ``skills/<category>/<skill>/SKILL.md`` until ``skills/<category>`` is itself
    a registered root, so adding a category folder silently hides its skills.
    Derived from get_all_skill_files(), so ignored trees (node_modules, venvs,
    .git) never become roots and empty categories are never registered.

    Returns sorted Paths; the pack root itself appears when a skill sits flat
    at ``skills/<skill>/SKILL.md``.
    """
    return sorted({sf.parent.parent for sf in get_all_skill_files()})

def _skills_root_link_guard(dest_base: Path, action: str) -> bool:
    """True (and logs) when dest_base IS the linked skills root.

    With the root linked to the pack, per-skill provisioning/removal under it
    would operate directly on the pack sources — rmtree there deletes real
    skill packs. Manage the root with link_skills_root / disconnect instead.
    """
    pack_root = (REPO_ROOT / "skills").resolve()
    try:
        linked = dest_base.is_symlink() and dest_base.resolve() == pack_root
    except OSError:
        linked = False
    if linked:
        log_warn(f"Skills root {dest_base} is linked to the pack; "
                 f"per-skill {action} skipped — edit the pack itself.")
    return linked


def remove_provisioned_skills(dest_base: Path, dry_run: bool = False):
    if not dest_base.is_dir():
        return 0
    if _skills_root_link_guard(dest_base, "removal"):
        # disconnect of a root-linked harness: drop the link, restore an empty
        # real dir so the harness starts clean, keep the pack untouched.
        if not dry_run:
            dest_base.unlink()
            dest_base.mkdir(parents=True, exist_ok=True)
            log_ok(f"Unlinked skills root {dest_base} (pack left intact)")
        return 1
    removed = 0
    for sf in get_all_skill_files():
        name = safe_skill_name(sf)
        if not name:
            continue
        dest = dest_base / name
        if dest.is_symlink():
            # A linked skill: drop the link ONLY. shutil.rmtree refuses to walk
            # through a symlink, but unlinking the dir link is the intent here —
            # the pack source under skills/ must never be deleted.
            if dry_run:
                log_sub(f"[DRY-RUN] Would unlink skill '{name}' -> {dest.resolve()}")
            else:
                dest.unlink()
                log_ok(f"Unlinked skill '{name}' from {dest_base} (pack source intact)")
            removed += 1
        elif dest.is_dir():
            if dry_run:
                log_sub(f"[DRY-RUN] Would remove skill '{name}' from {dest_base}")
            else:
                shutil.rmtree(dest)
                log_ok(f"Removed skill '{name}' from {dest_base}")
            removed += 1
    return removed


# --- Hermes helpers ----------------------------------------------------------
def hermes_home():
    h = HOME / ".hermes"
    return h if h.is_dir() else HOME / ".hermes"


def disconnect_hermes_instance(target_dir: Path, label: str, dry_run: bool):
    log_header(f"Disconnecting from Hermes ({label})...")
    cfg = target_dir / "config.yaml"
    if cfg.exists():
        if dry_run:
            log_sub(f"[DRY-RUN] Would remove agents-arwaky MCP servers from {cfg}")
        else:
            removed = remove_mcp_servers(cfg, dry_run)
            if removed:
                log_ok(f"Removed agents-arwaky MCP servers from {cfg}")
            else:
                log_skip(f"No agents-arwaky MCP servers found in {cfg}")
    remove_provisioned_skills(target_dir / "skills", dry_run)
    remove_env_keys(target_dir / ".env",
                    ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"], dry_run)


# --- connect helpers ---------------------------------------------------------
def engine_merge_mcp(file, servers, force=False):
    args = ["merge-mcp-servers", str(file), _json.dumps(servers)]
    if force:
        args.append("--force")
    try:
        return engine(*args)
    except RuntimeError as exc:
        log_err(str(exc))
        return []

def engine_set_env(file, pairs):
    return engine("set-env-keys", str(file), _json.dumps(pairs))


ASSET_DIRS = ("scripts", "references", "resources", "examples", "templates", "assets")


def resolve_skill_link(verified: bool, copy_skills: bool) -> bool:
    """link=True only when the harness is verified to follow skill symlinks."""
    return verified and not copy_skills


def merge_dir_into(src: Path, dest: Path) -> int:
    """Union-move every entry of src into dest; src (the live harness copy)
    wins on same-name files. Returns the number of moved entries. Used when a
    harness state dir (.hub) already has an empty/older twin in the pack."""
    moved = 0
    for child in sorted(src.iterdir()):
        target = dest / child.name
        if child.is_dir():
            if target.exists() and not target.is_dir():
                target.unlink()
            target.mkdir(parents=True, exist_ok=True)
            moved += merge_dir_into(child, target)
            if not any(child.iterdir()):
                child.rmdir()
        else:
            if target.is_file():
                target.unlink()
            shutil.move(str(child), str(target))
            moved += 1
    return moved


def link_skills_root(dest_root: Path, src_root: Path, force=False, dry_run=False):
    """Replace a harness's whole skills directory with ONE symlink to the pack.

    The harness's skills dir becomes ``<pack>/skills`` itself, so adding,
    removing or editing a skill in the pack is instantly visible to every
    linked harness — no re-provision step at all. This is the strongest form
    of the self-improvement loop: the pack is the single place to manage.

    Migration safety (``force``): leftover real children in the old dir are
    MOVED into the pack, never deleted — an identical per-skill symlink (old
    layout) is just unlinked. Without ``force`` a non-empty dir aborts loudly.
    State files (.hub, .usage.json, .curator_*, .bundled_manifest) travel with
    the skills root because the harnesses write runtime state next to their
    skills; .gitignore keeps them out of the pack's history.
    """
    if dest_root.is_symlink():
        if dest_root.resolve() == src_root.resolve():
            log_skip(f"Skills root already linked: {dest_root} -> {src_root}")
            return False
        if not force:
            log_err(f"Skills root {dest_root} links to {dest_root.resolve()}, "
                    f"not the pack. Use --force to replace it.")
            return False
        if dry_run:
            log_sub(f"[DRY-RUN] Would relink skills root {dest_root} -> {src_root}")
            return True
        dest_root.unlink()
    elif dest_root.is_dir():
        leftovers = []
        stale_links = []
        for child in sorted(dest_root.iterdir()):
            if child.is_symlink():
                try:
                    if child.resolve().is_relative_to(src_root):
                        stale_links.append(child)
                        continue
                except OSError:
                    pass
                leftovers.append(child)
            else:
                leftovers.append(child)
        if leftovers and not force:
            log_warn(f"{dest_root} holds {len(leftovers)} item(s) not in the pack "
                     f"(harness-native skills / state). Nothing was touched. "
                     f"Re-run with --force to MOVE them into {src_root} first.")
            for c in leftovers[:8]:
                log_sub(f"  would move: {c.name}")
            if len(leftovers) > 8:
                log_sub(f"  ... and {len(leftovers) - 8} more")
            return False
        if dry_run:
            log_sub(f"[DRY-RUN] Would move {len(leftovers)} item(s) into {src_root}, "
                    f"unlink {len(stale_links)} old link(s), then link "
                    f"{dest_root} -> {src_root}")
            return True
        src_root.mkdir(parents=True, exist_ok=True)
        for child in leftovers:
            target = src_root / child.name
            if target.exists():
                if child.is_dir() and target.is_dir():
                    if child.name.startswith("."):
                        # state dir (.hub): harness copy is the LIVE one —
                        # union-merge it into the pack so state keeps working.
                        merge_dir_into(child, target)
                        shutil.rmtree(child, ignore_errors=True)
                        continue
                    if _copy_matches_pack(child, target):
                        shutil.rmtree(child)  # pure snapshot; pack is newer
                        continue
                if target.exists():
                    # a real skill diverged (agent edited it in copy-mode) or
                    # a file collision: never clobber the pack — stash to
                    # review instead of overwriting.
                    stamp = 1
                    while (src_root / f"{child.name}.harness-{stamp}").exists():
                        stamp += 1
                    target = src_root / f"{child.name}.harness-{stamp}"
                    log_warn(f"{child.name} differs from the pack; "
                             f"stored as {target.name} for review")
            shutil.move(str(child), str(target))
        for link in stale_links:
            link.unlink()
        dest_root.rmdir()
    else:
        if dry_run:
            log_sub(f"[DRY-RUN] Would link skills root {dest_root} -> {src_root}")
            return True
        dest_root.parent.mkdir(parents=True, exist_ok=True)
    dest_root.symlink_to(src_root, target_is_directory=True)
    log_ok(f"Skills root linked: {dest_root} -> {src_root} (manage skills once, "
           f"in the pack)")
    return True


def provision_skill_to_dir(src, dest_base, force=False, dry_run=False, link=True):
    """Provision one skill (SKILL.md + companion assets) into a harness dir.

    link=True (default) symlinks the whole skill DIRECTORY to its pack source
    under ``skills/``, so a self-improving agent that edits a provisioned skill
    writes through the link into the repo and every other harness picks the
    improvement up on its next read. Hermes proves the pattern works: its
    scanner walks with followlinks and its atomic writes replace the FILE
    inside the linked dir, keeping the link intact.

    link=False keeps the old snapshot behaviour (copy2 + copytree).

    A pre-existing real copy is only replaced by a link when it is still
    identical to the pack source, or when ``force`` says so. A copy an agent
    edited in place gets a loud warning instead of being destroyed: its edits
    exist nowhere else.
    """
    if not Path(src).is_file():
        log_err(f"Source file not found: {src}")
        return False
    name = safe_skill_name(src)
    try:
        dest_dir = safe_child(dest_base, name)
    except ValueError as exc:
        log_err(str(exc))
        return False
    src_dir = Path(src).parent
    dest_file = dest_dir / "SKILL.md"
    if link and _skills_root_link_guard(dest_base, "provisioning"):
        return False

    if dry_run:
        how = "link" if link else "copy"
        log_sub(f"[DRY-RUN] Would {how} skill '{name}' -> {dest_dir}")
        return True

    if link and dest_dir.is_symlink():
        if dest_dir.resolve() == src_dir.resolve():
            log_skip(f"Skill '{name}' already linked to the pack")
            return False
        log_err(f"Skill '{name}': {dest_dir} is a link to {dest_dir.resolve()}, "
                f"not the pack. Fix it manually before re-connecting.")
        return False

    if link and dest_dir.resolve() == src_dir.resolve():
        # provisioning the pack into itself would create a self-referential link
        log_skip(f"Skill '{name}': target {dest_dir} is the pack source itself")
        return False

    if dest_dir.is_dir() and not dest_dir.is_symlink():
        if link:
            if any(dest_dir.iterdir()) and not _copy_matches_pack(dest_dir, src_dir):
                if not force:
                    log_warn(f"Skill '{name}' at {dest_dir} differs from the pack; "
                             f"left as a copy (not relinked). Re-run with --force to "
                             f"replace it with a symlink to skills/{src_dir.name}.")
                    return False
                log_warn(f"Skill '{name}': --force discards local edits at {dest_dir}")
            shutil.rmtree(dest_dir)
        elif dest_file.exists() and not force:
            log_skip(f"Skill '{name}' already exists (use --force to overwrite)")
            return False
        else:
            shutil.rmtree(dest_dir)

    if link:
        dest_base.mkdir(parents=True, exist_ok=True)
        dest_dir.symlink_to(src_dir, target_is_directory=True)
        try:
            log_ok(f"Skill '{name}' linked -> {src_dir.relative_to(Path(REPO_ROOT))}")
        except ValueError:
            log_ok(f"Skill '{name}' linked -> {src_dir}")
        return True

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_file)
    for extra in ASSET_DIRS:
        e = src_dir / extra
        if e.is_dir():
            shutil.rmtree(dest_dir / extra, ignore_errors=True)
            shutil.copytree(e, dest_dir / extra)
    log_ok(f"Skill '{name}' provisioned")
    return True

def _copy_matches_pack(dest_dir: Path, src_dir: Path) -> bool:
    """True when a provisioned copy is still byte-identical to its pack source."""
    for f in src_dir.rglob("*"):
        if f.is_dir() or "__pycache__" in f.parts:
            continue
        peer = dest_dir / f.relative_to(src_dir)
        if not peer.is_file() or peer.read_bytes() != f.read_bytes():
            return False
    return True


PLACEHOLDER_KEYS = {"sk-your-9router-consumer-key-here", "<YOUR_API_KEY>", "change-me", ""}


def get_9router_credentials():
    """Read NINEROUTER_URL/KEY from .env candidates; fallback default URL."""
    router_url = "http://127.0.0.1:20128"
    router_key = ""
    for cand in (
        agents_arwaky_config_dir() / "ninerouter.env",
        config_home() / "9router/.env",
        REPO_ROOT / "modules/shared/config/ninerouter.env",
    ):
        if cand.is_file():
            try:
                for line in cand.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("NINEROUTER_URL="):
                        router_url = line.split("=", 1)[1].strip().strip('"\'')
                    elif line.startswith("NINEROUTER_KEY="):
                        router_key = line.split("=", 1)[1].strip().strip('"\'')
            except OSError:
                pass
            # Break only for a non-placeholder key; skip candidates with empty/placeholder values
            if router_key and router_key not in PLACEHOLDER_KEYS:
                break
    return router_url, router_key


def inject_9router_env(target, dry_run=False):
    url, key = get_9router_credentials()
    if not key or key in PLACEHOLDER_KEYS:
        log_warn(
            f"No active 9Router API Key found (empty/placeholder); env injection "
            f"SKIPPED for {target}. Run 'aa 9router' to configure."
        )
        return
    pairs = {"NINEROUTER_URL": url, "NINEROUTER_KEY": key}
    m_pairs = {"MNEMOSYNE_DATA_DIR": str(data_home() / "mnemosyne")}
    # systemd user-session layer wins over harness .env files: some harnesses
    # (Qwen Code) read dotenv WITHOUT overriding already-exported vars, so a
    # stale key here shadows every correct key injected below. Keep it in sync.
    synced_session = False
    if not dry_run:
        envd = config_home() / "environment.d/9router.conf"
        if envd.is_file():
            engine_set_env(envd, pairs)
            synced_session = True
    envs = []
    if target == "antigravity":
        envs = [HOME / ".gemini/config/.env"]
        for sub in ("antigravity-cli", "antigravity"):
            d = HOME / ".gemini" / sub
            if d.is_dir():
                envs.append(d / ".env")
    elif target == "hermes":
        h = hermes_home()
        envs = [h / ".env"]
        if (h / "profiles").is_dir():
            envs += [p / ".env" for p in sorted((h / "profiles").iterdir()) if p.is_dir()]
    elif target == "opencode":
        cfg = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "opencode"
        envs = [cfg / ".env"]
        if (HOME / ".opencode").is_dir():
            envs.append(HOME / ".opencode/.env")
    elif target in ("qwencode", "qwen"):
        envs = [Path(os.environ.get("QWEN_HOME", HOME / ".qwen")) / ".env"]
    if not dry_run:
        for e in envs:
            engine_set_env(e, pairs)
            engine_set_env(e, m_pairs)
        log_ok(f"Injected NINEROUTER_URL/KEY + MNEMOSYNE_DATA_DIR into {target} environment.")
        if synced_session:
            log_ok("Synced ~/.config/environment.d/9router.conf (login-session key layer).")
    else:
        log_sub(f"[DRY-RUN] Would inject env into {target}")


def load_generated_servers():
    """Read mcpServers from mcp_servers.generated.json (or default static map)."""
    gen = REPO_ROOT / "mcp_servers.generated.json"
    if gen.exists():
        try:
            data = _json.loads(gen.read_text(encoding="utf-8"))
            return data.get("mcpServers", {})
        except (OSError, ValueError) as exc:
            log_warn(f"Could not read {gen} ({exc}); using default servers.")
    return default_servers_dict()


def default_servers_dict():
    return {
        "context7": {"command": "context7-mcp"},
        "fetch": {"command": "fetch-mcp"},
        "ponytail": {"command": "ponytail-mcp"},
        "anytype": {"command": "anytype-mcp"},
        "codegraph": {"command": "codegraph-mcp", "args": ["serve", "--mcp"]},
        "vision": {"command": "vision-arwaky-mcp"},
        "qwen-web": {"command": "qwen-web-mcp"},
        "blender": {"command": "blender-mcp"},
        "lint": {"command": "lint-arwaky-mcp"},
        "workspace": {"command": "workspace-mcp"},
        "mnemosyne": {"command": "mnemosyne-mcp", "args": ["mcp"]},
    }
