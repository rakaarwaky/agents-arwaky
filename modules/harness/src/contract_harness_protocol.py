"""Harness-domain protocol contracts (one capability ABC + adapter surface).

The capability layer exposes exactly ONE method — ``execute(op, targets,
flags?)`` — covering connect, disconnect, and skill provisioning (FRD
Protocol API). Everything after it is the internal adapter surface:
path-leaf ABCs and the composite ``IHarnessAdapter`` (composition only;
not part of the FRD Protocol API). Adapters are stateless utility leaves
owning one provider's paths, config format, env keys, and the
custom-API support flag.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.harness.src.taxonomy_harness_vo import ExitCode


class IHarnessProtocol(ABC):
    """Single capability method covering connect / disconnect / provision.

    FR-HARNESS-001, FR-HARNESS-002, and FR-HARNESS-003 dispatch through
    *op* (``connect`` | ``disconnect`` | ``provision_skills``) over
    resolved *targets*, with an optional *flags* bag.
    """

    @abstractmethod
    def execute(self, op: str, targets: tuple[str, ...],
                flags: dict[str, bool] | None = None) -> ExitCode:
        """Run *op* over *targets*; return exit code (0 = success)."""
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
    "IHarnessCredentialCandidatesProtocol",
    "IHarnessEnvFilesProtocol",
    "IHarnessHomeProtocol",
    "IHarnessMcpConfigFileProtocol",
    "IHarnessMcpTargetsProtocol",
    "IHarnessProtocol",
    "IHarnessSessionConfFilesProtocol",
    "IHarnessSkillsDirProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IHarnessAdapter": IHarnessAdapter,
    "IHarnessConfigFilesProtocol": IHarnessConfigFilesProtocol,
    "IHarnessCredentialCandidatesProtocol": IHarnessCredentialCandidatesProtocol,
    "IHarnessEnvFilesProtocol": IHarnessEnvFilesProtocol,
    "IHarnessHomeProtocol": IHarnessHomeProtocol,
    "IHarnessMcpConfigFileProtocol": IHarnessMcpConfigFileProtocol,
    "IHarnessMcpTargetsProtocol": IHarnessMcpTargetsProtocol,
    "IHarnessProtocol": IHarnessProtocol,
    "IHarnessSessionConfFilesProtocol": IHarnessSessionConfFilesProtocol,
    "IHarnessSkillsDirProtocol": IHarnessSkillsDirProtocol,
}
