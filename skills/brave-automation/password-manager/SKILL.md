---
name: password-manager
description: "Import and export browser credentials as Chromium Password Manager CSVs via the baa CLI: import a CSV into the Login Data DBs, or export saved passwords back to CSV."
when-to-use: "Use when the user wants to import credentials from a CSV into local Brave/Chromium Login Data databases, or export saved browser passwords back to a CSV file. Not for headless scraping without profiles, non-Chromium browsers, or cloud password managers. Profile provisioning and Google session scripting belong to the sibling account-manager skill; setup and troubleshooting belong to brave-setup."
argument-hint: "<import | export> <path> [--profile <name>] [--csv FILE]"
---

# Password Manager (`baa password`)

You move credentials between CSV files and each Brave profile's `Login Data`
SQLite database through the `baa` CLI. `import` feeds a CSV into Chromium's
native password stores; `export` pulls saved passwords back out. Setup and
troubleshooting belong to the sibling `brave-setup` skill; profile provisioning
belongs to the sibling `account-manager` skill.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | **Profiles must exist first.** Rows whose profile is not registered land nowhere. | Unregistered profiles have no `Login Data` DB to write to. | `baa profile list` shows every profile named in the CSV before import. |
| R2 | **Idempotent import.** Re-running with the same CSV upserts, no duplicate rows. | Safe to re-run after a failed import or key rotation. | `baa password import` exits 0; row count in `Login Data` matches the CSV. |
| R3 | **Safe Storage key is per-system.** The AES key encrypting `Login Data` rows can rotate after a Brave upgrade; re-import after rotation. | Stale key produces unreadable rows. | On a `DecryptionError` during import, re-run after the key stabilizes. |
| R4 | **Close Brave before import.** A running Brave instance locks the `Login Data` DB. | File-lock errors abort the import. | No `pgrep -a brave` hits, or `baa password import` retries cleanly. |

## Routing

| File | Purpose |
|------|---------|
| [`references/import.md`](references/import.md) | `import <path>` — import a Chromium Password Manager CSV into the `Login Data` DBs. |
| [`references/export.md`](references/export.md) | `export <path>` — export saved passwords from Brave into a CSV file. |
