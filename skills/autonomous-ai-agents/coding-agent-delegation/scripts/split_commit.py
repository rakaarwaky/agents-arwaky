#!/usr/bin/env python3
"""Split an existing dirty worktree diff into atomic commits by file set.

Use when a headless worker finished the edits but died before committing
(budget/exit 55). Reads a JSON plan of [{name, message, files}] and stages +
commits each group in order, leaving every other change unstaged.

Usage (run from the repo/worktree root):
  python split_commit.py --plan /tmp/plan.json --add-untracked path/a.py,path/b.py
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def run(*args: str) -> str:
    res = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"FAILED {args}: {res.stderr.strip() or res.stdout.strip()}")
    return res.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, help="JSON file: [{name,message,files}]")
    parser.add_argument(
        "--add-untracked", default="", help="comma-separated new files to stage"
    )
    args = parser.parse_args()

    groups = json.loads(Path(args.plan).read_text(encoding="utf-8"))

    for path in (p.strip() for p in args.add_untracked.split(",") if p.strip()):
        run("git", "add", "-f", path)

    msg = ROOT / ".split-commit-msg"
    for group in groups:
        run("git", "reset", "-q")
        for path in group["files"]:
            run("git", "add", "-f", path)
        stat = run("git", "diff", "--cached", "--stat")
        if not stat:
            sys.exit(f"group {group['name']!r} staged nothing — check the file paths")
        msg.write_text(group["message"], encoding="utf-8")
        run("git", "commit", "-q", "-F", str(msg))
        print(f"committed {group['name']}: {stat.splitlines()[-1].strip()}")

    if msg.exists():
        msg.unlink()

    print("--- leftover (must be empty or explained) ---")
    print(run("git", "status", "--porcelain") or "(clean)")
    print("--- recent commits ---")
    print(run("git", "log", "--oneline", "-3"))


if __name__ == "__main__":
    main()
