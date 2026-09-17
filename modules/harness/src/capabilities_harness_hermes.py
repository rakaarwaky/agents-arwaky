"""Hermes Agent harness connector — port of connect/hermes_adapter.py."""
from __future__ import annotations

from modules.harness.src.capabilities_harness_shared import (
    REPO_ROOT,
    disconnect_hermes_instance,
    get_all_skill_files,
    hermes_home,
    hermes_targets,
    inject_9router_env,
    link_skills_root,
    load_generated_servers,
    log_header,
    log_ok,
    log_sub,
    provision_skill_to_dir,
    resolve_skill_link,
    engine_merge_mcp,
)
from modules.shared.src.harness.contract_harness_protocol import IHarnessConnector

HARNESS_ID = "hermes"
ALIASES = ("--hermes", "hermes")
ENV_TARGET = "hermes"
SKILL_LINK_VERIFIED = True  # Hermes walks skills with followlinks


class HermesConnector(IHarnessConnector):
    """MCP merge into all profiles, whole-root skill link, env injection.

    # Block 1: Configuration
    # Block 2: connect
    # Block 3: disconnect
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        self._home = hermes_home()

    # -- Block 2: connect -----------------------------------------------------------
    def connect(self, force: bool, dry_run: bool, mcp_only: bool, skills_only: bool, env_only: bool, copy_skills: bool = False) -> None:
        log_header("Connecting to Hermes Agent (MCP & env: all profiles · Skills: default only)...")
        h = self._home
        servers = load_generated_servers()
        if not skills_only and not env_only:
            for label, target_dir in hermes_targets(h):
                log_sub(f"Target MCP Config: {target_dir / 'config.yaml'}")
                if dry_run:
                    log_sub(f"[DRY-RUN] Would merge MCP servers into {target_dir / 'config.yaml'}")
                    continue
                target_dir.mkdir(parents=True, exist_ok=True)
                engine_merge_mcp(target_dir / "config.yaml", servers, force)
                log_ok(f"Hermes MCP servers configured in {target_dir / 'config.yaml'}")
        if not mcp_only and not env_only:
            link = resolve_skill_link(SKILL_LINK_VERIFIED, copy_skills)
            skills_root = h / "skills"
            if link:
                log_sub(f"Target Skills: {skills_root} -> {REPO_ROOT / 'skills'} "
                        f"(whole-root symlink; manage the pack once)")
                link_skills_root(skills_root, REPO_ROOT / "skills", force, dry_run)
            else:
                log_sub(f"Target Skills: {skills_root} (default profile only, copied)")
                for skill_md in get_all_skill_files():
                    provision_skill_to_dir(skill_md, skills_root, force, dry_run, link=False)
        if env_only or (not mcp_only and not skills_only):
            inject_9router_env(ENV_TARGET, dry_run)
        log_ok("Hermes connect complete.")

    # -- Block 3: disconnect -----------------------------------------------------------
    def disconnect(self, force: bool, dry_run: bool) -> None:
        log_header("Disconnecting from Hermes Agent (Main & Multi-Profiles)...")
        h = self._home
        disconnect_hermes_instance(h, "Main Profile", dry_run)
        profiles = h / "profiles"
        if profiles.is_dir():
            for pdir in sorted(profiles.iterdir()):
                if pdir.is_dir():
                    disconnect_hermes_instance(pdir, f"Profile: {pdir.name}", dry_run)
        log_ok("Hermes disconnect complete.")


def register() -> dict:
    """Registration entry point (harness registry API)."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "skill_link_verified": SKILL_LINK_VERIFIED,
        "connect": HermesConnector().connect,
        "disconnect": HermesConnector().disconnect,
    }
