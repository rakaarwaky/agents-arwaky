# Step 3: Final Report

Report to the user:

1. **Target** — `<target>` (`<type>`), scope used.
2. **Issues** — total by severity; the triage summary from Step 2 (top issues, patterns, unverified).
3. **Report location** — absolute path to `{output_dir}/report.md`.
4. **Evidence** — where screenshots/transcripts/logs live under `{output_dir}/`.
5. **Worktree** — if a worktree was used, it is left in place. Post-action (after the QA issues are actioned):

   ```
   "$ORCA" worktree rm --worktree <worktree_id> --force --json
   ```

   (Headless run: no worktree.)

Report: "Dogfood complete."
