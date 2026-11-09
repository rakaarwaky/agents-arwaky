# Step 0: Plan the Task & Spawn Grok Build

Hermes never writes review files. This run has exactly one subagent — the Grok Build TUI in a dedicated Orca worktree. Plan the brief, create the worktree, drop the task, stop.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — review the target in place. One of:
   - `commit`: spawn the auto-selected persona roster in parallel, each reads the last commit's diff and writes a per-persona review file; aggregate counts into a summary file.
   - `uncommit`: same, but the diff is the working tree vs HEAD (staged + unstaged).
   - `pr <N>`: same, but the diff comes from `gh pr diff <N>`.
   - `path <p>`: spawn personas that read the current files of `<p>` (no diff), each writes a per-persona review file; aggregate counts.
2. **Persona roster** — auto-selected by Grok from the target's content (diff summary or directory tree). State the rule explicitly: "Pick 1–3 most relevant personas from the roster; see step-0 auto-selection rules." Do not list the personas in the brief; Grok selects them.
3. **Target scope** — the specific target (commit hash, `pr <N>`, or absolute path). Read-only git (no `checkout`/`switch`/`reset`/`stash`/`fetch`); write only per-persona review files under the scratch dir.
4. **Constraints** — every reviewer subagent writes only its own per-persona review file; no source-file modification; no cleanup of other paths; a failed/timed-out persona records `ERROR` and the run continues.
5. **Acceptance criteria** — one per-persona review file per selected persona in the scratch dir (`grok-review-<REVIEW_ID>-<persona>.md`), each with the Summary + Issues structure; a summary file with aggregate counts by severity and persona.
6. **Deliverable** — the per-persona files + summary file in the scratch dir. Do NOT modify source files, do NOT commit, do NOT push, do NOT open a PR.

## Create the Orca Worktree

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo (`git -C <parent-dir> rev-parse --show-toplevel` on a path inside `<target>`; tie-break preferring the standalone clone).

```
"$ORCA" worktree create --repo path:<repo_path> --name review-<mode>-<target-slug> --agent grok --no-parent --surface terminal --json
```

- `mode`: `commit`, `uncommit`, `pr`, or `path` (from the argument).
- `target-slug`: for `path` mode, lowercase `[a-z0-9-]` slug of the path, ≤ 40 chars. For `commit` / `uncommit`, use the last 6 hex chars of `HEAD` or `worktree-<timestamp>`. For `pr`, use `pr-<number>`.
- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked, fall back to plain `git worktree add` at `~/orca/workspaces/<repo-basename>/review-<mode>-<target-slug>` and drive Grok headless **inside that worktree** via `grok -p '<brief>' --cwd <worktree_path> --always-approve`. Never run bare `grok` / `grok -p` directly in the Hermes terminal session outside a worktree context.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/review <mode> [<target>]

<constraints and acceptance criteria from the brief>
```

- `<mode>` is `commit`, `uncommit`, `pr`, or `path`.
- `<target>` is the second argument when mode is `pr` (the PR number) or `path` (the path). Omit it for `commit` and `uncommit`.

Confirm `accepted: true`. **After this send, do not send any more text to Grok.**

## Report & Stop

> Dropped /review into Grok Build at <worktree_path> (<mode>: <target>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
