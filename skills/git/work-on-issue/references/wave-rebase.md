# Wave Rebase and Sibling-PR Conflicts

Phase F. After a wave of PRs merges, rebase every still-open branch onto the new default
tip before CI re-runs. A stale base fails self-lint and format against already-merged code;
the fix is a rebase, not a debug session.

## Rebase discipline

1. Rebase **one** branch at a time.
2. Confirm `git status` is clean inside that worktree before and after the rebase.
3. Force-push only that branch, then move to the next.
4. A blind rebase-and-force-push loop across worktrees leaves dirty rebase states that
   block the next wave — stop and resolve the dirty tree before continuing.

```bash
# WT = Orca worktree path (ORCA worktree show --worktree id:<repoId>::<path> --json)
cd "$WT"
git status
git fetch origin
git rebase origin/<default>
git status
# only if clean:
git push --force-with-lease
```

Prefer `--force-with-lease` over `--force`.

## Stale CI report

A "still failing" report may be from an older SHA than the branch head (a fix was pushed
after the run started). Confirm before debugging:

```bash
gh api repos/O/R/actions/runs/<run> -q .head_sha
gh api .../jobs/<id>/logs   # shows the SHA GitHub actually built
git rev-parse origin/<branch>
git show origin/<branch>:<file>
```

Treat a failure as live only when the run's `head_sha` matches the branch tip.

## Sibling-PR conflict shape (the expensive one)

When PR A (long-lived refactor, e.g. an API-seam change) is rebased onto default and
default has since merged PR B (built against the OLD API), the rebase is usually
textually clean but fails to compile: B's new file still calls the helper A deleted.
Git has no conflict markers — you get unresolved-import / missing-field errors for
symbols that no longer exist.

Diagnose:

```bash
# Deleted symbol is gone from the tree…
rg -n 'fn <deleted_symbol>|def <deleted_symbol>|function <deleted_symbol>' .

# …but a file merged in B still references it
rg -n '<deleted_symbol>' <new_file>
```

Fix by porting B's call sites onto A's replacement, matching the pattern already used
elsewhere in the same PR (`git show origin/<default>:<file> | rg '<replacement>'`).
Do **not** restore the deleted symbol — A's removal is the intent.

Expect N call sites, not one. When hand-editing a conflict block, compare against a
sibling call for the exact closer/trailing-comma shape; mismatched closers are a common
follow-on failure after a mechanical port.

## When to stop and ask

Stop the wave and escalate if:

- Two open worktrees touch the same files and both need the default tip.
- A rebase needs a semantic rewrite larger than a call-site port.
- CI is red on default itself (not branch-specific) — fix default first.
