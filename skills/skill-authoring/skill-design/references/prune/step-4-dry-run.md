---
title: Step 4 — Dry-run & approval
role: step
---

# Step 4: Dry-run & approval

Generate the planned prune report in the shape `step-7-verify-report.md` defines and present it.

- With `--dry-run`, stop after the report. No snapshot, no execute.
- With `--headless`, skip the confirmation and proceed straight to Step 5.
- With no mode flag, ask: *"Here is the planned prune. Shall I proceed with the git snapshot and execute these changes?"* and wait for confirmation before Step 5.
