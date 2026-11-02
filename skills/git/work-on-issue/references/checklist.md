# Completion checklist

- [ ] Every candidate issue verified against HEAD, or closed with evidence comment.
- [ ] All non-code decisions answered in one quiz (or none needed).
- [ ] One Orca worktree per issue (`worktree create --no-parent`, json id captured).
- [ ] Each child used isolated build artifacts; no shared-target fallback.
- [ ] Each child's commits and verification re-checked in that worktree path.
- [ ] User report cites files, mechanism, and real command output — not child self-reports.
- [ ] Finished worktrees marked `--workspace-status in-review` (or retired when done).
- [ ] If PRs merged mid-batch: remaining branches rebased onto current default tip.
