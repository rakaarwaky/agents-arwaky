# Passwords: Generate CSV and Import into Login Data DBs

**Goal:** turn `passwords.csv` into Chromium-compatible password manager CSVs
and import credentials directly into each profile's `Login Data` SQLite
database, encrypted with the system Brave Safe Storage AES key.

## Workflow

```text
passwords.csv
  │
  ▼
baa password generate   ──►  out/*.csv   (one CSV per profile)
  │
  ▼
baa password import     ──►  Login Data DBs (per profile)
```

## Commands

### Generate Chromium Password Manager CSVs

```bash
baa password generate                       # uses default passwords.csv
baa password generate --csv other.csv       # alternative input path
```

Writes one CSV per profile into the output directory (default:
`$XDG_DATA_HOME/baa/exports/`). Each file matches the native
Chromium "Passwords" CSV format and can also be imported manually via
Brave's UI if desired — but the CLI path skips the UI entirely.

### Import into Login Data DBs

```bash
baa password import                          # import all generated CSVs
baa password import --profile work           # import for one profile only
```

Opens each profile's `Login Data` SQLite DB, decrypts existing rows with
the current Safe Storage key, upserts the new credentials, and writes back.
Idempotent: re-running with the same CSV produces no duplicate rows.

### Wipe credentials for a profile

```bash
baa password wipe --profile ci
```

Removes all imported rows for the named profile. Use before
decommissioning a profile.

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `DecryptionError` during import | Safe Storage key rotated (Brave upgrade) | Re-provision or re-import after the key stabilizes (Rule R6) |
| Rows present in CSV but missing after import | Profile not registered yet | Run `baa profile ensure` first |
| `sqlite3.OperationalError: database is locked` | Brave has the profile open | Close Brave, re-run import |

## Completion

- `baa password generate` exits 0 and output CSVs exist
- `baa password import` exits 0
- Row count in `Login Data` matches `passwords.csv` row count (query the DB with `sqlite3` if needed)
