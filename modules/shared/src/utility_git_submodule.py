"""Git submodule updater (capabilities layer), delegating to the utility functions."""
from __future__ import annotations

from pathlib import Path

from abc import ABC, abstractmethod
from modules.shared.src.utility_git_update import (
    get_current_commit,
    has_newer_commits,
    pull_submodule,
)


class IGitUpdater(ABC):
    """Git submodule update operations contract."""

    @abstractmethod
    def pull_submodule(self, dir: Path) -> bool:
        """Pull latest from remote into *dir*. Returns True on success."""
        ...

    @abstractmethod
    def has_newer_commits(self, dir: Path) -> tuple[bool, str | None, str | None]:
        """Return (has_updates, local_sha, remote_sha)."""
        ...

    @abstractmethod
    def get_current_commit(self, dir: Path) -> str | None:
        """Return current HEAD sha for *dir*, or None."""
        ...


class GitSubmoduleUpdater(IGitUpdater):
    """Default IGitUpdater backed by the git submodule utility functions."""

    def pull_submodule(self, dir: Path) -> bool:
        return pull_submodule(dir)

    def has_newer_commits(self, dir: Path) -> tuple[bool, str | None, str | None]:
        return has_newer_commits(dir)

    def get_current_commit(self, dir: Path) -> str | None:
        return get_current_commit(dir)
