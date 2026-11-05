# Step 0: Plan the Task & Spawn Grok Build in an Orca Worktree

Hermes never writes code. This entire run has exactly one subagent — the Grok Build TUI inside an Orca worktree. Hermes's job in this step: turn `<task-description>` into a self-contained brief, create the worktree with `--agent grok`, drop the brief, and stop talking to Grok.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief that covers:

1. **Goal** — the task in one or two sentences, restated plainly.
2. **Scope** — in-scope paths, and an explicit out-of-scope list (sibling trees, new top-level directories, anything the task never named). Resolve scope the same way `grok/step-0-setup.md` describes (check candidate paths on disk; if genuinely ambiguous, ask the user ONE clarifying question naming both candidates).
3. **Constraints** — style, tests to run, things not to touch, repo conventions from AGENTS.md / CONTRIBUTING.md.
4. **Acceptance criteria** — what "done" looks like: tests passing, linter clean, specific commands that must exit 0.
5. **Deliverable** — commit the work in the worktree with a conventional commit message; do NOT push, do NOT open a PR, do NOT merge.

## Create the Orca Worktree

Resolve `orca-ide` to its absolute path (`/home/raka/.local/bin/orca-ide`) and the owning repo exactly as in `grok/step-0-setup.md` (owning-repo resolution, tie-break, project-name check, reuse-or-create).

**Pitfall — Orca CLI path resolution:** Do not rely on `orca-ide` being on `$PATH` or on `$ORCA` being exported. The shell does not export `ORCA`, so `${ORCA}` expands to empty and bash reports `: command not found` instead of running the CLI. Always call the binary by its absolute path.

Create:

```
/home/raka/.local/bin/orca-ide worktree create --repo path:<repo_path> --name <task-slug> --agent grok --no-parent --surface terminal --json
```

- `task-slug`: lowercase `[a-z0-9-]` slug of the task, ≤ 40 chars.
- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked (e.g. `agent_session_operation_unknown`), fall back to plain `git worktree add` at `~/orca/workspaces/<repo-basename>/<task-slug>` and drive Grok by running the `grok` CLI in that directory instead of using Orca's terminal surface.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/implement <task-description>

<constraints & acceptance criteria from the brief>
```

`<task-description>` is the skill argument, expanded verbatim. Confirm `accepted: true` in the response. **After this send, do not send any more text to Grok.** No status checks, no course corrections, no "are you done yet".

## Report & Stop

Report to the user, in one line:

> Dropped /implement into Grok Build at <worktree_path> (branch <worktree_branch>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
