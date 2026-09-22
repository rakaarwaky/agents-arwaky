---
name: omniroute-gateway
description: Use when managing, configuring, or debugging the local OmniRoute AI Gateway service (host-native, localhost:7777).
metadata:
  tags: []
---

# OmniRoute AI Gateway (localhost:7777)

## Architecture Facts

- Runs as systemd user service `omniroute.service`
  (`~/.config/systemd/user/omniroute.service`).
- The service runs the host-native `omniroute` binary (installed via
  `npm install -g omniroute`). No Podman container is involved.
  `systemctl --user restart omniroute.service` is the supported way to
  bounce it.
- Config/env vars live in `~/.omniroute/.env`. The port is set there as
  `PORT=7777` (default OmniRoute port is 20128; this setup overrides it to 7777).
- Data directory: `~/.omniroute/` — the SQLite database is
  `~/.omniroute/storage.sqlite` (with `-wal`/`-shm` siblings).

## Key database tables

- `combos`: Custom model route aggregations.
- `apiKeys`: OmniRoute API keys accepted by `/v1/chat/completions`.
- `usageHistory`: Per-request token counts, cost, and model stats.

Query read-only:

```bash
DB="$HOME/.omniroute/storage.sqlite"
sqlite3 "file:$DB?mode=ro" ".tables"
```

## Authentication

- Requests to `http://localhost:7777/v1/chat/completions` require an API
  key Bearer header: `Authorization: Bearer <API_KEY>`.
- Environment variable used across harness profiles: `OMNIROUTE_KEY`.

## Diagnostic Workflow

1. **Check service status:**
   ```bash
   systemctl --user status omniroute.service
   ```
   Restart: `systemctl --user restart omniroute.service`

2. **Confirm the API endpoint is alive:**
   ```bash
   curl -s http://localhost:7777/v1/models | jq '.data[].id'
   ```

3. **Test chat completion with API key:**
   ```bash
   curl -s -X POST http://localhost:7777/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $OMNIROUTE_KEY" \
     -d '{
       "model": "auto",
       "messages": [{"role": "user", "content": "ping"}],
       "max_tokens": 20
     }'
   ```

4. **Inspect recent logs:**
   ```bash
   journalctl --user -u omniroute.service -n 50 --no-pager
   ```
