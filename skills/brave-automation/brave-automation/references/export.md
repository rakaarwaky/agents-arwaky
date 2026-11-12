# Export — Pull Saved Passwords Back to CSV

**Goal:** export every saved credential from the Brave profiles (and any
configured `passwords.csv`) into a single Chromium-compatible CSV file.

## Commands

```bash
# Export all Brave and configured passwords into the default passwords.csv
baa password export

# Write to an alternative destination
baa password export -o out.csv

# Merge an existing credentials CSV into the export
baa password export --csv existing.csv -o merged.csv

# Export into a specific directory
baa password export --all-dir exports/
```

Produces one file matching the native Chromium "Passwords" CSV format, usable
for manual import via Brave's UI or for re-seeding another host.

## Prerequisites

- At least one profile has credentials registered (sibling `account-manager` skill)

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Export produces fewer rows than expected | `Login Data` DB locked or key rotated | Close Brave; re-run after key stabilizes |
| `DecryptionError` on some rows | Safe Storage key rotated since import | Re-import (sibling) after key stabilizes, then re-export |

## Completion

- `baa password export` exits 0
- The destination CSV exists and parses with the expected header row
