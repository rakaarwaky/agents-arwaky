"""Git updater contract (ABC) for AES submodule tooling (P4-A4)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IGitUpdater(ABC):
    """Contract for git submodule update operations."""

    @abstractmethod
    def pull_submodule(self, dir: Path) -> bool:
        """Pull latest from remote into *dir*. Returns True on success."""

    @abstractmethod
    def has_newer_commits(self, dir: Path) -> tuple[bool, str | None, str | None]:
        """Return (has_updates, local_sha, remote_sha)."""

    @abstractmethod
    def get_current_commit(self, dir: Path) -> str | None:
        """Return current HEAD sha for *dir*, or None."""
