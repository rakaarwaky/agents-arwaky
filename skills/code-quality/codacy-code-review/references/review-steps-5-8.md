# Review Workflow — Steps 5–8

This file contains Steps 5–8 of the Codacy PR review workflow (after the local analysis in Steps 1–4 and Cloud data fetch in Step 3).

## Step 5: Check coverage

Coverage data comes from the Cloud CLI (Step 3). Review:
- Overall coverage delta (did it go up or down?)
- Files with uncovered lines introduced by the PR
- Use `--diff` output to see which specific lines lack coverage (✘ markers)

Flag files with new uncovered lines as needing tests.

## Step 6: Verify alignment

**With the ticket/issue:** Check that the code changes address the stated requirements. Note any functionality described in the ticket that is not present in the changes. Note any changes that go beyond the scope of the ticket.

**With the PR description:** Verify the description accurately reflects what was changed. Note discrepancies.

If the ticket or PR description is missing, incomplete, or inaccurate, note specific improvements to suggest.

## Step 7: Propose test plan

Based on the changed code and coverage data:
1. List the scenarios that should be tested (happy path, edge cases, error cases)
2. For each scenario, check whether a test already exists in the PR diff
3. Flag scenarios with no corresponding test and no coverage in Codacy

## Step 8: Summary

Present a structured review summary:

```
## Codacy Review Summary

### Quality gate
[Pass / Fail — from Codacy PR analysis]

### Issues introduced
[List issues by severity, or "None — see Analysis coverage"]

### Analysis coverage
[Tools that ran; any skipped (with reason) or cloud-only]

### Coverage
[Delta, uncovered lines in new code]

### Alignment
- Ticket: [aligned / gaps noted]
- PR description: [accurate / suggestions]

### Test plan
[Proposed scenarios and whether tests exist]

### Suggested improvements
- PR description: [if applicable]
- Ticket/issue: [if applicable]
```
