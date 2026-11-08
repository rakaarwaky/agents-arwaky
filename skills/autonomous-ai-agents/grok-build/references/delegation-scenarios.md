# Grok Build — Delegation Scenarios

Companion to the grok-build SKILL.md. Three operational recipes: read-only audit
notes, PR review, and parallel issue fixing with worktrees. Load before running
these scenarios; flag tables live in flags-and-tui.md.

## Read-Only Audit → Markdown Note

To have Grok review local artifacts and return a clean markdown note without mutating
anything:

1. Prepare stable input files first with Hermes tools (`read_file`, `write_file`).
   Snapshot only relevant context into a temp file.
2. Run Grok headless **without**   `--always-approve` so it cannot auto-write; demand
   markdown only.
   Pitfall: a headless `grok -p "<brief>"` with no `--max-turns` cap can
   exceed the foreground timeout and exit 124 while still having written
   partial filesystem changes before it died — verify the tree after every
   headless run (especially on timeout) with the Delegation Verification
   Protocol below; never assume a timed-out run left the tree untouched, and
   cap long one-shots with `--max-turns` so a hang cannot run unbounded.
3. Save stdout into the destination note with `write_file()`.

Pitfall: for document rewrites, a loose "rewrite this" prompt may return a change
summary instead of the full file. Pipe the file in and demand "Return ONLY the full
revised markdown document. No intro, no explanation, no code fences. Start immediately
with `# Title`". Verify the first lines with `read_file()` before overwriting the
destination.

## PR Review Patterns

### Quick Review (Headless, inside an Orca worktree)

```bash
# Create an Orca worktree for the review
"$ORCA" worktree create --repo path:<repo_path> --name review-<slug> --agent grok --no-parent --json
cd <worktree_path>
git diff main...feature-branch | grok -p 'Review this diff for bugs, security issues, and style problems. Be thorough.' --cwd <worktree_path>
```

### Clone-to-Temp Review (safe, no repo mutation)

```bash
REVIEW=$(mktemp -d)
git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && gh pr checkout 42
grok -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.' --cwd $REVIEW
gh pr comment 42 --body '<review text>'
```

## Parallel Issue Fixing with Orca Worktrees

```bash
# Create Orca-managed worktrees (preferred — tracks agent state)
"$ORCA" worktree create --repo path:<repo_path> --name fix-issue-78 --agent grok --no-parent --json
"$ORCA" worktree create --repo path:<repo_path> --name fix-issue-99 --agent grok --no-parent --json

# Launch Grok headless inside each worktree (background)
cd <worktree_path_78> && grok -p 'Fix issue #78: <desc>. Commit when done.' --cwd <worktree_path_78> --always-approve
cd <worktree_path_99> && grok -p 'Fix issue #99: <desc>. Commit when done.' --cwd <worktree_path_99> --always-approve

# After completion: push and open PRs from each worktree
git -C <worktree_path_78> push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...'

# Retire worktrees after PRs merge
"$ORCA" worktree rm --worktree <worktree_id_78> --force --json
```

Fallback: plain `git worktree add` works without the Orca daemon, but you
lose agent-state tracking and terminal management.

## Delegation Verification Protocol (supervised Orca-TUI runs)

The TUI brief you send is the only contract the agent has. It may do more than
you asked (e.g. invent a broader design on a task you briefed as a narrow
change) and it runs with permissions bypassed, so nothing stops it from
committing or even pushing before you read back what happened. Treat every
supervised run as untrusted until verified:

1. **Worktree base must match the plan.** `orca worktree create --agent grok`
   can base the new branch on the remote default (`origin/main`) even when
   the brief assumes a different base (e.g. stacked on a sibling feature
   branch): before driving the run, `git log --oneline -3` in the worktree
   and reset to the intended base (`git reset --hard <base-sha>` on the
   new branch, or recreate) — a stacked task built on the wrong base will
   either conflict or miss its predecessor's work. Untracked/staged
   leftovers in a freshly created worktree are yours to reconcile; only
   `git reset --hard` after verifying nothing of value is in it.
2. After the run, re-read the actual worktree state — `git status --short`,
   `git log --oneline -3`, and the full `git diff <base>..HEAD` — rather than
   trusting the commit message or a "done" summary. If the diff diverges from
   the brief, re-brief with an explicit "do exactly these N changes, nothing
   else" constraint (or reset the divergent commit first) instead of patching
   over it.
2. The agent may commit and push on its own before you do — after a wait times
   out, re-check `git log` and the remote branch before assuming the worktree
   the worktree is still in the state you last saw. If it already opened a PR whose title
   or body describe a superseded design, rewrite both to match the final diff,
   not the original intent. Use `git push --force-with-lease=<ref>:<sha>` (never
   bare `--force`) to replace a superseded commit on an already-pushed branch,
   and check `gh pr list --head <branch>` to catch a PR that was opened as an
   unintended side effect of the agent's push.
