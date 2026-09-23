"""Harness-domain protocol contracts (capability + adapter ABCs).

The capability layer is business-action shaped (FRD API Contract table);
adapters are stateless utility leaves owning one provider's paths,
config format, env keys, and the custom-API support flag. Each path
helper is its own one-feature ABC; injectors may type a full adapter
as the composite ``IHarnessAdapter`` (composition only).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.harness.src.taxonomy_harness_vo import ExitCode


class IHarnessConnectProtocol(ABC):
    """FR-001: connect a harness — MCP config, env entries, router wiring."""

    @abstractmethod
    def connect(self, harness_ids: tuple[str, ...], force: bool = False, dry_run: bool = False,
                mcp_only: bool = False, skills_only: bool = False, env_only: bool = False,
                router: bool = False, copy_skills: bool = False) -> ExitCode:
        """Write the generated artifacts; return exit code (0 = success)."""
        ...


class IHarnessDisconnectProtocol(ABC):
    """FR-002: disconnect a harness — remove what connect wrote."""

    @abstractmethod
    def disconnect(self, harness_ids: tuple[str, ...], dry_run: bool = False) -> ExitCode:
        """Remove generated artifacts; return exit code (0 = success)."""
        ...


class IHarnessSkillsProtocol(ABC):
    """FR-003: provision the skill pack into a harness's skill dir."""

    @abstractmethod
    def provision_skills(self, harness_ids: tuple[str, ...], copy: bool = False,
                        dry_run: bool = False, force: bool = False) -> ExitCode:
        """Link or copy the pack; return exit code (0 = success)."""
        ...


class IHarnessHomeProtocol(ABC):
    """FR: resolve the harness home directory."""

    @abstractmethod
    def home(self) -> Path:
        """Home directory for this harness provider."""
        ...


class IHarnessConfigFilesProtocol(ABC):
    """FR: resolve the harness config file paths."""

    @abstractmethod
    def config_files(self) -> tuple[Path, ...]:
        """Config files owned by this harness provider."""
        ...


class IHarnessEnvFilesProtocol(ABC):
    """FR: resolve the harness env-file paths."""

    @abstractmethod
    def env_files(self) -> tuple[Path, ...]:
        """Env files owned by this harness provider."""
        ...


class IHarnessMcpConfigFileProtocol(ABC):
    """FR: resolve the harness MCP config file path."""

    @abstractmethod
    def mcp_config_file(self, target_dir: Path | None = None) -> Path:
        """MCP config file for this harness (under *target_dir* when given)."""
        ...


class IHarnessMcpTargetsProtocol(ABC):
    """FR: resolve the harness MCP write targets."""

    @abstractmethod
    def mcp_targets(self) -> tuple[tuple[str, Path], ...]:
        """Named MCP write targets for this harness provider."""
        ...


class IHarnessSkillsDirProtocol(ABC):
    """FR: resolve the harness skills directory."""

    @abstractmethod
    def skills_dir(self) -> Path:
        """Directory where skills are provisioned for this harness."""
        ...


class IHarnessSessionConfFilesProtocol(ABC):
    """FR: resolve the harness session-config file paths."""

    @abstractmethod
    def session_conf_files(self) -> tuple[Path, ...]:
        """Session config files owned by this harness provider."""
        ...


class IHarnessCredentialCandidatesProtocol(ABC):
    """FR: resolve candidate credential file paths."""

    @abstractmethod
    def credential_candidates(self) -> tuple[Path, ...]:
        """Candidate credential files for this harness provider."""
        ...


class IHarnessAdapter(
    IHarnessHomeProtocol,
    IHarnessConfigFilesProtocol,
    IHarnessEnvFilesProtocol,
    IHarnessMcpConfigFileProtocol,
    IHarnessMcpTargetsProtocol,
    IHarnessSkillsDirProtocol,
    IHarnessSessionConfFilesProtocol,
    IHarnessCredentialCandidatesProtocol,
):
    """Composite DI type: full adapter path surface (no methods of its own).

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


__all__ = [
    "ExitCode",
    "IHarnessAdapter",
    "IHarnessConfigFilesProtocol",
    "IHarnessConnectProtocol",
    "IHarnessCredentialCandidatesProtocol",
    "IHarnessDisconnectProtocol",
    "IHarnessEnvFilesProtocol",
    "IHarnessHomeProtocol",
    "IHarnessMcpConfigFileProtocol",
    "IHarnessMcpTargetsProtocol",
    "IHarnessSessionConfFilesProtocol",
    "IHarnessSkillsDirProtocol",
    "IHarnessSkillsProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IHarnessAdapter": IHarnessAdapter,
    "IHarnessConfigFilesProtocol": IHarnessConfigFilesProtocol,
    "IHarnessConnectProtocol": IHarnessConnectProtocol,
    "IHarnessCredentialCandidatesProtocol": IHarnessCredentialCandidatesProtocol,
    "IHarnessDisconnectProtocol": IHarnessDisconnectProtocol,
    "IHarnessEnvFilesProtocol": IHarnessEnvFilesProtocol,
    "IHarnessHomeProtocol": IHarnessHomeProtocol,
    "IHarnessMcpConfigFileProtocol": IHarnessMcpConfigFileProtocol,
    "IHarnessMcpTargetsProtocol": IHarnessMcpTargetsProtocol,
    "IHarnessSessionConfFilesProtocol": IHarnessSessionConfFilesProtocol,
    "IHarnessSkillsDirProtocol": IHarnessSkillsDirProtocol,
    "IHarnessSkillsProtocol": IHarnessSkillsProtocol,
}
