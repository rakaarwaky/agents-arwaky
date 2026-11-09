# Step 3: Final Report

Report to the user:

1. **Mode + target** — `<mode>` and `<target>` (commit hash, `pr <N>`, or path).
2. **Personas** — the 1–3 auto-selected personas that ran.
3. **Issues** — total by severity; per-persona breakdown; cross-persona corroborated findings.
4. **Top issues** — the bug-severity findings from the triage, with `file:line` and the raising persona.
5. **Errored personas** — which failed and why (from Grok's summary).
6. **Deliverables** — absolute path to the summary file and the per-persona review files in the scratch dir.
7. **Worktree** — left in place. Post-action (after findings are actioned or accepted):

   ```
   "$ORCA" worktree rm --worktree <worktree_id> --force --json
   ```

Report: "Review complete."
