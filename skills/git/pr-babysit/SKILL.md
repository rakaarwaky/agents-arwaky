---
name: pr-babysit
description: Watch a GitHub PR end to end: track a PR number, auto-fix CI failures, resolve conflicts, address review and bot comments, and merge when green. Optional --ship flag lands the PR to the default branch when ship-ready.
when-to-use: Triggers on "/pr-babysit". Phrasing: "watch PR 123 until green", "babysit PR 123 and merge when ready", "fix issue #123 and open a PR", "keep fixing PR 123 until it can merge", "pr-babysit add --ship 123".
argument-hint: "add [--ship] <number> | check <number> | ship on <number>"
disable-model-invocation: true
---

# PR Babysitter

One sequential pipeline per PR: take a PR number, fix it until green and ready to merge, merge when `--ship` is active. Standalone PRs only — stacked PRs (Graphite / `gh stack`) stop at "tell the user the stack tool owns those."

## Global Rules

- **Fixes in a worktree**: All code changes happen in a worktree (Orca worktree for direct runs, or `spawn_subagent` `isolation: "worktree"` when a subagent owns the pass). The main workspace is never modified.
- **Never force-push without `--force-with-lease`**.
- **Never skip a review thread** — human or bot. Every unresolved thread is evaluated.
- **Never reply with "will fix", "acknowledged", or a bare acknowledgment.** Reply with a fix commit SHA or a substantive technical explanation.
- **Merge only in step 5**, only when `ship` is `true` and every gate passes. No auto-merge on a PR whose base is not the repo default branch.
- **State is per-session**: `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`. `INSTANCE_ID` is a UUID generated on first `add` (resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`, run `<python> <HOST_PY> uuid --full`, reject WindowsApps stubs) and held in conversation context.

## Routing

| Step | Reference | When it runs |
|------|-----------|--------------|
| 0 — Add to watchlist | [`references/step-0-add-pr.md`](references/step-0-add-pr.md) | `/pr-babysit add [--ship] <number>` |
| 1 — Commit/title grammar | [`references/step-1-commit-title.md`](references/step-1-commit-title.md) | Authoring a fix commit in step 3 (auto-fix) |
| 2 — Watch CI | [`references/step-2-watch-ci.md`](references/step-2-watch-ci.md) | Always, after the PR exists |
| 3 — Auto-fix red checks | [`references/step-3-auto-fix.md`](references/step-3-auto-fix.md) | CI reports a red check; loops back to step 2 after each push |
| 4 — Decision tree | [`references/step-4-decision-tree.md`](references/step-4-decision-tree.md) | After each step 3 push and always before step 5; CI logs ambiguous → [`references/step-4-troubleshoot.md`](references/step-4-troubleshoot.md) |
| 5 — Merge | [`references/step-5-merge.md`](references/step-5-merge.md) | `ship` is `true` and step 4 reports `healthy`; ship-ready gates + merge commands |
