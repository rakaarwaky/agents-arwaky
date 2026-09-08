"""Google Drive backup gateway — implements IBackupGateway (P4 decouple)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from contract_backup_gateway_protocol import IBackupGateway

GDRIVE_HELPER = Path(__file__).resolve().parent / "gdrive.py"


class GDriveGateway(IBackupGateway):
    """Backup gateway via tools/backup/gdrive.py subprocess."""

    def upload(self, local_path: Path, remote_name: str = "") -> dict:
        result = subprocess.run(
            [sys.executable, str(GDRIVE_HELPER), "upload", str(local_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Google Drive upload failed: {result.stderr.strip()}")
        return {"name": remote_name or local_path.name, "stdout": result.stdout.strip()}

    def download(self, query_or_id: str, destination: Path) -> Path:
        result = subprocess.run(
            [sys.executable, str(GDRIVE_HELPER), "download", query_or_id, str(destination)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Google Drive download failed: {result.stderr.strip()}")
        return destination

    def list(self, prefix: str = "") -> list:
        result = subprocess.run(
            [sys.executable, str(GDRIVE_HELPER), "list"],
            capture_output=True, text=True,
        )
        return result.stdout.splitlines()
