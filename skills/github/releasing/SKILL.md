---
name: releasing
description: release, cut a release, ship a new version, publish a release, tag a version, headless release, release run recovery.
when-to-use: Release the mergify CLI autonomously — compute the next CalVer tag, bump via the bump script, open and merge a release prep PR, build and publish the draft release through GitHub workflows, and recover failed release runs.
argument-hint: [--tag <tag>] [--target_commitish <sha>]
---

# Releasing `mergify-cli` — autonomous headless release agent

This is an **agent instruction**, not a human runbook. You are an autonomous
release agent: you run every stage below end-to-end, stop only on hard
failures that need the Recovery table, and report a final status at the end.
The only step you report to the user and do *not* execute is the Homebrew tap
PR merge, which needs a human.

Everything is driven by `.github/workflows/release.yml`. **There is no version
to bump in any file** — `pyproject.toml` and `Cargo.toml` keep their placeholder
versions and the workflow stamps the tag at build time. The release prep PR is
how the version stamp and changelog get committed; it is not a manual edit of
version files.

Versions are calver: `YYYY.M.D.N` (no zero padding, `N` starts at 1 each UTC day).

`RELEASING.md` at the repo root explains *why* the flow is shaped this way
(GitHub's immutable-releases policy). Read it when something goes wrong or the
workflow itself needs changing.

## Guardrails

- **Never run `gh release create` or push a tag by hand.** A release created
  outside the workflow has no binaries, and once published it is immutable — the
  asset assertion then permanently blocks the PyPI publish for that version.
- **Never click / script "Draft a new release" in the Releases UI.** Same trap.
- **Step 4 (Publish) is irreversible and outward-facing** — it locks the release
  and pushes to PyPI. The headless flow proceeds straight to publish; this is the
  intended autonomous behavior, not a stop-and-ask step.

## Step 0 — version bump

Working directory: project root.

1. Compute `NEW_VERSION`. `YYYY.M.D` is the current UTC date; `N` follows the
   calver rule (preamble above).

   ```shell
   last=$(gh release list --limit 1 --json tagName --jq '.[0].tagName')   # e.g. 2026.10.24.1
   today=$(date -u +%Y.%-m.%-d)                                     # no zero padding
   # N = 1 if last tag is from a different day, else last N + 1
   N=1
   if [ -n "$last" ]; then
     last_date="${last%.*}"
     last_N="${last##*.}"
     [ "$last_date" = "$today" ] && N=$((last_N + 1))
   fi
   NEW_VERSION="$today.$N"
   ```

2. Use the bump script at project-root `scripts/` — check for `scripts/bump.sh`
   or `scripts/bump.py`:

   ```shell
   if [ -f scripts/bump.sh ]; then
     bash scripts/bump.sh "$NEW_VERSION"
   elif [ -f scripts/bump.py ]; then
     python3 scripts/bump.py "$NEW_VERSION"
   else
     mkdir -p scripts
     cat > scripts/bump.sh <<'EOF'
   #!/usr/bin/env bash
   sed -i -E 's/^__RELEASE_VERSION__ = .*/__RELEASE_VERSION__ = "'"$1"'"/' \
     pyproject.toml Cargo.toml 2>/dev/null || true
   echo "## $1" >> CHANGELOG.md
   for f in scripts pyproject.toml Cargo.toml CHANGELOG.md; do [ -e "$f" ] && git add -A "$f" || true; done
   git commit -m "release: bump to $1"
   EOF
     chmod +x scripts/bump.sh
     bash scripts/bump.sh "$NEW_VERSION"
   fi
   ```

## Step 1 — release prep PR

1. Create the prep branch and open the PR:

   ```shell
   git checkout -b "release/$NEW_VERSION"
   git push -u origin "release/$NEW_VERSION"
   gh pr create --base main --head "release/$NEW_VERSION" \
     --title "release: $NEW_VERSION" \
     --body "Calver release prep for $NEW_VERSION." \
     --label release
   ```

2. The PR must be green (CI passing on the release branch) before proceeding.

   ```shell
   gh pr checks <pr-number> --watch
   ```

3. Auto-approve and merge with admin, then switch back to main:

   ```shell
   gh pr review <pr-number> --approve
   gh pr merge <pr-number> --admin --squash
   git checkout main
   git pull origin main
   ```

## Step 2 — pre-flight checks

Before triggering the workflow, verify main is clean:

```shell
gh run list --workflow=ci.yaml --branch main --limit 1    # main is green
gh release list --limit 3                                  # no leftover draft
git log --oneline $(git describe --tags --abbrev=0)..origin/main  # what ships
```

Report anything red and stop to Recovery. Do not silently proceed on a
failing CI or a leftover draft.

## Step 3 — build the draft

Trigger `release.yml`:

```shell
gh workflow run release.yml   # no tag input — the workflow computes the tag
# or, only when a specific version is needed:
gh workflow run release.yml -f tag=$NEW_VERSION -f target_commitish=<sha>
```

Leave `tag` empty unless a specific version is required; leave
`target_commitish` empty unless cherry-picking a release off an older line.

Watch it (~5–10 min):

```shell
gh run list --workflow=release.yml --limit 1
gh run watch <run-id> --exit-status
```

The workflow builds the five-target wheel matrix, extracts the `mergify` binary
from each wheel, packages the archives + `SHA256SUMS`, dumps `cli-schema.json`,
signs the binaries with build provenance, and creates the **draft** release
with notes generated from the PRs merged since the previous tag.

Then verify — the draft must carry exactly these seven assets:

```shell
tag=$(gh release list --limit 1 --json tagName --jq '.[0].tagName')
gh release view "$tag" --json isDraft,url,assets --jq '{draft:.isDraft,url:.url,assets:[.assets[].name]}'
```

- `mergify-<tag>-x86_64-unknown-linux-gnu.tar.gz`
- `mergify-<tag>-aarch64-unknown-linux-gnu.tar.gz`
- `mergify-<tag>-x86_64-apple-darwin.tar.gz`
- `mergify-<tag>-aarch64-apple-darwin.tar.gz`
- `mergify-<tag>-x86_64-pc-windows-msvc.zip`
- `SHA256SUMS`
- `cli-schema.json`

Do not stop here (see Guardrails); proceed immediately to Step 4.

## Step 4 — publish

```shell
gh release edit "$tag" --draft=false --latest
```

That fires `release: published`, which re-asserts the seven assets, rebuilds
the wheels with the same version stamp, and pushes to PyPI via Trusted
Publishing (~5–10 min). Watch the `release` run the same way as in Step 3:

```shell
gh run list --workflow=release.yml --limit 1
gh run watch <run-id> --exit-status
```

Note edits must happen *before* this (`gh release edit "$tag" --notes-file
notes.md`) — drafts are mutable, published releases are not. In the headless
flow there are no note edits; the notes come from the prep PR.

## Step 5 — verify after publishing

```shell
gh run list --workflow=release.yml --limit 2          # publish job green
curl -s https://pypi.org/pypi/mergify-cli/json | jq -r .info.version
gh pr list --repo Mergifyio/homebrew-tap --author mergify-ci-bot
```

Confirm PyPI reports the new version and the Homebrew tap PR is open.

The Homebrew formula bump is automatic: the `homebrew-tap-sync` workflow in
`Mergifyio/mergify-ci-bot` opens a PR against `Mergifyio/homebrew-tap` within
~20 minutes of publish, updating `RELEASE` and the four per-arch checksums from
`SHA256SUMS`. **This PR still needs a human to merge it.** Report it as the
final status:

Release $NEW_VERSION published to PyPI; Homebrew tap PR <url> open — needs human merge.

The docs site picks up `cli-schema.json` off the latest release on its own —
nothing to do there.

## Recovery

| Symptom | Fix |
|---|---|
| Step 3 failed mid-run | No release exists yet, or a draft does. Delete the draft (`gh release delete <tag> --cleanup-tag`) and re-run Step 3. |
| Draft missing assets | Delete the draft and re-run Step 3 — never backfill by hand. |
| `assert-binaries-present` failed after publish | The release was created outside the workflow and is now immutable. Delete the release *and* its tag, then re-run Step 3 with the same tag. |
| PyPI publish failed (transient / outage) | Wheels are built; re-run just the failed job: `gh run rerun <run-id> --failed`. |
| Wrong version already on PyPI | PyPI versions can't be reused or overwritten. Ship the next `N` — do not try to reuse the tag. |
| Release prep PR merge failed | Check CI on the release branch; fix in the same branch, re-merge, then continue from Step 2. |
| Bump script missing and created one that fails | The script is a version-stamp helper; if it cannot commit, do it manually (`git commit -m "release: bump to $NEW_VERSION"`), then continue. |
