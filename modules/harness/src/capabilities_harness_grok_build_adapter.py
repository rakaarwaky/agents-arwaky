"""Grok Build harness leaf adapter (capabilities layer) — provider data + protocol.

Implements `IHarnessProtocol` (AES403) and exports the `grok-build` provider
spec merged into `HARNESS_REGISTRY` by the root container. Provider data lives
in `GrokBuildAdapter`; the protocol implementor routes the provider-scoped ops
(`supported` / `satisfied`) through `utility_harness_mechanics`.

Leaf: imports stdlib + modules/shared only.
"""
from __future__ import annotations

import os
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


# ─── Block 1: Class Definition & Constructor ──────────────
class GrokBuildHarnessAdapter(IHarnessProtocol):
    """Grok Build provider behind the harness protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, object] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        targets: tuple[str, ...],
        flags: dict[str, bool] | None = None,
    ) -> ExitCode:
        """Dispatch a provider-scoped op against this file's grok-build unit."""
        return dispatch_provider_op(self._units, op, targets, flags, label="grok-build adapter")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"GrokBuildHarnessAdapter(providers={len(self._units)})"


# ---------------------------------------------------------------------------
# Provider spec (one registered instance per harness id)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GrokBuildAdapter:
    """Grok Build provider data (TOML config, custom-API provider entries)."""

    id: str = "grok-build"
    aliases: tuple[str, ...] = ("grok", "grok-build")
    display: str = "Grok Build"
    skill_link_verified: bool = True
    supports_mcp: bool = True
    supports_env: bool = True
    # Custom-API wiring binds the 9Router combo provider into config.toml
    # ([model_providers.<id>] + [model.<combo>], Grok Build's verified shape).
    supports_custom_api: bool = True
    custom_api_kind: str = "config-toml"
    router_provider_id: str = "my9router"
    router_provider_name: str = "9router"
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


SPEC = GrokBuildAdapter()

#: harness_id → provider spec (merged by root_harness_container).
ADAPTER_UNITS: dict[str, object] = {SPEC.id: SPEC}


__all__ = [
    "ADAPTER_UNITS",
    "GrokBuildAdapter",
    "GrokBuildHarnessAdapter",
]
