"""OpenCode harness leaf adapter (utility layer) — provider-specific paths/keys only.

Leaf: imports stdlib + modules/shared only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
    tool_config_dir,
)


@dataclass(frozen=True)
class OpencodeAdapter:
    """OpenCode provider data (config dir under XDG_CONFIG_HOME)."""

    id: str = "opencode"
    aliases: tuple[str, ...] = ("opencode",)
    display: str = "OpenCode"
    # Verified 2026-09-13: `opencode debug skill` lists the full pack THROUGH
    # a root-level skills symlink.
    skill_link_verified: bool = True
    supports_mcp: bool = True
    supports_env: bool = True
    # OpenCode has no known config-format hook for a custom API provider.
    supports_custom_api: bool = False
    custom_api_kind: str = ""
    router_provider_id: str = ""
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcp"
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    skill_sync_commands: tuple[str, ...] = ()

    def home(self) -> Path:
        return tool_config_dir("opencode")

    def config_files(self) -> tuple[Path, ...]:
        return (self.home() / "opencode.jsonc",)

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return (target_dir or self.home()) / "opencode.jsonc"

    def env_files(self) -> tuple[Path, ...]:
        files = [self.home() / ".env"]
        legacy = Path.home() / ".opencode"
        if legacy.is_dir():
            files.append(legacy / ".env")
        return tuple(files)

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        return (("OpenCode", self.home()),)

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
