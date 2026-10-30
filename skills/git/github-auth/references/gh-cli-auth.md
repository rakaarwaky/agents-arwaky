---

## Method 2: gh CLI Authentication

If `gh` is installed, it handles both API access and git credentials in one step.

### Interactive Browser Login (Desktop)

> **PITFALL (agent-driven sessions on Windows):** when driving `gh auth login` through a pty background process, answer prompts with `process(submit)` — never `process(write)` with a bare `\n`. Enter on a Windows PTY (ConPTY/pywinpty) is a carriage return; a lone `\n` is not delivered as a line terminator, so gh's "Press Enter to open the browser" prompt (a blocking line read) silently never returns and the login hangs. Also note the browser may not open on the user's desktop from a background session — if they report that, fall back to the device flow below.

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser

```text

### Manual OAuth Device Flow (no TTY needed — PROVEN)

Fallback when interactive login is impractical (agent-driven sessions, no browser launch, headless). Uses gh's public OAuth client id; the user just enters a code at github.com/login/device. Scopes: `repo,read:org,gist` is the documented minimum for `gh auth login --with-token`; append `,workflow` only if you need to push workflow files.

```bash
# 1. Request a device code (gh's official client_id)
RESP=$(curl -s -X POST -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a&scope=repo,read:org,gist" \
  https://github.com/login/device/code)
DEVICE_CODE=$(echo "$RESP" | sed 's/.*"device_code":"\([^"]*\)".*/\1/')
USER_CODE=$(echo "$RESP" | sed 's/.*"user_code":"\([^"]*\)".*/\1/')
INTERVAL=$(echo "$RESP" | sed 's/.*"interval":\([0-9]*\).*/\1/'); INTERVAL=${INTERVAL:-5}
echo "Tell the user: go to https://github.com/login/device and enter code: $USER_CODE"

# 2. Poll for the token (respect interval; +5s on slow_down; ~15 min expiry).
#    Run this loop as a background process and show the user the code first.
while true; do
  sleep "$INTERVAL"
  POLL=$(curl -s -X POST -H "Accept: application/json" \
    -d "client_id=178c6fc778ccc68e1d6a&device_code=${DEVICE_CODE}&grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    https://github.com/login/oauth/access_token)
  case "$POLL" in
    *access_token*)
      # Never echo the token; pipe it straight into gh.
      # timeout guards the headless-keyring hang (see pitfall below) —
      # on exit 124, fall back to writing ~/.config/gh/hosts.yml directly.
      echo "$POLL" | sed 's/.*"access_token":"\([^"]*\)".*/\1/' | timeout 20 gh auth login --with-token \
        || { echo "WITH_TOKEN_HUNG_OR_FAILED — use the hosts.yml fallback below"; exit 1; }
      gh auth setup-git
      gh auth status
      echo "LOGIN_COMPLETE"; break ;;
    *authorization_pending*) ;;                      # keep polling
    *slow_down*) INTERVAL=$((INTERVAL + 5)) ;;       # back off per GitHub docs
    *expired_token*) echo "CODE_EXPIRED — restart the flow"; exit 1 ;;
    *access_denied*) echo "USER_DENIED"; exit 1 ;;
    *) echo "UNEXPECTED: $POLL"; exit 1 ;;
  esac
done

```text

Note: on Windows winget installs, gh lands at `/c/Program Files/GitHub CLI` — add it to PATH in the same shell: `export PATH="$PATH:/c/Program Files/GitHub CLI"`.

> **PITFALL (headless Linux): `gh auth login --with-token` can hang forever.**
> On keyring-less/headless boxes (VPS, containers, no dbus session), gh's
> credential storage may block indefinitely waiting on a secret-service
> keyring — even with `--insecure-storage`, and with no output. If the
> command doesn't return within ~20s (wrap it in `timeout 20 …` to detect
> this), skip gh's login machinery and write the credential store directly:
>
> ```bash
> # $TOKEN = the access token from the device flow above (never echo it)
> mkdir -p ~/.config/gh
> LOGIN=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user \
>   | sed 's/.*"login": *"\([^"]*\)".*/\1/')
> printf 'github.com:\n    users:\n        %s:\n            oauth_token: %s\n    git_protocol: https\n    oauth_token: %s\n    user: %s\n' \
>   "$LOGIN" "$TOKEN" "$TOKEN" "$LOGIN" > ~/.config/gh/hosts.yml
> chmod 600 ~/.config/gh/hosts.yml
> gh auth status          # reads hosts.yml directly — verifies without the keyring
> gh auth setup-git       # wires the git credential helper (does not hang)
> ```
>
> `gh auth status` and `setup-git` read the file store without touching the
> keyring, so they work immediately. Proven on a headless x86_64 VPS
> (gh 2.97.0, Aug 2026) after `--with-token` hung twice.

### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git

```text

If `--with-token` hangs here, use the hosts.yml fallback from the pitfall above.

### Verify

```bash
gh auth status

```text

---

## Using the GitHub API Without gh

When `gh` is not available, you can still access the full GitHub API using `curl` with a personal access token. This is how the other GitHub skills implement their fallbacks.

### Setting the Token for API Calls

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

```text

### Extracting the Token from Git Credentials

If git credentials are already configured (via credential.helper store), the token can be extracted:

```bash
# Read from git credential store — run it from this skill's own scripts/ directory
# (the pack is symlinked at ~/.hermes/skills, ~/.qwen/skills and ~/.config/opencode/skills,
# so resolve the root rather than hardcoding one).
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/git-credential-token.py" ] && break
done
uv run python "$R/github/github-auth/scripts/git-credential-token.py"

```text

### Helper: Detect Auth Method

`scripts/gh-env.sh` in this skill is the single implementation — it resolves `gh`
→ `$GITHUB_TOKEN` → `$HERMES_HOME/.env` → `~/.git-credentials`, and exports
`GH_AUTH_METHOD`, `GH_OWNER_REPO`, `GH_OWNER`, `GH_REPO`. Source it instead of
re-implementing the chain:

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/github/github-auth/scripts/gh-env.sh" ] && source "$R/github/github-auth/scripts/gh-env.sh" && break
done
echo "AUTH_METHOD=$GH_AUTH_METHOD"
echo "OWNER=$GH_OWNER REPO=$GH_REPO"
[ "$GH_AUTH_METHOD" = "none" ] && echo "Need to set up authentication first"

```text

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |
| `gh auth status` OK but `git push` still asks for password / `could not read Username` | `gh` auth and git's credential helper are not wired together. Run `gh auth setup-git` once — it registers gh as git's credential helper so HTTPS push/pull uses the gh token. After that, `git push origin <branch>` works with no token embedding. (Seen on a host where `gh auth status` showed `✓ Logged in` yet `git push` failed with `fatal: could not read Username for 'https://github.com'`.) |
