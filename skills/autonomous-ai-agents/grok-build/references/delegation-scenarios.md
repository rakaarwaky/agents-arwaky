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

## Delegation Verification Protocol (supervised Orca-TUI runs)

The TUI brief you send is the only contract the agent has. It may do more than
you asked (e.g. invent a broader design on a task you briefed as a narrow
change) and it runs with permissions bypassed, so nothing stops it from
committing or even pushing before you read back what happened. Treat every
supervised run as untrusted until verified:

1. After the run, re-read the actual worktree state — `git status --short`,
   `git log --oneline -3`, and the full `git diff <base>..HEAD` — rather than
   trusting the commit message or a "done" summary. If the diff diverges from
   the brief, re-brief with an explicit "do exactly these N changes, nothing
   else" constraint (or reset the divergent commit first) instead of patching
   over it.
2. The agent may commit and push on its own before you do — after a wait times
   out, re-check `git log` and the remote branch before assuming the worktree
   is still in the state you last saw. If it already opened a PR whose title
   or body describe a superseded design, rewrite both to match the final diff,
   not the original intent. Use `git push --force-with-lease=<ref>:<sha>` (never
   bare `--force`) to replace a superseded commit on an already-pushed branch,
   and check `gh pr list --head <branch>` to catch a PR that was opened as an
   unintended side effect of the agent's push.
3. Same protocol applies to follow-up briefs sent while the previous run's
   commit is still unpushed: re-check `git status`/`git log` before assuming the
   worktree is clean, since the agent may have raced ahead of your last check
   and already committed (or pushed) the follow-up work itself — a commit you
   expected to make may already exist on top of the work you were inspecting.

## Post-Delegation Verification (before commit/push)

When a delegated agent finishes work inside a worktree, do not trust its
"done" summary — verify the worktree yourself before committing or pushing:

1. `git status --short` in the worktree: the agent may have left stray
   artifacts (scratch files it wrote at the repo root, e.g. a `commit-msg.txt`)
   or uncommitted variants of the files it claims to have fixed. Remove stray
   files and reconcile on-disk content with what should be committed.
2. If the agent committed for you, check the commit message:
   `git log --oneline -1`. An agent-narration message (e.g. "I've written the
   commit message to `commit-msg.txt`…") is not shippable — amend it to the
   repo's conventional format before pushing (`git commit --amend -m …`,
   force-with-lease).
3. Re-run the repo's own gate (in this repo: `CARGO_INCREMENTAL=0 cargo build
   --release && ./target/release/lint-arwaky-cli check .` expecting
   `Total: 0 violations`) on a clean tree before pushing. A green run on a
   dirty tree proves nothing about the committed blob.