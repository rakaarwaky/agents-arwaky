"""Google Antigravity harness leaf adapter (utility layer) — provider paths/keys only.

Leaf: imports stdlib + modules/shared only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.taxonomy_common_vo import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)


@dataclass(frozen=True)
class AntigravityAdapter:
    """Antigravity provider data (Gemini config dir; per-skill snapshots)."""

    id: str = "antigravity"
    aliases: tuple[str, ...] = ("agy", "antigravity")
    display: str = "Google Antigravity"
    # agy's skill-discovery probe still unverified (429 quota on 2026-09-13);
    # keep per-skill copies until a clean probe proves symlink following.
    skill_link_verified: bool = False
    supports_mcp: bool = True
    supports_env: bool = True
    supports_custom_api: bool = False
    custom_api_kind: str = ""
    router_provider_id: str = ""
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcpServers"
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    skill_sync_commands: tuple[str, ...] = ()
    # The canonical config is mirrored into the sub-tool homes as symlinks.
    mirror_dirs: tuple[str, ...] = ("antigravity-cli", "antigravity")

    def home(self) -> Path:
        return Path.home() / ".gemini"

    def config_files(self) -> tuple[Path, ...]:
        return (self.home() / "config",)

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return (target_dir or self.home() / "config") / "mcp_config.json"

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        return (("Antigravity", self.home() / "config"),)

    def env_files(self) -> tuple[Path, ...]:
        files = [self.home() / "config" / ".env"]
        for sub in self.mirror_dirs:
            d = self.home() / sub
            if d.is_dir():
                files.append(d / ".env")
        return tuple(files)

    def skills_dir(self) -> Path:
        return self.home() / "config" / "skills"

    def mirror_dir(self, sub: str) -> Path:
        return self.home() / sub

    def session_conf_files(self) -> tuple[Path, ...]:
        return (config_home() / "environment.d/9router.conf",)

    def credential_candidates(self) -> tuple[Path, ...]:
        return (
            agents_arwaky_config_dir() / "ninerouter.env",
            config_home() / "9router/.env",
            data_home() / "agents-arwaky/ninerouter.env",
        )
