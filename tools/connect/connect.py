#!/usr/bin/env python3
"""agents-arwaky Harness Connector / Disconnector (Python).

Drop-in replacement for tools/connect/connect-agent.sh disconnect subcommand.

Supports:
    aa disconnect --antigravity|--hermes|--opencode|--qwencode|--all
    aa disconnect --lean-ctx
    aa disconnect <targets> --dry-run

Removes agents-arwaky MCP servers, provisioned skills and env vars from
agent harness paths (NOT the current working directory's .agents/skills —
that is `aa unskill` / skill-manager).
"""
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
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"engine.py timed out after 30s: {args[:2]}")
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or f"engine.py exited {proc.returncode}"
        raise RuntimeError(f"engine.py: {err_msg}")
    return proc.stdout.splitlines()


def arwaky_server_names():
    return engine("arwaky-server-names", str(REPO_ROOT))


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
        m = re.search(r"^---\s*\n(.*?)\n---", text, re.S)
        if m:
            fm = m.group(1)
            nm = re.search(r"^name:\s*[\"']?(.+?)[\"']?\s*$", fm, re.M)
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


def disconnect_hermes(dry_run: bool):
    log_header("Disconnecting from Hermes Agent (Main & Multi-Profiles)...")
    h = hermes_home()
    disconnect_hermes_instance(h, "Main Profile", dry_run)
    profiles = h / "profiles"
    if profiles.is_dir():
        for pdir in sorted(profiles.iterdir()):
            if pdir.is_dir():
                disconnect_hermes_instance(pdir, f"Profile: {pdir.name}", dry_run)
    log_ok("Hermes disconnect complete.")


# --- Antigravity -------------------------------------------------------------
def disconnect_antigravity(dry_run: bool):
    log_header("Disconnecting from Google Antigravity...")
    cfg_dir = HOME / ".gemini" / "config"
    remove_mcp_servers(cfg_dir / "mcp_config.json", dry_run)
    remove_provisioned_skills(cfg_dir / "skills", dry_run)
    env_keys = ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"]
    remove_env_keys(cfg_dir / ".env", env_keys, dry_run)
    for sub in ("antigravity-cli", "antigravity"):
        d = HOME / ".gemini" / sub
        if d.is_dir():
            remove_mcp_servers(d / "mcp_config.json", dry_run)
            remove_env_keys(d / ".env", env_keys, dry_run)
    log_ok("Antigravity disconnect complete.")


# --- OpenCode ----------------------------------------------------------------
def disconnect_opencode(dry_run: bool):
    log_header("Disconnecting from OpenCode...")
    cfg_dir = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "opencode"
    remove_mcp_servers(cfg_dir / "opencode.jsonc", dry_run)
    remove_provisioned_skills(cfg_dir / "skills", dry_run)
    env_keys = ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"]
    remove_env_keys(cfg_dir / ".env", env_keys, dry_run)
    legacy = HOME / ".opencode"
    if legacy.is_dir():
        remove_env_keys(legacy / ".env", env_keys, dry_run)
    log_ok("OpenCode disconnect complete.")


