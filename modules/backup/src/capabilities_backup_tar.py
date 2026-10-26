"""Tar backup capability for local archives and restore.

The module retains the original script's ``main(argv)`` CLI entry point and
tar/restore helpers while routing aggregate calls through ``TarBackupGateway``.
"""
from __future__ import annotations

import os
import shutil
import sys
import tarfile
import threading
from datetime import UTC, datetime
from pathlib import Path

from modules.shared.src.backup.contract_backup_protocol import IBackupControlProtocol
from modules.shared.src.backup.taxonomy_backup_constant import (
    BACKUP_STORE,
    TOOL_DATA,
)
from modules.shared.src.backup.taxonomy_backup_vo import (
    ARCHIVE_DEFAULT,
    DEST_DEFAULT,
    BackupArchive,
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    RestoreResult,
)
from modules.shared.src.common.taxonomy_common_vo import data_home


# ─── Block 1: Class Definition & Constructor ──────────────
class TarBackupGateway(IBackupControlProtocol):
    """tar/untar backup & restore with progress reporting."""

    # ─── Block 2: Protocol Method Implementation ──────────────

    def backup(self, tool: BackupToolQuery, dest: BackupDestination = DEST_DEFAULT) -> BackupResult:
        """Create a local tar.gz archive in the requested destination."""
        return backup_tool_result(str(tool), str(dest))

    def restore(self, tool: BackupToolQuery, archive: BackupArchive = ARCHIVE_DEFAULT) -> RestoreResult:
        """Restore *tool* data from a local tar.gz *archive*."""
        rc = cmd_restore([str(tool), str(archive)])
        return RestoreResult(rc == 0, str(tool), str(archive), "", "tar restore completed" if rc == 0 else "tar restore failed")

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
    """Archive *src* directory into a new gzip-compressed tar at *dest*."""
    file_count = sum(1 for _ in src.rglob("*") if _.is_file())
    created = False
    try:
        with (
            _Progress(f"Archiving {src.name} ({file_count} files)..."),
            tarfile.open(dest, "x:gz") as tar,
        ):
            created = True
            tar.add(src, arcname=src.name)
    except BaseException:
        if created:
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass
        raise


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


def backup_tool_result(tool: str, dest: str = "") -> BackupResult:
    """Create a local archive for *tool* (or all registered tools)."""
    if tool == "all":
        results = [backup_tool_result(item, dest) for item in TOOL_DATA]
        failures = [result.tool_id for result in results if not result.success]
        archives = [result.archive for result in results if result.archive]
        message = (
            f"Backed up {len(results) - len(failures)} of {len(results)} tools"
            if not failures
            else f"Backup failed for: {', '.join(failures)}"
        )
        return BackupResult(
            success=not failures,
            tool_id="all",
            archive=";".join(archives),
            message=message,
        )

    subdir = TOOL_DATA.get(tool, tool)
    src = data_home() / subdir
    if not src.exists():
        message = f"No data for {tool} at {src}; nothing to back up."
        print(f"  ⚠ {message}")
        return BackupResult(True, tool, "", message)

    store = BACKUP_STORE if not dest else Path(dest).expanduser()
    try:
        store.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        message = f"Could not create backup destination {store}: {exc}"
        print(f"  ✗ {message}", file=sys.stderr)
        return BackupResult(False, tool, "", message)

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    archive = store / f"{tool}-{timestamp}.tar.gz"
    suffix = 1
    while archive.exists():
        archive = store / f"{tool}-{timestamp}-{suffix}.tar.gz"
        suffix += 1
    log_info(f"Backing up {tool} -> {archive}")
    try:
        tar_dir(src, archive)
    except (OSError, tarfile.TarError) as exc:
        message = f"Could not create backup archive {archive}: {exc}"
        print(f"  ✗ {message}", file=sys.stderr)
        return BackupResult(False, tool, str(archive), message)
    log_ok(f"{tool} backed up locally.")
    return BackupResult(True, tool, str(archive), "local backup completed")


def backup_tool(tool: str, dest: str = "") -> int:
    """Back up *tool* to the local store and return its exit code."""
    return 0 if backup_tool_result(tool, dest).success else 1


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
    """Run backup for one or all tools to the local store or destination dir."""
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
    print("Usage: aa backup <tool|all> [destination-dir]")
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
