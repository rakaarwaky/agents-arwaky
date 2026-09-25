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


# ─── Block 1: Class Definition & Constructor ──────────────
class OpencodeHarnessAdapter(IHarnessProtocol):
    """OpenCode provider behind the harness protocol (AES403 implementor)."""

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
        """Dispatch a provider-scoped op against this file's opencode unit."""
        return dispatch_provider_op(self._units, op, targets, flags, label="opencode adapter")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
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
    # OpenCode supports OpenAI-compatible providers via opencode.json's
    # provider.<id> block (verified 2026-09-25: existing 9router entry with
    # combo models my9router / 9vision).
    supports_custom_api: bool = True
    custom_api_kind: str = "opencode-json"
    router_provider_id: str = "my9router"
    router_provider_name: str = "9router"
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcp"
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    skill_sync_commands: tuple[str, ...] = ()

    def home(self) -> Path:
        """Resolve the OpenCode harness home directory."""
        return tool_config_dir("opencode")

    def config_files(self) -> tuple[Path, ...]:
        """Return the config files used by the OpenCode harness."""
        return (self.home() / "opencode.jsonc",)

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        """Return the path to the OpenCode MCP configuration file."""
        return (target_dir or self.home()) / "opencode.jsonc"

    def env_files(self) -> tuple[Path, ...]:
        """Return the environment files consumed by the OpenCode harness."""
        files = [self.home() / ".env"]
        legacy = Path.home() / ".opencode"
        if legacy.is_dir():
            files.append(legacy / ".env")
        return tuple(files)

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        """Return the MCP server targets known to the OpenCode harness."""
        return (("OpenCode", self.home()),)

    def skills_dir(self) -> Path:
        """Return the skills directory for the OpenCode harness."""
        return self.home() / "skills"

    def session_conf_files(self) -> tuple[Path, ...]:
        """Return session configuration files referenced by the OpenCode harness."""
        return (config_home() / "environment.d/9router.conf",)

    def credential_candidates(self) -> tuple[Path, ...]:
        """Return candidate credential files searched by the OpenCode harness."""
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
