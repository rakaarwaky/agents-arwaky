---
name: flatpak-chromium-automation
description: Drive Flatpak Chromium CDP and manage profiles.
when-to-use: Use when CDP debugging of a Flatpak browser fails to bind its port, when orphan Flatpak instances hijack a debug launch, when pkill/pgrep patterns threaten the agent shell, when adding a Web Store extension that cannot be clicked through, or when a tool must see or create browser profiles deterministically, when editing Local State or Preferences with a closed browser, when probing user-data dirs under native, Flatpak, Snap, or macOS installs. Not for driving non-Flatpak browsers.
argument-hint: "<appid | ext-id | cmd | create | inspect>"
metadata:
  tags:
    - browser
    - chromium
    - brave
    - flatpak
    - automation
    - python
---

# Automating flatpak-packaged Chromium browsers

You drive Flatpak-packaged Brave/Chromium over CDP from the host, install Web
Store extensions unpacked, and manage (create, inspect, fix) the underlying
brave/chromium profile dirs and `Local State` — the three things that break
when the sandbox is in the way or when a tool must see profiles deterministically.

## Global rules

- **The sandbox sees only `/tmp` and `~/.var/app/<APPID>/`** — host `/etc` and
  `~/.config` policy paths silently load nothing; verify with `chrome://policy`
  over CDP.
- **Break every pkill/pgrep pattern with a bracket class** (`"92[3]3"`) so the
  agent shell's own command line cannot match.
- **The "Add extension" prompt is a native window** — it is in no CDP target,
  DOM, or accessibility tree; never burn time trying to click it.
- **`--load-extension` is per-launch only** — no verified per-profile
  permanent install path exists under flatpak yet; any "permanent" claim needs
  a fresh-launch verification that the extension installed under its official
  ID.

## Routing

| Topic | Reference | Purpose |
| ----- | --------- | ------- |
| Sandbox paths & launch | [`references/sandbox-paths-and-launch.md`](references/sandbox-paths-and-launch.md) | Which paths the browser can see, orphan-instance cleanup, pkill self-match guard. |
| CRX fetch & unpack | [`references/crx-fetch.md`](references/crx-fetch.md) | Download endpoint, CRX3/CRX2 binary layout, unpacked-dir ID caveat. |
| Profile provisioning | [`references/profile-provisioning.md`](references/profile-provisioning.md) | Create/inspect/fix Brave/Chromium profiles: `Local State` `info_cache` registry, user-data dir locations, Bitwarden CLI companion setup. |
