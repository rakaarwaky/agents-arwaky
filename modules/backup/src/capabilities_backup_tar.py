"""Tar backup gateway — EXACT port of tools/backup/backup_manager.py.

The original script's logic (tar_dir, untar, backup_tool, restore_tool,
cmd_backup, cmd_restore, cmd_list, cmd_help, main) is kept exactly as
written, with only the module-level constants relocated into a class
(``TarBackupGateway``) to satisfy the AES capability layer and the import
paths swapped to the AES shared modules. The original script's
``main(argv)`` CLI entry point is kept as the module-level function
``main`` at the bottom of this file.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import threading
from datetime import UTC, datetime
from pathlib import Path

from modules.shared.src.contract_backup_protocol import IBackupProtocol
from modules.shared.src.taxonomy_backup_constant import TOOL_DATA
from modules.shared.src.taxonomy_backup_vo import (
    ARCHIVE_DEFAULT,
    BackupArchive,
    BackupDestination,
    BackupOutcome,
    BackupResult,
    BackupToolQuery,
    DEST_DEFAULT,
    ExitCode,
    RestoreResult,
)
from modules.shared.src.taxonomy_common_vo import data_home
from modules.shared.src.utility_paths_resolver import repo_root

ROOT = repo_root()

BACKUP_STORE = data_home() / "backups"
# gdrive gateway lives in the AES backup feature; invoked as a module entry.
GDRIVE_HELPER = "-m:modules.backup.src.capabilities_backup_gdrive"


# ─── Block 1: Class Definition & Constructor ──────────────
class TarBackupGateway(IBackupProtocol):
    """tar/untar backup & restore with progress spinner + optional gdrive upload.

    Thin AES capability wrapper around the unchanged original script
    functions above; the original ``backup_tool`` / ``restore_tool`` /
    ``cmd_*`` functions remain the source of truth and are simply
    delegated to, preserving their exact behaviour (return codes,
    print statements, edge cases).
    """

    # ─── Block 2: Protocol Method Implementation ──────────────

    def backup(self, tool: BackupToolQuery, dest: BackupDestination = DEST_DEFAULT) -> BackupResult:
        """Create a tar.gz archive of *tool* data, optionally uploading to Drive."""
        rc = cmd_backup([str(tool)] + ([str(dest)] if str(dest) else []))
        archive = f"{tool}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.tar.gz"
        return BackupResult(rc == 0, str(tool), archive, False, "tar backup completed" if rc == 0 else "tar backup failed")

    def restore(self, tool: BackupToolQuery, archive: BackupArchive = ARCHIVE_DEFAULT) -> RestoreResult:
        """Restore *tool* data from a local tar.gz *archive*."""
        rc = cmd_restore([str(tool), str(archive)])
        return RestoreResult(rc == 0, str(tool), str(archive), "", "tar restore completed" if rc == 0 else "tar restore failed")

    def list_archives(self) -> BackupOutcome:
        """Return the archives visible to this gateway plus their print lines."""
        lines = cmd_list()
        return BackupOutcome(success=True, tool_id="", result=ExitCode(lines))

    def status(self) -> ExitCode:
        """Report the backup store path, existence, and archive count."""
        exists = BACKUP_STORE.is_dir()
        count = len(list(BACKUP_STORE.glob("*.tar.gz"))) if exists else 0
        print(f"Backup store: {BACKUP_STORE}")
        print(f"  exists: {'yes' if exists else 'no'}")
        print(f"  archives: {count}")
        return ExitCode(0)

    def help(self) -> ExitCode:
        """Show backup usage information."""
        return ExitCode(cmd_help())

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "TarBackupGateway()"

    def main(self, argv: list[str]) -> int:
        """Original script's ``main`` entry point (kept as-is above)."""
        return main(argv)


class _Progress:
    """Simple spinner for long-running operations."""

    def __init__(self, message: str):
        self.message = message
        self._stop = threading.Event()
        self._thread = None

    def _spin(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self._stop.is_set():
            sys.stdout.write(f"\r  {chars[i % len(chars)]} {self.message}")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        if sys.stdout.isatty():
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *args):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)


