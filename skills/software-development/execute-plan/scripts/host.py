#!/usr/bin/env python3
"""Linux-only host helpers for bundled orchestrator skills.
Output root: ~/.grok/plans/<projectreponame>/
"""

from __future__ import annotations
import argparse, json, re, shutil, stat, subprocess, sys, uuid
from pathlib import Path

def resolve_python() -> str:
    current = sys.executable or ""
    if current and sys.version_info.major == 3: return current
    found = shutil.which("python3")
    if found: return found
    raise SystemExit("host.py: no Python 3 interpreter found")

def _plans_root() -> Path:
    return Path.home() / ".grok" / "plans"

def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)

def _repo_slug() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            name = Path(result.stdout.strip()).name
            slug = _slugify(name)
            if slug: return slug
    except (OSError, subprocess.SubprocessError):
        raise SystemExit("host.py: git command failed")
    raise SystemExit("host.py: not inside a git repository")

def scratch_dir() -> Path:
    path = _plans_root() / _repo_slug()
    path.mkdir(parents=True, exist_ok=True)
    try: path.chmod(stat.S_IRWXU)
    except OSError: pass
    return path

def run_id(hex_len: int = 8) -> str:
    return uuid.uuid4().hex[:hex_len]

def cmd_setup(_args: argparse.Namespace) -> int:
    payload = {"python": resolve_python(), "scratch_dir": str(scratch_dir()), "run_id": run_id(8)}
    json.dump(payload, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0

def cmd_cleanup(args: argparse.Namespace) -> int:
    for raw in args.paths:
        try: Path(raw).unlink()
        except FileNotFoundError: pass
        except OSError as exc: print(f"host.py: could not remove {raw}: {exc}", file=sys.stderr)
    return 0

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="host.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    c = sub.add_parser("cleanup")
    c.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    return {"setup": cmd_setup, "cleanup": cmd_cleanup}[args.cmd](args)

if __name__ == "__main__":
    raise SystemExit(main())
