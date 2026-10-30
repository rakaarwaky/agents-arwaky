#!/usr/bin/env python3
"""Route every dirty path in a repo into named buckets, then prove coverage.

Run from the repo root:  python3 classify.py
Writes <OUT>/<bucket>.txt lists for series.py and prints a count table plus any
UNROUTED paths (must be 0 before you start committing).

Edit classify() and TRANSIENT for the repo at hand. Bucket-name prefixes encode
commit order, so keep them stable once series.py references them.
"""
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(".commit-split")  # add this dir to .gitignore before running

# Paths that churn on every run: they get an ignore rule + git rm --cached,
# never a content commit.
TRANSIENT = {
    "state/gateway.heartbeat",
    ".hermes_history",
}


def status_entries():
    raw = subprocess.run(
        ["git", "-c", "core.quotepath=false", "status", "--porcelain=v1"],
        capture_output=True, text=True, check=True,
    ).stdout
    for line in raw.splitlines():
        if not line.strip():
            continue
        xy, path = line[:2], line[3:].split(" -> ")[-1]
        if xy == "??":
            yield "??", path
        elif xy.strip() in ("D", "M", "MM", "AM", "AD", "T"):
            yield xy.strip(), path
        else:
            print("UNMATCHED STATUS", repr(line), file=sys.stderr)


def classify(path, xy):
    """Return a bucket name. Sorting the names gives the commit order.

      a-*   ignore rules (first)     v-*  untrack churn (git rm --cached)
      w/x/y- hand-written groups consumed by series.py
      c/d/e-  deletions grouped by REASON, not directory
      f..j-   additions grouped by feature
      l/m/n/o- memories, config, submodule, profile config
      p/r-    content edits          z-*  bookkeeping last
      zz-transient  never committed as content
    """
    if path in TRANSIENT or path.endswith((".heartbeat", ".lifecycle.json")):
        return "zz-transient"
    if path == ".gitignore":
        return "a-gitignore"
    if xy == "D":
        return "z-review"
    if xy == "??":
        return "z-review"
    return "z-review"


def main():
    buckets = defaultdict(list)
    for xy, path in status_entries():
        buckets[classify(path, xy)].append(path)
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        if f.name[0] in "vwxy":
            continue  # hand-written groups are inputs, not outputs
        f.unlink()
    for name in sorted(buckets):
        (OUT / f"{name}.txt").write_text(
            "".join(p + "\n" for p in sorted(set(buckets[name]))))
        print(f"{name:26s} {len(set(buckets[name])):5d}")
    rv = sorted(set(buckets.get("z-review", [])))
    print(f"{'UNROUTED':26s} {len(rv):5d}")
    for p in rv[:30]:
        print("      !", p)
    return 1 if rv else 0


if __name__ == "__main__":
    sys.exit(main())
