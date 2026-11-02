# Phase A — Load and triage

Never close or skip work from a `status: done` label, an audit date, or a merged PR's `Closes #N` line alone. GitHub can silently fail to close issues a PR body declares while the fix itself did land. Verify every claim against the current tree.

1. Dump open issues once:
   `gh issue list --state open --limit 300 --json number,title,body,labels,updatedAt --jq '.[] | "### #\(.number)\n\(.title)\n\(.body)\n"' > /tmp/issues.md`
2. Check per-issue state: `gh issue view N --json state,closed` — OPEN despite a merged `Closes #N` means the closer didn't fire. Still verify the fix by code inspection before closing manually with an evidence comment.
3. Verify every claim at HEAD: grep the exact file:line the issue cites. Text still matching the code = still valid, keep open. A fix may have landed in an unrelated PR: `git log --oneline --since <issue-date> -- <path>`.
4. Cross-references when `gh` is old and rejects newer fields: `gh api repos/{o}/{r}/issues/N/timeline --paginate --jq '[.[]|select(.event=="cross-referenced")|.source.issue.number]|unique'` and grep `gh pr list --state merged --json number,body` for `Closes #N`.
5. Close only verified ones, each with a comment stating the evidence (file:line or command output).

Full command recipes: [triage-verification.md](triage-verification.md).
