"""Google Antigravity harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

from connect_shared import (  # type: ignore[import-not-found]
    HOME,
    copy_skill_to_dir,
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

HARNESS_ID = "antigravity"
ALIASES = ("--antigravity", "antigravity", "agy")
ENV_TARGET = "antigravity"


def connect(force, dry_run, mcp_only, skills_only, env_only):
    log_header("Connecting to Google Antigravity...")
    cfg_dir = HOME / ".gemini" / "config"
    mcp_file = cfg_dir / "mcp_config.json"
    skills_dir = cfg_dir / "skills"
    servers = load_generated_servers()
    if not skills_only and not env_only:
        if dry_run:
            log_sub(f"[DRY-RUN] Would merge MCP servers into {mcp_file}")
        else:
            engine_merge_mcp(mcp_file, servers, force)
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
        inject_9router_env(ENV_TARGET, dry_run)
    log_ok("Antigravity connect complete.")


def disconnect(dry_run):
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


def register() -> dict:
    """Register this harness adapter in the global registry."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "connect": connect,
        "disconnect": disconnect,
    }
