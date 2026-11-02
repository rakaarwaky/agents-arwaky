# PR Babysitter — single-PR pipeline driver

One sequential pipeline: watch a PR, fix it until green, merge when `--ship` is active. Standalone PRs only — if the PR is part of a Graphite or `gh stack` chain, stop and tell the user the stack tool owns those.

## Inputs

- `/pr-babysit add [--ship] <number>` — an existing PR to babysit.
- "fix issue #123 and open a PR" — no PR yet; create one first.

## Pipeline

| Step | Reference | Runs when |
|------|-----------|-----------|
| 0 — Add to watchlist | [step-0-add-pr.md](step-0-add-pr.md) | PR number supplied; persists state, sets `ship` flag |
| 1 — Commit/title grammar | [step-1-commit-title.md](step-1-commit-title.md) | A fix commit is authored in step 4, or a PR is opened in step 2 |
| 2 — Create PR | [step-2-create-pr.md](step-2-create-pr.md) | No PR exists yet; skeleton bodies in [step-2-pr-body-feature.md](step-2-pr-body-feature.md) / [step-2-pr-body-bugfix.md](step-2-pr-body-bugfix.md) |
| 3 — Watch CI | [step-3-watch-ci.md](step-3-watch-ci.md) | Always, after the PR exists; polls until a terminal check state |
| 4 — Auto-fix red checks | [step-4-auto-fix.md](step-4-auto-fix.md) | CI reports a red check; fix + push, loop back to step 3 |
| 5 — Decision tree | [step-5-decision-tree.md](step-5-decision-tree.md) | After each step 4 push, and always before step 6; handles conflicts, review threads, bot findings, worktree recovery; [step-5-troubleshoot.md](step-5-troubleshoot.md) for ambiguous CI logs |
| 6 — Merge | [step-6-merge.md](step-6-merge.md) | `ship` is `true` and step 5 reports `healthy` |

## State

Per-session: `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`. `INSTANCE_ID` is a UUID generated on first `add` (resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`, run `<python> <HOST_PY> uuid --full`, reject WindowsApps stubs) and held in conversation context. Schema: see step 0.

## Safety guardrails

- Never force-push without `--force-with-lease`.
- Fix work happens in a worktree (created via `spawn_subagent` `isolation: "worktree"` when a subagent owns the pass, or an Orca worktree for direct runs); the main workspace tree is never modified.
- Never skip or ignore a review thread — human or bot. Every unresolved thread is evaluated.
- Never reply with "will fix" / "acknowledged" / "good point". Reply with a fix SHA or a substantive technical explanation.
- Merge only in step 6, only when `ship` is `true` and every gate in step 5 / step 6 passes. No auto-merge on a PR whose base is not the repo default branch.
