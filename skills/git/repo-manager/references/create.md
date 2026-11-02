# Create Repository

Create a new GitHub repository, optionally under an organization or from a template. Prefer `gh`; fall back to `git` + `curl` only where `gh` lacks coverage (Global Rule: Prefer `gh`).

## Steps

1. **Pick the target** — user's own account (`owner/repo`) or an org (`org/repo`). Confirm visibility (`public` / `private`) and optional description and license.

2. **Create with `gh`**:

   ```bash
   # Public, clone into cwd
   gh repo create my-new-project --public --clone

   # Private with description and license
   gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

   # Under an organization
   gh repo create my-org/my-new-project --public --clone

   # From an existing local directory (push it)
   cd /path/to/existing/project
   gh repo create my-project --source . --public --push

   # From a template repository
   gh repo create my-new-app --template owner/template-repo --public --clone
   ```

3. **curl fallback (user repo)** — when `gh` is unavailable:

   ```bash
   curl -s -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user/repos \
     -d '{"name": "my-new-project", "description": "A useful tool", "private": false, "auto_init": true, "license_template": "mit"}'

   # Then push an existing local directory
   git remote add origin https://github.com/$GH_USER/my-new-project.git
   git push -u origin main
   ```

4. **curl fallback (org repo)**:

   ```bash
   curl -s -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/orgs/my-org/repos \
     -d '{"name": "my-new-project", "private": false}'
   ```

## Completion Criteria

- The repo exists at `https://github.com/<owner>/<repo>` (verify with `gh repo view <owner>/<repo>` or a successful push).
- If `--clone` was used, the working directory is inside the cloned repo.
- If `--source . --push` was used, `git remote -v` shows `origin` and the first commit is pushed.
