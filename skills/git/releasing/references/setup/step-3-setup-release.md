# Setup step 3 — release workflow

**All setup work happens in an Orca worktree, never in the main clone.**

Copy the template from [`../../templates/release.yml`](../../templates/release.yml) into the target repo (inside an Orca worktree):

```shell
orca worktree create --repo path:<repo> --name "setup/release-workflow" --agent grok --no-parent --json
cd <worktree path>
cp <skill>/templates/release.yml .github/workflows/release.yml
```

## If the repo already has release workflows

If the repo has any existing release workflow(s) (e.g. `auto-release.yml`, `tag-release-prs.yml`, or an existing `release.yml`):

1. **Read the existing workflow(s)** — note the job names, build commands, and release mechanism (draft or direct).
2. **Merge into a single `release.yml`** using the template structure:
   - `open-release-pr` job (workflow_dispatch only): compute version, bump, open PR to `main` with `release` label
   - `create-tag` job (on merged PR with `release` label): extract version, create and push the tag
   - `build` → `smoke-test` → `provenance` → `release` jobs (on tag push): build and publish
3. **Delete the other release workflow files** (any workflow that the merged `release.yml` now replaces) after confirming the merged `release.yml` covers their triggers.
4. **Adapt the template to the repo's language:**
   - Build command: `uv build` (Python), `cargo build --release` (Rust), `npm run build` (Node)
   - Smoke test: use the repo's actual CLI entry point
   - Provenance: add only if the repo publishes to a registry (PyPI, npm, crates.io)
5. **Base branch is `main`**, not `develop`.

## Automated Tag Triggers and Token Configuration

GitHub Actions suppresses downstream workflows when tags are pushed using the default `GITHUB_TOKEN` to prevent recursive event loops.

1. **Autonomous Tag Push (`BOT_RELEASE_TOKEN`):**
   - Provide a repository secret `BOT_RELEASE_TOKEN` (a Personal Access Token with `contents: write` scope).
   - In `release.yml`, pass:
     ```yaml
     env:
       GITHUB_TOKEN: ${{ secrets.BOT_RELEASE_TOKEN || secrets.GITHUB_TOKEN }}
     ```
   - When `BOT_RELEASE_TOKEN` is present, GitHub Actions registers the tag push as an external user event and triggers `push.tags` build/publish jobs automatically.
   - If `BOT_RELEASE_TOKEN` is absent, the workflow safely falls back to `GITHUB_TOKEN`, and Risa triggers the build via `gh workflow run release.yml --ref "$NEW_VERSION"`.

2. **Branch Guard on Workflow Dispatch:**
   - Ensure `prepare-release` executes only on `main`:
     ```yaml
     if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'
     ```
   - This prevents manual tag workflow dispatches (`--ref vX.Y.Z`) from accidentally running the PR preparation job.

## CI gate

Add or keep a `ci.yml` that runs tests + build on every push and PR. The test shards in `ci.yml` are the authoritative gate — they run on every PR and block merges. The release workflow's `build` job assumes CI has already passed; it does not re-run the full test suite.

## Verification

After writing the workflow:

```shell
# Dry-run the workflow YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```

IF `python3` with PyYAML is not available, use `ruby -ryaml -e "YAML.load_file('.github/workflows/release.yml')" || true` as a fallback.

## Merge the setup PR

```shell
git push -u origin "setup/release-workflow"
gh pr create --base main --head "setup/release-workflow" \
  --title "setup: release workflow" \
  --body "Adds release.yml and ci.yml for automated releases."
# Label setup PRs so the PR babysitter knows to skip auto-queuing.
gh pr edit <number> --add-label setup
orca worktree rm --worktree <worktree id> --json
```
