# Step 0: Plan the Task & Spawn Grok Build

Hermes never writes review files. This run has exactly one subagent — the Grok Build TUI in a dedicated Orca worktree. Plan the brief, create the worktree, drop the task, stop.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — review module `<path>` in place, no diff: spawn the selected persona roster in parallel, each reads the module's tracked files and writes a per-persona review file to the scratch dir; aggregate issue counts into a summary file.
2. **Persona roster** — the selected personas (all 10 for the bare form / `--all`, or exactly the flagged ones). State the list explicitly so Grok does not guess.
3. **Module scope** — one module = one directory; subdirectories in scope, paths outside out of scope. Read-only git (no `checkout`/`switch`/`reset`/`stash`/`fetch`); write only per-persona review files under the scratch dir.
4. **Constraints** — every reviewer subagent writes only its own per-persona review file; no source-file modification; no cleanup of other paths; a failed/timed-out persona records `ERROR` and the run continues.
5. **Acceptance criteria** — one per-persona review file per selected persona in the scratch dir (`grok-review-<REVIEW_ID>-<persona>.md`), each with the Summary + Issues structure; a summary file with aggregate counts by severity and persona.
6. **Deliverable** — the per-persona files + summary file in the scratch dir. Do NOT modify source files, do NOT commit, do NOT push, do NOT open a PR.

## Create the Orca Worktree

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo (`git -C <parent-dir> rev-parse --show-toplevel` on a path inside `<path>`; tie-break preferring the standalone clone).

```
"$ORCA" worktree create --repo path:<repo_path> --name review-<path-slug> --agent grok --no-parent --surface terminal --json
```

- `path-slug`: lowercase `[a-z0-9-]` slug of `<path>`, ≤ 40 chars.
- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked, fall back to plain `git worktree add` at `~/orca/workspaces/<repo-basename>/review-<path-slug>` and drive Grok by running the `grok` CLI in that directory.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/review <path> <persona flags, or --all>

<constraints and acceptance criteria from the brief>
```

Confirm `accepted: true`. **After this send, do not send any more text to Grok.**

## Report & Stop

> Dropped /review into Grok Build at <worktree_path> (module: <path>, <N> personas). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