# --- Qwen Code ---------------------------------------------------------------
def disconnect_qwencode(dry_run: bool):
    log_header("Disconnecting from Qwen Code (qwencode)...")
    qwen_home = Path(os.environ.get("QWEN_HOME", HOME / ".qwen"))
    remove_mcp_servers(qwen_home / "settings.json", dry_run)
    remove_provisioned_skills(qwen_home / "skills", dry_run)
    remove_env_keys(qwen_home / ".env",
                    ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"], dry_run)
    log_ok("Qwen Code disconnect complete.")


# --- legacy lean-ctx remnants -------------------------------------------------
def disconnect_legacy_lean_ctx(dry_run: bool):
    log_header("Cleaning up legacy lean-ctx remnants...")
    names = arwaky_server_names() + ["lean-ctx"]

    # 1. Hermes config.yaml mcp_servers.lean-ctx
    h = hermes_home()
    remove_mcp_servers(h / "config.yaml", dry_run)

    # 2. HERMES.md lean-ctx comment blocks (main + profiles)
    hermes_mds = [h / "HERMES.md"]
    if (h / "profiles").is_dir():
        hermes_mds.extend((h / "profiles").glob("*/HERMES.md"))
    for hmd in hermes_mds:
        if not hmd.is_file():
            continue
        if dry_run:
            log_sub(f"[DRY-RUN] Would strip lean-ctx blocks from {hmd}")
            continue
        try:
            s = hmd.read_text(encoding="utf-8")
            before = s
            s = re.sub(r"(?s)<!--\s*lean-ctx-rules\s*-->.*?<!--\s*/lean-ctx-rules\s*-->\n?", "", s)
            s = re.sub(r"(?s)<!--\s*lean-ctx-compression\s*-->.*?<!--\s*/lean-ctx-compression\s*-->\n?", "", s)
            s = re.sub(r"(?s)<!--\s*lean-ctx-solution\s*-->.*?<!--\s*/lean-ctx-solution\s*-->\n?", "", s)
            s = re.sub(r"(?s)<!--\s*lean-ctx\s*-->.*?<!--\s*/lean-ctx\s*-->\n?", "", s)
            s = re.sub(r"(?s)#\s*Lean-CTX.*?(?=\n# |\Z)", "", s, flags=re.I)
            if s != before:
                hmd.write_text(s, encoding="utf-8")
                log_ok(f"Stripped lean-ctx blocks from {hmd}")
        except OSError:
            log_warn(f"Could not process {hmd}")

    # 3. Skill dirs named lean-ctx
    skill_bases = [h / "skills"]
    if (h / "profiles").is_dir():
        skill_bases.extend((h / "profiles").glob("*/skills"))
    for base in skill_bases:
        if base.is_dir():
            d = base / "lean-ctx"
            if d.exists():
                if dry_run:
                    log_sub(f"[DRY-RUN] Would remove skill dir {d}")
                else:
                    shutil.rmtree(d, ignore_errors=True)
                    log_ok(f"Removed skill dir {d}")

    # 4. Zed settings.json
    zed = HOME / ".config" / "zed" / "settings.json"
    remove_mcp_servers(zed, dry_run)

    # 5. All ~/.config/*/mcp_servers.json templates
    for tpl in (HOME / ".config").glob("*/mcp_servers.json"):
        if tpl.is_file():
            removed = remove_mcp_servers(tpl, dry_run)
            if removed or dry_run:
                log_ok(f"Removed agents-arwaky servers from {tpl}")

    # 5b. Qwen settings.json.bak
    qwen_bak = HOME / ".qwen" / "settings.json.bak"
    if qwen_bak.is_file():
        removed = remove_mcp_servers(qwen_bak, dry_run)
        if removed or dry_run:
            log_ok(f"Removed agents-arwaky servers from {qwen_bak}")

    # 6. Binary remnants in internal-bin
    ibin = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share")) / "agents-arwaky" / "internal-bin"
    for b in ("lean-ctx", "_lc", "_lc_compress"):
        f = ibin / b
        if f.exists():
            if dry_run:
                log_sub(f"[DRY-RUN] Would remove binary {f}")
            else:
                f.unlink(missing_ok=True)
                log_ok(f"Removed binary {f}")

    log_ok("Legacy lean-ctx cleanup complete.")


# =============================================================================
# CONNECT (port of connect-agent.sh connect_* functions)
# =============================================================================
import json as _json


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
        log_skip(f"No active 9Router API Key found (empty/placeholder); skipping env injection for {target}.")
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


# --- per-harness connect functions ---
def connect_antigravity(force, dry_run, mcp_only, skills_only, env_only):
    log_header("Connecting to Google Antigravity...")
    cfg_dir = HOME / ".gemini" / "config"
    mcp_file = cfg_dir / "mcp_config.json"
    skills_dir = cfg_dir / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would merge MCP servers into {mcp_file}")
        else:
            merged = engine_merge_mcp(mcp_file, servers, force)
            for sub in ("antigravity-cli", "antigravity"):
                d = HOME / ".gemini" / sub
                if d.is_dir():
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "mcp_config.json").unlink(missing_ok=True)
                    try:
                        (d / "mcp_config.json").symlink_to(mcp_file)
                    except OSError:
                        pass
            log_ok("Antigravity MCP servers configured.")
    if not mcp_only and not env_only:
        for sf in get_all_skill_files():
            copy_skill_to_dir(sf, skills_dir, force, dry_run)
        for sub in ("antigravity-cli", "antigravity"):
            d = HOME / ".gemini" / sub
            if d.is_dir():
                try:
                    (d / "skills").unlink(missing_ok=True)
                    (d / "skills").symlink_to(skills_dir, target_is_directory=True)
                except OSError:
                    pass
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env("antigravity", dry_run)
    log_ok("Antigravity connect complete.")


