"""Grok Build harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

import os
from pathlib import Path

from modules.harness.src.capabilities_harness_shared import (  # type: ignore[import-not-found]
    HOME,
    PLACEHOLDER_KEYS,
    REPO_ROOT,
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
    log_sub,
    log_warn,
    remove_env_keys,
    remove_mcp_servers,
    remove_provisioned_skills,
)
from modules.harness.contract.contract_harness_protocol import IHarnessConnector

HARNESS_ID = "grok-build"
ALIASES = ("--grok-build", "grok-build", "--grok", "grok")
ENV_TARGET = "grok-build"
SKILL_LINK_VERIFIED = True
PROVIDER_ID = "b-ai/qwen3.8-flash"
ROUTER_BASE_URL = "http://127.0.0.1:20128/v1"


def _grok_home() -> Path:
    return Path(os.environ.get("GROK_HOME", HOME / ".grok"))


def _router_v1(url: str) -> str:
    base = url.rstrip("/")
    return base if base.endswith("/v1") else base + "/v1"


def sync_router_provider(cfg_file: Path, dry_run: bool):
    """Bind the 9Router provider in Grok Build's config.toml."""
    from modules.shared.src.config.capabilities_config_engine import save_file, load_file
    url = _router_v1(get_9router_credentials()[0])
    if dry_run:
        log_sub(f"[DRY-RUN] Would add 9Router provider '{PROVIDER_ID}' at {url} in {cfg_file}")
        return

    if not cfg_file.exists():
        log_warn(f"{cfg_file} not found; provider sync SKIPPED.")
        return

    try:
        data, fmt = load_file(cfg_file)
    except (OSError, Exception) as exc:
        log_warn(f"Could not read {cfg_file} ({exc}); provider sync SKIPPED.")
        return

    # Set models default
    models_section = data.setdefault("models", {})
    models_section["default"] = PROVIDER_ID
    data["models"] = models_section

    # Set model entry under top-level "model" key (not inside "models")
    data["model"] = {PROVIDER_ID: {
        "model": PROVIDER_ID,
        "base_url": url,
        "name": PROVIDER_ID,
        "env_key": "NINEROUTER_KEY",
        "api_backend": "responses",
    }}

    if not dry_run:
        save_file(cfg_file, data, fmt)
    log_ok(f"9Router provider '{PROVIDER_ID}' bound to NINEROUTER_KEY at {url}.")

    live_key = get_9router_credentials()[1]
    if not live_key or live_key in PLACEHOLDER_KEYS:
        log_warn("No active 9Router key to verify provider against.")
        return
    try:
        import urllib.request, urllib.error, json
        req = urllib.request.Request(
            url + "/chat/completions",
            data=json.dumps({"model": PROVIDER_ID,
                             "messages": [{"role": "user", "content": "ping"}],
                             "max_tokens": 1}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {live_key}"},
            method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            log_ok(f"9Router live check passed (HTTP {resp.status}).")
    except urllib.error.HTTPError as exc:
        log_warn(f"9Router live check FAILED ({exc.code}). Check the key with 'aa 9router'.")
    except (OSError, ValueError) as exc:
        log_warn(f"9Router live check FAILED ({exc}).")


def connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills=False):
    log_header("Connecting to Grok Build...")
    g = _grok_home()
    cfg_file = g / "config.toml"
    skills_dir = g / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would merge MCP servers into {cfg_file}")
        else:
            cfg_file.parent.mkdir(parents=True, exist_ok=True)
            if not cfg_file.exists():
                cfg_file.write_text("", encoding="utf-8")
            engine_merge_mcp(cfg_file, servers, force)
            log_ok(f"Grok Build MCP servers configured in {cfg_file}")
        sync_router_provider(cfg_file, dry_run)
    if not mcp_only and not env_only:
        link = resolve_skill_link(SKILL_LINK_VERIFIED, copy_skills)
        if link:
            log_sub(f"Target Skills: {skills_dir} -> {REPO_ROOT / 'skills'} "
                    f"(whole-root symlink; manage the pack once)")
            link_skills_root(skills_dir, REPO_ROOT / "skills", force, dry_run)
        else:
            for sf in get_all_skill_files():
                provision_skill_to_dir(sf, skills_dir, force, dry_run, link=False)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env(ENV_TARGET, dry_run)
    log_ok("Grok Build connect complete.")


def disconnect(dry_run):
    log_header("Disconnecting from Grok Build...")
    g = _grok_home()
    remove_mcp_servers(g / "config.toml", dry_run)
    remove_provisioned_skills(g / "skills", dry_run)
    env_keys = ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"]
    remove_env_keys(g / ".env", env_keys, dry_run)
    log_ok("Grok Build disconnect complete.")


class GrokBuildConnector(IHarnessConnector):
    """Module-level connect/disconnect bound to the IHarnessConnector contract."""

    def connect(self, force: bool, dry_run: bool, mcp_only: bool, skills_only: bool, env_only: bool, copy_skills: bool = False) -> None:
        connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills)

    def disconnect(self, force: bool, dry_run: bool) -> None:
        disconnect(dry_run)


def register() -> dict:
    """Register this harness adapter in the global registry."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "connect": connect,
        "disconnect": disconnect,
    }
