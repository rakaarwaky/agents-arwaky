"""Tar backup gateway capability — port of backup/backup_manager.py."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from modules.shared.src.backup.contract_backup_protocol import IBackupGateway
from modules.shared.src.backup.taxonomy_backup_vo import BackupResult, RestoreResult
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.xdg.utility_xdg_paths import data_home

BACKUP_STORE = data_home() / "backups"
GDRIVE_HELPER = repo_root() / "tools/backup/gdrive.py"

#: tool -> data subdir (relative to XDG_DATA_HOME)
TOOL_DATA = {
    "anytype": "anytype-mcp",
    "9router": "9router",
    "mnemosyne": "mnemosyne",
    "google-workspace": "google-workspace-mcp",
}


def _log_info(msg: str) -> None: print(f"==> {msg}")
def _log_ok(msg: str) -> None:  print(f"  [OK] {msg}")
def _log_warn(msg: str) -> None: print(f"  [WARN] {msg}")


class _Progress:
    """Simple spinner for long-running operations (TTY-only)."""

    def __init__(self, message: str) -> None:
        self.message = message
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _spin(self) -> None:
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self._stop.is_set():
            sys.stdout.write(f"\r  {chars[i % len(chars)]} {self.message}")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stdout.flush()

    def __enter__(self) -> "_Progress":
        if sys.stdout.isatty():
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)


def tar_dir(src: Path, dest: Path) -> None:
    file_count = sum(1 for _ in src.rglob("*") if _.is_file())
    with _Progress(f"Archiving {src.name} ({file_count} files)..."), tarfile.open(dest, "w:gz") as tar:
        tar.add(src, arcname=src.name)


def untar(src: Path, dest: Path) -> None:
    """Extract a validated .tar.gz; blocks traversal / symlink / device nodes."""
    dest = dest.resolve()
    if not tarfile.is_tarfile(src):
        raise ValueError(f"Not a valid tar archive: {src}")
    with tarfile.open(src, "r:gz") as check_tar:
        check_tar.getmembers()  # ensure full readability
    with tarfile.open(src, "r:gz") as tar:
        try:
            tar.extractall(dest, filter="data")  # Python 3.12+
        except TypeError:
            for member in tar.getmembers():
                member_path = (dest / member.name).resolve()
                if not str(member_path).startswith(str(dest) + os.sep):
                    raise ValueError(f"Blocked path traversal in archive: {member.name}") from None
                if member.issym() or member.islnk():
                    raise ValueError(f"Blocked symlink/hardlink in archive: {member.name}") from None
                if member.isdev():
                    raise ValueError(f"Blocked device node in archive: {member.name}") from None
            tar.extractall(dest)


class TarBackupGateway(IBackupGateway):
    """tar/untar backup & restore with progress spinner + optional gdrive upload.

    # Block 1: Configuration (store, tool map)
    # Block 2: Backup (tar + optional upload)
    # Block 3: Restore (staged extraction + swap)
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        self._store = BACKUP_STORE

    def list_archives(self) -> list[Path]:
        if not self._store.exists():
            return []
        return sorted(self._store.glob("*.tar.gz"))

    # -- Block 2: Backup -------------------------------------------------------------
    def _upload_gdrive(self, archive: Path) -> int:
        with _Progress(f"Uploading {archive.name} to Google Drive..."):
            result = subprocess.run(
                [sys.executable, str(GDRIVE_HELPER), "upload", str(archive)],
                capture_output=True, text=True, check=False,
            )
        if result.returncode != 0:
            print(f"  [FAIL] Google Drive upload failed: {result.stderr.strip()}", file=sys.stderr)
            return result.returncode
        print(result.stdout)
        return 0

    def backup(self, tool: str, dest: str = "") -> BackupResult:
        """Tar the tool data dir; when dest=='gdrive' also upload."""
        upload_to_gdrive = dest == "gdrive" or dest.startswith("gdrive:")
        store = self._store
        store.mkdir(parents=True, exist_ok=True)
        subdir = TOOL_DATA.get(tool, tool)
        src = data_home() / subdir
        if not src.exists():
            print(f"  \u26a0 No data for {tool} at {src}, skipping.")
            return BackupResult(True, tool, "", upload_to_gdrive, "no data, skipped")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        archive = store / f"{tool}-{ts}.tar.gz"
        _log_info(f"Backing up {tool} -> {archive}")
        tar_dir(src, archive)
        _log_ok(f"{tool} backed up.")
        if upload_to_gdrive:
            rc = self._upload_gdrive(archive)
            if rc != 0:
                return BackupResult(False, tool, str(archive), True, "gdrive upload failed")
        return BackupResult(True, tool, str(archive), upload_to_gdrive, "backed up")

    # -- Block 3: Restore --------------------------------------------------------------
    def restore(self, tool: str, archive: Path) -> RestoreResult:
        """Staged extraction into <tool>.restore-<pid>, then atomic swap."""
        src = Path(archive)
        if not src.exists() or not src.is_file():
            print(f"  \u2717 Archive not found: {src}", file=sys.stderr)
            return RestoreResult(False, tool, str(src), "", "archive not found")
        if not tarfile.is_tarfile(src):
            print(f"  \u2717 Not a valid tar archive: {src}", file=sys.stderr)
            return RestoreResult(False, tool, str(src), "", "not a tar archive")
        subdir = TOOL_DATA.get(tool, tool)
        target = data_home() / subdir
        staging = target.with_name(f"{target.name}.restore-{os.getpid()}")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        _log_info(f"Restoring {tool} from {src} (staged)...")
        try:
            untar(src, staging)
        except (ValueError, tarfile.TarError, OSError) as exc:
            shutil.rmtree(staging, ignore_errors=True)
            print(f"  \u2717 Restore failed: {exc}", file=sys.stderr)
            return RestoreResult(False, tool, str(src), str(target), str(exc))
        if target.exists():
            backup_old = target.with_name(f"{target.name}.pre-restore")
            shutil.rmtree(backup_old, ignore_errors=True)
            target.rename(backup_old)
            try:
                staging.rename(target)
            except OSError:
                backup_old.rename(target)  # roll back
                raise
            shutil.rmtree(backup_old, ignore_errors=True)
        else:
            staging.rename(target)
        _log_ok(f"{tool} restored to {target}.")
        return RestoreResult(True, tool, str(src), str(target), "restored")
