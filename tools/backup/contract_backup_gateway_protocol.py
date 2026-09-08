"""Backup gateway protocol — contract layer for storage backends (Plan4 #4)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IBackupGateway(ABC):
    """Protocol for backup storage backends (Google Drive, S3, local, etc.)."""

    @abstractmethod
    def upload(self, local_path: Path, remote_name: str) -> dict:
        """Upload a local archive to remote storage. Returns metadata dict."""
        ...

    @abstractmethod
    def download(self, query_or_id: str, destination: Path) -> Path:
        """Download a remote archive to local path. Returns local path."""
        ...

    @abstractmethod
    def list(self, prefix: str = "") -> list:
        """List remote archives matching prefix. Returns list of metadata dicts."""
        ...
