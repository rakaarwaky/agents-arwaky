"""Shared harness-connection infrastructure — capabilities layer (P4-A2).

Engine bridge, skill provisioning helpers, env injection and server
registry shared by all per-harness adapters.
"""
from __future__ import annotations

import functools
import json as _json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()


# --- logging helpers ---------------------------------------------------------
def log_header(msg): print(f"==> {msg}")
def log_sub(msg):    print(f"  -> {msg}")
def log_ok(msg):     print(f"  \u2713 {msg}")
def log_skip(msg):   print(f"  \u21b7 {msg}")
def log_warn(msg):   print(f"  \u26a0 {msg}")
def log_err(msg):    print(f"  \u2717 {msg}", file=sys.stderr)


# --- engine bridge -----------------------------------------------------------
def engine(*args):
    """Run tools/lib/engine.py and return stdout lines.

    Raises RuntimeError on non-zero exit so config failures are not hidden (E2).
    """
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/lib/engine.py"), *args],
            capture_output=True, text=True, timeout=30, check=False,
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
def extract_skill_name(skill_md: Path) -> str:
    """Extract `name:` from SKILL.md frontmatter; fallback to parent dir name."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            fm = m.group(1)
            nm = re.search(r"^name:\s*[\"']?(.+?)[\"']?\s*$", fm, re.MULTILINE)
            if nm:
                return nm.group(1).strip()
    except OSError:
        pass
    return skill_md.parent.name


def sanitize_skill_name(raw: str, fallback: str) -> str:
    raw = (raw or "").strip().replace("\\", "/")
    raw = posixpath.basename(raw)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    if not name:
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", fallback).strip(".-") or "skill"
    return name[:64]


def safe_skill_name(skill_md: Path) -> str:
    return sanitize_skill_name(extract_skill_name(skill_md), skill_md.parent.name)


def ensure_under(base: Path, child: Path) -> Path:
    base_resolved = base.resolve()
    child_resolved = child.resolve()
    if child_resolved == base_resolved:
        return child_resolved
    if base_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing path outside target directory: {child_resolved}")
    return child_resolved


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
    are no longer scanned directly.
    """
    seen = set()
    base = REPO_ROOT / "tools" / "skills"
    if not base.is_dir():
        return
    for p in base.rglob("SKILL.md"):
        if any(part in {"node_modules", ".venv", "venv", "target", ".git"} for part in p.parts):
            continue
        name = extract_skill_name(p)
        if name and name not in seen:
            seen.add(name)
            yield p


def remove_provisioned_skills(dest_base: Path, dry_run: bool = False):
    if not dest_base.is_dir():
        return 0
    removed = 0
    for sf in get_all_skill_files():
        name = extract_skill_name(sf)
        if not name:
            continue
        dest = dest_base / name
        if dest.is_dir():
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


def copy_skill_to_dir(src, dest_base, force=False, dry_run=False):
    """Copy SKILL.md + companion assets (mirrors bash copy_skill_to_dir)."""
    name = extract_skill_name(src)
    dest_dir = dest_base / name
    dest_file = dest_dir / "SKILL.md"
    if dry_run:
        log_sub(f"[DRY-RUN] Would install skill '{name}' -> {dest_file}")
        return True
    if dest_file.exists() and not force:
        log_skip(f"Skill '{name}' already exists (use --force to overwrite)")
        return False
    if dest_dir.exists() and not dest_dir.is_dir():
        dest_dir.unlink(missing_ok=True)
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_file)
    src_dir = src.parent
    for extra in ("scripts", "references", "resources", "examples"):
        e = src_dir / extra
        if e.is_dir():
            shutil.rmtree(dest_dir / extra, ignore_errors=True)
            shutil.copytree(e, dest_dir / extra)
    log_ok(f"Skill '{name}' provisioned")
    return True


def get_9router_credentials():
    """Read NINEROUTER_URL/KEY from .env candidates; fallback default URL."""
    router_url = "http://127.0.0.1:20128"
    router_key = ""
    secret_home = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "agents-arwaky/config"
    for cand in (
        secret_home / "ninerouter.env",
        HOME / ".config/9router/.env",
        REPO_ROOT / "tools/config/ninerouter.env",
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
            if router_key:
                break
    return router_url, router_key


PLACEHOLDER_KEYS = {"sk-your-9router-consumer-key-here", "<YOUR_API_KEY>", "change-me", ""}


def inject_9router_env(target, dry_run=False):
    url, key = get_9router_credentials()
    if not key or key in PLACEHOLDER_KEYS:
        log_warn(
            f"No active 9Router API Key found (empty/placeholder); env injection "
            f"SKIPPED for {target}. Run 'aa 9router' to configure."
        )
        return
    pairs = {"NINEROUTER_URL": url, "NINEROUTER_KEY": key}
    m_pairs = {"MNEMOSYNE_DATA_DIR": str(HOME / ".local/share/mnemosyne")}
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
        "mnemosyne": {"command": "mnemosyne-mcp"},
    }
