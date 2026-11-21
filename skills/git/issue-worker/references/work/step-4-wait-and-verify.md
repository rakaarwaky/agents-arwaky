# Step 4: Monitor & Verify Implementations

Actively monitor running Grok `/implement` sessions until completion and independently verify all code changes, test suites, and reproduction commands within each worktree.

## 4a: Active Monitoring & Wait Loop

Do not yield conversation turns passively while child sessions are executing. Poll terminal status actively:

1. **Poll Terminal Idle State**:
   ```bash
   "$ORCA" terminal wait --terminal "$TERMINAL_HANDLE" --for tui-idle --timeout-ms 60000 --json
   ```
   If `satisfied: false`, re-run the wait loop until idle.

2. **Read Session Output**:
   Read terminal buffer pages using cursor paging:
   ```bash
   "$ORCA" terminal read --terminal "$TERMINAL_HANDLE" --cursor "$CURSOR" --limit 1000 --json
   ```
   Check if the child Grok session has exited or announced completion of the `/implement` task.

## 4b: Independent Verification inside Worktree

A child agent's closing summary is a self-report, not verified truth. The orchestrator must independently verify every claim directly inside the worktree path `$WT_PATH`:

1. **Clean Worktree & Commit Log**:
   ```bash
   git -C "$WT_PATH" status --short
   git -C "$WT_PATH" log --oneline origin/main..HEAD
   ```
   Confirm all changes are committed cleanly and no untracked or scratch files remain.

2. **Inspect Changed Files & Blast Radius**:
   ```bash
   git -C "$WT_PATH" diff --stat origin/main..HEAD
   ```
   Confirm modifications are strictly confined to the in-scope paths declared in Step 2.

3. **Re-execute Symptom Reproduction Commands**:
   For every issue grouped into this worktree, execute the reproduction command formulated during Step 1:
   ```bash
   cd "$WT_PATH" && <repro-command>
   ```
   Verify that the previously failing behavior now passes with exit code 0.

4. **Run Regression & Linter Checks**:
   ```bash
   cd "$WT_PATH" && <targeted-test-command>
   ```
   Verify that new tests pass and no linter regressions were introduced.

## 4c: Handle Verification Outcomes

- **On Verification Success**:
  Mark the worktree ready for review:
  ```bash
  "$ORCA" worktree set --worktree "path:$WT_PATH" --workspace-status in-review --json
  ```
  Record the group as verified and advance it to Step 5.

- **On Verification Failure or Grok Error**:
  If the child Grok session failed or verification commands fail:
  1. Record the exact failure output and error traces.
  2. Leave all issues in this group open.
  3. Retire the failed worktree:
     ```bash
     "$ORCA" worktree rm --worktree "id:$REPO_ID::$WT_PATH" --force --json
     ```
  4. Do not perform manual code fixes in the worktree. Surface the failure in the final report.

Proceed to Step 5 (`step-5-ship-and-report.md`).
