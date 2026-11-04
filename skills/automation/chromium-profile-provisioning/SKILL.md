---
name: chromium-profile-provisioning
description: Use when creating, inspecting, or fixing Brave/Chromium profile dirs, Local State info_cache, user-data locations, or provisioning profiles alongside the Bitwarden CLI. Not driving pages.
when-to-use: Use when a tool must see or create browser profiles deterministically, when editing Local State or Preferences with a closed browser, when probing user-data dirs under native, Flatpak, Snap, or macOS installs, or when wiring NAME|user|pass|url envs into vault items plus browser profiles. Not for driving pages.
argument-hint: "<create | inspect> <profile-name> [user-data-dir] [--dry-run] [--yes]"
metadata:
  tags:
    - browser
    - chromium
    - brave
    - automation
    - python
---

# Provisioning Chromium/Brave browser profiles

You create, inspect, and repair Brave/Chromium profile directories and their
`Local State` registry — never driving pages. A tool that must see or create
profiles deterministically writes the registry itself, because a freshly
launched profile dir is invisible to `Local State` readers until the browser
registers it.

## Global rules

- **Profile = dir AND registry entry.** A profile is real only when both the
  directory and its `Local State` `info_cache` registration exist; registry
  edits lose to a browser that rewrites `Local State` on exit.
- **Edit only a provably-closed browser.** Liveness is decided by the
  `SingletonSocket` connect probe, never by the `SingletonLock` pid — under
  flatpak that pid is sandbox-internal and `os.kill` on it wedges the guard.
- **One parser for the env format.** A `NAME|user|pass|url` env feeding two
  subsystems is parsed in exactly one module; shell-sourcing it is forbidden.
- **Validate names before filesystem use.** Reject `/`, `\`, `..`, and leading
  `-`; the dir name gets re-injected as a browser flag.

## Routing

| Topic | Reference | Purpose |
| ----- | --------- | ------- |
| Registry semantics & locations | [`references/registry-and-locations.md`](references/registry-and-locations.md) | What makes a profile real, user-data dir probe order, the closed-browser gate. |
| Creating a profile | [`references/create-profile.md`](references/create-profile.md) | 4-step registry write, correctness traps, fake-tree testing. |
| Env format & Bitwarden CLI | [`references/env-and-bitwarden.md`](references/env-and-bitwarden.md) | Single-parser rule, `NAME|user|pass|url` semantics, pinned `bw` setup. |
