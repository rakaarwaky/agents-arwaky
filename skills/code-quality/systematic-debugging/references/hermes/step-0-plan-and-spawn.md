# Step 0: Plan the Task & Spawn Grok Build

Hermes never writes code. This run has exactly one subagent — the Grok Build TUI in a dedicated Orca worktree. Plan the brief, create the worktree, drop the task, stop.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — run the systematic debugging pipeline over `<issue-or-error>`: intake (symptom, target lang, repro command, affected paths) → investigate (red-capable feedback loop) → pattern analysis → ranked falsifiable hypotheses → TDD fix (RED-GREEN-REFACTOR) → verify → guardrails. No fix without root-cause investigation first; no production code without a failing test first (the iron law).
2. **Language** — `--lang` if given, else detect from the affected files (Python / TypeScript-Node / Rust) so Grok picks the matching step-3x / step-5x variant.
3. **Repro** — `--repro <command>` if given; otherwise Grok builds the tight red-capable loop in step 1.
4. **Phase** — `--phase <1|2|3|4>` if given (resume mid-run); otherwise start at phase 1.
5. **Constraints** — TDD discipline: one failing test written before the fix, one variable at a time, rule of three (3+ failures → question architecture); guardrails' red-flag list checked before declaring done.
6. **Acceptance criteria** — a failing regression test proves the fix; verification gate passes; the run state's `fix_attempts`, `hypotheses`, and `repro_command` are finalized.
7. **Deliverable** — one commit in the worktree: the regression test + the minimal fix + the refactored code. Do NOT push, do NOT open a PR, do NOT merge.

## Create the Orca Worktree

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo (same resolution as the other lanes: `git -C <parent-dir> rev-parse --show-toplevel` on a path inside `<affected_paths>` or the current workspace cwd; tie-break preferring the standalone clone).

```
"$ORCA" worktree create --repo path:<repo_path> --name debug-<issue-slug> --agent grok --no-parent --surface terminal --json
```

- `issue-slug`: lowercase `[a-z0-9-]` slug of the issue, ≤ 40 chars.
- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked, fall back to plain `git worktree add` at `~/orca/workspaces/<repo-basename>/debug-<issue-slug>` and drive Grok headless **inside that worktree** via `grok -p '<brief>' --cwd <worktree_path> --always-approve`. Never run bare `grok` / `grok -p` directly in the Hermes terminal session outside a worktree context.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/systematic-debugging <issue-or-error> [--phase <1|2|3|4>] [--lang <lang>] [--repro <command>]

<constraints and acceptance criteria from the brief>
```

Confirm `accepted: true`. **After this send, do not send any more text to Grok.** A debugging run that needs a mid-run decision (a red-flag stop, a 3-failures architecture question) is Grok's to surface in its final report — not something you ping it about.

## Report & Stop

> Dropped /systematic-debugging into Grok Build at <worktree_path> (issue: <issue-or-error>, lang: <lang>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
