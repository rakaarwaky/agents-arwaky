"""Git updater contract for the AES tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IGitUpdater(ABC):
    """Git submodule update operations."""

    @abstractmethod
    def pull_submodule(self, dir: Path) -> bool:
        """Pull latest commits for the submodule. Returns True on success."""

    @abstractmethod
    def has_newer_commits(self, dir: Path) -> tuple[bool, str | None, str | None]:
        """Check if remote has newer commits than local.

        Returns:
            (has_updates, local_commit, remote_commit)
        """

    @abstractmethod
    def get_current_commit(self, dir: Path) -> str | None:
        """Get current HEAD commit hash of the submodule."""
