# Step 0: Plan the Task & Spawn Grok Build

Hermes never writes the design document. This run has exactly one subagent — the Grok Build TUI in a dedicated Orca worktree. Plan the brief, create the worktree, drop the task, stop.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — produce a polished design document + PR plan from `<description>`: run the write → review → revise loop until the reviewer approves with 0 open issues, then summarize.
2. **Description** — `<description>` verbatim, plus any file paths, links, constraints, or extra context the user provided. All of it goes into the brief — the writer's prompt (Grok's Step 1) must include everything.
3. **Constraints** — design-only: deliverables are `design_doc_file` and `summary_file` only; no feature implementation, no source/test edits, no branches/commits/worktrees, no PRs. Implementation is a separate `/execute-plan` run, not part of this one.
4. **Review panel** — `design-doc-reviewer` persona; issues carry `Severity` (`bug`/`suggestion`/`nit`), `Section`, `Description`, `Suggestion`, `Status` (`open` → `addressed`/`wontfix`/`needs-user-input`).
5. **Acceptance criteria** — `design_doc_file` and `summary_file` exist in the scratch dir; the final `review_file` shows 0 open issues; the `## PR Plan` section of the design doc is present and well-formed (validate-plan-parseable — this is the hand-off gate for `/execute-plan`).
6. **Deliverable** — the two files in the scratch dir. Do NOT commit them into the repo, do NOT push, do NOT open a PR.

## Create the Orca Worktree

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo (same resolution as the other lanes: `git -C <parent-dir> rev-parse --show-toplevel` on a path named in the brief, else the current workspace cwd; tie-break preferring the standalone clone).

```
"$ORCA" worktree create --repo path:<repo_path> --name design-<task-slug> --agent grok --no-parent --surface terminal --json
```

- `task-slug`: lowercase `[a-z0-9-]` slug of `<description>`, ≤ 40 chars.
- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked, fall back to plain `git worktree add` at `~/orca/workspaces/<repo-basename>/design-<task-slug>` and drive Grok by running the `grok` CLI in that directory.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/design <description>

<constraints and acceptance criteria from the brief>
```

Confirm `accepted: true`. **After this send, do not send any more text to Grok.** A `needs-user-input` status the reviewer sets is Grok's to surface in its final report — you do not ping it mid-loop.

## Report & Stop

> Dropped /design into Grok Build at <worktree_path> (task: <description>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
