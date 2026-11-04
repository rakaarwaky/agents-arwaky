# Step 5 — Validate issue state before deciding

Before any implementation, confirm the issue is real, current, and not already resolved. This is the gate that separates stale/fake issues from valid ones.

## Validate the issue

1. **Read the live issue state.**
   ```bash
   gh issue view N --json number,title,state,closed,body,labels,updatedAt
   ```
   If `state` is `CLOSED`, stop — do not reopen without user confirmation.

2. **Check for a duplicate or superseding issue.** Search open issues for the same root cause:
   ```bash
   gh issue list --state open --search "<key phrase from issue>" --json number,title,state
   ```
   If an earlier open issue covers the same bug, mark this one as a duplicate and close it with an evidence comment referencing the earlier issue number.

3. **Verify the claimed bad pattern still exists at HEAD.** Grep the exact file:line the issue cites:
   ```bash
   rg -n '<exact symbol or line from issue>' <path from issue>
   ```
   - Pattern still present → issue is valid, keep open, proceed to decision quiz (step 6).
   - Pattern gone / code already correct → issue may be stale or already fixed.

4. **Check whether a fix already landed in an unrelated PR.**
   ```bash
   git log --oneline --since <issue-created-at> -- <path from issue>
   gh pr list --state merged --json number,body --jq '.[] | select(.body|test("Closes #N|Fixes #N|Resolves #N")) | .number'
   ```
   If a merged PR's body closes this issue but the issue is still open, the closer did not fire. Verify the fix by code inspection, then close manually with an evidence comment (see step 4).

## Verdict

| Finding | Action |
| --- | --- |
| Bad pattern still present at HEAD | Keep open → decision quiz (step 6) |
| Already fixed / pattern gone | Close with evidence comment |
| Duplicate of an earlier open issue | Close referencing the earlier issue |
| Issue state already CLOSED | Stop; do not reopen without user confirmation |

Never close on a `status: done` label, an audit date, or a bare `Closes #N` line alone — verify against the tree first, then close with an evidence comment (file:line or command output).
