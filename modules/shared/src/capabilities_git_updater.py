"""Git submodule updater capability — default IGitUpdater over git utility functions."""
from __future__ import annotations
from modules.shared.src.taxonomy_core_vo import Timestamp

from pathlib import Path


from modules.shared.src.contract_git_protocol import IGitUpdater
from modules.shared.src.utility_git_update import (
    get_current_commit,
    has_newer_commits,
    pull_submodule,
)


class GitSubmoduleUpdater(IGitUpdater):
    """Default IGitUpdater backed by the git submodule utility functions."""

    def pull_submodule(self, directory: Path) -> bool:
        return pull_submodule(directory)

    def has_newer_commits(self, directory: Path) -> tuple[bool, str | None, str | None]:
        return has_newer_commits(directory)

    def get_current_commit(self, directory: Path) -> str | None:
        return get_current_commit(directory)

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
