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
---

# Playwright Cache Restore

Restore a wiped or incomplete `~/.cache/ms-playwright/` cache, or route
`playwright install` through a reachable mirror, so headless Chromium
launches again on a network-restricted host.

## Global Rules

- **Verify dir names before placing files.** Dashes in browser names normalize to underscores on disk (Global Rules: Cache dir naming); placing in the dashed dir makes Playwright wipe it on every install. The layout table is the single home for exact dir names.
- **Create both marker files after every manual placement.** Without `INSTALLATION_COMPLETE`, Playwright re-downloads; see the marker-file rule in `cache-recovery.md`.
- **Prefer the mirror path over manual placement** when a reachable mirror or proxy exists (`PLAYWRIGHT_DOWNLOAD_HOST`); it handles the marker files automatically.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Cache layout, pitfall, markers, recovery procedure | [`references/cache-recovery.md`](references/cache-recovery.md) | Exact dir names for Playwright 1.63 revision 1243, the dash-to-underscore pitfall, marker files, and the curl-based placement procedure. |
| Verify the cache | [`references/verify.md`](references/verify.md) | Marker sweep, no-download install, headless Chromium launch check. |
| Mirror / proxy alternative | [`references/mirror.md`](references/mirror.md) | `PLAYWRIGHT_DOWNLOAD_HOST` setup and when it beats manual placement. |
