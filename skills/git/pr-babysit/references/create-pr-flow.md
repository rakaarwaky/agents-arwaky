# Create-PR flow (one-shot)

Auth, token resolution, and owner/repo extraction live in `github-auth` — source its helper rather than re-implementing the fallback chain:

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills"          "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
echo "Using: $AUTH"; echo "Owner: $OWNER, Repo: $REPO"
```

Then route:

| Task | Recipe |
|------|--------|
| Branch, commit, push, open the PR | [branch-commit-pr.md](branch-commit-pr.md) |
| Commit/PR title grammar (Conventional Commits) | [conventional-commits.md](conventional-commits.md) |
| Watch CI until green | [ci-monitoring.md](ci-monitoring.md) |
| Auto-fix a red check, push, re-verify | [ci-auto-fix.md](ci-auto-fix.md) |
| Red log is ambiguous — flake vs real failure | [ci-troubleshooting.md](ci-troubleshooting.md) |
| Squash/rebase/merge, auto-merge, branch cleanup | [merging.md](merging.md) |
| End-to-end "Fix issue #123" with premise validation, regression test, class-level fix | [issue-to-pr.md](issue-to-pr.md) |

[pr-body-feature.md](pr-body-feature.md) and [pr-body-bugfix.md](pr-body-bugfix.md) are body skeletons for `gh pr create --body-file` — fill the matching one when the PR body runs longer than a few lines.
