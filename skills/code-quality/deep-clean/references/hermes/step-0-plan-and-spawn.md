# Step 0: Plan the Task & Spawn Grok Build

Hermes never writes code. This run has exactly one subagent — the Grok Build TUI in a dedicated Orca worktree. Plan the brief, create the worktree, drop the task, stop.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — run the deep-clean pipeline over `<path>`: snapshot, dead-code removal (language variant for the target language), consolidation, 4-lens sweep, structural audit, tiered application, verification gates.
2. **Language** — detect from `<path>` (Python / Rust / TypeScript) so Grok picks the right step-1x / step-2x variant.
3. **Constraints** — if `--dry-run`, tell Grok to run report-only and apply nothing. Otherwise headless autonomous: RISKY-tier and low-confidence items go to the manual-review section, not auto-applied.
4. **Acceptance criteria** — the language's verification gates pass on a clean tree; the step 7 report exists with its "Bugs found" section (possibly empty); a snapshot commit/stash exists before any deletion.
5. **Deliverable** — one commit in the worktree itemising counts removed, files merged, and structural changes applied. Do NOT push, do NOT open a PR, do NOT merge.

## Create the Orca Worktree

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo (same resolution as `grok/` references: `git -C <parent-dir> rev-parse --show-toplevel` on a candidate path inside `<path>`, tie-break preferring the standalone clone).

```
"$ORCA" worktree create --repo path:<repo_path> --name <path-slug> --agent grok --no-parent --surface terminal --json
```

- `path-slug`: lowercase `[a-z0-9-]` slug of `<path>`, ≤ 40 chars.
- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked, fall back to plain `git worktree add` at `~/orca/workspaces/<repo-basename>/<path-slug>` and drive Grok headless **inside that worktree** via `grok -p '<brief>' --cwd <worktree_path> --always-approve`. Never run bare `grok` / `grok -p` directly in the Hermes terminal session outside a worktree context.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/deep-clean <path> <if --dry-run, append: --dry-run>

<language, constraints, and acceptance criteria from the brief>
```

Confirm `accepted: true`. **After this send, do not send any more text to Grok.**

## Report & Stop

> Dropped /deep-clean into Grok Build at <worktree_path> (target: <path>, language: <lang>, mode: <headless | dry-run>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
