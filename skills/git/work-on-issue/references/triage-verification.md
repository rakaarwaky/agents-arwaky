# Triage Verification

Phase A recipes. The body owns the rules; this file owns the command shapes.

## Dump all open issues once

```bash
gh issue list --state open --limit 300 \
  --json number,title,body,labels,updatedAt \
  --jq '.[] | "### #\(.number)\n\(.title)\n\(.body)\n"' \
  > /tmp/issues.md
```

Read `/tmp/issues.md` in windows; do not re-query per issue for the initial pass.

## Per-issue live state

```bash
gh issue view N --json state,closed
```

OPEN despite a merged `Closes #N` means the closer didn't fire. Before closing manually,
verify the fix by code inspection and leave an evidence comment (file:line or command output).

## Verify claims at HEAD

```bash
# The issue cites a concrete path — does the bad pattern still match?
rg -n '<exact-symbol-or-line-from-issue>' <path-from-issue>

# A fix may have landed in an unrelated PR after the issue was filed
git log --oneline --since <issue-date> -- <path>
```

- Issue text still matching the code = still valid, keep open.
- Text stale / code already correct = candidate close; still write an evidence comment.

## Cross-references on old `gh`

Older `gh` rejects `stateReason` / `closingIssuesReferences`. The error prints the valid
field names — read it, then use the timeline:

```bash
gh api repos/{o}/{r}/issues/N/timeline --paginate \
  --jq '[.[]|select(.event=="cross-referenced")|.source.issue.number]|unique'

gh pr list --state merged --json number,body \
  --jq '.[] | select(.body|test("Closes #N|Fixes #N|Resolves #N")) | .number'
```

## Close with evidence

```bash
gh issue close N --reason completed --comment "Verified fixed at HEAD: <file:line> shows <what>. Proof: \`<command>\` → <output>."
```

Never close on label, audit date, or a bare `Closes #N` without tree evidence.
