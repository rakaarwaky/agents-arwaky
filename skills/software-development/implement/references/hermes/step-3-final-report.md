# Step 3: Memory Flush (if applicable) & Final Report

If Grok's run produced new issue patterns (visible in `review-<run_id>.md` or in Grok's terminal output), flush them to the workspace memory file the same way `grok/step-8-memory-flush.md` describes — run the memory helper from the worktree:

```
cd <worktree_path> && "${PYTHON}" "<memory_helper_path>" update --file <spec-json>
```

Build the JSON spec from the issues Grok raised. Generalize patterns before writing (same rules as `grok/step-8-memory-flush.md`). If the helper fails, log a warning and continue — never fail the run over memory.

## Final Report

Report to the user:

1. What was implemented (from `impl-summary-<run_id>.md`).
2. Review panel outcome (issues found, all resolved).
3. PR URL and branch name.
4. Worktree path and the post-merge retirement command:

   ```
   "$ORCA" worktree rm --worktree <worktree_id> --force --json
   ```

5. Memory update status (file path, or "no new patterns").

Report: "Cleanup complete."