def log_info(msg):
    """Print an informational log message prefixed with ==>."""
    print(f"==> {msg}")


def log_ok(msg):
    """Print an informational log message prefixed with [OK]."""
    print(f"  [OK] {msg}")


def log_warn(msg):
    """Print an informational log message prefixed with [WARN]."""
    print(f"  [WARN] {msg}")


def tar_dir(src: Path, dest: Path):
    """Archive *src* directory into a gzip-compressed tar at *dest*."""
    file_count = sum(1 for _ in src.rglob("*") if _.is_file())
    with _Progress(f"Archiving {src.name} ({file_count} files)..."), tarfile.open(dest, "w:gz") as tar:
        tar.add(src, arcname=src.name)


def untar(src: Path, dest: Path):
    """Safely extract tar.gz *src* into *dest*, rejecting traversal and symlinks."""
    dest = dest.resolve()
    # Verify archive integrity before extract (R-7)
    if not tarfile.is_tarfile(src):
        raise ValueError(f"Not a valid tar archive: {src}")
    try:
        with tarfile.open(src, "r:gz") as check_tar:
            check_tar.getmembers()  # ensure full readability
    except (tarfile.TarError, OSError) as e:
        raise ValueError(f"Corrupt or truncated archive {src}: {e}") from e
    with tarfile.open(src, "r:gz") as tar:
        try:
            # Python 3.12+: filter="data" blocks traversal/symlinks
            tar.extractall(dest, filter="data")
        except TypeError:
            # Fallback for older Python: validate ALL members before extraction
            for member in tar.getmembers():
                member_path = (dest / member.name).resolve()
                if not str(member_path).startswith(str(dest) + os.sep):
                    raise ValueError(
                        f"Blocked path traversal in archive: {member.name}"
                    ) from None
                if member.issym() or member.islnk():
                    raise ValueError(
                        f"Blocked symlink/hardlink in archive: {member.name}"
                    ) from None
                if member.isdev():
                    raise ValueError(
                        f"Blocked device node in archive: {member.name}"
                    ) from None
            # All members validated safe (R-7) => extraction is safe here
            tar.extractall(dest)


