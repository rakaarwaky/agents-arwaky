# Verify

**Goal:** the service is active, enabled, reachable, and auto-restarts.

## Checks

```bash
systemctl --user is-active <name>.service   # -> active
systemctl --user is-enabled <name>.service   # -> enabled
curl -sS -o /dev/null -w "%{http_code}" http://localhost:<port>/   # -> 307 or 200
```

Kill the PID, wait `RestartSec`, confirm it auto-restarts.

## Completion

- All three checks pass.
- After a `kill -9`, `is-active` is `active` again within ~`RestartSec`.
