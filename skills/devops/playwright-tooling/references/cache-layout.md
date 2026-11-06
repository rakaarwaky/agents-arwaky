# Cache layout + recovery (Playwright 1.63, revision 1243)

Exact dir names, marker files, and the recovery procedure for a CDN that `curl` can reach but Playwright's Node client cannot.

| Component | Cache dir name | Download URL |
|---|---|---|
| chromium | `chromium-1243` | `https://cdn.playwright.dev/builds/cft/153.0.8010.12/linux64/chrome-linux64.zip` |
| chromium-headless-shell | `chromium_headless_shell-1243` | `https://cdn.playwright.dev/builds/cft/153.0.8010.12/linux64/chrome-headless-shell-linux64.zip` |
| ffmpeg | `ffmpeg-1011` | `https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-linux.zip` |

**Goal:** every expected cache dir exists with both marker files, so `playwright install` exits 0 without attempting a download.

## Critical pitfall: dashes are normalized to underscores

Playwright's registry (`readDescriptors` in `coreBundle.js`) does
`name.replace(/-/g, "_")` on the browser name **before** building the
directory path. So `chromium-headless-shell` revision 1243 installs to
`chromium_headless_shell-1243` (with **underscores**), not
`chromium-headless-shell-1243` (with dashes).

Placing the browser in the dashed dir makes Playwright's
`_deleteStaleBrowsers` treat it as "unused" and wipe it on every
`playwright install` run, then fail the re-download. Verify the exact
dir name from the layout table before placing files.

## Required marker files

Each browser cache dir must contain two zero-byte marker files:

- `INSTALLATION_COMPLETE`
- `DEPENDENCIES_VALIDATED`

Without `INSTALLATION_COMPLETE`, Playwright treats the dir as an
incomplete install and re-downloads. Create both after every manual
placement.

## Recovery procedure (CDN unreachable)

`curl` typically succeeds where Playwright's Node.js fetch times out.
Procedure:

1. Verify the exact target dir name from the layout table above (dashes → underscores).
2. `mkdir -p ~/.cache/ms-playwright/<dir>`
3. Download the zip with `curl` from the matching URL in the table.
4. Unzip into the dir: `unzip -q <zip> -d ~/.cache/ms-playwright/<dir>`
5. Create both marker files: `touch ~/.cache/ms-playwright/<dir>/{INSTALLATION_COMPLETE,DEPENDENCIES_VALIDATED}`
6. Re-run `playwright install <browser>` — it should detect the markers and exit 0 without downloading.

For mirrors: if the raw CDN is unreachable even to `curl`, use a reachable mirror that serves the same build. The marker-file check is what makes `playwright install` skip the download — the content just has to be present and structurally valid.
