# Step 3: Final Report

Report to the user (completion checklist per `grok/step-9-waves-verify.md`):

1. **Issues processed** — total, with verdict breakdown: `fixed-on-main` (closed with evidence), `still-broken` (Grok pass spawned), `needs-decision` (quiz answers applied).
2. **Verification evidence** — per issue: files, mechanism, and the real command output you re-ran (not child self-reports).
3. **PRs** — one draft PR per fixed issue: branch, URL, base. `Closes #N` lands only on merge.
4. **Closed issues** — each with its evidence comment (file:line / command output).
5. **Failed / open items** — any Grok pass that failed or was not spawned; each stays open with a one-line reason. Suggest a re-drop for the next wave.
6. **Worktrees** — verified ones marked `in-review`; post-PR-merge action per worktree:

   ```
   ORCA worktree rm --worktree id:<repoId>::<worktree_path> --force --json
   ```

   (CWD-drop noise expected — commit stays on the branch, `git show --stat` is the verified handle.)

7. **Rebase status** — if any PR merged mid-batch, confirm remaining branches were rebased onto the current default tip.

Report: "Issue worker complete."
