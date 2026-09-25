"""Qwen Code (qwencode) harness leaf adapter (capabilities layer) — provider data + protocol.

Implements `IHarnessProtocol` (AES403) and exports the `qwencode` provider spec
merged into `HARNESS_REGISTRY` by the root container. Provider data lives in
`QwencodeAdapter`; the protocol implementor routes the provider-scoped ops
(`supported` / `satisfied`) through `utility_harness_mechanics`.

Leaf: imports stdlib + modules/shared only. The provider's settings.json
structure (skills.directories, SessionStart hooks, modelProviders entries)
is written by the capability layer through generic JSON helpers; this
adapter only declares WHICH files, keys and flags belong to the provider.
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
class QwencodeHarnessAdapter(IHarnessProtocol):
    """Qwen Code provider behind the harness protocol (AES403 implementor)."""

    def __init__(self, units: dict[str, object] | None = None) -> None:
        self._units = dict(units) if units is not None else dict(ADAPTER_UNITS)

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        targets: tuple[str, ...],
        flags: dict[str, bool] | None = None,
    ) -> ExitCode:
        """Dispatch a provider-scoped op against this file's qwencode unit."""
        return dispatch_provider_op(self._units, op, targets, flags, label="qwencode adapter")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return f"QwencodeHarnessAdapter(providers={len(self._units)})"


# ---------------------------------------------------------------------------
# Provider spec (one registered instance per harness id)
# ---------------------------------------------------------------------------
def _home() -> Path:
    return Path(os.environ.get("QWEN_HOME", Path.home() / ".qwen"))


def _skill_sync_command() -> str:
    """Absolute repo python invocation so the hook never depends on the
    ``aa`` launcher being on the session's PATH."""
    return (
        "python3 -m modules.root_cli_entry connect "
        "--qwencode --skills-only"
    )


@dataclass(frozen=True)
class QwencodeAdapter:
    """Qwen Code provider data (JSONC settings.json, single-level skill scan)."""

    id: str = "qwencode"
    aliases: tuple[str, ...] = ("qwen", "qwen-code", "qwencode")
    display: str = "Qwen Code (qwencode)"
    # Headless probe verified qwen -p sees a symlinked skill dir in ~/.qwen/skills.
    skill_link_verified: bool = True
    supports_mcp: bool = True
    supports_env: bool = True
    # Custom-API wiring binds the my9router provider entry in settings.json.
    supports_custom_api: bool = True
    custom_api_kind: str = "settings-jsonc"
    router_provider_id: str = "my9router"
    env_key: str = "NINEROUTER_KEY"
    mcp_key: str = "mcpServers"
    env_keys: tuple[str, ...] = ("NINEROUTER_URL", "NINEROUTER_KEY", "MNEMOSYNE_DATA_DIR")
    # Harness scans one level below each registered skills root: the category
    # folders must be registered into skills.directories (never hand-edited).
    one_level_skill_scan: bool = True
    # SessionStart hook that re-registers skill directories each session.
    skill_sync_hook_name: str = "arwaky-skill-sync"
    # Hook command runs the repo CLI from the repository checkout; the
    # absolute path keeps it independent of the session's PATH.
    skill_sync_commands: tuple[str, ...] = (_skill_sync_command(),)

    def home(self) -> Path:
        return _home()

    def config_files(self) -> tuple[Path, ...]:
        return (self.home() / "settings.json",)

    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return (target_dir or self.home()) / "settings.json"

    def env_files(self) -> tuple[Path, ...]:
        return (self.home() / ".env",)

    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        return (("Qwen Code", self.home()),)

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


SPEC = QwencodeAdapter()

#: harness_id → provider spec (merged by root_harness_container).
ADAPTER_UNITS: dict[str, object] = {SPEC.id: SPEC}


__all__ = [
    "ADAPTER_UNITS",
    "QwencodeAdapter",
    "QwencodeHarnessAdapter",
]
