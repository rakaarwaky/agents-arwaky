"""Domain error hierarchy for the AES tools (all derive from ArwakyError)."""
from __future__ import annotations


class ArwakyError(Exception):
    """Base class for every agents-arwaky domain error."""

    def __init__(self, message: str) -> None:
        self._message = message

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return self._message


class ToolInstallError(ArwakyError):
    """Raised when a tool install fails."""


class ToolUpdateError(ArwakyError):
    """Raised when a tool update fails."""


class ToolUninstallError(ArwakyError):
    """Raised when a tool uninstall fails."""


class ManifestParseError(ArwakyError):
    """Raised when the tool manifest cannot be parsed."""


class DaemonStartError(ArwakyError):
    """Raised when a daemon container fails to start."""


class DaemonStopError(ArwakyError):
    """Raised when a daemon container fails to stop."""


class SkillProvisionError(ArwakyError):
    """Raised when skill provisioning/pruning fails."""


class ConfigWriteError(ArwakyError):
    """Raised when a harness config file cannot be written."""


class GitUpdateError(ArwakyError):
    """Raised when a git submodule update fails."""
