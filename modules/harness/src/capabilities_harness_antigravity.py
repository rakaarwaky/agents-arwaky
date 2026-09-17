"""Google Antigravity harness connector — port of connect/antigravity_adapter.py."""
from __future__ import annotations

from pathlib import Path

from modules.harness.src.capabilities_harness_shared import (
    HOME,
    get_all_skill_files,
    inject_9router_env,
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

HARNESS_ID = "antigravity"
ALIASES = ("--antigravity", "antigravity", "agy")
ENV_TARGET = "antigravity"
SKILL_LINK_VERIFIED = False  # agy skill-symlink probe never completed; keep copies


class AntigravityConnector(IHarnessConnector):
    """MCP merge, skill copy into ~/.gemini and 9router env injection.

    # Block 1: Configuration
    # Block 2: connect
    # Block 3: disconnect
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        self._cfg_dir = HOME / ".gemini" / "config"
        self._mcp_file = self._cfg_dir / "mcp_config.json"
        self._skills_dir = self._cfg_dir / "skills"

    # -- Block 2: connect -----------------------------------------------------------
    def connect(self, force: bool, dry_run: bool, mcp_only: bool, skills_only: bool, env_only: bool, copy_skills: bool = False) -> None:
        log_header("Connecting to Google Antigravity...")
        servers = load_generated_servers()
        if not skills_only and not env_only:
            if dry_run:
                log_sub(f"[DRY-RUN] Would merge MCP servers into {self._mcp_file}")
            else:
                engine_merge_mcp(self._mcp_file, servers, force)
                for sub in ("antigravity-cli", "antigravity"):
                    d = HOME / ".gemini" / sub
                    if d.is_dir():
                        d.mkdir(parents=True, exist_ok=True)
                        (d / "mcp_config.json").unlink(missing_ok=True)
                        try:
                            (d / "mcp_config.json").symlink_to(self._mcp_file)
                        except OSError:
                            pass
                log_ok("Antigravity MCP servers configured.")
        if not mcp_only and not env_only:
            link = resolve_skill_link(SKILL_LINK_VERIFIED, copy_skills)
            for skill_md in get_all_skill_files():
                provision_skill_to_dir(skill_md, self._skills_dir, force, dry_run, link=link)
            for sub in ("antigravity-cli", "antigravity"):
                d = HOME / ".gemini" / sub
                if d.is_dir():
                    try:
                        (d / "skills").unlink(missing_ok=True)
                        (d / "skills").symlink_to(self._skills_dir, target_is_directory=True)
                    except OSError:
                        pass
        if env_only or (not mcp_only and not skills_only):
            inject_9router_env(ENV_TARGET, dry_run)
        log_ok("Antigravity connect complete.")

    # -- Block 3: disconnect -----------------------------------------------------------
    def disconnect(self, force: bool, dry_run: bool) -> None:
        log_header("Disconnecting from Google Antigravity...")
        remove_mcp_servers(self._cfg_dir / "mcp_config.json", dry_run)
        remove_provisioned_skills(self._cfg_dir / "skills", dry_run)
        env_keys = ["NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR"]
        remove_env_keys(self._cfg_dir / ".env", env_keys, dry_run)
        for sub in ("antigravity-cli", "antigravity"):
            d = HOME / ".gemini" / sub
            if d.is_dir():
                remove_mcp_servers(d / "mcp_config.json", dry_run)
                remove_env_keys(d / ".env", env_keys, dry_run)
        log_ok("Antigravity disconnect complete.")


def register() -> dict:
    """Registration entry point (harness registry API)."""
    return {
        "id": HARNESS_ID,
        "aliases": ALIASES,
        "env_target": ENV_TARGET,
        "skill_link_verified": SKILL_LINK_VERIFIED,
        "connect": AntigravityConnector().connect,
        "disconnect": AntigravityConnector().disconnect,
    }
