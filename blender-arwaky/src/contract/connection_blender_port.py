"""
Contract: Port interface for Blender socket connection management.

Defines the contract for low-level socket connection to Blender addon.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import ActionName, Details, SuccessFlag


class BlenderConnectionPort(ABC):
    """Port interface for managing Blender socket connections."""

    @abstractmethod
    def connect(self) -> SuccessFlag:
        """Establish connection to Blender. Returns True if successful."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to Blender."""
        pass

    @abstractmethod
    def is_connected(self) -> SuccessFlag:
        """Check if the socket is currently connected and alive."""
        pass

    @abstractmethod
    def send_command(self, command_type: ActionName, params: Details | None = None) -> Details:
        """Send a command to Blender and return the response."""
        pass
