# Logout — Drop the Google Session for a Profile

**Goal:** clear the active Google session cookie for a named profile while
leaving local credential entries in `Login Data` intact.

## Commands

```bash
# Log out one profile
baa google logout --profile work

# Log out all profiles
baa google logout

# Run headless
baa google logout --profile work --headless
```

The local credential entries in `Login Data` are left intact — only the active
session is dropped. To fully decommission an account, follow with
`baa password wipe --profile <name>` (sibling `password-manager` skill).

## Full lifecycle example

```bash
# 1. Provision and import (sibling skills)
baa profile ensure work
baa password import --profile work

# 2. Verify credentials landed
baa google session --profile work   # expect: no session yet

# 3. Authenticate once
baa google login --profile work

# 4. Subsequent runs: just check
baa google session --profile work   # expect: valid session
# ...run automation...

# 5. Decommission
baa google logout --profile work
baa password wipe --profile work
```

## Completion

- `baa google session --profile <name>` reports no session after `logout`
- Credential rows in `Login Data` are unchanged (query with `sqlite3` if needed)
