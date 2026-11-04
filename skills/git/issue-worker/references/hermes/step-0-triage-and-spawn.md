# Step 0: Triage, Decide & Spawn Grok per Issue

Hermes owns issue triage and the decision quiz — that is coordination, not coding. All implementation is delegated to Grok Build, one worktree per issue. This step: verify claims at HEAD, ask every open question in one quiz, then for each issue that needs work, spawn a Grok worktree and drop a self-contained brief.

## 0a: Triage & Verify (Hermes)

For each issue number in the argument list (or the open-issue dump when auditing in bulk — recipes in `grok/step-4-verify-triage.md`):

- **Verify before deciding**: never trust a `status: done` label, an audit date, or a merged PR's `Closes #N` line alone. Grep the exact file:line the issue cites at HEAD; check `git log --oneline --since <issue-date> -- <path>` for a fix that landed in an unrelated PR.
- **Verdict per issue**: `fixed-on-main` (close with an evidence comment — Hermes does this, it's coordination), `still-broken` (needs a fix pass → spawn Grok), `needs-decision` (open question → add to the quiz).

## 0b: One Quiz for All Decisions

Collect every open question across all issues and ask them in **one** interactive quiz — one question per decision, recommended option first. Skip only when every remaining issue has a fully determined fix at HEAD. The user's answers are final and are written into every spawned brief as constraints.

## 0c: Spawn Grok per Issue

For each `still-broken` issue:

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`), get the repo id (`ORCA repo list --json`), and create the worktree (defaults from `grok/step-7-fanout.md`):

```
"$ORCA" worktree create --repo id:<repoId> --name issue-<N> --agent grok --no-parent --surface terminal --json
```

Compose the brief (Grok has zero context — children see nothing else of this conversation):

1. **Goal** — fix issue `<N>` (`<title>`); the verified evidence that it is still broken at HEAD (file:line + command output from 0a).
2. **Constraints** — the user's quiz answers that apply to this issue; work **only** inside the assigned worktree; per-worktree build artifact dir (never the repo-shared one — `grok/step-8-build-isolation.md`); targeted checks only (`<tool> check/test -p <package>`), never workspace-wide gate scripts; no local commits owned by Grok beyond the fix commit, no push, no PR, no tracker writes — the orchestrator owns push + PR.
3. **Acceptance criteria** — the issue's symptom no longer reproduces (command + expected output stated in the brief); regression test pinning the behavior exists; files changed + mechanism + verification output are in the closing report.

Drop the task, once, per worktree, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json` (wait for TUI idle first — `grok/step-7-fanout.md`):

```
/issue-worker implement <N>

<constraints and acceptance criteria from the brief>
```

Confirm `accepted: true` for each. **After the send, do not send any more text to that Grok session.** Waves: spawn at most ≤ 10 worktrees concurrently (the wave limit from `grok/step-7-fanout.md`); wave N+1 spawns after wave N's results arrive.

## Report & Stop

> Dropped N /issue-worker passes into Grok Build (issues <list>, <K> worktrees live). Waiting for completion.

Then end the turn. When the Orca terminals become idle (detected when this conversation resumes), proceed to Step 1.
