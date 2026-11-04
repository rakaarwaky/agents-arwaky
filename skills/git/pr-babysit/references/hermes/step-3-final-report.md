# Step 3: Final Report

Report to the user:

1. **PR** — `<number>` (`<title>`), repo.
2. **Fix passes** — total `fix_count`, which checks were fixed in each pass (commit SHAs), which threads were addressed.
3. **Outcome**:
   - `ship: true` → "Merged to `<base_ref>` (<squash|auto>), branch deleted."
   - `ship: false` → "Green and ready to merge. Run `/pr-babysit ship on <number>` when you want it landed."
4. **Open items** — any unfixed failures or unresolved threads from the last pass, with a one-line reason each.
5. **Worktree** — retired (Step 2) or left in place if the run stopped red (post-action: `"$ORCA" worktree rm --worktree <worktree_id> --force --json`).
6. **Watchlist** — the PR entry's final state (`last_status`, removed-if-merged). Suggest re-check cadence or a re-invocation trigger (e.g. "re-run on the next CI failure or new review thread").

Report: "PR babysit complete."
