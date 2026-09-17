"""OpenCode harness connector — port of connect/opencode_adapter.py."""
from __future__ import annotations

import os
from pathlib import Path

from modules.harness.src.capabilities_harness_shared import (
    HOME,
    REPO_ROOT,
    get_all_skill_files,
    inject_9router_env,
    link_skills_root,
    load_generated_servers,
    log_header,
    log_ok,
    log_sub,
    provision_skill_to_dir,
    remove_env_keys,
    remove_mcp_servers,
    remove_provisioned_skills,
    resolve_skill_link,
    engine_merge_mcp,
)
from modules.shared.src.harness.contract_harness_protocol import IHarnessConnector

HARNESS_ID = "opencode"
ALIASES = ("--opencode", "opencode")
ENV_TARGET = "opencode"
SKILL_LINK_VERIFIED = True  # verified 2026-09-13 via `opencode debug skill`


def _cfg_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "opencode"


class OpencodeConnector(IHarnessConnector):
    """MCP merge into opencode.jsonc, whole-root skill link, env injection.

    # Block 1: Configuration
    # Block 2: connect
    # Block 3: disconnect
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        self._cfg = _cfg_dir()

    # -- Block 2: connect -----------------------------------------------------------
    def connect(self, force: bool, dry_run: bool, mcp_only: bool, skills_only: bool, env_only: bool, copy_skills: bool = False) -> None:
        log_header("Connecting to OpenCode...")
        cfg = self._cfg
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
                log_sub(f"Target Skills: {skills_dir} -> {REPO_ROOT / 'skills'} "
                        f"(whole-root symlink; manage the pack once)")
                link_skills_root(skills_dir, REPO_ROOT / "skills", force, dry_run)
            else:
                for skill_md in get_all_skill_files():
                    provision_skill_to_dir(skill_md, skills_dir, force, dry_run, link=False)
        if env_only or (not mcp_only and not skills_only):
            inject_9router_env(ENV_TARGET, dry_run)
        log_ok("OpenCode connect complete.")

    # -- Block 3: disconnect -----------------------------------------------------------
    def disconnect(self, force: bool, dry_run: bool) -> None:
        log_header("Disconnecting from OpenCode...")
        cfg = self._cfg
        remove_mcp_servers(cfg / "opencode.jsonc", dry_run)
        remove_provisioned_skills(cfg / "skills", dry_run)
        env_keys = ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"]
        remove_env_keys(cfg / ".env", env_keys, dry_run)
        legacy = HOME / ".opencode"
        if legacy.is_dir():
            remove_env_keys(legacy / ".env", env_keys, dry_run)
        log_ok("OpenCode disconnect complete.")


def register() -> dict:
    """Registration entry point (harness registry API)."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "skill_link_verified": SKILL_LINK_VERIFIED,
        "connect": OpencodeConnector().connect,
        "disconnect": OpencodeConnector().disconnect,
    }
