---
name: releasing
description: "Release, cut a release, ship a new version, publish or tag a release, recover a failed release run."
when-to-use: 'Cut a CalVer release of any project autonomously — bump via the bump script in an Orca worktree, open and merge a release prep PR, build and publish the draft through GitHub workflows, and recover failed release runs. Triggers: "release", "cut a release", "ship a new version", "publish a release", "tag a version", "release run recovery".'
argument-hint: "--tag <tag> --target_commitish <sha>"
---

# Releasing — autonomous headless release agent

Execute end-to-end releases for any project through automated version bumps, release prep pull requests, artifact builds, and publishing. Audience: Orca bot agents running in an autonomous release role (Risa-AutoRelease or similar). Language: English, imperative mood.

## Rules

| ID | Rule | Check |
|----|------|-------|
| R1 | Confirm the repo has a CalVer or SemVer versioning scheme and a bump script at `scripts/bump.sh` or `scripts/bump.py` before proceeding. If missing, run the setup lane first (R9). | `git remote -v` and version format match the project's scheme. |
| R2 | Drive versioning strictly through the bump script and release workflow; never manually edit version strings in config files. | Verify placeholder version retention in version files. |
| R3 | Enforce mandatory prep PR flow: never commit version bumps directly to main or push tags manually. Create the git tag after the prep PR merges (step 1 step 6), or rely on the repo's auto-tag workflow if one exists. | The release branch PR is opened, approved, and merged with green CI; a `vX.Y.Z` tag exists on the remote before step 3. |
| R4 | Never create releases via `gh release create` or the GitHub Releases UI — releases are initiated only by workflow dispatch. | Ensure release drafts are initiated strictly by workflow dispatch. |
| R5 | Treat Step 4 (Publish) as irreversible and autonomous, proceeding straight to publish without stopping for approval. | Verify automated transition from validated draft to published release. |
| R6 | Label every release prep PR with `release` before merging. When the auto-release automation fires on a `pr_merged` event, check the merged PR's labels first. If the `release` label is present, skip — no new cycle. This prevents loop triggers. | `gh pr view <n> --json labels --jq '[.labels[].name]'` includes `"release"` before any action; absence means proceed. |
| R7 | All release prep work happens in an Orca worktree. The main clone stays clean. | `orca worktree create` is called before any `git checkout -b` or `git commit` on the release branch. |
| R8 | git-cliff is the mandatory changelog source. If `git-cliff` is not installed, install it before generating the changelog. If `cliff.toml` is missing, create it with a valid `commit_parsers` array. | `git-cliff` installed and `cliff.toml` exists before any release step finishes. |
| R9 | Drive the repo's own release pipeline — read `repo.json` and the repo's `.github/workflows/` first; never invent a parallel release flow. Match the repo's release commit/tag conventions. If `repo.json` marks a repo `release.yaml: need-setup`, run the setup lane first. | The release is triggered through the repo's existing workflow, not a hand-built one; `repo.json`'s `release.yaml` field matches the lane actually run. |
| R10 | Compute the next version from the last git tag, not the last GitHub release (a repo may tag without publishing, or publish without tagging). Verify with `git tag --list 'v*' --sort=-v:refname`. | Version math uses the tag list, not `gh release list` alone. |
| R11 | Scope ceilings: max 1 Orca worktree per release cycle; max 1 release prep PR per cycle; max 2 fix-and-retry attempts per failing check before stopping and reporting to the owner. Forbidden actions: editing files outside the target repo, deleting branches or worktrees other than the one this run created, force-pushing to any branch, rewriting published release history. | `orca worktree ps` shows at most 1 active worktree for this run; no force-push in reflog; release count matches PR count. |
| R12 | Forbidden tools: never `gh release create` (R4), never `git tag -f` on an existing tag, never edit `.github/workflows/release.yml` in the main clone (only in a worktree). | No `gh release create` or `git tag -f` in shell history; workflow files unchanged on main. |
| R13 | Changelog rolling window: `CHANGELOG.md` keeps only the newest 2 releases (current + summary of previous). `scripts/changelog.sh` is called after each `git-cliff --prepend`. Older releases remain as git tags. | `grep -cE '^## (\[)?(v|[0-9])' CHANGELOG.md` <= 2 after a release. |
| R14 | Lockfile sync: after stamping the version, if the repo has a `uv.lock` (Python) or `Cargo.lock` (Rust), regenerate it so CI's `--locked` / `--frozen` checks pass. The bump script does this automatically; if the bump script is missing, run `uv lock` or `cargo update` before opening the prep PR. | `uv lock --check` (Python) or `cargo metadata --no-deps` (Rust) passes in the worktree before the PR is opened. |

