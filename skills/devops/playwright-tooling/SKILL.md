---
name: playwright-tooling
description: Recover Playwright browser cache on restricted hosts.
when-to-use: "Use when playwright install times out on a network-restricted host, manually placed browser dirs are wiped every run, or headless-shell/FFmpeg is missing from the Playwright cache."
argument-hint: "[<browser>]"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [playwright, chromium, cache, network, browser-automation]
    related_skills: [qwen-web]
---

# Playwright Tooling

Playwright browser infrastructure: cache recovery, headless Chromium setup, and mirror routing for network-restricted hosts.

## When to Use

- `playwright install` times out or fails on GFW/corporate proxy/data-cap hosts.
- `curl` reaches the CDN but Playwright's Node fetch cannot.
- Browser dirs are wiped on each `playwright install` run.
- headless-shell or FFmpeg is missing from `~/.cache/ms-playwright/`.

## Global Rules

- **Verify dir names before placing files.** Dashes in browser names normalize to underscores on disk; placing in the dashed dir makes Playwright wipe it on every install.
- **Create both marker files after every manual placement.** Without `INSTALLATION_COMPLETE`, Playwright re-downloads.
- **Prefer the mirror path over raw CDN** when the CDN is reachable by `curl` but not by Playwright's Node fetch client.
- **Cache dir naming is the single source of truth** for exact directory names — see the layout table in `references/cache-layout.md`.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Cache layout + recovery | [`references/cache-layout.md`](references/cache-layout.md) | Dir names, marker files, CDN-unreachable recovery procedure. |
| Verification | [`references/verify.md`](references/verify.md) | Post-placement checks: marker presence, install exit 0, headless launch. |
