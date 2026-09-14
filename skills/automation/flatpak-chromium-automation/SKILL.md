---
name: flatpak-chromium-automation
description: Use when automating flatpak Brave/Chromium browsers.
metadata:
  tags: [browser, chromium, brave, flatpak, automation]
---

# Automating flatpak-packaged Chromium browsers

## Which paths the browser process can actually see

The sandbox does NOT bind host `/etc` or `~/.config` (outside `~/.var/app/...`):
`/etc/brave/policies/managed/*.json` and `--policy-directory=/home/<user>/.config/...`
silently load nothing (verify via `chrome://policy` over CDP — statuses come
back as errors/not-listed rather than an exception). Paths that ARE visible:
anything under `/tmp` or `~/.var/app/<APPID>/`. Probe without launching:
`flatpak run --command=ls <APPID> <path>`.

## Orphan instances hijack your debug launch

A live browser owns the user-data dir singleton, so a fresh
`flatpak run com.brave.Browser --remote-debugging-port=... --profile-directory=...`
just hands off to the running instance and exits: no port listens, no error,
and it looks like "flatpak breaks CDP". CDP works fine from the host
(127.0.0.1) once the launch is genuinely first-in. Before launching debug
sessions, check `flatpak ps` and probe the target dir's `SingletonSocket`;
killing the `flatpak run` wrapper does NOT kill the browser — clean up with
`flatpak kill <instance-id>`, and re-verify with `pgrep -f "[/]app/brave/brave"`
(`[/]` bracket so the pattern cannot match your own shell, see below).

## pkill/pgrep self-match kills your own shell

`pkill -f "remote-debugging-port=9233"` issued from an agent shell matches the
shell's own command line (it contains that string) and SIGTERMs the command
mid-run. Always break the pattern with a bracket class: `pkill -f "92[3]3"`.

## Extension install without clicking anything

Brave/Chromium's "Add extension" prompt is a NATIVE window — it is not in any
CDP target, page DOM, or accessibility tree reachable via
`connect_over_cdp`/Playwright, so web-store install flows are not automatable.
Do not burn time trying to click it.

Working method (verified end-to-end): fetch the official CRX by extension id
from the update endpoint, unpack it, and launch with
`--load-extension=<dir> --disable-extensions-except=<dir>`. The MV3 service
worker appears in `/json/list` and the extension popup runs normally under
CDP. Endpoint + CRX3/CRX2 binary layout, and the caveat that unpacked dirs get
path-derived IDs instead of the store ID: `references/crx-fetch.md`.

`--load-extension` is per-launch only; there is no verified per-profile
permanent install path in the flatpak sandbox yet (External Extensions with
`external_crx` and policy force-install both failed to take here) — treat any
"permanent" claim as needing a fresh-launch verification that the extension
got installed under its official ID.
