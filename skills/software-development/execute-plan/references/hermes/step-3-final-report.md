# Step 3: Memory Flush (if applicable) & Final Report

If Grok's per-PR reviews or final review surfaced new issue patterns (visible in any `exec-review-<PLAN_ID>-*.md`), flush them to the workspace memory file the same way `grok/step-12-memory-flush.md` describes — run the memory helper from the main clone (the workspace id is derived from the main clone's remote URL, not the worktree's):

```
"${PYTHON}" "<memory_helper_path>" update --file <spec-json>
```

Build the JSON spec from the issues Grok raised across all PRs. Generalize patterns before writing (same rules as `grok/step-12-memory-flush.md`). If the helper fails, log a warning and continue — never fail the run over memory.

## Final Report

Report to the user:

1. **Summary** — total PRs implemented, files changed (from `exec-summary-*.md` files).
2. **Execution stats** — PRs completed / failed / skipped, DAG levels, max parallelism (from the state file).
3. **Review stats** — total rounds, issues fixed by severity and specialist (from the state file).
4. **Final PR** — URL or compare URL; note modular branches were merged and deleted locally; list `deferred_issues` with reasons.
5. **Post-merge action** — `"$ORCA" worktree rm --worktree <final_orca_worktree_id> --force --json`.
6. **Failed PRs** — any failed/skipped PRs; suggest `/execute-plan --resume <PLAN_ID>`.
7. **Memory update** — patterns written to workspace memory (path + count), or "no new patterns".

Report: "Cleanup complete."