## Routing

Pick the lane from `repo.json`'s `release.yaml` field before running any step:

| `repo.json` `release.yaml` | Lane | What to run |
|---|---|---|
| `"ready"` (or absent — default for known repos) | **release** | The steps under [`references/release/`](references/release/step-0-version-bump.md) |
| `"need-setup"` | **setup** | The steps under [`references/setup/`](references/setup/step-0-add-repo.md) first; after the repo has a full pipeline, set `release.yaml` to `"ready"` and run the release lane |

A repo is "ready" when it has: (1) a version scheme stamped in a config file, (2) a release workflow in `.github/workflows/`, (3) a `cliff.toml` changelog source with git-cliff installed, and (4) a bump script. The setup lane is for new repos.

**Output format:** a published GitHub release (not a draft) with the expected build artifacts attached, plus the release URL reported back in the thread.

Release lane (`release.yaml: ready` repos):

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/release/step-0-version-bump.md`](references/release/step-0-version-bump.md) | Resolve the repo's version scheme and changelog source from `repo.json` + the repo's own workflows. Drive the existing pipeline. Auto-install git-cliff + auto-create `cliff.toml` only when the repo uses git-cliff. Compute `NEW_VERSION`; generate the changelog; trim to 2 releases; stamp the version and commit. |
| Step 1 | [`references/release/step-1-prep-pr.md`](references/release/step-1-prep-pr.md) | Release prep PR in an Orca worktree: create worktree, run bump/changelog, push branch, open PR with `release` label, watch CI, auto-approve and merge with admin, retire worktree. |
| Step 2 | [`references/release/step-2-preflight.md`](references/release/step-2-preflight.md) | Pre-flight checks: verify main is clean (CI green, no leftover draft release), report what ships since the previous tag. Stop on anything red. |
| Step 3 | [`references/release/step-3-build-draft.md`](references/release/step-3-build-draft.md) | Trigger the repo's own release workflow (tag-driven), watch it, verify the release carries the expected assets. |
| Step 4 | [`references/release/step-4-publish.md`](references/release/step-4-publish.md) | Draft-based repos: undraft the release (`gh release edit --draft=false --latest`) and verify it becomes public. |
| Step 5 | [`references/release/step-5-verify.md`](references/release/step-5-verify.md) | Verify the release is live (not a draft) with the expected assets; report final status and URL. |

Setup lane (`release.yaml: need-setup` repos):

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Setup 0 | [`references/setup/step-0-add-repo.md`](references/setup/step-0-add-repo.md) | Add the repo to `repo.json` (owner/repo/default_branch + the three `need-setup`/`ready` fields). Confirm with owner before editing. |
| Setup 1 | [`references/setup/step-1-pre-setup.md`](references/setup/step-1-pre-setup.md) | Audit what is missing (version file, release workflow, cliff.toml, bump script) and pick the version scheme. |
| Setup 2 | [`references/setup/step-2-setup-changelog.md`](references/setup/step-2-setup-changelog.md) | Install git-cliff, create `cliff.toml` with a `commit_parsers` array and the 2-release header, and copy `templates/changelog.sh` into the repo. |
| Setup 3 | [`references/setup/step-3-setup-release.md`](references/setup/step-3-setup-release.md) | Copy `templates/release.yml` into the repo. If the repo already has release workflows, merge them into a single `release.yml` and delete the rest. Base branch is `main`. |
| Setup 4 | [`references/setup/step-4-setup-bump.md`](references/setup/step-4-setup-bump.md) | Scaffold `scripts/bump.sh` that stamps the version, runs git-cliff, trims to 2 releases, and commits. |
| Setup 5 | [`references/setup/step-5-open-pr.md`](references/setup/step-5-open-pr.md) | Open the setup PR with the `setup` label, mark all three `repo.json` fields `"ready"` after merge, then run the release lane. |
| Setup 6 | [`references/setup/step-6-automation.md`](references/setup/step-6-automation.md) | Create dedicated per-repository Orca release automation for the new repo |
