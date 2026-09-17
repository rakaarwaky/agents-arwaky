"""Shared harness-connection infrastructure — port of connect/connect_shared.py."""
from __future__ import annotations

import functools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.config.capabilities_config_engine import (
    arwaky_server_names,
    remove_mcp_servers as _remove_mcp_servers_raw,
    remove_env_keys,
)
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.skill_pack.capabilities_skill_pack import get_all_skill_files
from modules.shared.src.skill_names.utility_skill_names import (
    ensure_under,
    extract_skill_name,
    safe_child,
    safe_skill_name,
)
from modules.shared.src.xdg.utility_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)


def _get_all_skill_files() -> list[Path]:
    """Indirection so tests can monkeypatch connect_shared.get_all_skill_files."""
    return get_all_skill_files()

# Repo root (module-level so tests can monkeypatch REPO_ROOT directly).
REPO_ROOT = repo_root()
HOME = Path.home()


# --- logging helpers ---------------------------------------------------------
def log_header(msg: str) -> None: print(f"==> {msg}")
def log_sub(msg: str) -> None:    print(f"  -> {msg}")
def log_ok(msg: str) -> None:     print(f"  \u2713 {msg}")
def log_skip(msg: str) -> None:   print(f"  \u21b7 {msg}")
def log_warn(msg: str) -> None:   print(f"  \u26a0 {msg}")
def log_err(msg: str) -> None:    print(f"  \u2717 {msg}", file=sys.stderr)


# --- skills ------------------------------------------------------------------
def discover_skill_roots() -> list[Path]:
    """Category folders that directly hold skills (one level below = loadable)."""
    return sorted({sf.parent.parent for sf in _get_all_skill_files()})


def remove_mcp_servers(file: Path, dry_run: bool = False) -> list:
    """Remove agents-arwaky servers from a JSON/JSONC/YAML/TOML MCP config.

    Auto-resolves the server name list via ``arwaky_server_names()`` so callers
    (the per-harness adapters) only need to pass the config path.
    """
    if not file.exists():
        return []
    servers = arwaky_server_names(REPO_ROOT)
    return _remove_mcp_servers_raw(file, servers, dry_run)


def _skills_root_link_guard(dest_base: Path, action: str) -> bool:
    """True (and logs) when dest_base IS the linked skills root."""
    pack_root = (Path(REPO_ROOT) / "skills").resolve()
    try:
        linked = dest_base.is_symlink() and dest_base.resolve() == pack_root
    except OSError:
        linked = False
    if linked:
        log_warn(f"Skills root {dest_base} is linked to the pack; "
                 f"per-skill {action} skipped — edit the pack itself.")
    return linked


def remove_provisioned_skills(dest_base: Path, dry_run: bool = False) -> int:
    """Unlink/remove provisioned skills; a root-linked harness drops the link only."""
    if not dest_base.is_dir():
        return 0
    if _skills_root_link_guard(dest_base, "removal"):
        if not dry_run:
            dest_base.unlink()
            dest_base.mkdir(parents=True, exist_ok=True)
            log_ok(f"Unlinked skills root {dest_base} (pack left intact)")
        return 1
    removed = 0
    for skill_md in _get_all_skill_files():
        name = safe_skill_name(skill_md)
        if not name:
            continue
        dest = dest_base / name
        if dest.is_symlink():
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
def hermes_home() -> Path:
    h = HOME / ".hermes"
    return h if h.is_dir() else HOME / ".hermes"


def hermes_targets(h: Path) -> list[tuple[str, Path]]:
    targets = [("Main Profile", h)]
    profiles = h / "profiles"
    if profiles.is_dir():
        targets.extend((f"Profile: {p.name}", p) for p in sorted(profiles.iterdir()) if p.is_dir())
    return targets


def disconnect_hermes_instance(target_dir: Path, label: str, dry_run: bool) -> None:
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
def engine_merge_mcp(file: Path, servers: dict, force: bool = False) -> list:
    from modules.shared.src.config.capabilities_config_engine import merge_mcp_servers

    try:
        return merge_mcp_servers(file, servers, force)
    except (RuntimeError, ValueError) as exc:
        log_err(str(exc))
        return []


def engine_set_env(file: Path, pairs: dict) -> None:
    from modules.shared.src.config.capabilities_config_engine import set_env_keys
    set_env_keys(file, pairs)


ASSET_DIRS = ("scripts", "references", "resources", "examples", "templates", "assets")


def resolve_skill_link(verified: bool, copy_skills: bool) -> bool:
    """link=True only when the harness is verified to follow skill symlinks."""
    return verified and not copy_skills


def merge_dir_into(src: Path, dest: Path) -> int:
    """Union-move every entry of src into dest; src wins on same-name files."""
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


def link_skills_root(dest_root: Path, src_root: Path, force: bool = False, dry_run: bool = False) -> bool:
    """Replace a harness's whole skills directory with ONE symlink to the pack.

    Leftover real children are MOVED into the pack (never deleted); identical
    per-skill symlinks are unlinked; state files travel with the skills root.
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
        leftovers: list[Path] = []
        stale_links: list[Path] = []
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
                        merge_dir_into(child, target)
                        shutil.rmtree(child, ignore_errors=True)
                        continue
                    if _copy_matches_pack(child, target):
                        shutil.rmtree(child)
                        continue
                if target.exists():
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


def provision_skill_to_dir(src: Path, dest_base: Path, force: bool = False, dry_run: bool = False, link: bool = True) -> bool:
    """Provision one skill dir (symlink by default) into a harness dir."""
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


def get_9router_credentials() -> tuple[str, str]:
    """Read NINEROUTER_URL/KEY from .env candidates; fallback default URL."""
    router_url = "http://127.0.0.1:20128"
    router_key = ""
    for cand in (
        agents_arwaky_config_dir() / "ninerouter.env",
        config_home() / "9router/.env",
        Path(REPO_ROOT) / "tools/config/ninerouter.env",
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
            if router_key and router_key not in PLACEHOLDER_KEYS:
                break
    return router_url, router_key


def inject_9router_env(target: str, dry_run: bool = False) -> None:
    """Inject NINEROUTER_URL/KEY + MNEMOSYNE_DATA_DIR into a harness .env layer."""
    url, key = get_9router_credentials()
    if not key or key in PLACEHOLDER_KEYS:
        log_warn(
            f"No active 9Router API Key found (empty/placeholder); env injection "
            f"SKIPPED for {target}. Run 'aa 9router' to configure."
        )
        return
    pairs = {"NINEROUTER_URL": url, "NINEROUTER_KEY": key}
    m_pairs = {"MNEMOSYNE_DATA_DIR": str(data_home() / "mnemosyne")}
    synced_session = False
    if not dry_run:
        envd = config_home() / "environment.d/9router.conf"
        if envd.is_file():
            engine_set_env(envd, pairs)
            synced_session = True
    envs: list[Path] = []
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


def load_generated_servers() -> dict:
    """Read mcpServers from mcp_servers.generated.json (or the static fallback)."""
    gen = Path(REPO_ROOT) / "mcp_servers.generated.json"
    if gen.exists():
        try:
            data = json.loads(gen.read_text(encoding="utf-8"))
            return data.get("mcpServers", {})
        except (OSError, ValueError) as exc:
            log_warn(f"Could not read {gen} ({exc}); using default servers.")
    return default_servers_dict()


def default_servers_dict() -> dict:
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
