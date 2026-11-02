# Step 8 — Run waves and verify children

Wave N+1 spawns after wave N's results arrive. Stacking all waves at once multiplies isolation contention.

A child's summary is a self-report, not evidence. For each finished child, inside **its** worktree:

1. `git log --oneline <default>..HEAD` and `git status` — clean tree, expected commits only.
2. Read the changed code at the cited file:line.
3. Re-run the key test yourself when the claim is load-bearing (e.g. "already fixed on main").
4. Only then report what landed to the user.
5. **Orchestrator opens PRs**: after a wave verifies, the orchestrator pushes each worktree branch and opens one PR per issue to main (draft by default). `Closes #N` is added to the issue only after the PR merges — the skill never merges.
6. Mark the Orca worktree: `ORCA worktree set --worktree path:<WT> --workspace-status in-review --json`.

Scan a worktree by `cd`ing into Orca's checkout path (`ORCA worktree show --worktree id:<repoId>::<path> --json` → path). Running checkers against a worktree path from the repo root often produces phantom violations from broken relative paths.

## Completion checklist

Before reporting the batch, confirm every box:

- [ ] Every candidate issue verified against HEAD, or closed with evidence comment.
- [ ] All non-code decisions answered in one quiz (or none needed).
- [ ] One Orca worktree per issue (`worktree create --no-parent`, json id captured).
- [ ] Each child used isolated build artifacts; no shared-target fallback.
- [ ] Each child's commits and verification re-checked in that worktree path.
- [ ] Orchestrator pushed each worktree branch and opened one PR per issue to main (draft by default).
- [ ] `Closes #N` added to each issue only after its PR merges (the skill does not merge).
- [ ] User report cites files, mechanism, and real command output — not child self-reports.
- [ ] Finished worktrees marked `--workspace-status in-review` (or retired when done).
- [ ] If PRs merged mid-batch: remaining branches rebased onto current default tip (see Step 9).
