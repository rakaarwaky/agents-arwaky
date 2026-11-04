---
name: flatpak-chromium-automation
description: Use when driving Flatpak Brave/Chromium pages under sandbox paths over CDP, or installing Web Store extensions unpacked. Not profile setup.
when-to-use: Use when CDP debugging of a Flatpak browser fails to bind its port, when orphan Flatpak instances hijack a debug launch, when pkill/pgrep patterns threaten the agent shell, or when adding a Web Store extension that cannot be clicked through. Not for creating or provisioning browser profiles.
argument-hint: "<appid | ext-id | cmd>"
metadata:
  tags:
    - browser
    - chromium
    - brave
    - flatpak
    - automation
---

# Automating flatpak-packaged Chromium browsers

You drive Flatpak-packaged Brave/Chromium over CDP from the host and install
Web Store extensions unpacked — the two things that break when the sandbox is
in the way. Profile setup is out of scope.

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
