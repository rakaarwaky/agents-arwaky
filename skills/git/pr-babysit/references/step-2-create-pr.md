# Step 2 — Create PR (when the PR does not exist yet)

When the user says "fix issue #123 and open a PR" or the PR number was not supplied: source `github-auth`'s helper for auth and repo resolution, branch, commit, push, open the PR, then continue into step 3.

Auth, token resolution, and owner/repo extraction live in `github-auth` — source its helper rather than re-implementing the fallback chain:

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
echo "Using: $AUTH"; echo "Owner: $OWNER, Repo: $REPO"
```

## Branch, commit, push

```bash
git fetch origin
git checkout -b feat/<short-description> origin/main   # or fix/<short-description>
# make the changes
git add -A
git commit -m "feat: <short description>"   # grammar: step-1-commit-title.md
git push -u origin HEAD
```

## Open the PR

**With gh:**

```bash
gh pr create \
  --title "feat: <short description>" \
  --body "## Summary
- <what changed>

## Test Plan
- [ ] <how verified>

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base <branch>`.

For anything longer than a few lines, fill the matching skeleton and pass it with `--body-file`:

- [step-2-pr-body-feature.md](step-2-pr-body-feature.md)
- [step-2-pr-body-bugfix.md](step-2-pr-body-bugfix.md)

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — store it for the whole pipeline. To create as a draft, add `"draft": true`.

## When the issue is the entry point

"Fix issue #123 and open a PR" — read the issue body and full comment thread first (`gh issue view <N> --comments`), sweep for duplicate open PRs (`gh pr list --search "#<N>" --state all` plus keyword variants), reproduce the bug on the current default branch, add a regression test, then branch/commit/push/PR as above. The PR is what dispatches CI; open it as soon as the diff is ready.

## Next

The pipeline continues with step 3 (watch CI).
