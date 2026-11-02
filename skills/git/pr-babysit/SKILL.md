---
name: pr-babysit
description: Complete GitHub PR skill — create, monitor CI, auto-fix red checks, address review comments, resolve merge conflicts, merge/squash, ship. Watchlist mode monitors many PRs in parallel.
when-to-use: Triggers on "/pr-babysit". Create-a-PR phrasing: "pr to main", "open a PR", "merge PR when green", "take this branch to a merged PR", "fix issue #123 and open a PR". Babysit phrasing: "check every open PR", "fix PR 162", "merger to main" (land ready PRs when green).
argument-hint: "add [--ship] <number> | remove <number> | list | check | ship [on|off] [number...]"
disable-model-invocation: true
---

# PR Workflow & Babysitter

One skill for the whole GitHub PR lifecycle. The create path opens a PR from a worktree or branch — branch, conventional commit, push, create — and shepherds CI to green via an auto-fix loop. The babysit path monitors many open PRs in parallel, fixes failures in isolated worktrees, and lands ready PRs when shipping is enabled.

## Global Rules

Rules that apply to both create and babysit modes. Reference files cite these; they never restate them.

- **Fixes in subagents only**: Fixes and commits happen in subagents (spawned via `spawn_subagent`) with worktree isolation — never as direct orchestrator edits on the main workspace.
- **Three PR topologies**: Independent PRs (standalone, target default branch), Graphite stacks (managed by `gt`), GitHub stacked PRs (managed by `gh stack`).
- **Ship is explicit**: `ship` is off by default; enable with `ship on|off [number...]`. When `ship` is true, PRs land when green.
- **Worktree isolation**: Orca worktrees are the isolation boundary; each child works only inside its assigned worktree.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Mode selection | [`references/mode-selection.md`](references/mode-selection.md) | Dispatch by first argument: `add`/`remove`/`list`/`check`/`ship` babysitter, `--squash`/`--auto` merge modifier, or bare intent phrase → create-PR flow. |
| Create-PR flow | [`references/create-pr-flow.md`](references/create-pr-flow.md) | One-shot create-PR flow: source the `gh-env.sh` helper, then branch, conventional commit, push, open the PR; route to CI monitor/auto-fix/merge recipes as needed. |
| Commit/PR title grammar | [`references/conventional-commits.md`](references/conventional-commits.md) | Conventional Commits title format. |
| Watch CI | [`references/ci-monitoring.md`](references/ci-monitoring.md) | Watch CI until green. |
| Auto-fix red check | [`references/ci-auto-fix.md`](references/ci-auto-fix.md) | Auto-fix a red check, push, re-verify. |
| CI troubleshooting | [`references/ci-troubleshooting.md`](references/ci-troubleshooting.md) | Red log ambiguous — flake vs real failure. |
| Merging | [`references/merging.md`](references/merging.md) | Squash/rebase/merge, auto-merge, branch cleanup. |
| Issue to PR | [`references/issue-to-pr.md`](references/issue-to-pr.md) | End-to-end "Fix issue #123" with premise validation, regression test, class-level fix. |
| PR body skeletons | [`references/pr-body-feature.md`](references/pr-body-feature.md), [`references/pr-body-bugfix.md`](references/pr-body-bugfix.md) | Body skeletons for `gh pr create --body-file`. |
| Watchlist mode | [`references/watchlist.md`](references/watchlist.md) | PR babysitter orchestrator: todo scaffold, commands, state file, check cycle, shipping, and Hermes variant. |
