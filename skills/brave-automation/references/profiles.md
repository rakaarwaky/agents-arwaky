# Profiles: Provision, List, and Verify

**Goal:** register Brave profiles into Chromium's `Local State` from `profile.csv`
and confirm they exist on disk.

## Commands

### List current profiles

```bash
baa profile list
```

Shows every profile registered in `Local State` plus its on-disk path.
Use this after every provisioning or import run (Rule R5).

### Ensure profiles from CSV

```bash
baa profile ensure                     # all profiles in profile.csv
baa profile ensure work personal        # only the named profiles
baa profile ensure --csv other.csv      # alternative CSV path
```

Creates the profile directory, writes the `Local State` entry, and registers
the profile without launching Brave. Idempotent: re-running with unchanged
CSV produces no new writes.

### Verify

```bash
baa profile list
```

Each name in `profile.csv` should appear. Missing names indicate a CSV
parse failure or a name collision — check the log in
`$XDG_STATE_HOME/baa/logs/`.

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Profile not in `baa profile list` after `ensure` | `Local State` locked by a running Brave instance | Close all Brave windows, re-run `ensure` |
| `ensure` raises `FileNotFoundError` | Brave not installed or wrong install path detected | Confirm Brave binary location; pass install path if needed |
| Duplicate-name error | Two rows in `profile.csv` share the same `name` | Rename one row |

## Completion

- `baa profile list` shows every expected profile name
- Each profile directory exists on disk under Brave's Profiles path
