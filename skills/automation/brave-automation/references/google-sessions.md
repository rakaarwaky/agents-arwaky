# Google Sessions: Login, Logout, and Persistence

**Goal:** script Google login and logout in isolated Brave profiles and
persist the resulting session so re-authentication is not required across
runs.

## Prerequisites

- Profile already registered (see `references/profiles.md`)
- Credentials for the Google account already imported (see `references/passwords.md`)

## Commands

### Log in to Google in a named profile

```bash
baa google login --profile work
baa google login --profile work --url https://myaccount.google.com
```

Launches the named Brave profile, drives the Google OAuth flow headlessly
via CDP, and stores the session cookie into the profile's cookie store.
Exits 0 on successful auth; non-zero on failure with the error in
`$XDG_STATE_HOME/baa/logs/`.

### Check session state

```bash
baa google session --profile work
```

Reports whether the profile currently holds a valid Google session
(cookie present, not expired). Use this before re-running any task that
assumes logged-in state, to avoid unnecessary re-auth.

### Log out

```bash
baa google logout --profile work
```

Clears the Google session cookie for the profile. The local credential
entries in `Login Data` are left intact — only the active session is
dropped.

### Full lifecycle example

```bash
# 1. Provision and import
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

## Notes

- Session cookies persist in the profile's SQLite cookie store; they
  survive Brave restarts. No GUI interaction is needed after the initial
  `login`.
- If Google detects a fresh profile, the first `login` may trigger an
  additional verification step (email link or app password). The CLI
  reports this as a `SessionChallenge` error; resolve it once manually,
  then re-run `baa google login`.

## Completion

- `baa google session --profile <name>` reports a valid session after `login`
- Automation tasks run without re-prompting for credentials
