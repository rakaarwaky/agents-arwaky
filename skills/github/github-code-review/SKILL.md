---
name: github-code-review
description: GitHub PR thread review via gh: fetch diff, inline comments, APPROVE / REQUEST_CHANGES / COMMENT, reply to threads.
when-to-use: Review an open PR on GitHub — view its diff, post inline comments, submit a formal APPROVE / REQUEST_CHANGES / COMMENT review, post a summary comment, or reply to a review thread (not local-diff analysis).
argument-hint: <number> [--approve|--request-changes|--comment] [--body <text>]
metadata:
  tags:
    - GitHub
    - Code-Review
    - Pull-Requests
    - Git
    - Quality
    - Review-Threads
  related_skills:
    - github-auth
    - github-pr-workflow
---

# GitHub Code Review

Drive the GitHub-side review mechanics: read an open PR, post inline comments and a
formal review, and reply to review threads. Everything here is `gh` or REST against
GitHub; the `gh`/`curl` split only matters for PR-level interactions.

**Out of scope:** analyzing a local diff for correctness, security, quality, and
performance before you push. Every agent harness ships that (Qwen Code: the bundled
`/review` skill), so this skill deliberately does not restate it — use the built-in
reviewer, then come here to get the findings onto the PR.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository

### Setup (for PR interactions)

Auth and repo detection live in `github-auth`'s helper — source it rather than
re-implementing the fallback chain (it also resolves correctly from `~/.qwen`,
`~/.hermes`, or `~/.config/opencode` roots):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
[ "$AUTH" = "none" ] && echo "Not authenticated — resolve it with the github-auth skill first"
```

The per-command recipes live in `references/pr-review-commands.md`; this file routes between them.

| Task | Recipe |
|------|--------|
| View PR diff, list changed files | [`references/pr-review-commands.md`](references/pr-review-commands.md) |
| Leave inline review comments | [`references/pr-review-commands.md`](references/pr-review-commands.md) |
| Submit a formal APPROVE / REQUEST_CHANGES / COMMENT review | [`references/pr-review-commands.md`](references/pr-review-commands.md) |

## References

| File | Read it when |
|------|--------------|
| [`references/pr-review-commands.md`](references/pr-review-commands.md) | gh/curl recipes for viewing PRs, inline comments, and formal reviews |
| [`references/review-output-template.md`](references/review-output-template.md) | The shape of the top-level summary comment |
| [`references/pr-review-workflow.md`](references/pr-review-workflow.md) | The full end-to-end recipe — "review PR #N", "look at this PR" |
