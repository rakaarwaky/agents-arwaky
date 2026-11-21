# Step 2 — pre-flight checks

Before triggering the workflow, verify main is clean:

```shell
gh run list --workflow=ci.yml --branch main --limit 1    # main is green (or ci.yaml if named so)
gh release list --limit 3                                  # no leftover draft
git log --oneline $(git describe --tags --abbrev=0)..origin/main  # what ships
```

If any fix is needed (CI failure, stale workflow file, etc.), create or reuse an Orca worktree for the fix, push a branch, open a PR, and merge. **Never edit files in the main clone.**

Report what ships since the previous tag. Report anything red and stop. Fix CI on the release branch or delete the leftover draft, then re-run Step 2. Do not silently proceed on a failing CI or a leftover draft.
