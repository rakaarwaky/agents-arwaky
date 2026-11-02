# Step 4 — publish

The publish step is the intended autonomous step — it is irreversible and outward-facing. Proceed straight through to publish.

```shell
gh release edit "$tag" --draft=false --latest
```

That fires `release: published`, which re-asserts the seven assets, rebuilds the wheels with the same version stamp, and pushes to PyPI via Trusted Publishing (~5–10 min). Watch the `release` run the same way as in [step-3-build-draft.md](step-3-build-draft.md):

```shell
gh run list --workflow=release.yml --limit 1
gh run watch <run-id> --exit-status
```

Note edits must happen *before* this (`gh release edit "$tag" --notes-file notes.md`) — drafts are mutable, published releases are not. In the headless flow there are no note edits; the notes come from the prep PR.
