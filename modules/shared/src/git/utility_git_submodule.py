"""Git submodule updater (capabilities layer), delegating to the utility functions."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.git.contract_git_protocol import IGitUpdater
from modules.shared.src.git.utility_git_update import (
    get_current_commit,
    has_newer_commits,
    pull_submodule,
)


class GitSubmoduleUpdater(IGitUpdater):
    """Default IGitUpdater backed by the git submodule utility functions."""

    def pull_submodule(self, dir: Path) -> bool:
        return pull_submodule(dir)

    def has_newer_commits(self, dir: Path) -> tuple[bool, str | None, str | None]:
        return has_newer_commits(dir)

    def get_current_commit(self, dir: Path) -> str | None:
        return get_current_commit(dir)
