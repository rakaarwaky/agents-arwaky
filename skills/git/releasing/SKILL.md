---
name: releasing
description: "Release, cut a release, ship a new version, publish or tag a release for the mergify CLI, recover a failed release run."
when-to-use: "Cut a CalVer release of the mergify CLI autonomously — bump via the bump script, open and merge a release prep PR, build and publish the draft through GitHub workflows, and recover failed release runs. Triggers: "release", "cut a release", "ship a new version", "publish a release", "tag a version", "release run recovery"."
argument-hint: [--tag <tag>] [--target_commitish <sha>]
---

# Releasing `mergify-cli` — autonomous headless release agent

## Global Rules

- This is an **agent instruction**, not a human runbook. Run every step end-to-end, stop only on hard failures (see the Recovery row), and report a final status at the end.
- The only step reported to the user and *not* executed is the Homebrew tap PR merge, which needs a human.
- Everything is driven by `.github/workflows/release.yml`. There is no version to bump in any file — `pyproject.toml` and `Cargo.toml` keep placeholder versions and the workflow stamps the tag at build time. The release prep PR commits the version stamp and changelog; it is not a manual edit of version files.
- Versions are calver: `YYYY.M.D.N` (no zero padding, `N` starts at 1 each UTC day).
- **Never run `gh release create` or push a tag by hand.** A release created outside the workflow has no binaries, and once published it is immutable — the asset assertion then permanently blocks the PyPI publish for that version.
- **Never click / script "Draft a new release" in the Releases UI.** Same trap.
- **Step 4 (Publish) is irreversible and outward-facing** — it locks the release and pushes to PyPI. The headless flow proceeds straight to publish; this is the intended autonomous behavior, not a stop-and-ask step.
- `RELEASING.md` at the repo root explains *why* the flow is shaped this way (GitHub's immutable-releases policy). Read it when something goes wrong or the workflow itself needs changing.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/step-0-version-bump.md`](references/step-0-version-bump.md) | Version bump and changelog generation: compute `NEW_VERSION`, generate changelog with `git-cliff`, run the bump script (`scripts/bump.sh` / `scripts/bump.py`). Working directory: project root. |
| Step 1 | [`references/step-1-prep-pr.md`](references/step-1-prep-pr.md) | Release prep PR: create branch, open PR, wait for green CI, auto-approve and merge with admin, switch back to main. |
| Step 2 | [`references/step-2-preflight.md`](references/step-2-preflight.md) | Pre-flight checks: verify main is clean (CI green, no leftover draft release), report what ships since the previous tag. Stop to Recovery on anything red. |
| Step 3 | [`references/step-3-build-draft.md`](references/step-3-build-draft.md) | Build the draft: trigger `release.yml`, watch (~5–10 min), verify the draft carries exactly seven assets. Proceed immediately to Step 4. |
| Step 4 | [`references/step-4-publish.md`](references/step-4-publish.md) | Publish: `gh release edit "$tag" --draft=false --latest`, watch the publish job (~5–10 min), confirm PyPI + Homebrew tap PR. |
| Step 5 | [`references/step-5-verify.md`](references/step-5-verify.md) | Verify after publishing: confirm PyPI reports the new version and the Homebrew tap PR is open. Report final status. |
| Recovery | [`references/recovery.md`](references/recovery.md) | Failed stages playbook: delete draft, rerun failed job, immutable-release traps, prep-PR re-merge. |
