"""Completion-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ICompletionAggregate(ABC):
    """Aggregate over shell completion generation for the aa CLI."""

    @abstractmethod
    def generate(self, shell: str) -> str:
        """Return the completion script for *shell* (bash|zsh)."""
        return ""

    @abstractmethod
    def install(self) -> int:
        """Install completions into the user's shell profile."""
        return 0

