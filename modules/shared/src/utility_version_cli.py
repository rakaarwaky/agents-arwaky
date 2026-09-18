"""Standalone version-bump CLI (moved from tools/build/bump_version.py main)."""
from __future__ import annotations

import sys

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.version.utility_version import bump, read_version


def main(argv: list[str]) -> int:
    part = argv[0] if argv else "patch"
    cur = read_version()
    try:
        nxt = bump(cur, part)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    version_file = repo_root() / "config" / "version.txt"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text(nxt + "\n", encoding="utf-8")
    print(f"agents-arwaky {cur} -> {nxt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
