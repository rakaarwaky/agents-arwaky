# Create — Provision Accounts from profile.csv

**Goal:** register one or more isolated Brave profiles from `profile.csv` rows,
confirm they exist on disk, and leave `Local State` consistent.

## Inputs

- `profile.csv` (or `--csv FILE`) with columns: `name`, `email`, `label`.
  `name` must be unique and contain no `/` or `..` (path-traversal guard).
- `--profile <name>` targets a single account; omit for all rows.

## Commands

```bash
# Provision all accounts in profile.csv
baa profile ensure

# Provision one account
baa profile ensure work

# Use an alternative CSV
baa profile ensure --csv other.csv

# Dry-run: print what would be created without touching Local State
baa profile ensure --dry-run

# Skip the safety prompt when Brave appears to be running
baa profile ensure -y

# Remediate drift between Local State/disk and profile.csv
baa profile ensure --strict --auto-fix
baa profile ensure --strict --prune
```

`ensure` creates the profile directory, writes the `Local State` entry, and
registers the profile without launching Brave. Idempotent: re-running with an
unchanged CSV produces no new writes.

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Profile not in `baa profile list` after `ensure` | `Local State` locked by a running Brave instance | Close all Brave windows (`pgrep -a brave`), re-run `ensure` |
| `ensure` raises `FileNotFoundError` | Brave not installed or wrong install path detected | Confirm Brave binary location; pass install path if needed |
| Duplicate-name error | Two rows in `profile.csv` share the same `name` | Rename one row |

## Completion

- `baa profile list` shows every expected profile name
- Each profile directory exists on disk under Brave's Profiles path
