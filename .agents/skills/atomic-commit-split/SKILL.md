---
name: atomic-commit-split
description: Use when a dirty tree must become an atomic commit series.
metadata:
  tags: []
---

# Atomic commit split

Turn one giant dirty tree into N self-contained commits. For repos where the
same paths churn every run (agent homes, backup repos, generated trees).

## Workflow

1. **Survey before deciding.** `git status --porcelain=v1 | awk '{print $1}'
   | sort | uniq -c | sort -rn`, then group deletions by path prefix
   (`sed 's/^ D //' | awk -F/ '{print $1"/"$2"/"$3"/"$4}' | uniq -c`). Read the
   real diffs for the small stuff (config, memories) — the message must say what
   changed, not that something changed.
2. **Write a classifier script**, not manual `git add` chains. It reads
   `git status --porcelain`, maps every path to one named bucket, writes
   `bucket.txt` files, prints counts. Parse with
   `xy, path = line[:2], line[3:].split(" -> ")[-1]` and match on
   `xy.strip() in ("D","M","MM","AM","AD","T")` — comparing two-column forms
   literally silently drops ` M`/`M `.
3. **Route runtime churn to gitignore, not to a commit.** Heartbeats, lifecycle
   JSON, session indexes, prompt snapshots, scratch/queue dirs. Commit the
   `.gitignore` change FIRST, then `git rm -r --cached --force -- <paths>` to
   untrack. Files stay on disk.
4. **Order the series** so each commit stands alone: gitignore → untrack churn →
   deletions (grouped by *reason*, not directory) → submodule bump → config →
   additions → content edits → bookkeeping (lock files last).
5. **Stage with a guard**: `git reset -q` first (kills leftovers), then
   `git add --pathspec-from-file=<list>` — never `git add -A` on the whole tree.
   Print expected-vs-staged file counts per commit; report drift, don't hide it.
6. **Verify coverage before committing anything**: expand the full dirty set
   (`git ls-files --cached --others --exclude-standard -- <paths>`, which
   flattens dirs and drops ignored junk) and assert `dirty - covered == 0`. A
   silent gap is how half a prune disappears.
7. End state: `git status --porcelain | wc -l` == 0 **and**
   `git diff --name-only HEAD | wc -l` == 0 (nothing on disk lost by the split).

## Pitfalls

- **Deleting a path your own new ignore rule covers**: `git add -f` dies with
  `fatal: pathspec ... did not match any files` because the worktree entry is
  gone. Use `git rm -r --cached --force -- <path>` for already-deleted files.
- **`--pathspec-from-file` needs a repo-relative path**, and the list file must
  be gitignored, or your scratch becomes commit #21.
- A bare root pattern (`processes.json`) already matches nested copies, so the
  `**/` twin is redundant — always run `git ls-files` against new rules to see
  which tracked files you just shadowed.
- Secret-check the series, not the files:
  `git log <base>..HEAD -p | grep -inE '^\+.*(api_key|bot_token|sk-[A-Za-z0-9]{20,}|PRIVATE KEY)'`.
  Env-var *names* in docs are fine; values are not.
- Don't push unless asked. Report `git rev-list --count origin/<br>..<br>`.
- After a bulk prune, state out loud what the deleted trees were (duplicate
  copies vs real retirements) and flag any tracked symlink whose target is
  missing — pre-existing damage, not caused by the split, never silently fixed.

## Reusable scripts

`scripts/classify.py` — status → buckets, prints counts + UNROUTED list (exit 1
if anything is unrouted). Edit `classify()` and `TRANSIENT` per repo.
`scripts/series.py` — ordered step table with guarded stage/commit + `coverage()`
assertion; run with no args for a per-commit dry run.
