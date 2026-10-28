# Safety Guardrails

## Safety Guardrails

Follow these rules strictly:

- **Never work on the default branch in the main clone.** Every subagent runs in its own Orca worktree. The orchestrator's main clone is read-only for git mutations except during stack assembly (Step 8a) and branch preparation (Step 3).
- **Never force-push without `--force-with-lease`.** Always use `git push --force-with-lease`, never `git push --force`. `gt submit` handles this internally. In plain-git mode the orchestrator uses `git push --force-with-lease origin <branch>` unconditionally — the lease is a no-op for newly-created branches (no upstream to lease against), but protects the resume case, the rare concurrent-push case, and the re-resolved-conflict case.
- **Orchestrator owns all git, Orca worktree, and stack-tooling operations, including merge conflict resolution.** Subagents implement code and commit in Orca worktrees. They never create branches, push, interact with Orca worktree lifecycle, or use Graphite or `gh`. The orchestrator resolves merge conflicts directly during branch preparation (Step 3) and stack assembly (Step 8a) using `read_file` and `write` — this is the sole exception to the "no source file modification" rule.
- **Sequential stack assembly operations.** All branch-mutating and remote-mutating operations during Step 8 (Graphite: `gt create`, `gt submit`; plain-git: `git checkout -B`, `git cherry-pick`, `git push --force-with-lease origin`, `gh pr create`) run sequentially. Never run them concurrently — ordering is load-bearing for stack consistency.
- **Follow the Orca Worktree Protocol exactly.** It is the only contract for moving commits and refs between a subagent's Orca worktree and the orchestrator's main repo:
  - Step 4a creates the Orca worktree with `orca-ide worktree create --base-branch <pr.branch>` and records `pr.orca_worktree_id` and `pr.worktree_path`.
  - Step 4b/5c fetch with `git fetch <pr.worktree_path> HEAD --no-tags` — no destination refspec, no `--force`.
  - Step 3, 4b, 5c, 8a all treat `pr.commit_sha` (not `refs/heads/<pr.branch>`) as the authoritative reference for a PR's changes.
  - Step 8a tears down each PR's Orca worktree with `orca-ide worktree rm --worktree <pr.orca_worktree_id> --force --json` immediately before manipulating that PR's branch ref.

  See the *Orca Worktree Protocol* section near the top of this document for the full rules. There is no git lock contention between Orca worktrees (they share the main clone's object store). Subagent prompts instruct retry on git lock errors as a general safety measure, but contention is not expected.
- **All fix work happens in Orca worktrees, never in the main workspace.** The orchestrator's main clone working tree must not be modified by subagents.
- **Use `orca-ide worktree rm --worktree <id> --force --json` for subagent Orca worktrees** (created by Step 4a via `orca worktree create`). This retires the worktree through Orca's registry and avoids orphans. **Use `git worktree remove` for temporary merge worktrees** created directly by the orchestrator in Step 3 (diamond dependency handling) — these are raw git worktrees under a `mktemp` directory and are not Orca-managed.
- **Persist state after every status transition.** If the session crashes, the state file enables resumption. The `orca_worktree_id` field is critical for safe resumption — a crash between `orca worktree create` and the state-file write leaves an orphaned worktree that Step 7 will clean up via the `worktree_cleaned` flag.
- **Never merge PRs.** The skill creates and submits PRs. Merging is a human decision.
- **Explicit composition with `/pr-babysit` (Graphite mode only).** After stack submission, the user runs `/pr-babysit add <bottom-pr-number>` separately. The skill does not auto-chain. In plain-git mode, `/pr-babysit` is not suggested because it depends on `gt` for stack walking (it invokes `gt checkout`, `gt bottom`, `gt up`, `gt sync`).

