# List — Inspect Registered Profiles

**Goal:** show every profile registered in `Local State`, which ones are missing
from `profile.csv`, and their on-disk paths.

## Commands

```bash
# List all profiles and flag CSV entries that are not yet provisioned
baa profile list

# Use an alternative CSV for the missing-entries comparison
baa profile list --csv other.csv

# Target a specific browser
baa profile list --browser chromium
```

Run this after every create/reset run (Rule R4) to confirm state.

## Completion

- Every expected profile name appears in the output
- No CSV-only entries flagged missing
