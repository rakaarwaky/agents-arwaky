---
name: github-issues
description: Create, triage, label, assign GitHub issues via gh or REST; search, comment, close, reopen.
when-to-use: File a bug report or feature request, list/search open issues, triage and label them, assign owners, comment, close or reopen — via gh or the REST API. Triggers: "create an issue", "list open issues", "triage issues", "close issue #N", "which issues can be closed".
argument-hint: <number> [--add-label <label>] [--add-assignee <user>] [--body <text>] [--close|--reopen]
metadata:
  tags:
    - GitHub
    - Issues
    - Project-Management
    - Bug-Tracking
    - Triage
  related_skills:
    - github-auth
    - github-pr-workflow
---

# GitHub Issues Management

Create, search, triage, and manage GitHub issues. Each scenario shows `gh` first, then the `curl` fallback.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repo with a GitHub remote, or specify the repo explicitly

### Setup

Auth and repo detection live in `github-auth`'s helper — source it rather than
re-implementing the fallback chain (it also resolves from `~/.qwen`, `~/.hermes`,
or `~/.config/opencode` roots):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
[ "$AUTH" = "none" ] && echo "Not authenticated — resolve it with the github-auth skill first"
```

The per-scenario recipes live in `references/`; this file routes between them.

| Task | Recipe |
|------|--------|
| List, search, view issues (gh + curl) | [references/viewing-issues.md](references/viewing-issues.md) |
| Create an issue, pick a bug/feature template | [references/creating-issues.md](references/creating-issues.md) |
| Label, assign, comment, close/reopen, link to PRs, branch from issue | [references/managing-issues.md](references/managing-issues.md) |

## References

| File | Read it when |
|------|--------------|
| [`references/viewing-issues.md`](references/viewing-issues.md) | List, search, or view issues (gh and curl variants) |
| [`references/creating-issues.md`](references/creating-issues.md) | Create an issue with labels/assignees; bug and feature templates |
| [`references/managing-issues.md`](references/managing-issues.md) | Edit labels, assignment, comments, close/reopen, branch from an issue |
| [`references/triage-and-bulk.md`](references/triage-and-bulk.md) | Issue triage workflow and bulk label/close operations |
| [`templates/bug-report.md`](templates/bug-report.md) | Bug report skeleton for new issues |
| [`templates/feature-request.md`](templates/feature-request.md) | Feature request skeleton for new issues |

For auditing which open issues can close and fanning fixes out to isolated worktrees, use the `work-on-issue` skill instead — this skill owns the CRUD mechanics only.
