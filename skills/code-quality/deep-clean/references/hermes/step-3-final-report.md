# Step 3: Final Report

Report to the user:

1. **Summary** — what was cleaned over `<path>`: items removed, files merged, structural changes (from Grok's report).
2. **Verification** — which gates you re-ran on the clean committed tree and their results.
3. **Bugs found** — each bug in the "Bugs found" section, prominently, with file:line.
4. **RISKY items** — each deferred item with its risk description and test-coverage status, for the user to decide.
5. **Commit / PR** — commit SHA (or "dry-run — no commit"), PR URL if shipped.
6. **Worktree** — left in place. Post-merge/acceptance action:

   ```
   "$ORCA" worktree rm --worktree <worktree_id> --force --json
   ```

Report: "Cleanup complete."
