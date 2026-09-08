#!/usr/bin/env python3
"""Unified Backup & Restore (Python) — pengganti backup-manager.sh.
Memanggil gdrive.py (sudah Python) untuk Google Drive, dan tar data dirs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import data_home  # type: ignore[import-untyped]

BACKUP_STORE = data_home() / "backups"
GDRIVE_HELPER = ROOT / "tools/backup/gdrive.py"

# tool -> data subdir (relative to XDG_DATA_HOME)
TOOL_DATA = {
    "anytype": "anytype-mcp",
    "9router": "9router",
    "mnemosyne": "mnemosyne",
    "google-workspace": "google-workspace-mcp",
}


def log_info(msg): print(f"==> {msg}")
def log_ok(msg):  print(f"  [OK] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")


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


def tar_dir(src: Path, dest: Path):
    file_count = sum(1 for _ in src.rglob("*") if _.is_file())
    with _Progress(f"Archiving {src.name} ({file_count} files)..."), tarfile.open(dest, "w:gz") as tar:
        tar.add(src, arcname=src.name)


def untar(src: Path, dest: Path):
    dest = dest.resolve()
    # Verifikasi integritas archive sebelum extract (R-7)
    if not tarfile.is_tarfile(src):
        raise ValueError(f"Not a valid tar archive: {src}")
    try:
        with tarfile.open(src, "r:gz") as check_tar:
            check_tar.getmembers()  # pastikan bisa dibaca penuh
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
            # Semua member sudah divalidasi aman (R-7) => extract di sini aman
            tar.extractall(dest)


def backup_tool(tool: str, dest: str = ""):
    upload_to_gdrive = dest == "gdrive" or dest.startswith("gdrive:")
    store = BACKUP_STORE
    store.mkdir(parents=True, exist_ok=True)
    subdir = TOOL_DATA.get(tool, tool)
    src = data_home() / subdir
    if not src.exists():
        print(f"  \u26a0 No data for {tool} at {src}, skipping.")
        return 0
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive = store / f"{tool}-{ts}.tar.gz"
    log_info(f"Backing up {tool} -> {archive}")
    tar_dir(src, archive)
    log_ok(f"{tool} backed up.")
    if upload_to_gdrive:
        # Argumen list tanpa shell=True; helper path berasal dari repo (S603 ok)
        with _Progress(f"Uploading {archive.name} to Google Drive..."):
            result = subprocess.run(
                [sys.executable, str(GDRIVE_HELPER), "upload", str(archive)],
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
    src_path = Path(src)
    if not src_path.exists() or not src_path.is_file():
        print(f"  \u2717 Archive not found: {src_path}", file=sys.stderr)
        return 1
    subdir = TOOL_DATA.get(tool, tool)
    target = data_home() / subdir

    # Bersihkan data lama sebelum restore (cegah kontaminasi file stale)
    if target.exists():
        log_info(f"Cleaning existing data at {target} before restore...")
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    log_info(f"Restoring {tool} from {src_path}")
    untar(src_path, target)
    log_ok(f"{tool} restored to {target}.")
    return 0


def cmd_backup(argv):
    tool = argv[0] if argv else "all"
    dest = argv[1] if len(argv) > 1 else ""
    tools = list(TOOL_DATA.keys()) if tool == "all" else [tool]
    rc = 0
    for t in tools:
        if backup_tool(t, dest) not in (0, None):
            rc = 1
    return rc


def cmd_restore(argv):
    if len(argv) < 2:
        print("Usage: aa restore <tool|all> <archive.tar.gz>", file=sys.stderr)
        return 1
    tool = argv[0]
    archive = argv[1]
    if tool == "all":
        rc = 0
        for t in TOOL_DATA:
            if restore_tool(t, archive) != 0:
                rc = 1
        return rc
    return restore_tool(tool, archive)


def cmd_list():
    print("Available backup archives:")
    if BACKUP_STORE.exists():
        for f in sorted(BACKUP_STORE.glob("*.tar.gz")):
            print(f"  {f.name}")
    return 0


def cmd_help():
    print("Usage: aa backup <tool|all> [dest|gdrive]")
    print("       aa restore <tool|all> <archive.tar.gz>")
    print("       aa backup list")
    print(f"Tools: {', '.join(TOOL_DATA)}")
    return 0


def main(argv):
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
