# Step 3 — build the draft

Trigger `release.yml`:

```shell
gh workflow run release.yml   # no tag input — the workflow computes the tag
# or, only when a specific version is needed:
gh workflow run release.yml -f tag=$NEW_VERSION -f target_commitish=<sha>
```

Leave `tag` empty unless a specific version is required; leave `target_commitish` empty unless cherry-picking a release off an older line.

Watch it (~5–10 min):

```shell
gh run list --workflow=release.yml --limit 1
gh run watch <run-id> --exit-status
```

The workflow builds the five-target wheel matrix, extracts the `mergify` binary from each wheel, packages the archives + `SHA256SUMS`, dumps `cli-schema.json`, signs the binaries with build provenance, and creates the **draft** release with notes generated from the PRs merged since the previous tag.

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

Recovery:

- Step 3 failed mid-run: no release exists yet, or a draft does. Delete the draft (`gh release delete <tag> --cleanup-tag`) and re-run Step 3.
- Draft missing assets: delete the draft and re-run Step 3 — never backfill by hand.

Do not stop here (the publish step is the intended autonomous step); proceed immediately to [step-4-publish.md](step-4-publish.md).
