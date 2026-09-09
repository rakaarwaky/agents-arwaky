#!/usr/bin/env python3
"""Unified version bump (P1-CI3): bump <patch|minor|major>."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
VERSION_FILE = ROOT / "tools/config/version.txt"


def read_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.1.0"


def bump(current: str, part: str) -> str:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", current.strip())
    if not m:
        raise ValueError(f"Unrecognized version format: {current!r}")
    major, minor, patch = (int(g) for g in m.groups())
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        raise SystemExit(f"Usage: bump_version.py <patch|minor|major> (current: {current})")
    return f"{major}.{minor}.{patch}"


def main(argv) -> int:
    part = argv[0] if argv else "patch"
    cur = read_version()
    nxt = bump(cur, part)
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(nxt + "\n", encoding="utf-8")
    print(f"agents-arwaky {cur} -> {nxt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
