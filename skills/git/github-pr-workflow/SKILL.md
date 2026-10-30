---
name: github-pr-workflow
description: Run the GitHub PR lifecycle from a worktree or branch — branch, commit, push, open a PR (pr to main), monitor CI, auto-fix red checks, merge/squash.
when-to-use: "Take work to a merged PR: create a branch, commit, push, open a PR, watch CI, auto-fix red checks, and merge (squash / auto-merge), including the orca worktree + GitHub PR flow. Observed run phrasing: \"fix PR 162\", \"pr to main\", \"merger pr\", PR titles \"Remove PRD Acceptance Table, Fix Lint Enforcement\" and \"remove FRD.md surface links enable strict_member_docs\". Triggers: \"open a PR\", \"make sure CI is green\", \"fix the failing check\", \"merge when green\", \"auto-fix the CI failure\", \"finish this branch into a PR\"."
argument-hint: <number> [--squash|--auto] [--draft] [--reviewer <user>] [--label <label>]
metadata:
  tags:
    - GitHub
    - Pull-Requests
    - CI/CD
    - Git
    - Automation
    - Merge
    - Issues
  related_skills:
    - github-auth
    - github-code-review
    - github-issues
    - systematic-debugging
    - test-driven-development
    - requesting-code-review
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

Auth, token resolution, and owner/repo extraction all live in `github-auth`'s
helper — source it rather than re-implementing the fallback chain (it also
resolves from `~/.qwen`, `~/.hermes`, or `~/.config/opencode` pack roots):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
echo "Using: $AUTH"; echo "Owner: $OWNER, Repo: $REPO"
```

The per-scenario recipes live in `references/`; this file routes between them.

| Task | Recipe |
|------|--------|
| Branch, commit, push, open the PR (Conventional Commits) | [references/branch-commit-pr.md](references/branch-commit-pr.md) |
| Watch CI checks until green (gh + curl polling) | [references/ci-monitoring.md](references/ci-monitoring.md) |
| Diagnose and fix a red check, push, re-verify | [references/ci-auto-fix.md](references/ci-auto-fix.md) |
| Merge (squash/rebase/merge, auto-merge, delete branch) | [references/merging.md](references/merging.md) |

## References

| File | Read it when |
|------|--------------|
| `references/branch-commit-pr.md` | Create the branch, write conventional commits, push, open the PR (§1–3) |
| `references/conventional-commits.md` | The full type/scope/footer grammar and worked examples for commit messages and PR titles |
| `references/ci-monitoring.md` | Check CI status once or poll until complete, via gh or curl |
| `references/ci-auto-fix.md` | The auto-fix loop for a red check: read logs, fix, push, re-verify |
| `references/ci-troubleshooting.md` | A check is red and the log is ambiguous — failure-pattern table, flake vs real failure, rerun and bisect guidance |
| `references/merging.md` | Squash/rebase/merge, enable auto-merge, clean up the branch |
| `references/issue-to-pr.md` | The full end-to-end recipe for turning an issue into a tested, verified PR ("Fix issue #123") |

`templates/pr-body-feature.md` and `templates/pr-body-bugfix.md` are the body skeletons for `gh pr create --body-file` — fill the matching one when the PR body runs longer than a few lines.
