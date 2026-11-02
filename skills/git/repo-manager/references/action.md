# GitHub Actions, Secrets & Releases

Manage CI workflows, runs, repository secrets, and releases. Prefer `gh`; fall back to `git` + `curl` only where `gh` lacks coverage (Global Rule: Prefer `gh`). For secrets, `gh secret set` is dramatically simpler than the NaCl-encrypted REST path.

## Steps

1. **List & trigger workflows**:

   ```bash
   gh workflow list
   # Manually trigger a workflow_dispatch
   gh workflow run ci.yml --ref main
   gh workflow run deploy.yml -f environment=staging
   ```

2. **View & rerun runs**:

   ```bash
   gh run list --limit 10
   gh run view <RUN_ID>
   gh run view <RUN_ID> --log-failed
   gh run rerun <RUN_ID>
   gh run rerun <RUN_ID> --failed
   ```

3. **Set & manage secrets**:

   ```bash
   gh secret list
   gh secret set API_KEY --body "your-secret-value"
   gh secret set SSH_KEY < ~/.ssh/id_rsa
   gh secret delete API_KEY
   ```

   REST fallback (secrets need the repo's public key + NaCl encryption):

   ```bash
   # 1. Fetch the public key
   curl -s -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/$OWNER/$REPO/actions/secrets/public-key

   # 2. Encrypt and set (Python with PyNaCl)
   python3 -c "
   from base64 import b64encode
   from nacl import encoding, public
   import json
   public_key = '<base64_key>'
   key_id = '<key_id>'
   sealed = public.SealedBox(
       public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder)
   ).encrypt('your-secret-value'.encode('utf-8'))
   print(json.dumps({
       'encrypted_value': b64encode(sealed).decode('utf-8'),
       'key_id': key_id
   }))"

   curl -s -X PUT \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/$OWNER/$REPO/actions/secrets/API_KEY \
     -d '<output from python script>'
   ```

4. **Create & manage releases**:

   ```bash
   gh release create v1.0.0 --title "v1.0.0" --generate-notes
   gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
   gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
   gh release list
   gh release download v1.0.0 --dir ./downloads
   ```

   REST fallback (upload asset uses a separate host):

   ```bash
   RELEASE_ID=<id_from_create_response>
   curl -s -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     -H "Content-Type: application/octet-stream" \
     "https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=binary-amd64" \
     --data-binary @./dist/binary-amd64
   ```

5. **Download failed-run logs (REST)**:

   ```bash
   RUN_ID=<run_id>
   curl -s -L -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
     -o /tmp/ci-logs.zip
   cd /tmp && unzip -o ci-logs.zip -d ci-logs
   ```

## Completion Criteria

- `gh workflow list` shows the expected workflows; `gh run list` shows recent runs.
- `gh run rerun <ID>` or a manual `gh workflow run` produces a new run (its ID appears in `gh run list`).
- `gh secret list` shows the new secret's name; after a release, `gh release list` includes the new tag.
- The REST asset upload path targets `uploads.github.com`, not `api.github.com` — verify the asset appears in the release's asset list.
