# Setup

Auth, username, and repo detection all live in `github-auth`'s helper — source it rather than re-implementing the fallback chain (it also resolves from `~/.qwen`, `~/.hermes`, or `~/.config/opencode` roots):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
AUTH="$GH_AUTH_METHOD"; OWNER_REPO="$GH_OWNER_REPO"; OWNER="$GH_OWNER"; REPO="$GH_REPO"
[ "$AUTH" = "none" ] && echo "Not authenticated — resolve it with the github-auth skill first"
```
