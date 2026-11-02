# Step 5 — verify after publishing

```shell
gh run list --workflow=release.yml --limit 2          # publish job green
curl -s https://pypi.org/pypi/mergify-cli/json | jq -r .info.version
gh pr list --repo Mergifyio/homebrew-tap --author mergify-ci-bot
```

Confirm PyPI reports the new version and the Homebrew tap PR is open.

The Homebrew formula bump is automatic: the `homebrew-tap-sync` workflow in `Mergifyio/mergify-ci-bot` opens a PR against `Mergifyio/homebrew-tap` within ~20 minutes of publish, updating `RELEASE` and the four per-arch checksums from `SHA256SUMS`. **This PR still needs a human to merge it.** Report it as the final status:

> Release $NEW_VERSION published to PyPI; Homebrew tap PR <url> open — needs human merge.

The docs site picks up `cli-schema.json` off the latest release on its own — nothing to do there.
