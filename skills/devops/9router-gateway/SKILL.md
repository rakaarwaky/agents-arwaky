---
name: 9router-gateway
description: "Use when managing, configuring, or debugging the local 9Router AI Gateway service (localhost:20128)."
---
# 9Router AI Gateway (localhost:20128)

## Architecture Facts

- Runs as systemd user service `9router.service` (`~/.config/systemd/user/9router.service`).
- The service does **not** run a host binary — it runs a **Podman container** named
  `9router` from `ghcr.io/decolua/9router:latest` with `--network=host`, so the
  gateway listens directly on the host port. `ExecStop` is `podman stop`, and
  `ExecStartPre` pre-cleans a stale container, so `systemctl --user restart
  9router.service` is the supported way to bounce it.
- Secrets/config come from `EnvironmentFile=%h/agents-arwaky/tools/config/ninerouter.env`
  (do not echo its contents; it carries the initial admin password).
- Port / Base URL: `http://localhost:20128/v1`
- Data directory: host `~/.local/share/9router/data/`, bind-mounted to `/app/data`
  in the container (`DATA_DIR=/app/data`). There is **no** `~/.9router/`.
  - Authoritative SQLite database: `~/.local/share/9router/data/db/data.sqlite`
    (queryable from the host — it is a normal file; expect `-wal`/`-shm` siblings).
  - Logs: journald (the container logs with `-l journald`), read them with
    `journalctl --user -u 9router.service`.
- Key tables in `~/.local/share/9router/data/db/data.sqlite`:
  - `combos`: Custom model route aggregations (e.g. `my9router`, `9vision`). Columns: `id`, `name`, `kind`, `models` (JSON array of provider model IDs).
  - `providerConnections`: Configured accounts & credentials for providers (Bai, KGW, OpenCode, etc.).
  - `providerNodes`: External/internal provider node definitions.
  - `apiKeys`: 9Router API keys accepted by `/v1/chat/completions`. Columns: `id`, `key`, `name`, `machineId`, `isActive`, `createdAt`.
  - `usageHistory` & `usageDaily`: Per-request token counts, cost, timestamps, and model stats.
  - `settings`: Global configuration options in JSON format.
  - `kv`: Key-value scoped configurations.
  - Also present: `proxyPools`, `requestDetails`, `_meta`.

Open the database read-only so you never race the running container's writer:

```bash
DB="$HOME/.local/share/9router/data/db/data.sqlite"
sqlite3 "file:$DB?mode=ro" ".tables"
```

## Authentication

- Requests to `http://localhost:20128/v1/chat/completions` require an API Key Bearer header:
  `Authorization: Bearer <API_KEY>`
- Environment variable used across Hermes profiles: `HERMES_CUSTOM_9ROUTER_API_KEY`.
- Keys can be inspected in the database (the `key` column holds the live secret —
  list which entries exist, don't dump values into logs or transcripts):
  ```bash
  sqlite3 "file:$HOME/.local/share/9router/data/db/data.sqlite?mode=ro" \
    "SELECT id, name, isActive FROM apiKeys;"
  ```

## Diagnostic Workflow

1. **Check Service Status:**
   ```bash
   systemctl --user status 9router.service
   ```
   To restart: `systemctl --user restart 9router.service`

2. **Confirm API Endpoint is Alive:**
   ```bash
   curl -s http://localhost:20128/v1/models | jq '.data[].id'
   ```

3. **Test Chat Completion with API Key:**
   ```bash
   curl -s -X POST http://localhost:20128/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $HERMES_CUSTOM_9ROUTER_API_KEY" \
     -d '{
       "model": "my9router",
       "messages": [{"role": "user", "content": "ping"}],
       "max_tokens": 20
     }'
   ```

4. **Inspect Combos in Database:**
   ```bash
   sqlite3 "file:$HOME/.local/share/9router/data/db/data.sqlite?mode=ro" \
     "SELECT id, name, models FROM combos;"
   ```

5. **Inspect Recent Error Logs / Requests:**
   ```bash
   sqlite3 "file:$HOME/.local/share/9router/data/db/data.sqlite?mode=ro" \
     "SELECT timestamp, provider, model, status, promptTokens, completionTokens FROM usageHistory ORDER BY id DESC LIMIT 10;"
   ```
   Or journald (the container logs to the unit, there is no log directory):
   ```bash
   journalctl --user -u 9router.service -n 50 --no-pager
   ```
   Container-side alternatives: `podman ps --filter name=9router` to confirm it is
   up, `podman logs 9router` for the raw app output.
