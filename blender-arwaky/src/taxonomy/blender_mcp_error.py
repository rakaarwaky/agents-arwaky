from __future__ import annotations

from .core_types_vo import AssetId, Details, ErrorMessage, ProviderName


class BlenderMCPError(Exception):
    """Base error for all BlenderMCP exceptions."""

    def __init__(self, message: ErrorMessage | None = None, details: Details | None = None) -> None:
        message = message or ErrorMessage("")
        super().__init__(message)
        self.details = details or {}
        self._error_message: ErrorMessage = ErrorMessage(str(message))

    def to_mcp_format(self) -> Details:
        """Serialize error for MCP response."""
        return {
            "code": self.__class__.__name__,
            "message": str(ErrorMessage(str(self))),
            "details": getattr(self, "details", None),
        }


class DomainError(BlenderMCPError):
    """Base for domain-specific errors in the BlenderMCP system."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Domain error"))


class SceneValidationError(DomainError):
    """Raised when a scene invariant is violated or validation fails."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Scene validation failed"))


class AssetNotFoundError(DomainError):
    """Raised when an asset is not found in a provider's database."""

    def __init__(self, asset_id: AssetId, provider: ProviderName):
        super().__init__(ErrorMessage(f"Asset {asset_id} not found in provider {provider}"))
        self.asset_id = asset_id
        self.provider = provider


class ValidationError(DomainError):
    """Raised when input parameters fail domain validation rules or constraints."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Input validation failed"))


class ConnectionError(DomainError):
    """Raised when a persistent connection to an external service or socket fails."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Connection failed"))


class ProviderError(DomainError):
    """Raised when an external asset provider returns an error."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Provider error"))


class ExecutionError(DomainError):
    """Raised when a command execution in Blender fails or returns a runtime error."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Execution failed"))


class BlenderConnectionError(ConnectionError):
    """Raised when the specific socket connection to the Blender instance is lost."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Blender connection lost"))


class InvalidCommandError(DomainError):
    """Raised when a command string is not recognized by the internal dispatcher."""

    def __init__(self, message: ErrorMessage | None = None) -> None:
        super().__init__(message or ErrorMessage("Invalid command"))
