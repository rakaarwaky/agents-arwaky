# Step 5: Dry-run & default execution

Present the planned prune; only `--dry-run` gates the run.

**Goal:** present the planned prune report, then proceed automatically unless the run is `--dry-run`.

## Mode behavior

Generate the planned prune report in the shape `step-8-verify-report.md` defines and present it.

- **Default (no `--dry-run`)**: fully autonomous — do not ask for confirmation. Proceed straight to Step 6.
- **`--dry-run`**: report only — stop after the report. No snapshot, no execute, no changes to the tree.

## Completion

- The prune report is presented in the Step 8 shape.
- `--dry-run` runs stop here, with no snapshot or execute.
- Default runs continue to Step 6 without waiting for user approval.
