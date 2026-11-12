# Step 0 — Prerequisites & setup

- Authenticated with GitHub (see the `github-workflow` skill).
- Inside a git repo with a GitHub remote, or specify the repo explicitly.

Auth and repo detection live in `github-workflow`'s helper — source it rather than re-implementing the fallback chain (it also resolves from `~/.qwen`, `~/.hermes`, or `~/.config/opencode` roots):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-workflow/scripts/gh-env.sh" ] && source "$R/github/github-workflow/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
[ "$AUTH" = "none" ] && echo "Not authenticated — resolve it with the github-workflow skill first"
```
