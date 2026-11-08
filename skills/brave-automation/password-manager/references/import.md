# Import — Feed a CSV into the Login Data DBs

**Goal:** turn a Chromium Password Manager CSV into credentials persisted in
each named profile's `Login Data` SQLite database, encrypted with the system
Brave Safe Storage AES key.

## Prerequisites

- The target profiles are registered (sibling `account-manager` skill)
- Brave is not running (Rule R4) — a running instance locks the `Login Data` DB

## Commands

```bash
# Import the default passwords.csv into all Brave profiles
baa password import

# Import an alternative CSV
baa password import --csv other.csv

# Validate the CSV without writing to any browser database
baa password import --no-sync
```

Opens each profile's `Login Data` SQLite DB, decrypts existing rows with the
current Safe Storage key, upserts the new credentials, and writes back.
Idempotent: re-running with the same CSV produces no duplicate rows.

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `DecryptionError` during import | Safe Storage key rotated (Brave upgrade) | Re-import after the key stabilizes (Rule R3) |
| Rows present in CSV but missing after import | Profile not registered yet | Run `baa profile ensure` first |
| `sqlite3.OperationalError: database is locked` | Brave has the profile open | Close Brave, re-run import |

## Completion

- `baa password import` exits 0
- Row count in `Login Data` matches the CSV (query with `sqlite3` if needed)
