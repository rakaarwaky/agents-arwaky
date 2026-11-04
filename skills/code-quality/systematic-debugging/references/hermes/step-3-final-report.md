# Step 3: Final Report

Report to the user:

1. **Issue** — the original symptom / failing command.
2. **Root cause** — the hypothesis that held, and why the others were falsified (from Grok's report).
3. **Fix** — the minimal change, and the regression test that proves it (test name + what it asserts).
4. **Verification** — which gates you re-ran on the clean committed tree and their results.
5. **Open decisions** — any red-flag stops or architecture questions Grok surfaced; each needs a user decision before it can close.
6. **Commit / PR** — commit SHA (or "uncommitted"), PR URL if shipped.
7. **Worktree** — left in place. Post-merge/acceptance action:

   ```
   "$ORCA" worktree rm --worktree <worktree_id> --force --json
   ```

Report: "Debugging run complete."
