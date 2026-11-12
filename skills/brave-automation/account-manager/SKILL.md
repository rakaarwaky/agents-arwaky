---
name: account-manager
description: "Manage Brave browser profiles and Google sessions via the baa CLI: create, list, verify, and reset isolated accounts, plus scripted Google login, logout, and session checks."
when-to-use: "Use when the user wants to create or manage local Brave/Chromium accounts, provision or verify isolated browser profiles from profile.csv, script Google login or logout in a named profile, or check a saved Google session. Not for headless scraping without profiles, non-Chromium browsers, or cloud password managers. Setup, credential import/export, and troubleshooting belong to the sibling brave-setup and password-manager skills."
argument-hint: "<list | create | login | logout> [subcommand] [NAMES] [--profile <name>] [--email <email>] [--password <password>] [--csv FILE]"
created_by: curator
---

# Account Manager (`baa account`)

You manage local Brave/Chromium accounts through the `baa` CLI: provision isolated
profiles from `profile.csv` into Chromium's `Local State`, verify what landed, and
script Google login, logout, and session checks per profile. Setup and
troubleshooting belong to the sibling `brave-setup` skill; credential import/export
belongs to the sibling `password-manager` skill.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | **Linux + Chromium only.** Confirm the host before running anything; the shared taxonomy raises on other platforms. | Unsupported platforms produce opaque errors. | `uname -s` returns `Linux`; Brave (native, Flatpak, or Snap) is installed. |
| R2 | **One profile per account.** Each account gets its own named profile; never mix sessions or credentials across profiles. | Cross-profile leakage defeats the isolation model. | Each account maps to one profile name; no shared session storage. |
| R3 | **`profile.csv` is the source of truth.** Edit the CSV, then run the matching `baa` subcommand — never hand-edit `Local State` directly. | Manual edits are error-prone and not reproducible. | All profile changes go through `baa profile ensure` / `create`. |
| R4 | **Verify after every write.** A silent success that leaves a profile unregistered is the main failure mode. | Catch drift between CSV and live Chromium state early. | `baa profile list` shows every expected name after create/reset. |
| R5 | **Google login first may trigger a challenge.** A fresh profile can hit an email-link or app-password verification (`SessionChallenge`); resolve it once manually, then re-run login. | Google flags unknown profiles; re-running after resolution succeeds. | `baa google session <name>` reports a valid session after `login`. |

## Routing

| File | Purpose |
|------|---------|
| [`references/create.md`](references/create.md) | `create` subcommand — provision one or more accounts from `profile.csv` with `--profile`, `--email`, `--password`. |
| [`references/list.md`](references/list.md) | `list` subcommand — show every registered profile and which `profile.csv` entries are missing. |
| [`references/google-login.md`](references/google-login.md) | `login` subcommand — Google login in a named profile with session persistence. |
| [`references/google-logout.md`](references/google-logout.md) | `logout` subcommand — drop the Google session for a profile. |
