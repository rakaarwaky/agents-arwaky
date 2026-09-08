"""Qwen Code (qwencode) harness adapter — capabilities layer (P4-A2)."""
from __future__ import annotations

import os
from pathlib import Path

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

HARNESS_ID = "qwencode"
ALIASES = ("--qwencode", "qwencode", "--qwen", "qwen", "qwen-code")
ENV_TARGET = "qwencode"


def _qwen_home() -> Path:
    return Path(os.environ.get("QWEN_HOME", HOME / ".qwen"))


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
