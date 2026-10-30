# Recovery — failed release runs

Stop and fix with this table whenever a stage below fails; do not improvise.

| Symptom | Fix |
|---|---|
| Step 3 failed mid-run | No release exists yet, or a draft does. Delete the draft (`gh release delete <tag> --cleanup-tag`) and re-run Step 3. |
| Draft missing assets | Delete the draft and re-run Step 3 — never backfill by hand. |
| `assert-binaries-present` failed after publish | The release was created outside the workflow and is now immutable. Delete the release *and* its tag, then re-run Step 3 with the same tag. |
| PyPI publish failed (transient / outage) | Wheels are built; re-run just the failed job: `gh run rerun <run-id> --failed`. |
| Wrong version already on PyPI | PyPI versions can't be reused or overwritten. Ship the next `N` — do not try to reuse the tag. |
| Release prep PR merge failed | Check CI on the release branch; fix in the same branch, re-merge, then continue from Step 2. |
| Bump script missing and created one that fails | The script is a version-stamp helper; if it cannot commit, do it manually (`git commit -m "release: bump to $NEW_VERSION"`), then continue. |