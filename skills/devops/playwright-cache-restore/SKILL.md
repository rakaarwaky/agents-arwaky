---
name: playwright-cache-restore
description: "Restore Playwright browser cache (Chromium, headless shell, FFmpeg) when the CDN is unreachable or `playwright install` times out. Use when `playwright install chromium` fails on a network-restricted host, manually placed browser dirs are wiped every run, or headless-shell/FFmpeg is missing from `~/.cache/ms-playwright/`."
when-to-use: "Use when `playwright install` times out or fails on GFW/corporate proxy/data-cap hosts, `curl` reaches the CDN but Playwright's Node fetch cannot, browser dirs are wiped on each run, or headless-shell/FFmpeg is missing."
argument-hint: "[<browser>]"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  tags:
    - playwright
    - chromium
    - cache
    - network
    - browser-automation
  related_skills:
    - qwen-web
    - qwen-web-arwaky-dev
---

## When to Use

- `playwright install chromium` times out or fails on a network-restricted host (GFW, corporate proxy, data caps).
- Manually placed browser dirs keep getting wiped by `playwright install` on every run.
- `python -m playwright install` reports "Failed to download" but `curl` can reach the CDN.
- Chromium headless-shell or FFmpeg missing from `~/.cache/ms-playwright/` while the main Chromium binary is present.

## Cache Layout (Playwright 1.63, revision 1243)

| Component | Cache dir name | Download URL |
|---|---|---|
| chromium | `chromium-1243` | `https://cdn.playwright.dev/builds/cft/153.0.8010.12/linux64/chrome-linux64.zip` |
| chromium-headless-shell | `chromium_headless_shell-1243` | `https://cdn.playwright.dev/builds/cft/153.0.8010.12/linux64/chrome-headless-shell-linux64.zip` |
| ffmpeg | `ffmpeg-1011` | `https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-linux.zip` |

## Critical Pitfall: Dashes Are Normalized to Underscores

Playwright's registry (`readDescriptors` in `coreBundle.js`) does
`name.replace(/-/g, "_")` on the browser name **before** building the
directory path. So `chromium-headless-shell` revision 1243 installs to
`chromium_headless_shell-1243` (with **underscores**), not
`chromium-headless-shell-1243` (with dashes).

Placing the browser in the dashed dir causes Playwright's
`_deleteStaleBrowsers` to treat it as "unused", wipe it on every
`playwright install` run, then fail the re-download. Always verify the exact
dir name from the cache layout table above before placing files.

## Required Marker Files

Each browser cache dir must contain two zero-byte marker files:
- `INSTALLATION_COMPLETE`
- `DEPENDENCIES_VALIDATED`

Without `INSTALLATION_COMPLETE`, Playwright treats the dir as an incomplete
install and re-downloads. Create both after every manual placement.

## Recovery Procedure (CDN unreachable)

`curl` typically succeeds where Playwright's Node.js fetch times out (the
Node client uses a different network path and has a hard 30s timeout that
`curl` can exceed with `--max-time`).

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

## Verification

```bash
# All three markers present
for d in chromium-1243 chromium_headless_shell-1243 ffmpeg-1011; do
  ls ~/.cache/ms-playwright/$d/INSTALLATION_COMPLETE \
     ~/.cache/ms-playwright/$d/DEPENDENCIES_VALIDATED 2>/dev/null \
    && echo "$d OK" || echo "$d MISSING"
done

# playwright install exits 0 with no download attempt
python -m playwright install chromium
# Expected: exit 0, only BEWARE lines, no download

# Functional check: launch headless Chromium
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    print('OK:', b.version)
    b.close()
"
```

## Why Playwright's Node Client Fails but curl Works

Playwright's browser download uses Node.js `https` with a **hard 30s
per-request timeout** (`clientRequestTimeout`). On slow or throttled
connections (GFW, corporate proxy, data caps), the download never completes
within 30s and the whole install aborts. `curl` with `--max-time 600` and
`--continue-at -` can resume after partial downloads, so it succeeds where
the Node client cannot.

## Env Var Override (Alternative to Manual Placement)

If a mirror or proxy is available, set `PLAYWRIGHT_DOWNLOAD_HOST` before
running `playwright install`:

```bash
export PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
python -m playwright install chromium
```

The env var is read by Playwright's download layer and replaces the default
CDN host for all browser downloads. This is preferred over manual placement
when a mirror is reachable, since it handles marker files automatically.
