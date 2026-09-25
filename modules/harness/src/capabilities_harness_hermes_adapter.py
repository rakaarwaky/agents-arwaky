"""Hermes harness leaf adapter (capabilities layer) — provider data + protocol.

Implements `IHarnessProtocol` (AES403) and exports the `hermes` provider spec
merged into `HARNESS_REGISTRY` by the root container. Provider data lives in
`HermesAdapter`; the protocol implementor routes the provider-scoped ops
(`supported` / `satisfied`) through `utility_harness_mechanics`. Knows nothing
about business actions; capabilities dispatch here per harness id.

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


# ─── Block 1: Class Definition & Constructor ──────────────
class HermesHarnessAdapter(IHarnessProtocol):
    """Hermes provider behind the harness protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, object] | None = None) -> None:
        """Hold the provider spec registry; fall back to the default when absent."""
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        targets: tuple[str, ...],
        flags: dict[str, bool] | None = None,
    ) -> ExitCode:
        """Dispatch a provider-scoped op against this file's hermes unit."""
        return dispatch_provider_op(self._units, op, targets, flags, label="hermes adapter")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"HermesHarnessAdapter(providers={len(self._units)})"


# ---------------------------------------------------------------------------
# Provider spec (one registered instance per harness id)
# ---------------------------------------------------------------------------
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
    router_provider_id: str = "my9router"
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcpServers"
    # Keys the disconnector drops (incl. router refs installed with env keys).
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    skill_sync_commands: tuple[str, ...] = ()

    def home(self) -> Path:
        """Resolve the Hermes harness home directory."""
        return Path.home() / ".hermes"

    def config_files(self) -> tuple[Path, ...]:
        """Return the config files used by the Hermes harness."""
        return (self.home() / "config.yaml",)

    def env_files(self) -> tuple[Path, ...]:
        """Return the environment files consumed by the Hermes harness, including per-profile .env files."""
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
        """Return the path to the Hermes MCP configuration file."""
        return (target_dir or self.home()) / "config.yaml"

    def skills_dir(self) -> Path:
        """Return the skills directory for the Hermes harness."""
        return self.home() / "skills"

    def session_conf_files(self) -> tuple[Path, ...]:
        """systemd user-session env layer that shadows harness .env files."""
        return (config_home() / "environment.d/9router.conf",)

    def credential_candidates(self) -> tuple[Path, ...]:
        """Return candidate credential files searched by the Hermes harness."""
        return (
            agents_arwaky_config_dir() / "ninerouter.env",
            config_home() / "9router/.env",
            data_home() / "agents-arwaky/ninerouter.env",
        )


SPEC = HermesAdapter()

#: harness_id → provider spec (merged by root_harness_container).
ADAPTER_UNITS: dict[str, object] = {SPEC.id: SPEC}


__all__ = [
    "ADAPTER_UNITS",
    "HermesAdapter",
    "HermesHarnessAdapter",
]
