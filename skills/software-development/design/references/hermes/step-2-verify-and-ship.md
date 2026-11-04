# Step 2: Verify & Validate the Hand-off

Hermes owns the verification. Read Grok's artifacts, confirm the review loop actually closed, and validate the PR plan so `/execute-plan` can safely consume it.

## 2a: Read the Artifacts

Read all three files from the scratch dir:

- `design-doc-<DESIGN_ID>.md`
- `design-summary-<DESIGN_ID>.md`
- `design-review-<DESIGN_ID>.md`

Cross-check:

- **0 open issues**: the final `review_file` must show no issue with `Status: open`. Any `needs-user-input` status is an open decision — surface it to the user and stop (do not proceed to the hand-off validation until the user decides; Grok will re-run the loop on a fresh drop if the user wants it closed).
- **wontfix discipline**: any `wontfix` status should carry a substantive technical explanation in the review file — not a bare "won't fix". If one is bare, flag it.
- **Scope held**: the design doc and summary must not contain implementation code, source-file edits, branches, commits, or PR links — the design-only boundary (Grok lane step 0 / Global rules). Any source-tree drift in the worktree (`git -C <worktree_path> status --short` should be clean or scratch-dir-only) means the boundary was violated; report it.

## 2b: Validate the PR Plan

This is the hand-off gate for `/execute-plan`. Extract the `## PR Plan` section from the design doc and run it through the plan validator the `execute-plan` skill uses:

```
python3 <execute-plan skill dir>/scripts/validate-plan.py <path to a file containing the PR Plan section>
```

(If the design doc is the whole file, point the validator at it directly — the validator reads the `## PR Plan` section from the file.)

- Exit `0`: `linearized_order`, `level_assignments`, `pr_count`, and `max_parallelism` are authoritative. Record them — they are the hand-off facts for the user.
- Exit `1` / `2`: the plan is malformed or the section is missing. Report the first error and stop — do not hand-edit the PR plan to make it parse. The design is not execute-plan-ready; tell the user to re-run `/design` with the validator's error in context, or to fix the plan by hand and re-invoke.

## 2c: Report

Report to the user:

> Design verified. 0 open issues (or: <K> need your input — listed). PR plan: <N> PRs, <L> levels, max parallelism <P>. Design doc: <abs path>. Ready for /execute-plan <abs path>.

Then proceed to Step 3.
