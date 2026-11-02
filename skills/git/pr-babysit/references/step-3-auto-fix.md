# Step 3 — Auto-Fix Red Checks

The CI fix loop. Works with either auth method.

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

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
  print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

Ambiguous failure? Load [step-4-troubleshoot.md](step-4-troubleshoot.md) to distinguish flake from real failure.

## Fix and Push

Fix in the worktree (the worktree recovery rules in [step-4-decision-tree.md](step-4-decision-tree.md) apply when a fix attempt fails):

```bash
git add -A
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

## Auto-Fix Loop

1. Read CI status (step 2) → identify failures
2. Read failure logs → understand the error
3. Fix the code in the worktree
4. `git add -A && git commit -m "fix: ..." && git push`
5. Re-check CI status (step 2)
6. Repeat while red. After any push, also run the decision-tree pass from [step-4-decision-tree.md](step-4-decision-tree.md) before declaring the PR green — a green CI does not guarantee review threads or bot findings are handled.
