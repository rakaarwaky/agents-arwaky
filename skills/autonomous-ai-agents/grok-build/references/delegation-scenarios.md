# Grok Build — Delegation Scenarios

Companion to the grok-build SKILL.md. Three operational recipes: read-only audit
notes, PR review, and parallel issue fixing with worktrees. Load before running
these scenarios; flag tables live in flags-and-tui.md.

## Read-Only Audit → Markdown Note

To have Grok review local artifacts and return a clean markdown note without mutating
anything:

1. Prepare stable input files first with Hermes tools (`read_file`, `write_file`).
   Snapshot only relevant context into a temp file.
2. Run Grok headless **without** `--always-approve` so it cannot auto-write; demand
   markdown only.
3. Save stdout into the destination note with `write_file()`.

Pitfall: for document rewrites, a loose "rewrite this" prompt may return a change
summary instead of the full file. Pipe the file in and demand "Return ONLY the full
revised markdown document. No intro, no explanation, no code fences. Start immediately
with `# Title`". Verify the first lines with `read_file()` before overwriting the
destination.

## PR Review Patterns

### Quick Review (Headless)

```bash
git diff main...feature-branch | grok -p 'Review this diff for bugs, security issues, and style problems. Be thorough.'
```

### Clone-to-Temp Review (safe, no repo mutation)

```bash
REVIEW=$(mktemp -d)
git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && gh pr checkout 42
grok -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.'
gh pr comment 42 --body '<review text>'
```

## Parallel Issue Fixing with Worktrees

```bash
git worktree add -b fix/issue-78 ~/.hermes/cache/scratch/issue-78 main
git worktree add -b fix/issue-99 ~/.hermes/cache/scratch/issue-99 main

# Launch Grok headless in each (background)
grok --always-approve -p 'Fix issue #78: <desc>. Commit when done.'  # in worktree 78
grok --always-approve -p 'Fix issue #99: <desc>. Commit when done.'  # in worktree 99

# After completion: push and open PRs, then clean up
cd ~/.hermes/cache/scratch/issue-78 && git push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...'
git worktree remove ~/.hermes/cache/scratch/issue-78
```

The same worktrees can be Orca-managed (`orca worktree create`), but plain `git
worktree` works without the Orca daemon.