4. **Judge inherited red by comparison with the base, not by an absolute
   green.** Before believing a CI/test failure is caused by your branch,
   run the same test command on the base branch (e.g. `main`) and diff the
   failing sets: identical failures on both are pre-existing repo red
   (main itself may be red for a while) and out of scope — note them in the
   PR body and stop; failures present only on your branch are yours to fix.
   CI can also fail on pre-existing lint in files you did not touch (e.g.
   import-sort I001 in unrelated script tests); in that case run the linter
   locally scoped to the failing files, apply the minimal `--fix`, and commit
   it with a message naming the rule so the follow-up is auditable.
5. Same protocol applies to follow-up briefs sent while the previous run's
   commit is still unpushed: re-check `git status`/`git log` before assuming the
   worktree is clean, since the agent may have raced ahead of your last check
   and already committed (or pushed) the follow-up work itself — a commit you
   expected to make may already exist on top of the work you were inspecting.

## Drop-and-Wait Handoff to a Grok TUI (Hermes full handoff)

When Hermes orchestrates a Grok Build TUI inside an Orca worktree (the
/implement or /execute-plan handoff), the full contract lives in the repo
skill's `references/hermes/` step files — load those before driving a run.
This section carries only the class-level rules that generalize beyond any
single skill:

- **Hermes never spawns its own subagents for implementer/reviewer roles and
  never runs the review panel itself** — the implement/review/fix loop runs
  inside Grok's own skill. If you find yourself launching `spawn_subagent`
  or `delegate_task` children to do Grok's job, stop: the worktree's Grok TUI
  is the only "subagent", and Hermes's only job before the wait is to plan the
  brief and drop it once.
- **One-shot drop, no pings.** Send exactly one `orca terminal send` message:
  the slash command (e.g. `/implement <task>` or `/execute-plan <doc>`) plus
  the brief's goal, scope, out-of-scope list, constraints, and acceptance
  criteria. Grok has zero conversation context — the brief must be
  self-contained. After `accepted: true`, send no further text: no status
  checks, no "is it done?", no course corrections. If you need to change
  scope, stop the TUI, revert out-of-scope work in your own tools, and
  re-drop.
- **Wait, don't poll.** Use `orca terminal wait --for tui-idle` (retry with a
  larger timeout while `satisfied: false`); fall back to `orca terminal read`
  only to inspect output, never to prod Grok. Two read/`wait` quirks:
  a `read` whose stream `tail` stays empty is not proof the agent has no
  input queued (its stream can be empty while it is actively editing files) —
  check the worktree's `git status`/`git log` instead; and
  `satisfied: true` can come back while `status` is still `running`, meaning
  'no pending input', not 'job finished'. A foreground `wait` whose timeout
  exceeds the terminal tool's cap is promoted to a tracked background
  process with a `session_id` — drive it via `process_manage`, never re-run
  the wait.
- **Verify and ship yourself.** When idle, read Grok's artifacts (its state
  file / summary / review files under its scratch dir), audit the worktree
  against the in-scope paths, run the repo's local gate on a clean tree, then
  commit, push (`--force-with-lease`), and open the PR in Hermes's own tools.
  Never hand-assemble missing work: on partial failure, report it and suggest
  the skill's `--resume` flag instead of re-doing Grok's assembly by hand.

## Post-Delegation Verification (before commit/push)

When a delegated agent finishes work inside a worktree, do not trust its
"done" summary — verify the worktree yourself before committing or pushing:
0. **After reverting a divergent run, re-check the full `git status --short`, not just the tree.** A timed-out or off-brief run can leave staged deletions or renames (a ` D path` or `R` entry) even after the tracked-file changes look clean. A blanket `git checkout -- .` reverts the *working-tree* copy of tracked files but does NOT unstage or restore index entries — and it silently discards pre-existing uncommitted user work that was in the tree when you started. Capture the dirty state first (snapshot `git status --short` / the specific `git diff HEAD -- <path>` of user-modified files before the run), then after the run diff the status again and reconcile every unintended entry by path (`git reset HEAD -- <path>` to unstage, `git checkout HEAD -- <path>` to restore a deleted tracked file, re-apply or restore the pre-existing diff). Never `git add -A` or bare `git commit -a` in a shared multi-agent tree; commit only the explicitly staged paths from the fix, and re-check `git diff --cached --name-only` after every `git add` to catch files a parallel agent pre-staged.

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
   dirty tree proves nothing about the committed blob. GitHub-side follow-up:
   `gh pr edit` against a repo with classic Projects can exit 1 on the
   deprecation GraphQL warning (repository.pullRequest.projectCards) even
   when the title/body write through — always re-read `gh pr view <n>
   --json title,body,state,headRefOid` to confirm what actually landed
   instead of trusting the exit code, and do not loop retrying the edit.
4. Never trust a delegated agent's self-report that a gate passed —
   re-run the gate yourself against the exact commit that will be pushed,
   and verify that commit's blobs (e.g. `git show HEAD:<path>`) when in
   doubt. A green local run reported by the agent can be a false positive
   on a dirty tree or on a commit different from the one that landed;
   and a CI failure you already dismissed as "stale" can belong to the
   newest SHA — re-fetch CI run state before believing any gate is green.