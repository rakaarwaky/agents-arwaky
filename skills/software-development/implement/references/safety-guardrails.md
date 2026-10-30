# Safety Guardrails

Follow these rules strictly.

- **Never touch the default branch or the main clone's working tree.** Every subagent runs in an Orca worktree. The orchestrator runs git only through `git -C <worktree_path>` inside the worktree (none of these change the main clone's checkout).
- **Never `git reset --hard` or `git checkout` in the main clone.** Those commands discard the user's local work.
- **Never force-push without a lease.** Always `git push --force-with-lease`, never `git push --force`. The lease is a no-op for newly created branches but protects against concurrent pushes.
- **Orchestrator owns all git, Orca worktree, and PR operations.** Subagents edit files inside their worktree only. They never commit, create branches, push, touch the worktree lifecycle, or call `gh`.
- **Orchestrator commits.** One commit when the unit reaches 0 open issues.
- **Orchestrator resolves merge conflicts.** During Step 8 (stack assembly) only, using `read_file` and `write`. This is the sole exception to the "no source file modification" rule.
- **Assembly operations run sequentially.** `git push` and `gh pr create` never run concurrently; ordering is load-bearing.
- **Follow the worktree lifecycle exactly.** See [`worktree-isolation.md`](worktree-isolation.md).
- **Never merge PRs.** The skill creates PRs. Merging to `main` is a human decision.
