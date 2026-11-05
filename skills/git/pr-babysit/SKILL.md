---
name: pr-babysit
description: "Watch a GitHub PR end to end: Hermes (orchestrator) tracks the PR and observes CI; Grok Build (worker) runs every fix pass — auto-fix red checks, resolve conflicts, address review/bot comments — in an Orca worktree; Hermes merges when green if --ship is set. Two roles: Hermes orchestrates and ships; Grok fixes. Read the lane matching the invoking agent, never self-identify as a role that is not you."
when-to-use: "Triggers on \"/pr-babysit\". Phrasing: \"watch PR 123 until green\", \"babysit PR 123 and merge when ready\", \"fix issue #123 and open a PR\", \"keep fixing PR 123 until it can merge\", \"pr-babysit add --ship 123\"."
argument-hint: "add [--ship] <number> | check <number> | ship on <number>"
disable-model-invocation: true
---

# PR Babysitter

Watch a standalone GitHub PR end to end: register it, keep it green, merge it when `--ship` is active. The pipeline is event-driven — CI re-runs and new review threads each trigger a fresh pass.

**All code changes are delegated to Grok Build.** Hermes owns watchlist state, CI observation, and the merge (the human-gated action); Grok owns every fix pass — red checks, conflicts, review threads — run inside an Orca worktree with `--agent grok`. Stacked PRs (Graphite / `gh stack`) stop at "tell the user the stack tool owns those."

## Global Rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build via Orca worktree)**: You never fix code, resolve conflicts, or reply to review threads yourself. Each fix pass is one Orca worktree with `--agent grok` on the PR's head branch; Grok Build runs the auto-fix loop inside it. No `spawn_subagent` — your only "subagent" is the Grok Build TUI.
- **Event-driven re-drops**: this skill is not a single long wait — it is a sequence of passes. Each event (CI goes red, a new review thread lands, a check flips) is a fresh Hermes invocation: observe the event, spawn a Grok worktree for that pass, wait, re-verify, update the watchlist. The per-session state file (`watched-prs-<INSTANCE_ID>.json`) carries `fix_count` and `last_status` across passes.
- **One fix pass = one worktree = one task drop.** Compose a self-contained brief (failing checks + log excerpts, open threads, `fix_count`) and drop it once. No mid-run course corrections, no status pings to Grok.
- **Never force-push without `--force-with-lease`** — binds every Grok fix pass (stated in the brief) and every Hermes operation.
- **Never skip a review thread** — human or bot. Every unresolved thread is part of the fix-pass acceptance criteria; a green CI with open threads is not green.
- **Merge only in Step 2**, only when `ship` is `true` and the ship-ready gates pass on a live re-query. No auto-merge on a PR whose base is not the repo default branch. Merging is Hermes's — Grok never merges.
- **CI verification is Hermes's.** Grok's "fixed it" claim is self-reported; Step 1 re-runs the CI check for the live head SHA before trusting it.
- **State is per-session**: `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`. `INSTANCE_ID` is a UUID generated on first `add` (resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`, run `<python> <HOST_PY> uuid --full`, reject WindowsApps stubs).

## Routing

Each reference file is step-scoped. Global rules above apply throughout; do not restate them in a step file.

The lane is chosen by **who is invoking this skill**, and is settled by a hard rule at load time — the invoking agent must read only one lane, never both, and must never self-identify as the other:

1. **If you are the Grok Build TUI (you are running inside an Orca worktree, you have the `/pr-babysit` command in your prompt, and a brief from the orchestrator), you are the worker.** Run Steps 0–4 in `references/grok/`. Do not read `references/hermes/`. Do not spawn Orca worktrees, drop briefs, or manage watchlist state — you are that worktree, not the one that spawned it.
2. **If you are the orchestrator invoking `/pr-babysit add|check|ship` from outside a worktree, you are the Hermes lane owner.** Run Steps 0–3 in `references/hermes/`. Do not read `references/grok/`. Do not run the auto-fix loop yourself; that belongs to the Grok worktree you spawn.

**Disambiguation test** (run this first, before reading any step file):
- Are you running inside an Orca worktree that was created with `orca worktree create --agent grok --name pr-babysit-<number>`? → **Grok lane.**
- Are you running in the main clone or in a separate orchestrator TUI, and did the user type `/pr-babysit add|check|ship`? → **Hermes lane.**
- You cannot be both in one process. If you are unsure, re-run the test: an Orca worktree path in your CWD means Grok lane; a main clone CWD means Hermes lane.

### Hermes lane (Steps 0–3)

| Step | Reference                                                                      | Purpose                                                                                                   |
| ----: | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 0    | [`references/hermes/step-0-watch-and-spawn.md`](references/hermes/step-0-watch-and-spawn.md) | Verify auth, fetch PR, register in the watchlist, check CI once; if red or open threads, spawn a Grok worktree on the head branch and drop the fix brief |
| 1    | [`references/hermes/step-1-wait-and-reverify.md`](references/hermes/step-1-wait-and-reverify.md) | Wait for the fix pass; re-run the CI check on the live head SHA; update `last_status`                     |
| 2    | [`references/hermes/step-2-merge.md`](references/hermes/step-2-merge.md)     | Merge (only when `ship` is `true` and the ship-ready gates pass on a live re-query); retire the worktree |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (fix passes, outcome, open items, watchlist state)                              |

### Grok lane (Steps 0–4, run by Grok Build per fix pass)

| Step | Reference | When it runs |
|------|-----------|--------------|
| 0 — PR context | [`references/grok/step-0-add-pr.md`](references/grok/step-0-add-pr.md) | PR details, repo, head/base refs for the pass |
| 1 — Watch CI | [`references/grok/step-1-watch-ci.md`](references/grok/step-1-watch-ci.md) | Always, at the start of the pass |
| 2 — Auto-fix red checks | [`references/grok/step-2-auto-fix.md`](references/grok/step-2-auto-fix.md) | CI reports a red check; loops back to step 1 after each push. Commit title grammar: Conventional Commits inline |
| 3 — Decision tree | [`references/grok/step-3-decision-tree.md`](references/grok/step-3-decision-tree.md) | After each step 2 push and always before declaring the PR green; CI logs ambiguous → [`references/grok/step-3-troubleshoot.md`](references/grok/step-3-troubleshoot.md) |
| 4 — Merge readiness | [`references/grok/step-4-merge.md`](references/grok/step-4-merge.md) | Ship-ready gate checks; Grok reports merge-ready (Hermes performs the merge) |
