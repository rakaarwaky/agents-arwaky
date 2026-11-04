# Cache recovery: layout, marker files, placement

Cache layout for Playwright 1.63 (revision 1243); exact dir names, marker files, and the recovery procedure for a CDN that `curl` can reach but Playwright's Node client cannot.

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

`curl` typically succeeds where Playwright's Node.js fetch times out
(see the why-it-fails reference).

```bash
# 1. Identify what's missing
ls ~/.cache/ms-playwright/
# Expected: chromium-1243, chromium_headless_shell-1243, ffmpeg-1011

# 2. For each missing component, download via curl and place in the CORRECT dir
# Example: chromium-headless-shell (underscore dir!)
mkdir -p ~/.cache/ms-playwright/chromium_headless_shell-1243
curl -fSL --max-time 600 -o /tmp/chhs.zip \
  "https://cdn.playwright.dev/builds/cft/153.0.8010.12/linux64/chrome-headless-shell-linux64.zip"
unzip -o /tmp/chhs.zip -d ~/.cache/ms-playwright/chromium_headless_shell-1243/
touch ~/.cache/ms-playwright/chromium_headless_shell-1243/INSTALLATION_COMPLETE \
      ~/.cache/ms-playwright/chromium_headless_shell-1243/DEPENDENCIES_VALIDATED
rm /tmp/chhs.zip

# 3. For ffmpeg
mkdir -p ~/.cache/ms-playwright/ffmpeg-1011
curl -fSL --max-time 120 -o /tmp/ffmpeg.zip \
  "https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-linux.zip"
unzip -o /tmp/ffmpeg.zip -d ~/.cache/ms-playwright/ffmpeg-1011/
touch ~/.cache/ms-playwright/ffmpeg-1011/INSTALLATION_COMPLETE \
      ~/.cache/ms-playwright/ffmpeg-1011/DEPENDENCIES_VALIDATED
rm /tmp/ffmpeg.zip
```

## Why the Node client fails but curl works

Playwright's browser download uses Node.js `https` with a **hard 30s
per-request timeout** (`clientRequestTimeout`). On slow or throttled
connections (GFW, corporate proxy, data caps), the download never
completes within 30s and the whole install aborts. `curl` with
`--max-time 600` and `--continue-at -` can resume after partial
downloads, so it succeeds where the Node client cannot.

## Completion

- Each expected dir in the layout table exists, in the exact name shown (underscores where the table shows them).
- `INSTALLATION_COMPLETE` and `DEPENDENCIES_VALIDATED` exist in every dir.
- The verification commands in `verify.md` pass.
