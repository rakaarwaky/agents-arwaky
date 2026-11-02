# Repository Info

View, list, and search GitHub repositories. Prefer `gh`; fall back to `curl` + REST only where `gh` lacks coverage (Global Rule: Prefer `gh`).

## Steps

1. **View a repo with `gh`**:

   ```bash
   gh repo view owner/repo-name
   # Machine-readable JSON
   gh repo view owner/repo-name --json description,visibility,defaultBranchRef,stargazersCount,forksCount
   ```

2. **List repos with `gh`**:

   ```bash
   # Your repos, newest first
   gh repo list --limit 20

   # Org repos
   gh repo list my-org --limit 50

   # Filter by visibility
   gh repo list --user --private
   ```

3. **Search repos with `gh`**:

   ```bash
   gh search repos "machine learning" --language python --sort stars
   gh search repos --owner my-org --language go
   ```

4. **curl fallback** (when `gh` is unavailable):

   ```bash
   # View repo details
   curl -s -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/$OWNER/$REPO \
     | python3 -c "
   import sys, json
   r = json.load(sys.stdin)
   print(f\"Name: {r['full_name']}\")
   print(f\"Description: {r['description']}\")
   print(f\"Stars: {r['stargazers_count']}  Forks: {r['forks_count']}\")
   print(f\"Default branch: {r['default_branch']}\")
   print(f\"Language: {r['language']}\")"

   # List your repos
   curl -s -H "Authorization: token $GITHUB_TOKEN" \
     "https://api.github.com/user/repos?per_page=20&sort=updated" \
     | python3 -c "
   import sys, json
   for r in json.load(sys.stdin):
       vis = 'private' if r['private'] else 'public'
       print(f\"  {r['full_name']:40}  {vis:8}  {r.get('language', ''):10}  ★{r['stargazers_count']}\")"

   # Search repos
   curl -s "https://api.github.com/search/repositories?q=machine+learning+language:python&sort=stars&per_page=10" \
     | python3 -c "
   import sys, json
   for r in json.load(sys.stdin)['items']:
       print(f\"  {r['full_name']:40}  ★{r['stargazers_count']:6}  {r['description'][:60] if r['description'] else ''}\")"
   ```

## Completion Criteria

- `gh repo view <owner>/<repo>` returns the repo's metadata (description, stars, default branch, language).
- `gh repo list --limit N` returns at most N repos; org list shows only that org's repos.
- `gh search repos` results are filtered by language/sort as requested; curl fallback responses parse to JSON without errors.
