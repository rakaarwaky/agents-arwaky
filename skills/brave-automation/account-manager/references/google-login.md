# Login — Google Authentication in a Named Profile

**Goal:** script Google login in an isolated Brave profile and persist the
resulting session cookie so re-authentication is not required across runs.

## Prerequisites

- Profile already registered (see `references/create.md`)
- Credentials for the Google account already imported into `Login Data`
  (sibling `password-manager` skill)

## Commands

```bash
# Login in a named profile (drives OAuth headlessly via CDP)
baa google login --profile work

# Target a specific Google URL
baa google login --profile work --url https://myaccount.google.com

# Login all profiles in profile.csv with a delay between them
baa google login --csv profile.csv --delay 5.0

# Run headless (no visible browser window)
baa google login --profile work --headless

# Do not persist the session cookie
baa google login --profile work --no-session

# Remediate profile drift before login
baa google login --profile work --strict --auto-fix
```

Exits 0 on successful auth; non-zero on failure with the error in
`$XDG_STATE_HOME/baa/logs/`.

## Check session state

```bash
baa google session --profile work
```

Reports whether the profile currently holds a valid Google session
(cookie present, not expired). Use before re-running any task that assumes
logged-in state.

## Session challenge

If Google detects a fresh profile, the first `login` may trigger an additional
verification step (email link or app password). The CLI reports this as a
`SessionChallenge` error; resolve it once manually, then re-run
`baa google login`.

## Completion

- `baa google session --profile <name>` reports a valid session after `login`
- Automation tasks run without re-prompting for credentials
