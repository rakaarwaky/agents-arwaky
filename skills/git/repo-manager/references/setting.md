# Repository Settings

Edit a repository's description, visibility, topics, default branch, and branch protection. Prefer `gh`; branch protection has no `gh` equivalent, so use the REST API (Global Rule: Prefer `gh`).

## Steps

1. **Basic settings with `gh repo edit`**:

   ```bash
   gh repo edit owner/repo-name --description "Updated description"
   gh repo edit owner/repo-name --visibility public
   gh repo edit owner/repo-name --enable-wiki=false --enable-issues=true
   gh repo edit owner/repo-name --default-branch main
   gh repo edit owner/repo-name --add-topic "machine-learning,python"
   gh repo edit owner/repo-name --enable-auto-merge
   ```

2. **Topics via API** (when the `gh` preview flag is unavailable):

   ```bash
   curl -s -X PUT \
     -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.mercy-preview+json" \
     https://api.github.com/repos/$OWNER/$REPO/topics \
     -d '{"names": ["machine-learning", "python", "automation"]}'
   ```

3. **Branch protection via API** (no `gh` command — always REST):

   ```bash
   # View current protection
   curl -s \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/$OWNER/$REPO/branches/main/protection

   # Set up branch protection
   curl -s -X PUT \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
     -d '{
       "required_status_checks": {
         "strict": true,
         "contexts": ["ci/test", "ci/lint"]
       },
       "enforce_admins": false,
       "required_pull_request_reviews": {
         "required_approving_review_count": 1
       },
       "restrictions": null
     }'
   ```

4. **Verify** — re-read the field you changed:

   ```bash
   gh repo view owner/repo-name --json description,visibility,defaultBranchRef,topics
   ```

## Completion Criteria

- `gh repo view <owner>/<repo> --json` reflects the new description, visibility, topics, or default branch.
- For branch protection, a second `GET .../branches/main/protection` returns the fields you set (status-check contexts, required reviews).
- For `--add-topic`, the topic appears in `gh repo view ... --json topics`.