def backup_tool(tool: str, dest: str = ""):
    """Back up *tool* data to BACKUP_STORE, optionally uploading to gdrive."""
    upload_to_gdrive = dest == "gdrive" or dest.startswith("gdrive:")
    store = BACKUP_STORE
    store.mkdir(parents=True, exist_ok=True)
    subdir = TOOL_DATA.get(tool, tool)
    src = data_home() / subdir
    if not src.exists():
        print(f"  ⚠ No data for {tool} at {src}, skipping.")
        return 0
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    archive = store / f"{tool}-{ts}.tar.gz"
    log_info(f"Backing up {tool} -> {archive}")
    tar_dir(src, archive)
    log_ok(f"{tool} backed up.")
    if upload_to_gdrive:
        # Argument list without shell=True; helper runs in-process as a module
        target, _, mod = GDRIVE_HELPER.partition(":")
        cmd = (
            [sys.executable, target, mod, "upload", str(archive)]
            if target == "-m"
            else [sys.executable, target, "upload", str(archive)]
        )
        with _Progress(f"Uploading {archive.name} to Google Drive..."):
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, check=False,
            )
        if result.returncode != 0:
            print(
                f"  [FAIL] Google Drive upload failed: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return result.returncode
        print(result.stdout)
    return 0


def restore_tool(tool: str, src: str):
    """Restore *tool* data from tar.gz *src* via staged extraction and swap."""
    src_path = Path(src)
    if not src_path.exists() or not src_path.is_file():
        print(f"  ✗ Archive not found: {src_path}", file=sys.stderr)
        return 1
    if not tarfile.is_tarfile(src_path):
        print(f"  ✗ Not a valid tar archive: {src_path}", file=sys.stderr)
        return 1
    subdir = TOOL_DATA.get(tool, tool)
    target = data_home() / subdir

    # Extract into staging first; only swap once validated (no data loss on corrupt archive).
    staging = target.with_name(f"{target.name}.restore-{os.getpid()}")
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    log_info(f"Restoring {tool} from {src_path} (staged)...")
    try:
        untar(src_path, staging)
    except (ValueError, tarfile.TarError, OSError) as exc:
        shutil.rmtree(staging, ignore_errors=True)
        print(f"  ✗ Restore failed: {exc}", file=sys.stderr)
        return 1

    # Swap: old data is only removed after staging is proven good.
    # Archives are rooted at the tool dir (arcname = src.name), so the
    # extracted content sits one level down; unwrap it or the restored
    # state lands nested (target/target/...).
    content = staging / target.name
    if not content.is_dir():
        content = staging  # tolerate archives rooted at the extraction dir
    if target.exists():
        backup_old = target.with_name(f"{target.name}.pre-restore")
        shutil.rmtree(backup_old, ignore_errors=True)
        target.rename(backup_old)
        try:
            content.rename(target)
        except OSError:
            backup_old.rename(target)  # roll back
            shutil.rmtree(staging, ignore_errors=True)
            raise
        shutil.rmtree(backup_old, ignore_errors=True)
    else:
        content.rename(target)
    shutil.rmtree(staging, ignore_errors=True)
    log_ok(f"{tool} restored to {target}.")
    return 0


def cmd_backup(argv):
    """Run backup for one or all tools, optionally targeting gdrive."""
    tool = argv[0] if argv else "all"
    if tool == "list":
        return cmd_list()
    dest = argv[1] if len(argv) > 1 else ""
    tools = list(TOOL_DATA.keys()) if tool == "all" else [tool]
    rc = 0
    for t in tools:
        if backup_tool(t, dest) not in (0, None):
            rc = 1
    return rc


def cmd_restore(argv):
    """Run restore for one tool or all tools from an archive or backup dir."""
    if len(argv) < 2:
        print("Usage: aa restore <tool|all> <archive.tar.gz|backup-dir>", file=sys.stderr)
        return 1
    tool = argv[0]
    archive = argv[1]
    if tool == "all":
        src_base = Path(archive)
        if not src_base.is_dir():
            print("  ✗ 'restore all' expects a backup directory containing per-tool archives.", file=sys.stderr)
            return 1
        rc = 0
        for t in TOOL_DATA:
            matches = sorted(src_base.glob(f"{t}-*.tar.gz"))
            if not matches:
                print(f"  Warning: no archive found for {t} in {src_base}, skipping.", file=sys.stderr)
                continue
            if restore_tool(t, str(matches[-1])) != 0:
                rc = 1
        return rc
    return restore_tool(tool, archive)


def cmd_list():
    """Print available backup archives to stdout."""
    print("Available backup archives:")
    archives = sorted(BACKUP_STORE.glob("*.tar.gz")) if BACKUP_STORE.exists() else []
    if not archives:
        print("  (none found — create one with 'aa backup <tool|all>')")
    for f in archives:
        print(f"  {f.name}")
    return 0


def cmd_help():
    """Print backup usage information to stdout."""
    print("Usage: aa backup <tool|all> [dest|gdrive]")
    print("       aa restore <tool|all> <archive.tar.gz>")
    print("       aa backup list")
    print(f"Tools: {', '.join(TOOL_DATA)}")
    return 0


def main(argv):
    """CLI entry point for the tar backup module (backup/restore/list/help)."""
    if not argv or argv[0] in ("help", "-h", "--help"):
        return cmd_help()
    if argv[0] == "list":
        return cmd_list()
    action = argv[0]
    rest = argv[1:]
    if action == "backup":
        return cmd_backup(rest)
    if action == "restore":
        return cmd_restore(rest)
    print(f"Unknown backup command: {action}", file=sys.stderr)
    return cmd_help()
