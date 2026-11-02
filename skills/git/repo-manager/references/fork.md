# Fork Repository

Fork an upstream repo into the user's account, clone it, and keep it in sync. Prefer `gh`; fall back to `git` + `curl` only where `gh` lacks coverage (Global Rule: Prefer `gh`).

## Steps

1. **Fork with `gh`** (creates the fork and clones it in one step):

   ```bash
   gh repo fork owner/repo-name --clone
   ```

2. **curl fallback (no `gh`)**:

   ```bash
   # Create the fork via API
   curl -s -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/owner/repo-name/forks

   # Clone the fork (GitHub creates it asynchronously)
   sleep 3
   git clone https://github.com/$GH_USER/repo-name.git
   cd repo-name

   # Add the original repo as "upstream" remote
   git remote add upstream https://github.com/owner/repo-name.git
   ```

3. **Keep the fork in sync**:

   ```bash
   # Pure git (works everywhere)
   git fetch upstream
   git checkout main
   git merge upstream/main
   git push origin main

   # gh shortcut
   gh repo sync $GH_USER/repo-name
   ```

## Completion Criteria

- `gh repo view <owner>/<repo>` shows the fork exists under the user's account (or `gh` reported the fork was created).
- `git remote -v` in the fork shows both `origin` (the user's fork) and `upstream` (the original repo).
- After a sync, `git log --oneline origin/main..upstream/main` is empty (fork is up to date).
