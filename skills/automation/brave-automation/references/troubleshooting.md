# Troubleshooting

**Goal:** resolve common `baa` failures quickly.

## Check in this order

1. **`baa profile list`** — are the expected profiles registered?
2. **`$XDG_STATE_HOME/baa/logs/`** — read the latest log for the exact
   exception and line number.
3. **`baa google session --profile <name>`** — is the session stale?
4. **Safe Storage key** — did Brave upgrade rotate the key? (Rule R6)

## CDP connection failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `cdp connect timeout` | Brave not running, or wrong port | `baa init` re-detects install path; confirm Brave is installed |
| `no profiles found by CDP` | Brave running with `--no-first-run` suppressing profile dir | Launch Brave normally at least once so profile dirs exist |
| Flatpak Brave: CDP unreachable | Flatpak sandbox blocks port binding | Use native or Snap Brave for CDP; Flatpak only supports session persistence via cookie files |

## `Local State` is locked

Any `ensure` or `import` that fails with a file-lock error means a Brave
instance has the file open.

```bash
# find and close all Brave processes
pgrep -a brave
pkill -f brave          # only if safe to do so
baa profile ensure      # retry
```

## Safe Storage key rotation

After a Brave upgrade, `baa password import` fails with a decryption error
even though the CSV is correct.

- The AES key lives in Brave's keychain (system `secret-service` or file-based
  depending on distribution).
- Re-import after the key stabilizes: `baa password import` again.
- If the key is irrecoverable (Brave was reinstalled), re-provision
  credentials from `passwords.csv`.

## XDG path issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `baa init` writes to wrong path | `XDG_STATE_HOME` / `XDG_DATA_HOME` unset | Export them in the shell before running `baa` |
| Permissions error on state dir | Dir created by a different user (e.g. `sudo baa init`) | Remove and re-run as the normal user |

## `profile.csv` parse errors

- CSV must be UTF-8, comma-separated, with a header row.
- `name` column values must not contain `/` or `..` (path traversal guard
  in the taxonomy).
- Run `python -c "import csv; rows=list(csv.DictReader(open('profile.csv'))); print(len(rows))"` to
  validate before `baa profile ensure`.

## Completion

- Identified failure resolved
- `baa profile list` and `baa google session` reflect expected state
