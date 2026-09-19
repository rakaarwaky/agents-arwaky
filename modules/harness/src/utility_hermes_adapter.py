"""Hermes harness leaf adapter (utility layer) — provider-specific paths/keys only.

Leaf: imports stdlib + modules/shared only. Knows nothing about business
actions; capabilities dispatch here per harness id.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)


@dataclass(frozen=True)
class HermesAdapter:
    """Hermes provider data: one home, many targets (default profile + named ones)."""

    id: str = "hermes"
    aliases: tuple[str, ...] = ("hermes",)
    display: str = "Hermes Agent"
    # Hermes walks skill dirs with followlinks; its atomic writes replace the
    # file inside a linked dir, keeping the link intact.
    skill_link_verified: bool = True
    supports_mcp: bool = True
    supports_env: bool = True
    # 9Router custom-API wiring writes provider entries into config.yaml.
    supports_custom_api: bool = True
    custom_api_kind: str = "router-env"
    router_provider_id: str = "b-ai/qwen3.8-flash"
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcpServers"
    # Keys the disconnector drops (incl. router refs installed with env keys).
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    skill_sync_commands: tuple[str, ...] = ()

    def home(self) -> Path:
        return Path.home() / ".hermes"

    def config_files(self) -> tuple[Path, ...]:
        return (self.home() / "config.yaml",)

    def env_files(self) -> tuple[Path, ...]:
        h = self.home()
        files = [h / ".env"]
        profiles = h / "profiles"
        if profiles.is_dir():
            files += [p / ".env" for p in sorted(profiles.iterdir()) if p.is_dir()]
        return tuple(files)

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        """(label, target_dir): the per-instance MCP config.yaml locations."""
        h = self.home()
        targets: list[tuple[str, Path]] = [("Main Profile", h)]
        profiles = h / "profiles"
        if profiles.is_dir():
            targets.extend((f"Profile: {p.name}", p) for p in sorted(profiles.iterdir()) if p.is_dir())
        return tuple(targets)

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return (target_dir or self.home()) / "config.yaml"

    def skills_dir(self) -> Path:
        return self.home() / "skills"

    def session_conf_files(self) -> tuple[Path, ...]:
        """systemd user-session env layer that shadows harness .env files."""
        return (config_home() / "environment.d/9router.conf",)

    def credential_candidates(self) -> tuple[Path, ...]:
        return (
            agents_arwaky_config_dir() / "ninerouter.env",
            config_home() / "9router/.env",
            data_home() / "agents-arwaky/ninerouter.env",
        )
