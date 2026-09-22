"""Harness-domain protocol contracts (capability + adapter ABCs).

The capability layer is business-action shaped (FRD API Contract table);
adapters are stateless utility leaves owning one provider's paths,
config format, env keys, and the custom-API support flag.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.harness.src.taxonomy_harness_vo import ExitCode


class IHarnessConnector(ABC):
    """FR-001: connect a harness — MCP config, env entries, router wiring."""

    @abstractmethod
    def connect(self, harness_ids: tuple[str, ...], force: bool = False, dry_run: bool = False,
                mcp_only: bool = False, skills_only: bool = False, env_only: bool = False,
                router: bool = False, copy_skills: bool = False) -> ExitCode:
        """Write the generated artifacts; return exit code (0 = success)."""
        return None


class IHarnessDisconnector(ABC):
    """FR-002: disconnect a harness — remove what connect wrote."""

    @abstractmethod
    def disconnect(self, harness_ids: tuple[str, ...], dry_run: bool = False) -> ExitCode:
        """Remove generated artifacts; return exit code (0 = success)."""
        return None


class IHarnessSkills(ABC):
    """FR-003: provision the skill pack into a harness's skill dir."""

    @abstractmethod
    def provision_skills(self, harness_ids: tuple[str, ...], copy: bool = False,
                        dry_run: bool = False, force: bool = False) -> ExitCode:
        """Link or copy the pack; return exit code (0 = success)."""
        return None


class IHarnessAdapter(ABC):
    """Utility-leaf surface: one provider's paths, config format, env keys.

    Adapters are stateless data + pure path helpers. They import only from
    modules/shared and stdlib — never another adapter or a capability layer.
    """

    id: str
    aliases: tuple[str, ...]
    display: str
    skill_link_verified: bool
    supports_mcp: bool
    supports_env: bool
    supports_custom_api: bool
    custom_api_kind: str
    router_provider_id: str
    env_key: str
    mcp_key: str
    env_keys: tuple[str, ...]

    @abstractmethod
    def home(self) -> Path:
        return None

    @abstractmethod
    def config_files(self) -> tuple[Path, ...]:
        return None

    @abstractmethod
    def env_files(self) -> tuple[Path, ...]:
        return None

    @abstractmethod
    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        return None

    @abstractmethod
    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        return None

    @abstractmethod
    def skills_dir(self) -> Path:
        return None

    @abstractmethod
    def session_conf_files(self) -> tuple[Path, ...]:
        return None

    @abstractmethod
    def credential_candidates(self) -> tuple[Path, ...]:
        return None


__all__ = [
    "ExitCode",
    "IHarnessAdapter",
    "IHarnessConnector",
    "IHarnessDisconnector",
    "IHarnessSkills",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IHarnessAdapter": IHarnessAdapter,
    "IHarnessConnector": IHarnessConnector,
    "IHarnessDisconnector": IHarnessDisconnector,
    "IHarnessSkills": IHarnessSkills,
}
