"""OpenCode harness leaf adapter (capabilities layer) — provider data + protocol.

Implements `IHarnessProtocol` (AES403) and exports the `opencode` provider spec
merged into `HARNESS_REGISTRY` by the root container. Provider data lives in
`OpencodeAdapter`; the protocol implementor routes the provider-scoped ops
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
    tool_config_dir,
)
from modules.shared.src.taxonomy_harness_vo import ExitCode
from modules.shared.src.utility_harness_mechanics import dispatch_provider_op


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class OpencodeHarnessAdapter(IHarnessProtocol):
    """OpenCode provider behind the harness protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, object] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def execute(
        self,
        op: str,
        targets: tuple[str, ...],
        flags: dict[str, bool] | None = None,
    ) -> ExitCode:
        """Dispatch a provider-scoped op against this file's opencode unit."""
        return dispatch_provider_op(self._units, op, targets, flags, label="opencode adapter")

    # ─── Block 3: Dunder Methods ─────────────────────────────────────
    def __repr__(self) -> str:
        return f"OpencodeHarnessAdapter(providers={len(self._units)})"


# ---------------------------------------------------------------------------
# Provider spec (one registered instance per harness id)
# ---------------------------------------------------------------------------
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


SPEC = OpencodeAdapter()

#: harness_id → provider spec (merged by root_harness_container).
ADAPTER_UNITS: dict[str, object] = {SPEC.id: SPEC}


__all__ = [
    "ADAPTER_UNITS",
    "OpencodeAdapter",
    "OpencodeHarnessAdapter",
]
