"""Qwen Code (qwencode) harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations
from modules.harness.src.taxonomy_harness_vo import HarnessConfig


import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from modules.harness.src.utility_harness_shared import (
    HOME,
    PLACEHOLDER_KEYS,
    REPO_ROOT,
    discover_skill_roots,
    link_skills_root,
    provision_skill_to_dir,
    resolve_skill_link,
    engine_merge_mcp,
    get_9router_credentials,
    get_all_skill_files,
    inject_9router_env,
    load_generated_servers,
    log_header,
    log_ok,
    log_skip,
    log_sub,
    log_warn,
    remove_env_keys,
    remove_mcp_servers,
    remove_provisioned_skills,
)
from modules.harness.src.contract_harness_protocol import IHarnessConnector

HARNESS_ID = "qwencode"
ALIASES = ("--qwencode", "qwencode", "--qwen", "qwen", "qwen-code")
ENV_TARGET = "qwencode"
# Symlink provisioning gate: Verified by headless probe: qwen -p sees a symlinked skill dir in ~/.qwen/skills.
SKILL_LINK_VERIFIED = True
PROVIDER_ID = "my9router"
ROUTER_ENV_KEY = "NINEROUTER_KEY"

# ─── Block 1: Class Definition & Constructor ──────────────

class QwencodeConnector(IHarnessConnector):
    """Module-level connect/disconnect bound to the IHarnessConnector contract."""

    # ─── Block 2: Protocol ABC Method Implementation ──────────

    def connect(self, force: bool, dry_run: bool, mcp_only: bool, skills_only: bool, env_only: bool, copy_skills: bool = False) -> None:
        connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills)

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def disconnect(self, force: bool, dry_run: bool) -> None:
        disconnect(dry_run)
def _qwen_home() -> Path:
    return Path(os.environ.get("QWEN_HOME", HOME / ".qwen"))


def _router_v1(url: str) -> str:
    base = url.rstrip("/")
    return base if base.endswith("/v1") else base + "/v1"


def _probe_router(url: str, key: str, model: str) -> tuple[bool, str]:
    """Live POST /chat/completions through the router; returns (ok, detail)."""
    req = urllib.request.Request(
        _router_v1(url) + "/chat/completions",
        data=json.dumps({"model": model,
                         "messages": [{"role": "user", "content": "ping"}],
                         "max_tokens": 1}).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except (OSError, ValueError) as exc:
        return False, str(exc)


def sync_router_provider(settings_file: Path, url: str, dry_run: bool):
    """Bind the my9router provider entry to NINEROUTER_KEY and verify auth.

    inject_9router_env() only writes ~/.qwen/.env; Qwen Code resolves a
    provider's credential from process.env[envKey], so a stale envKey (or an
    inline settings.env key captured by the interactive /auth Custom Provider
    flow) keeps failing with 401 even after aa connect. This syncs the entry
    the connector owns and then probes the router with the effective key.
    """
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log_warn(f"Could not read {settings_file} ({exc}); provider sync SKIPPED.")
        return
    openai_list = settings.setdefault("modelProviders", {}).setdefault("openai", [])
    if not isinstance(openai_list, list):
        log_warn("modelProviders.openai is not a list; provider sync SKIPPED.")
        return
    v1 = _router_v1(url)
    entry = next((m for m in openai_list
                  if isinstance(m, dict)
                  and (m.get("id") == PROVIDER_ID or m.get("baseUrl") == v1)), None)
    if entry is None:
        entry = {"id": PROVIDER_ID, "name": PROVIDER_ID}
        openai_list.append(entry)
    model = entry.get("id", PROVIDER_ID)
    selected = settings.get("security", {}).get("auth", {}).get("selectedType")
    changed = (entry.get("baseUrl") != v1 or entry.get("envKey") != ROUTER_ENV_KEY
               or selected != "openai" or settings.get("model", {}).get("name") != model)

    if dry_run:
        if changed:
            log_sub(f"[DRY-RUN] Would bind provider '{model}' in {settings_file} "
                    f"to {ROUTER_ENV_KEY} (baseUrl {v1})")
        else:
            log_sub(f"[DRY-RUN] Provider '{model}' already bound to {ROUTER_ENV_KEY}")
        return

    entry["baseUrl"] = v1
    entry.setdefault("name", model)
    prev_env_key = entry.get("envKey")
    entry["envKey"] = ROUTER_ENV_KEY
    settings.setdefault("security", {}).setdefault("auth", {})["selectedType"] = "openai"
    m = settings.setdefault("model", {})
    m["name"] = model
    m["baseUrl"] = v1
    # The interactive /auth "Custom Provider" flow parks the key inline under
    # settings.env as QWEN_CUSTOM_API_KEY_<...>. Once this connector owns the
    # provider, drop that shadow copy so a rotated 9Router key cannot go stale.
    inline = settings.get("env")
    if (isinstance(inline, dict) and prev_env_key and prev_env_key != ROUTER_ENV_KEY
            and prev_env_key.startswith("QWEN_CUSTOM_API_KEY_") and prev_env_key in inline):
        del inline[prev_env_key]
        if not inline:
            settings.pop("env", None)
    settings_file.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    log_ok(f"Provider '{model}' bound to {ROUTER_ENV_KEY} at {v1}.")

    _, live_key = get_9router_credentials()
    if not live_key or live_key in PLACEHOLDER_KEYS:
        log_warn(f"No active 9Router key to verify provider '{model}' against.")
        return
    ok, detail = _probe_router(url, live_key, model)
    if ok:
        log_ok(f"9Router live check passed ({detail}).")
    else:
        log_warn(f"9Router live check FAILED for '{model}' at {url} ({detail}). "
                 f"Check the key with 'aa 9router'.")


def _read_settings(settings_file: Path):
    """Parse settings.json, tolerating a fresh install (missing file -> {}).

    Returns (settings, usable). usable=False means the file is unreadable or
    malformed and must NOT be rewritten — never clobber a config we cannot parse.
    """
    try:
        raw = settings_file.read_text(encoding="utf-8") if settings_file.is_file() else ""
        settings = json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError) as exc:
        log_warn(f"Could not read {settings_file} ({exc}); leaving it untouched.")
        return None, False
    if not isinstance(settings, dict):
        log_warn(f"{settings_file} is not a JSON object; leaving it untouched.")
        return None, False
    return settings, True

def _write_settings(settings_file: Path, settings: dict):
    """Replace settings.json in one step.

    A SessionStart hook now rewrites this file while other Qwen Code sessions
    may be reading it at their own startup, so write a sibling and rename it
    over the target: readers see either the old file or the new one, never a
    truncated middle.
    """
    tmp = settings_file.with_name(settings_file.name + ".tmp")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, settings_file)

def _tilde(path: Path) -> str:
    """Render a path HOME-relative with a ~ prefix, the form settings.json uses."""
    try:
        return "~/" + path.relative_to(HOME).as_posix()
    except ValueError:
        return path.as_posix()

def _in_pack(entry: str, pack_root: Path) -> bool:
    """True when a skills.directories entry points at the pack (any spelling)."""
    try:
        return Path(os.path.expanduser(entry.strip())).resolve().is_relative_to(pack_root)
    except OSError:
        return False

def sync_skill_directories(settings_file: Path, roots, dry_run: bool):
    """Register every pack category folder as a skills root in settings.json.

    The loader scans exactly ONE level below each skills root, so the whole-root
    symlink only shows it the category folders themselves: a nested
    ``skills/<category>/<skill>/SKILL.md`` stays invisible until ``<category>``
    is registered here. Re-running the connector after a category is added,
    renamed or deleted is what keeps the pack fully loaded, so the list is
    rebuilt from disk every time instead of being appended to. Entries that
    point outside the pack are the user's own roots and are preserved.
    """
    pack_root = (REPO_ROOT / "skills").resolve()
    want = [_tilde(r) for r in roots]
    settings, usable = _read_settings(settings_file)
    if not usable:
        return
    skills = settings.setdefault("skills", {})
    if not isinstance(skills, dict):
        log_warn("skills is not an object; skill directory sync SKIPPED.")
        return
    current = skills.get("directories")
    if current is not None and not isinstance(current, list):
        log_warn("skills.directories is not a list; skill directory sync SKIPPED.")
        return
    current = [str(d) for d in (current or [])]
    foreign = [d for d in current if not _in_pack(d, pack_root)]
    if set(current) == set(foreign) | set(want):
        log_skip(f"{len(want)} pack skill directories already registered in {settings_file}")
        return
    added = [d for d in want if d not in current]
    dropped = [d for d in current if _in_pack(d, pack_root) and d not in want]
    if dry_run:
        log_sub(f"[DRY-RUN] Would register {len(want)} skill directories in "
                f"{settings_file} (+{len(added)} new, -{len(dropped)} stale)")
        for d in added:
            log_sub(f"  + {d}")
        for d in dropped:
            log_sub(f"  - {d}")
        return
    skills["directories"] = foreign + want
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    _write_settings(settings_file, settings)
    log_ok(f"Registered {len(want)} skill directories in {settings_file} "
           f"(+{len(added)} new, -{len(dropped)} stale).")
    for d in added:
        log_sub(f"  + {d}")
    for d in dropped:
        log_sub(f"  - {d}")
    if added or dropped:
        log_sub("Restart any running Qwen Code session to pick the list up.")

# Identifies the hook entry this connector owns; found and replaced by name so
# a moved checkout refreshes its command instead of leaving a dead duplicate.
SKILL_SYNC_HOOK = "arwaky-skill-sync"

def _skill_sync_command() -> str:
    """The re-registration command, runnable straight from a hook.

    Absolute script path and no reliance on the `aa` launcher being on this
    process' PATH; connect_shared puts tools/lib on sys.path itself.
    """
    return (f"python3 {(REPO_ROOT / 'tools' / 'cli' / 'arwaky.py').as_posix()}"
            f" connect --qwencode --skills-only")


def sync_skill_sync_hook(settings_file: Path, dry_run: bool):
    """Install (or refresh) the SessionStart hook that re-registers skill roots.

    Qwen Code reads skills.directories once at startup, and this connector
    measured SessionStart firing ~230ms AFTER skill discovery — so the hook
    cannot repair the session that runs it, only the next one. That is still
    what makes the pack self-maintaining: a category folder added at any time
    is registered by the next session start, and one restart later its skills
    are live. --skills-only keeps it off MCP, .env and the provider, and the
    directory sync writes nothing when the list already matches, so running it
    on every start is cheap and silent.
    """
    settings, usable = _read_settings(settings_file)
    if not usable:
        return
    command = _skill_sync_command()
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        log_warn("hooks is not an object; skill sync hook SKIPPED.")
        return
    starts = hooks.setdefault("SessionStart", [])
    if not isinstance(starts, list):
        log_warn("hooks.SessionStart is not a list; skill sync hook SKIPPED.")
        return
    for group in starts:
        if not isinstance(group, dict):
            continue
        owned = next((h for h in (group.get("hooks") or [])
                      if isinstance(h, dict) and h.get("name") == SKILL_SYNC_HOOK), None)
        if owned is None:
            continue
        if owned.get("command") == command:
            log_skip(f"Skill sync hook already installed in {settings_file}")
            return
        if dry_run:
            log_sub(f"[DRY-RUN] Would refresh the '{SKILL_SYNC_HOOK}' hook command in "
                    f"{settings_file}")
            return
        owned["command"] = command
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        _write_settings(settings_file, settings)
        log_ok(f"Refreshed the '{SKILL_SYNC_HOOK}' hook command in {settings_file}.")
        return
    if dry_run:
        log_sub(f"[DRY-RUN] Would install the '{SKILL_SYNC_HOOK}' SessionStart hook "
                f"in {settings_file}")
        return
    starts.append({
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "name": SKILL_SYNC_HOOK,
            "command": command,
            "timeout": 30000,
        }],
    })
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    _write_settings(settings_file, settings)
    log_ok(f"Installed the '{SKILL_SYNC_HOOK}' SessionStart hook in {settings_file}.")

def remove_skill_sync_hook(settings_file: Path, dry_run: bool):
    """Drop only the hook entry this connector owns; foreign hooks stay."""
    settings, usable = _read_settings(settings_file)
    if not usable:
        return
    hooks = settings.get("hooks")
    starts = hooks.get("SessionStart") if isinstance(hooks, dict) else None
    if not isinstance(starts, list) or not starts:
        log_skip("No skill sync hook to remove")
        return
    kept_groups, removed = [], 0
    for group in starts:
        if not isinstance(group, dict):
            kept_groups.append(group)
            continue
        owned, others = [], []
        for h in (group.get("hooks") or []):
            (owned if isinstance(h, dict) and h.get("name") == SKILL_SYNC_HOOK
             else others).append(h)
        removed += len(owned)
        if others:
            kept_groups.append({**group, "hooks": others})
    if not removed:
        log_skip("No skill sync hook to remove")
        return
    if dry_run:
        log_sub(f"[DRY-RUN] Would remove {removed} skill sync hook(s) from "
                f"{settings_file}")
        return
    settings["hooks"]["SessionStart"] = kept_groups
    _write_settings(settings_file, settings)
    log_ok(f"Removed {removed} skill sync hook(s) from {settings_file}.")

def connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills=False):
    log_header("Connecting to Qwen Code (qwencode)...")
    qwen_home = _qwen_home()
    settings_file = qwen_home / "settings.json"
    skills_dir = qwen_home / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would merge MCP servers into {settings_file}")
        else:
            qwen_home.mkdir(parents=True, exist_ok=True)
            engine_merge_mcp(settings_file, servers, force)
            log_ok(f"Qwen Code MCP servers configured in {settings_file}")
    if not mcp_only and not env_only:
        link = resolve_skill_link(SKILL_LINK_VERIFIED, copy_skills)
        if link:
            log_sub(f"Target Skills: {skills_dir} -> {REPO_ROOT / 'skills'} "
                    f"(whole-root symlink; manage the pack once)")
            link_skills_root(skills_dir, REPO_ROOT / "skills", force, dry_run)
            sync_skill_directories(settings_file, discover_skill_roots(), dry_run)
            sync_skill_sync_hook(settings_file, dry_run)
        else:
            for sf in get_all_skill_files():
                provision_skill_to_dir(sf, skills_dir, force, dry_run, link=False)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env(ENV_TARGET, dry_run)
        if settings_file.is_file():
            sync_router_provider(settings_file, get_9router_credentials()[0], dry_run)
    log_ok("Qwen Code connect complete.")


def disconnect(dry_run):
    log_header("Disconnecting from Qwen Code (qwencode)...")
    qwen_home = _qwen_home()
    remove_mcp_servers(qwen_home / "settings.json", dry_run)
    remove_provisioned_skills(qwen_home / "skills", dry_run)
    remove_skill_sync_hook(qwen_home / "settings.json", dry_run)
    # No roots left behind pointing into a pack this harness no longer reads.
    sync_skill_directories(qwen_home / "settings.json", (), dry_run)
    remove_env_keys(qwen_home / ".env",
                    ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"], dry_run)
    log_ok("Qwen Code disconnect complete.")

def register() -> dict:
    """Register this harness adapter in the global registry."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "connect": connect,
        "disconnect": disconnect,
    }

__all__ = ['HarnessConfig']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"HarnessConfig": HarnessConfig}