def connect_hermes(force, dry_run, mcp_only, skills_only, env_only):
    log_header("Connecting to Hermes Agent (Main & Multi-Profiles)...")
    h = hermes_home()
    servers = load_generated_servers()
    if not skills_only and not env_only:
        for label, target_dir in hermes_targets(h):
            log_sub(f"Target MCP Config: {target_dir / 'config.yaml'}")
            if dry_run:
                log_sub(f"[DRY-RUN] Would merge MCP servers into {target_dir / 'config.yaml'}")
                continue
            target_dir.mkdir(parents=True, exist_ok=True)
            merged = engine_merge_mcp(target_dir / "config.yaml", servers, force)
            log_ok(f"Hermes MCP servers configured in {target_dir / 'config.yaml'}")
    if not mcp_only and not env_only:
        for label, target_dir in hermes_targets(h):
            for sf in get_all_skill_files():
                copy_skill_to_dir(sf, target_dir / "skills", force, dry_run)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env("hermes", dry_run)
    log_ok("Hermes connect complete.")


def connect_opencode(force, dry_run, mcp_only, skills_only, env_only):
    log_header("Connecting to OpenCode...")
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "opencode"
    cfg_file = cfg / "opencode.jsonc"
    skills_dir = cfg / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would update MCP servers in {cfg_file}")
        else:
            cfg.mkdir(parents=True, exist_ok=True)
            merged = engine_merge_mcp(cfg_file, servers, force)
            log_ok(f"OpenCode MCP servers configured in {cfg_file}")
    if not mcp_only and not env_only:
        for sf in get_all_skill_files():
            copy_skill_to_dir(sf, skills_dir, force, dry_run)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env("opencode", dry_run)
    log_ok("OpenCode connect complete.")


def connect_qwencode(force, dry_run, mcp_only, skills_only, env_only):
    log_header("Connecting to Qwen Code (qwencode)...")
    qwen_home = Path(os.environ.get("QWEN_HOME", HOME / ".qwen"))
    settings_file = qwen_home / "settings.json"
    skills_dir = qwen_home / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would merge MCP servers into {settings_file}")
        else:
            qwen_home.mkdir(parents=True, exist_ok=True)
            merged = engine_merge_mcp(settings_file, servers, force)
            log_ok(f"Qwen Code MCP servers configured in {settings_file}")
    if not mcp_only and not env_only:
        for sf in get_all_skill_files():
            copy_skill_to_dir(sf, skills_dir, force, dry_run)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env("qwencode", dry_run)
    log_ok("Qwen Code connect complete.")


def load_generated_servers():
    """Read mcpServers from mcp_servers.generated.json (or default static map)."""
    gen = REPO_ROOT / "mcp_servers.generated.json"
    if gen.exists():
        try:
            data = _json.loads(gen.read_text(encoding="utf-8"))
            return data.get("mcpServers", {})
        except Exception:
            pass
    names = default_servers_dict()
    return names


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


