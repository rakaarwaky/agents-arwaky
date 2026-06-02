"""
Contract: Port interface for code execution in Blender.

Defines the contract for executing arbitrary Python code in Blender.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import Prompt


class CodeExecutionPort(ABC):
    """Port interface for executing Python code in Blender."""

    @abstractmethod
    async def execute_blender_code(self, code: Prompt) -> Prompt:
        """Execute arbitrary Python code in Blender and return result."""
        pass
