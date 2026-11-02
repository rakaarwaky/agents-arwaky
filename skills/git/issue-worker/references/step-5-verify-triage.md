# Step 5 — Load and triage

Never close or skip work from a `status: done` label, an audit date, or a merged PR's `Closes #N` line alone. GitHub can silently fail to close issues a PR body declares while the fix itself did land. Verify every claim against the current tree.

1. Dump open issues once:
   `gh issue list --state open --limit 300 --json number,title,body,labels,updatedAt --jq '.[] | "### #\(.number)\n\(.title)\n\(.body)\n"' > /tmp/issues.md`
2. Check per-issue state: `gh issue view N --json state,closed` — OPEN despite a merged `Closes #N` means the closer didn't fire. Still verify the fix by code inspection before closing manually with an evidence comment.
3. Verify every claim at HEAD: grep the exact file:line the issue cites. Text still matching the code = still valid, keep open. A fix may have landed in an unrelated PR: `git log --oneline --since <issue-date> -- <path>`.
4. Cross-references when `gh` is old and rejects newer fields: `gh api repos/{o}/{r}/issues/N/timeline --paginate --jq '[.[]|select(.event=="cross-referenced")|.source.issue.number]|unique'` and grep `gh pr list --state merged --json number,body` for `Closes #N`.
5. Close only verified ones, each with a comment stating the evidence (file:line or command output).

## Command recipes

### Dump all open issues once

```bash
gh issue list --state open --limit 300 \
  --json number,title,body,labels,updatedAt \
  --jq '.[] | "### #\(.number)\n\(.title)\n\(.body)\n"' \
  > /tmp/issues.md
```

Read `/tmp/issues.md` in windows; do not re-query per issue for the initial pass.

### Per-issue live state

```bash
gh issue view N --json state,closed
```

OPEN despite a merged `Closes #N` means the closer didn't fire. Before closing manually,
verify the fix by code inspection and leave an evidence comment (file:line or command output).

### Verify claims at HEAD

```bash
# The issue cites a concrete path — does the bad pattern still match?
rg -n '<exact-symbol-or-line-from-issue>' <path-from-issue>

# A fix may have landed in an unrelated PR after the issue was filed
git log --oneline --since <issue-date> -- <path>
```

- Issue text still matching the code = still valid, keep open.
- Text stale / code already correct = candidate close; still write an evidence comment.

### Cross-references on old `gh`

Older `gh` rejects `stateReason` / `closingIssuesReferences`. The error prints the valid
field names — read it, then use the timeline:

```bash
gh api repos/{o}/{r}/issues/N/timeline --paginate \
  --jq '[.[]|select(.event=="cross-referenced")|.source.issue.number]|unique'

gh pr list --state merged --json number,body \
  --jq '.[] | select(.body|test("Closes #N|Fixes #N|Resolves #N")) | .number'
```

### Close with evidence

```bash
gh issue close N --reason completed --comment "Verified fixed at HEAD: <file:line> shows <what>. Proof: \`<command>\` → <output>."
```

Never close on label, audit date, or a bare `Closes #N` without tree evidence.
