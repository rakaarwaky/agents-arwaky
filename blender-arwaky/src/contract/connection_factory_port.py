"""
Contract: Port interface for Blender connection factory.

Provides an abstraction for creating and managing the lifecycle
of a Blender socket connection. Decouples factory/singleton logic
from BlenderConnectionPort consumers.
AES Port layer — depends only on taxonomy entities and other ports.
"""

from abc import ABC, abstractmethod

from .connection_blender_port import BlenderConnectionPort


class BlenderConnectionFactoryPort(ABC):
    """Port interface for obtaining and managing a Blender connection."""

    @abstractmethod
    def get_connection(self) -> BlenderConnectionPort:
        """Get or create a Blender connection singleton."""
        pass

    @abstractmethod
    def shutdown(self):
        """Close and clean up the connection."""
        pass
