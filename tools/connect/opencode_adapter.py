"""OpenCode harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

import os
from pathlib import Path

from connect_shared import (  # type: ignore[import-not-found]
    HOME,
    REPO_ROOT,
    link_skills_root,
    provision_skill_to_dir,
    resolve_skill_link,
    engine_merge_mcp,
    get_all_skill_files,
    inject_9router_env,
    load_generated_servers,
    log_header,
    log_ok,
    log_sub,
    remove_env_keys,
    remove_mcp_servers,
    remove_provisioned_skills,
)

HARNESS_ID = "opencode"
ALIASES = ("--opencode", "opencode")
ENV_TARGET = "opencode"
# Symlink provisioning is only enabled for harnesses verified to follow
# skill-dir symlinks. opencode was verified on 2026-09-13: `opencode debug
# skill` lists the full pack THROUGH a root-level skills symlink.
SKILL_LINK_VERIFIED = True


def _cfg_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "opencode"


def connect(force, dry_run, mcp_only, skills_only, env_only, copy_skills=False):
    log_header("Connecting to OpenCode...")
    cfg = _cfg_dir()
    cfg_file = cfg / "opencode.jsonc"
    skills_dir = cfg / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would update MCP servers in {cfg_file}")
        else:
            cfg.mkdir(parents=True, exist_ok=True)
            engine_merge_mcp(cfg_file, servers, force)
            log_ok(f"OpenCode MCP servers configured in {cfg_file}")
    if not mcp_only and not env_only:
        link = resolve_skill_link(SKILL_LINK_VERIFIED, copy_skills)
        if link:
            # whole skills root -> pack: manage skills once in the repo
            log_sub(f"Target Skills: {skills_dir} -> {REPO_ROOT / 'skills'} "
                    f"(whole-root symlink; manage the pack once)")
            link_skills_root(skills_dir, REPO_ROOT / "skills", force, dry_run)
        else:
            for sf in get_all_skill_files():
                provision_skill_to_dir(sf, skills_dir, force, dry_run, link=False)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env(ENV_TARGET, dry_run)
    log_ok("OpenCode connect complete.")


def disconnect(dry_run):
    log_header("Disconnecting from OpenCode...")
    cfg = _cfg_dir()
    remove_mcp_servers(cfg / "opencode.jsonc", dry_run)
    remove_provisioned_skills(cfg / "skills", dry_run)
    env_keys = ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"]
    remove_env_keys(cfg / ".env", env_keys, dry_run)
    legacy = HOME / ".opencode"
    if legacy.is_dir():
        remove_env_keys(legacy / ".env", env_keys, dry_run)
    log_ok("OpenCode disconnect complete.")


def register() -> dict:
    """Register this harness adapter in the global registry."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "connect": connect,
        "disconnect": disconnect,
    }
