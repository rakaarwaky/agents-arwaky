# Step 0: Parse the Plan, Prepare the DAG & Spawn Grok Build

Hermes never writes code. This step turns the design document into a validated DAG + a self-contained brief, then drops the whole plan into a single Grok Build Orca worktree. Grok runs the full execution loop (worktrees, implementers, review panel, fix rounds, final assembly) internally — Hermes's only job is to wait and ship.

## Parse & Validate the DAG

Run the bundled validator (same as `grok/step-3-parse-dag.md`):

```
<python> <HOST_PY_DIR>/validate-plan.py <design_doc_path>
```

- Exit `0`: parse the JSON report. `linearized_order`, `level_assignments`, `pr_count`, and `max_parallelism` are authoritative.
- Exit `1` / `2`: report the first error from `errors` and stop. Do not spawn Grok on a malformed plan.

**Only proceed to spawn if the plan is valid.** An invalid or ambiguous DAG goes back to `/design`, not into Grok.

## Plan the Task Brief

Grok has zero conversation context. Compose a brief covering:

1. **Goal** — implement the full PR Plan DAG from `<design_doc_path>`: `pr_count` PRs, `max_parallelism` wide, in `linearized_order`.
2. **DAG summary** — the validated `linearized_order` with each PR's id, slug, and dependencies. This is Grok's authoritative execution order; it must not re-derive or re-order.
3. **Per-PR instructions** — for each PR, the `description`, `files/components affected`, and `dependencies` from the plan.
4. **Constraints** — style, tests, repo conventions from AGENTS.md / CONTRIBUTING.md; out-of-scope list (any path the plan never named).
5. **Acceptance criteria** — all PRs implemented, 3-reviewer panel (general, tests, simplicity) at 0 open issues on every PR, final branch assembled with all conflicts resolved, final PR opened as a draft to `main`.
6. **Deliverable** — one final branch `execute-plan/<PLAN_ID>-final` with all PRs merged, one draft PR opened. Grok writes `exec-summary-<PLAN_ID>-<pr-id>.md` and `exec-review-<PLAN_ID>-<pr-id>.md` to its scratch dir for every PR, and `exec-plan-<PLAN_ID>.json` as the state file.

## Create the Orca Worktree

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the main clone.

```
"$ORCA" worktree create --repo path:<main_clone_path> --name <PLAN_ID> --agent grok --no-parent --surface terminal --json
```

- Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip `refs/heads/`).
- **Failure:** if create fails or no Orca CLI resolves, report the error and stop. Never fall back to the main clone.

If `--agent grok` is blocked (e.g. `agent_session_operation_unknown`), fall back to a plain `git worktree add` at `~/orca/workspaces/<repo-basename>/<PLAN_ID>` and drive Grok by running the `grok` CLI in that directory instead of Orca's terminal surface.

## Drop the Task

Send exactly this, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/execute-plan <design_doc_path>

<constraints, DAG summary, and acceptance criteria from the brief>
```

Confirm `accepted: true` in the response. **After this send, do not send any more text to Grok.** No status checks, no course corrections, no "is PR-3 done?".

## Report & Stop

Report to the user in one line:

> Dropped /execute-plan into Grok Build at <worktree_path> (<pr_count> PRs, max parallelism <max_parallelism>). Waiting for completion.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.
