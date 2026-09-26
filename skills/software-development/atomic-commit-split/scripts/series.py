#!/usr/bin/env python3
"""Execute an ordered, guarded commit series built from classify.py's buckets.

  python3 series.py          # dry run: per-commit file counts + coverage check
  python3 series.py 3        # commit #3 only
  python3 series.py 10-14    # commits 10..14
  python3 series.py --all    # everything

Guards: reset the index per commit, stage only via --pathspec-from-file, and
report expected-vs-staged drift instead of committing a surprise set.
"""
import subprocess
import sys
from pathlib import Path

SPLIT = Path(".commit-split")

STEPS = [
    # (num, subject, body, bucket-list, mode)   mode: add | rm-cache
    (1, "chore(gitignore): stop tracking runtime churn", "", ["a-gitignore"], "add"),
    (2, "chore(repo): untrack the churn files gitignore now covers",
     "git rm --cached only; files stay on disk.", ["v-untrack"], "rm-cache"),
]


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"$ git {' '.join(args)}\n{r.stdout}{r.stderr}")
    return r.stdout


def load(name):
    p = SPLIT / f"{name}.txt"
    return [l.strip() for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def bucket_paths(spec):
    out = []
    for item in spec:
        out += load(item) if (SPLIT / f"{item}.txt").exists() else [item]
    return sorted(set(out))


def expand(paths):
    """Flatten dirs to files, honouring ignores -> the honest expected count."""
    if not paths:
        return []
    res = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", *paths],
        capture_output=True, text=True, check=True).stdout
    return sorted(set(res.split()))


def perform(num, subject, body, spec, mode):
    paths = bucket_paths(spec)
    want = expand(paths)
    git("reset", "-q")
    if mode == "rm-cache":
        r = subprocess.run(["git", "rm", "-r", "--cached", "-q", "--force", "--", *paths],
                           capture_output=True, text=True)
        if r.returncode:
            print("    rm --cached:", (r.stdout + r.stderr).strip()[:200])
    else:
        (SPLIT / ".pathspec").write_text("\n".join(paths) + "\n")
        r = subprocess.run(["git", "add",
                            "--pathspec-from-file=.commit-split/.pathspec", "-A"],
                           capture_output=True, text=True)
        if r.returncode:
            # Already-deleted files under a fresh ignore rule cannot be `add -f`'d
            # (the worktree entry is gone); rm --cached records the deletion.
            print("    add refused:", r.stderr.strip().splitlines()[:1])
            subprocess.run(["git", "rm", "-r", "--cached", "-q", "--force", "--", *paths],
                           capture_output=True, text=True)
    got = sorted(set(git("-c", "core.quotepath=false",
                         "diff", "--cached", "--name-only").splitlines()))
    print(f"[{num}] {subject}\n    expected {len(want)}, staged {len(got)}")
    if not got:
        print("    SKIP (nothing staged)")
        return False
    drift = [p for p in want if p not in got]
    extra = [p for p in got if p not in want]
    if drift[:3] or extra[:3]:
        print("    DRIFT missing:", drift[:5], "extra:", extra[:5])
    (SPLIT / ".msg").write_text(subject + ("\n\n" + body if body else "") + "\n")
    git("commit", "-q", "-F", ".commit-split/.msg")
    print("    ->", git("log", "--oneline", "-1").strip())
    return True


def all_dirty():
    paths = [l[3:].split(" -> ")[-1] for l in
             git("-c", "core.quotepath=false", "status", "--porcelain=v1").splitlines()
             if l.strip()]
    return set(expand(sorted(set(paths))))


def coverage():
    """Assert every dirty file lands in some commit before staging anything."""
    covered = set()
    for *_, spec, mode in STEPS:
        covered |= set(expand(bucket_paths(spec)))
    dirty = all_dirty()
    missing = sorted(dirty - covered)
    print(f"dirty {len(dirty)}, covered {len(covered)}, MISSING {len(missing)}")
    for p in missing[:20]:
        print("   ", p)
    return not missing


def parse(arg):
    if arg == "--all":
        return list(range(1, len(STEPS) + 1))
    if "-" in arg:
        a, b = arg.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(arg)]


def main():
    if len(sys.argv) < 2:
        for num, subj, body, spec, mode in STEPS:
            print(f"[{num:2d}] {subj}  ({mode}, {len(expand(bucket_paths(spec)))} files)")
        return 0 if coverage() else 1
    done = [n for n in parse(sys.argv[1])
            if perform(*next(s for s in STEPS if s[0] == n))]
    print("committed:", done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
