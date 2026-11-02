# Step 2 — pre-flight checks

Before triggering the workflow, verify main is clean:

```shell
gh run list --workflow=ci.yaml --branch main --limit 1    # main is green
gh release list --limit 3                                  # no leftover draft
git log --oneline $(git describe --tags --abbrev=0)..origin/main  # what ships
```

Report what ships since the previous tag. Report anything red and stop to [recovery.md](recovery.md). Do not silently proceed on a failing CI or a leftover draft.
