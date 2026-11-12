---
name: brave-automation
description: "baa CLI: Brave profiles, Google sessions, credentials."
when-to-use: "Use for any baa CLI task: install or repair baa, initialize the XDG workspace, create or list profiles, script Google login/logout/session checks, import or export Chromium Password Manager CSVs, or troubleshoot CDP/Local State/Safe Storage failures."
argument-hint: "<install | init | doctor | list | create | login | logout | import | export> [subcommand] [NAMES] [--profile <name>] [--email <email>] [--password <password>] [--csv FILE] [--dir PATH]"
---

# Brave Automation (`baa` CLI)

One umbrella for all Brave/Chromium browser automation through the `baa` CLI. Every job below loads its reference; the Global Rules govern every job. Split by job: install/init (setup), profile + Google session management (accounts), credential import/export (passwords).

## Global Rules

- **Linux + Chromium only.** Confirm the host before running anything. `uname -s` returns `Linux`; Brave (native, Flatpak, or Snap) is installed. Unsupported platforms produce opaque errors.
- **Never use `/tmp` for state.** Logs and sessions live under `$XDG_STATE_HOME/baa` and `$XDG_DATA_HOME/baa`. XDG compliance; state survives across runs. `baa init` output shows XDG paths; no writes to `/tmp`.
- **One workspace per host.** `baa init` is idempotent; re-running re-detects install paths without clobbering existing state. `baa init` exits 0 and XDG dirs exist under `$XDG_STATE_HOME/baa`. Re-detection after a Brave move or upgrade.
- **Verify after every write.** A silent success that leaves state unregistered is the main failure mode. `baa profile list` shows every expected name after create/reset; `baa --help` and `baa profile list` print after init. Catch drift between package install and CLI surface early.
- **Profiles must exist first.** Rows whose profile is not registered land nowhere; no `Login Data` DB to write to. `baa profile list` shows every profile named in the CSV before import. Unregistered profiles have no database.
- **Close Brave before import.** A running Brave locks the `Login Data` DB. No `pgrep -a brave` hits, or `baa password import` retries cleanly. File-lock errors abort the import.
- **Safe Storage key is per-system.** The AES key encrypting `Login Data` rows can rotate after a Brave upgrade; re-import after rotation. On `DecryptionError` during import, re-run after the key stabilizes. Stale key produces unreadable rows.

## Jobs (labeled subsections)

### 1. Setup — install, initialize, troubleshoot
Install the `baa` CLI from the `tools/` project with `uv` and verify console scripts. Initialize the XDG state/data workspace and configure `profile.csv` / `passwords.csv`. Repair CDP connection failures, `Local State` locks, Safe Storage key rotation, and XDG path issues.

- **Install:** verify `baa --help` and `baa profile list` both print their trees; no `ModuleNotFoundError`. A silent install that leaves the console script unresolvable is the main failure mode.
- **Init:** `baa init` is idempotent. Re-run after a Brave move or upgrade to re-detect install paths.
- **Troubleshoot:** CDP connection failures, `Local State` locks, Safe Storage key rotation, XDG path issues.

### 2. Accounts — profiles and Google sessions
Provision isolated profiles from `profile.csv` into Chromium's `Local State`. Script Google login, logout, and session checks per profile.

- **One profile per account.** Never mix sessions or credentials across profiles; cross-profile leakage defeats isolation.
- **`profile.csv` is the source of truth.** Edit the CSV, then run the matching `baa` subcommand — never hand-edit `Local State` directly.
- **Google login may trigger a challenge.** A fresh profile can hit an email-link or app-password verification (`SessionChallenge`); resolve once manually, then re-run login. `baa google session <name>` reports a valid session after `login`.

### 3. Passwords — credential import/export
Move credentials between CSV files and each Brave profile's `Login Data` SQLite database.

- **Idempotent import.** Re-running with the same CSV upserts, no duplicate rows. Safe to re-run after a failed import or key rotation.
- **Import feeds CSV into Chromium's native password stores; export pulls saved passwords back out.**

## References

| Topic | File | Purpose |
|-------|------|---------|
| Install | `references/install.md` | Install `baa` CLI from `tools/` with `uv`; verify console scripts. |
| Init | `references/init.md` | Initialize XDG workspace; configure `profile.csv` / `passwords.csv`. |
| Troubleshooting | `references/troubleshooting.md` | CDP failures, `Local State` locks, Safe Storage rotation, XDG path issues. |
| Create | `references/create.md` | `create` subcommand — provision accounts from `profile.csv`. |
| List | `references/list.md` | `list` subcommand — show registered profiles and missing CSV entries. |
| Google login | `references/google-login.md` | `login` subcommand — Google login in a named profile with session persistence. |
| Google logout | `references/google-logout.md` | `logout` subcommand — drop the Google session for a profile. |
| Import | `references/import.md` | `import <path>` — import a Chromium Password Manager CSV into `Login Data` DBs. |
| Export | `references/export.md` | `export <path>` — export saved passwords from Brave to a CSV file. |
