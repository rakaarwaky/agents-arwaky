# Step 2 — Auto-Fix Red Checks

The CI fix loop. Works with either auth method.

## Fix commit title grammar (Conventional Commits)

Authored when committing a CI fix. Format: `type(scope): description`

| Type | When to use | Example |
|------|------------|---------|
| `feat` | New feature | `feat(auth): add OAuth2 login flow` |
| `fix` | Bug fix | `fix(api): handle null response from /users endpoint` |
| `refactor` | Code restructuring | `refactor(db): extract query builder into separate module` |
| `docs` | Documentation only | `docs: update API usage examples` |
| `test` | Tests | `test(auth): add integration tests` |
| `ci` | CI/CD changes | `ci: add Python 3.12 to test matrix` |
| `chore` | Maintenance/deps/tooling | `chore: upgrade pytest to 8.x` |
| `perf` | Performance | `perf(search): add index on users.email` |
| `style` | Formatting | `style: run black formatter on src/` |
| `build` | Build system/external deps | `build: switch from setuptools to hatch` |
| `revert` | Reverts | `revert: revert "feat(auth): add OAuth2 login flow"` |

Scope (optional): short identifier — `auth`, `api`, `db`, `ui`, `cli`, etc.

Breaking changes: add `!` after type or `BREAKING CHANGE:` in footer:
```
feat(api)!: change authentication to use bearer tokens

BREAKING CHANGE: API endpoints now require Bearer token instead of API key header.
```

Multi-line body — wrap at 72 characters:
```
feat(auth): add JWT-based user authentication

- Add login/register endpoints
- Add User model with argon2 password hashing
- Add auth middleware

Closes #42
```

Issue linking in commit body/footer:
```
Closes #42          ← closes when merged
Fixes #42           ← same effect
Refs #42            ← references without closing
Co-authored-by: Name <email>
```

## Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
  print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

Ambiguous failure? Load [step-3-troubleshoot.md](step-3-troubleshoot.md) to distinguish flake from real failure.

## Fix and Push

Fix in the worktree (the worktree recovery rules in [step-3-decision-tree.md](step-3-decision-tree.md) apply when a fix attempt fails):

```bash
git add -A
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

## Auto-Fix Loop

1. Read CI status (step 1) → identify failures
2. Read failure logs → understand the error
3. Fix the code in the worktree
4. `git add -A && git commit -m "fix: ..." && git push` — commit title follows the grammar above
5. Re-check CI status (step 1)
6. Repeat while red. After any push, also run the decision-tree pass from [step-3-decision-tree.md](step-3-decision-tree.md) before declaring the PR green — a green CI does not guarantee review threads or bot findings are handled.
