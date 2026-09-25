"""Google Antigravity harness leaf adapter (capabilities layer) — provider data + protocol.

Implements `IHarnessProtocol` (AES403) and exports the `antigravity` provider
spec merged into `HARNESS_REGISTRY` by the root container. Provider data lives
in `AntigravityAdapter`; the protocol implementor routes the provider-scoped ops
(`supported` / `satisfied`) through `utility_harness_mechanics`.

Leaf: imports stdlib + modules/shared only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.contract_harness_protocol import IHarnessProtocol
from modules.shared.src.taxonomy_common_vo import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)
from modules.shared.src.taxonomy_harness_vo import ExitCode
from modules.shared.src.utility_harness_mechanics import dispatch_provider_op


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class AntigravityHarnessAdapter(IHarnessProtocol):
    """Antigravity provider behind the harness protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, object] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def execute(
        self,
        op: str,
        targets: tuple[str, ...],
        flags: dict[str, bool] | None = None,
    ) -> ExitCode:
        """Dispatch a provider-scoped op against this file's antigravity unit."""
        return dispatch_provider_op(self._units, op, targets, flags, label="antigravity adapter")

    # ─── Block 3: Dunder Methods ─────────────────────────────────────
    def __repr__(self) -> str:
        return f"AntigravityHarnessAdapter(providers={len(self._units)})"


# ---------------------------------------------------------------------------
# Provider spec (one registered instance per harness id)
# ---------------------------------------------------------------------------
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


SPEC = AntigravityAdapter()

#: harness_id → provider spec (merged by root_harness_container).
ADAPTER_UNITS: dict[str, object] = {SPEC.id: SPEC}


__all__ = [
    "ADAPTER_UNITS",
    "AntigravityAdapter",
    "AntigravityHarnessAdapter",
]
