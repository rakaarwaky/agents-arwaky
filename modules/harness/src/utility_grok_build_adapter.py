"""Grok Build harness leaf adapter (utility layer) — provider-specific paths/keys only.

Leaf: imports stdlib + modules/shared only.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)

@dataclass(frozen=True)
class GrokBuildAdapter:
    """Grok Build provider data (TOML config, custom-API provider entries)."""

    id: str = "grok-build"
    aliases: tuple[str, ...] = ("grok", "grok-build")
    display: str = "Grok Build"
    skill_link_verified: bool = True
    supports_mcp: bool = True
    supports_env: bool = True
    # Custom-API wiring binds the 9Router provider into config.toml's model table.
    supports_custom_api: bool = True
    custom_api_kind: str = "config-toml"
    router_provider_id: str = "b-ai/qwen3.8-flash"
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcp_servers"
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    skill_sync_commands: tuple[str, ...] = ()

    def home(self) -> Path:
        return Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))

    def config_files(self) -> tuple[Path, ...]:
        return (self.home() / "config.toml",)

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return (target_dir or self.home()) / "config.toml"

    def env_files(self) -> tuple[Path, ...]:
        return (self.home() / ".env",)

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        return (("Grok Build", self.home()),)

    def skills_dir(self) -> Path:
        return self.home() / "skills"

    def session_conf_files(self) -> tuple[Path, ...]:
        return (config_home() / "environment.d/9router.conf",)

    def credential_candidates(self) -> tuple[Path, ...]:
        return (
            agents_arwaky_config_dir() / "ninerouter.env",
            config_home() / "9router/.env",
            data_home() / "agents-arwaky/ninerouter.env",
        )
