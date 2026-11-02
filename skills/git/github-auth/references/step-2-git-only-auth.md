# Git-Only Authentication (No gh, No sudo)

Works on any machine with `git` installed. No root access needed.

## Option A: HTTPS with Personal Access Token (Recommended)

The most portable method — works everywhere, no SSH config needed.

### Step 1: Create a personal access token

Go to: **https://github.com/settings/tokens**

- Click "Generate new token (classic)"
- Give it a name like "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (if working with organization repos)
- Set expiration (90 days is a good default)
- Copy the token — it won't be shown again

### Step 2: Configure git to store the token

```bash
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

After entering credentials once, they're saved and reused for all future operations.

**Alternative: cache helper** (credentials expire from memory):

```bash
git config --global credential.helper 'cache --timeout=28800'
```

**Alternative: token in remote URL** (avoids credential prompts entirely, per-repo):

```bash
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

### Step 3: Configure git identity

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

### Step 4: Verify

```bash
git ls-remote https://github.com/<their-username>/<any-repo>.git
git config --global user.name
git config --global user.email
```

## Option B: SSH Key Authentication

For users who prefer SSH or already have keys set up.

### Step 1: Check for existing SSH keys

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

### Step 2: Generate a key if needed

```bash
# ed25519: modern, secure, fast
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Add the public key at **https://github.com/settings/keys** → "New SSH key" → paste → title it "hermes-agent-<machine-name>".

### Step 3: Test the connection

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

### Step 4: Configure git to use SSH for GitHub

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### Step 5: Configure git identity

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```
