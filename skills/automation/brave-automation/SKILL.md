---
name: brave-automation
description: Drive the local baa CLI to provision Brave profiles from CSV, import credentials into Chromium's native Login Data DBs, and persist Google sessions in isolated profiles.
when-to-use: Use when the user wants to set up or manage local Brave/Chromium browser profiles for automation, bulk-provision accounts from profile.csv or passwords.csv, generate Chromium Password Manager CSV imports, wipe or sync credentials across profiles, or script Google login/logout with persisted sessions. Not for headless scraping without profiles, non-Chromium browsers, or cloud password managers.
argument-hint: "<init | profile | password | google | session> [subcommand] [--csv FILE] [NAMES]"
metadata:
  tags:
    - brave
    - chromium
    - profiles
    - password-manager
    - google
    - linux
    - xdg
---

# Brave Automation (`baa`)

You automate local Brave/Chromium browser profile provisioning and credential management
via the `baa` CLI. All work runs on Linux with Python 3.10+ and the `baa` console
script installed from the `app/` project in this skill folder. Pipeline:
init workspace → ensure profiles → generate password CSV → import into Login Data DBs →
persist Google sessions. No GUI, no third-party extensions, no cloud password manager.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | **Linux + Chromium only.** The `baa` shared taxonomy raises on non-Linux platforms and non-Chromium browsers. Confirm the target host is Linux before running anything. | Unsupported platforms produce opaque errors. | `uname -s` returns `Linux`; Brave/Chromium is installed. |
| R2 | **Never use `/tmp` for state.** Logs and sessions live under `$XDG_STATE_HOME/baa` and `$XDG_DATA_HOME/baa`. Output a reviewer must find goes there, not `/tmp`. | XDG compliance; state survives across runs. | `baa init` output shows XDG paths; no writes to `/tmp`. |
| R3 | **CSV input is the source of truth.** `profile.csv` drives profile provisioning; `passwords.csv` drives credential imports. Edit the CSVs, then run the matching `baa` subcommand — never hand-edit Chromium's `Local State` or `Login Data` SQLite files directly. | Manual file edits are error-prone and not reproducible. | All profile/credential changes go through `baa profile ensure` / `baa password generate` / import subcommands. |
| R4 | **Isolated profiles per account.** Each automated task or account gets its own named profile. Do not mix sessions or credentials across profiles. | Cross-profile leakage defeats the isolation model. | Each account maps to one profile name; no shared session storage. |
| R5 | **Verify with `baa profile list` after any provisioning or import.** A silent success that leaves a profile unregistered or a credential unimported is the main failure mode. | Catch drift between CSV and live Chromium state early. | `baa profile list` shows the expected names; credential count matches `passwords.csv`. |
| R6 | **Safe Storage key is per-system.** The AES key used to encrypt Login Data entries comes from the system Brave Safe Storage. After a Brave upgrade or key rotation, re-import credentials. | Stale key produces unreadable Login Data rows. | If `baa password import` fails with a decryption error, re-run after Brave update or re-provision. |

## Routing

| File | Purpose |
|------|---------|
| [`references/setup.md`](references/setup.md) | Install `baa`, run `baa init`, locate and edit `profile.csv` / `passwords.csv`. |
| [`references/profiles.md`](references/profiles.md) | Provision, list, and verify Brave profiles from CSV. |
| [`references/passwords.md`](references/passwords.md) | Generate Chromium Password Manager CSVs and import credentials into Login Data DBs. |
| [`references/google-sessions.md`](references/google-sessions.md) | Google login, logout, and session persistence across isolated profiles. |
| [`references/troubleshooting.md`](references/troubleshooting.md) | Safe Storage key errors, profile not appearing, CDP connection failures, XDG path issues. |
