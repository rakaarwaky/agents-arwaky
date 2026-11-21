# Step 3 — build / tag

Which command depends on the repo. Read `repo.json` and the repo's own `.github/workflows/` before choosing.

**Worktree rule:** do all of this work in an Orca worktree — never in the main clone. The main clone stays clean.


## Pre-check: tag exists

Before triggering the workflow, confirm the tag exists on the remote:

```shell
git ls-remote --tags origin "$NEW_VERSION" | grep -q "$NEW_VERSION" \
  || { echo "tag $NEW_VERSION not found on remote — create it in step 1 (or via the repo's auto-tag workflow)"; exit 1; }
```

IF the tag is missing -> go back to [step-1-prep-pr.md](step-1-prep-pr.md) step 6 and create it.

## Tag-driven pipeline

The standard pipeline is a single self-contained `release.yml`:

1. A `create-tag` job watches for merged PRs with the `release` label whose title starts with `chore(release):`.
2. On merge, it derives the semantic version and pushes the `vX.Y.Z` tag using `BOT_RELEASE_TOKEN` (or `GITHUB_TOKEN`).
3. If `BOT_RELEASE_TOKEN` is configured, GitHub Actions recognizes the tag push as an external user event and triggers the `push.tags` build/publish run automatically. If `BOT_RELEASE_TOKEN` is absent or the event does not trigger within 20s, dispatch manually:

```shell
# 1. Check if the push run started automatically (give it 10-15s after tag push):
gh run list --workflow=release.yml -R <owner>/<repo> --limit 1

# If an automatic push run is already active or completed for this tag, watch it:
gh run watch <run-id> -R <owner>/<repo> --exit-status

# 2. Fallback: only if no run was triggered (BOT_RELEASE_TOKEN absent):
gh workflow run release.yml -R <owner>/<repo> --ref "$NEW_VERSION"
gh run list --workflow=release.yml -R <owner>/<repo> --limit 1
gh run watch <run-id> -R <owner>/<repo> --exit-status
```

Verify assets match the expected dist outputs for the repo's build command (e.g. `dist/*` for Python, `target/release/*` for Rust, package tarball for Node):

```shell
gh release list -R <owner>/<repo> --limit 1
gh release view "$NEW_VERSION" -R <owner>/<repo> --json assets,url --jq '{url:.url,assets:[.assets[].name]}'
```

Recovery:

- Build job failed: delete the release and its tag (`gh release delete <tag> -R <owner>/<repo> --cleanup-tag`), fix, re-dispatch.
- Assets missing: delete and re-dispatch — never backfill a published release by hand.
- For a repo that DOES use a draft→publish split (`softprops/action-gh-release` with draft, then undraft), use `gh release edit "$tag" --draft=false` and watch the follow-up publish job.

Proceed to [step-5-verify.md](step-5-verify.md) on success.