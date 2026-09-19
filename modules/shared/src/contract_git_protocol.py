"""Git submodule update operations contract (shared, AES102 `_protocol`)."""
from __future__ import annotations
from modules.shared.src.taxonomy_core_vo import Timestamp

from abc import ABC, abstractmethod
from pathlib import Path



class IGitUpdater(ABC):
    """Git submodule update operations contract."""

    @abstractmethod
    def pull_submodule(self, directory: Path) -> bool:
        """Pull latest from remote into *directory*. Returns True on success."""
        return None

    @abstractmethod
    def has_newer_commits(self, directory: Path) -> tuple[bool, str | None, str | None]:
        """Return (has_updates, local_sha, remote_sha)."""
        return None

    @abstractmethod
    def get_current_commit(self, directory: Path) -> str | None:
        """Return current HEAD sha for *directory*, or None."""
        return None

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
