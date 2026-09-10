"""Qwen Code (qwencode) harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from connect_shared import (  # type: ignore[import-not-found]
    HOME,
    PLACEHOLDER_KEYS,
    copy_skill_to_dir,
    engine_merge_mcp,
    get_9router_credentials,
    get_all_skill_files,
    inject_9router_env,
    load_generated_servers,
    log_header,
    log_ok,
    log_sub,
    log_warn,
    remove_env_keys,
    remove_mcp_servers,
    remove_provisioned_skills,
)

HARNESS_ID = "qwencode"
ALIASES = ("--qwencode", "qwencode", "--qwen", "qwen", "qwen-code")
ENV_TARGET = "qwencode"
PROVIDER_ID = "my9router"
ROUTER_ENV_KEY = "NINEROUTER_KEY"


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


def connect(force, dry_run, mcp_only, skills_only, env_only):
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
        for sf in get_all_skill_files():
            copy_skill_to_dir(sf, skills_dir, force, dry_run)
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
