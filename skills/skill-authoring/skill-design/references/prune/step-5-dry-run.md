# Step 4: Dry-run & approval

Present the planned prune and get the go-ahead before touching the tree.

**Goal:** present the planned prune report and proceed only when the mode flag or the user allows it.

## Mode behavior

Generate the planned prune report in the shape `step-7-verify-report.md` defines and present it.

- With `--dry-run`, stop after the report. No snapshot, no execute.
- With `--headless`, skip the confirmation and proceed straight to Step 5.
- With no mode flag, ask: *"Here is the planned prune. Shall I proceed with the git snapshot and execute these changes?"* and wait for confirmation before Step 5.

## Completion

- The prune report is presented in the Step 7 shape.
- `--dry-run` runs stop here, with no snapshot or execute.
- Interactive runs stop at the user's confirmation; `--headless` continues to Step 5 without asking.
