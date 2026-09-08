"""Hermes Agent harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

from connect_shared import (  # type: ignore[import-not-found]
    copy_skill_to_dir,
    disconnect_hermes_instance,
    engine_merge_mcp,
    get_all_skill_files,
    hermes_home,
    hermes_targets,
    inject_9router_env,
    load_generated_servers,
    log_header,
    log_ok,
    log_sub,
)

HARNESS_ID = "hermes"
ALIASES = ("--hermes", "hermes")
ENV_TARGET = "hermes"


def connect(force, dry_run, mcp_only, skills_only, env_only):
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
            engine_merge_mcp(target_dir / "config.yaml", servers, force)
            log_ok(f"Hermes MCP servers configured in {target_dir / 'config.yaml'}")
    if not mcp_only and not env_only:
        for label, target_dir in hermes_targets(h):
            for sf in get_all_skill_files():
                copy_skill_to_dir(sf, target_dir / "skills", force, dry_run)
    if env_only or (not mcp_only and not skills_only):
        inject_9router_env(ENV_TARGET, dry_run)
    log_ok("Hermes connect complete.")


def disconnect(dry_run):
    log_header("Disconnecting from Hermes Agent (Main & Multi-Profiles)...")
    h = hermes_home()
    disconnect_hermes_instance(h, "Main Profile", dry_run)
    profiles = h / "profiles"
    if profiles.is_dir():
        for pdir in sorted(profiles.iterdir()):
            if pdir.is_dir():
                disconnect_hermes_instance(pdir, f"Profile: {pdir.name}", dry_run)
    log_ok("Hermes disconnect complete.")


def register() -> dict:
    """Register this harness adapter in the global registry."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "connect": connect,
        "disconnect": disconnect,
    }
