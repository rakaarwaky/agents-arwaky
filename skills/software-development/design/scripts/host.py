#!/usr/bin/env python3
"""Linux-only host helpers for the design skill.

This module is the single source of truth for the artifact root:

    ~/.grok/plans/<projectreponame>/

The `setup` command creates the per-repo directory and returns it as
`scratch_dir`; the skill's step files derive every artifact path from that
value and must not hardcode a second copy of the location.

If the current directory is not inside a git repository, this script exits
with an error. No fallback directory is used.

This module only runs on Linux. On any other platform it exits immediately
with a clear message rather than silently failing to resolve Python.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path


def resolve_python() -> str:
    """Return an absolute Python 3 executable. Linux only."""
    if os.name != "posix" or sys.platform != "linux":
        raise SystemExit("host.py: this helper runs on Linux only")

    current = sys.executable or ""
    if current and sys.version_info.major == 3:
        return current

    found = shutil.which("python3")
    if found:
        return found

    raise SystemExit("host.py: no Python 3 interpreter found")


def _plans_root() -> Path:
    return Path.home() / ".grok" / "plans"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def _repo_slug() -> str:
    """Return the git repository name only. No fallback."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        raise SystemExit("host.py: git command failed")

    if result.returncode != 0 or not result.stdout.strip():
        raise SystemExit("host.py: not inside a git repository")

    name = Path(result.stdout.strip()).name
    slug = _slugify(name)

    if not slug:
        raise SystemExit("host.py: could not derive project repo name from git root")

    return slug


def scratch_dir() -> Path:
    """Per-repo artifact root: ``~/.grok/plans/<projectreponame>/``."""
    path = _plans_root() / _repo_slug()
    path.mkdir(parents=True, exist_ok=True)

    try:
        path.chmod(stat.S_IRWXU)
    except OSError:
        pass

    return path


def cmd_setup(_args: argparse.Namespace) -> int:
    payload = {
        "python": resolve_python(),
        "scratch_dir": str(scratch_dir()),
        "run_id": uuid.uuid4().hex[:8],
    }
    json.dump(payload, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    for raw in args.paths:
        try:
            Path(raw).unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"host.py: could not remove {raw}: {exc}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="host.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser(
        "setup",
        help="Create the artifact root and print JSON {python, scratch_dir, run_id}.",
    )

    c = sub.add_parser("cleanup", help="Unlink files; missing paths are ok.")
    c.add_argument("paths", nargs="+")

    args = parser.parse_args(argv)

    handlers = {
        "setup": cmd_setup,
        "cleanup": cmd_cleanup,
    }

    return handlers[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())