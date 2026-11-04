# Step 3: Final Report

Report to the user:

1. **Module** — `<path>`, selected persona roster.
2. **Issues** — total by severity; per-persona breakdown; cross-persona corroborated findings.
3. **Top issues** — the bug-severity findings from the triage, with `file:line` and the raising persona.
4. **Errored personas** — which failed and why (from Grok's summary).
5. **Deliverables** — absolute path to the summary file and the per-persona review files in the scratch dir.
6. **Worktree** — left in place. Post-action (after findings are actioned or accepted):

   ```
   "$ORCA" worktree rm --worktree <worktree_id> --force --json
   ```

Report: "Review complete."