# --- dispatcher --------------------------------------------------------------
def cmd_disconnect(args):
    targets = []
    dry_run = False
    lean_ctx_only = False

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--antigravity", "antigravity", "agy"):
            targets.append("antigravity")
        elif a in ("--hermes", "hermes"):
            targets.append("hermes")
        elif a in ("--opencode", "opencode"):
            targets.append("opencode")
        elif a in ("--qwencode", "qwencode", "--qwen", "qwen", "qwen-code"):
            targets.append("qwencode")
        elif a in ("--all", "all"):
            targets = ["antigravity", "hermes", "opencode", "qwencode"]
        elif a in ("--lean-ctx", "lean-ctx", "lean_ctx"):
            lean_ctx_only = True
        elif a == "--dry-run":
            dry_run = True
        elif a in ("--help", "-h", "help"):
            print(__doc__)
            return 0
        else:
            log_err(f"Unknown target or option: {a}")
            return 1
        i += 1

    if lean_ctx_only:
        disconnect_legacy_lean_ctx(dry_run)
        return 0

    if not targets:
        log_err("No target agent harness specified.")
        print(__doc__)
        return 1

    # dedupe preserving order
    seen = set()
    targets = [t for t in targets if not (t in seen or seen.add(t))]

    print("Disconnecting agents-arwaky from agent harnesses...")
    print("------------------------------------------------------------------")
    for t in targets:
        if t == "antigravity":
            disconnect_antigravity(dry_run)
        elif t == "hermes":
            disconnect_hermes(dry_run)
        elif t == "opencode":
            disconnect_opencode(dry_run)
        elif t == "qwencode":
            disconnect_qwencode(dry_run)
        print("")
    print("------------------------------------------------------------------")
    print("\u2713 Disconnect complete. agents-arwaky entries removed from selected harnesses.")
    return 0


def cmd_connect(args):
    targets = []
    force = dry_run = mcp_only = skills_only = env_only = False
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--antigravity", "antigravity", "agy"):
            targets.append("antigravity")
        elif a in ("--hermes", "hermes"):
            targets.append("hermes")
        elif a in ("--opencode", "opencode"):
            targets.append("opencode")
        elif a in ("--qwencode", "qwencode", "--qwen", "qwen", "qwen-code"):
            targets.append("qwencode")
        elif a in ("--all", "all"):
            targets = ["antigravity", "hermes", "opencode", "qwencode"]
        elif a in ("--force", "-f"):
            force = True
        elif a == "--dry-run":
            dry_run = True
        elif a == "--mcp-only":
            mcp_only = True
        elif a == "--skills-only":
            skills_only = True
        elif a == "--env-only":
            env_only = True
        elif a in ("--help", "-h", "help"):
            print(__doc__)
            return 0
        else:
            log_err(f"Unknown target or option: {a}")
            return 1
        i += 1
    if not targets:
        log_err("No target agent harness specified.")
        print(__doc__)
        return 1
    seen = set()
    targets = [t for t in targets if not (t in seen or seen.add(t))]
    print("Connecting agents-arwaky to agent harnesses...")
    print("------------------------------------------------------------------")
    for t in targets:
        if t == "antigravity":
            connect_antigravity(force, dry_run, mcp_only, skills_only, env_only)
        elif t == "hermes":
            connect_hermes(force, dry_run, mcp_only, skills_only, env_only)
        elif t == "opencode":
            connect_opencode(force, dry_run, mcp_only, skills_only, env_only)
        elif t == "qwencode":
            connect_qwencode(force, dry_run, mcp_only, skills_only, env_only)
        print("")
    print("------------------------------------------------------------------")
    print("\u2713 Connection complete. Agent harnesses are now synchronized with agents-arwaky.")
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    # Accept both "aa connect/disconnect ..." style and direct calls
    args = argv[1:]
    if args and args[0] in ("disconnect", "unconnect"):
        return cmd_disconnect(args[1:])
    if args and args[0] == "connect":
        return cmd_connect(args[1:])
    if args and args[0] in ("--antigravity", "--hermes", "--opencode", "--qwencode", "--all",
                            "antigravity", "hermes", "opencode", "qwencode", "all"):
        # default action: connect (for backward compat with connect-agent.sh calls)
        return cmd_connect(args)
    return cmd_disconnect(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
