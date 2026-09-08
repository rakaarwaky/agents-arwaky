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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import data_home

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
def log_ok(msg):  print(f"  \u2713 {msg}")


def tar_dir(src: Path, dest: Path):
    with tarfile.open(dest, "w:gz") as tar:
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
        raise ValueError(f"Corrupt or truncated archive {src}: {e}")
    with tarfile.open(src, "r:gz") as tar:
        try:
            # Python 3.12+: filter="data" blocks traversal/symlinks
            tar.extractall(dest, filter="data")
        except TypeError:
            # Fallback for older Python: validate ALL members before extraction
            for member in tar.getmembers():
                member_path = (dest / member.name).resolve()
                if not str(member_path).startswith(str(dest) + os.sep):
                    raise ValueError(f"Blocked path traversal in archive: {member.name}")
                if member.issym() or member.islnk():
                    raise ValueError(f"Blocked symlink/hardlink in archive: {member.name}")
                if member.isdev():
                    raise ValueError(f"Blocked device node in archive: {member.name}")
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
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = store / f"{tool}-{ts}.tar.gz"
    log_info(f"Backing up {tool} -> {archive}")
    tar_dir(src, archive)
    log_ok(f"{tool} backed up.")
    if upload_to_gdrive:
        result = subprocess.run(
            [sys.executable, str(GDRIVE_HELPER), "upload", str(archive)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  \u2717 Google Drive upload failed: {result.stderr.strip()}", file=sys.stderr)
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
    for t in tools:
        backup_tool(t, dest)
    return 0


def cmd_restore(argv):
    if len(argv) < 2:
        print("Usage: aa restore <tool|all> <archive.tar.gz>", file=sys.stderr)
        return 1
    tool = argv[0]
    archive = argv[1]
    if tool == "all":
        for t in TOOL_DATA:
            restore_tool(t, archive)
        return 0
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
