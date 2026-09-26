---
name: 9router-gateway
description: Use when managing, configuring, or debugging the local 9Router AI Gateway service (host-native, localhost:20128).
metadata:
  tags: []
---

# 9Router AI Gateway (localhost:20128, host-native)

## Architecture Facts

- Runs as systemd user service `9router.service`
  (`~/.config/systemd/user/9router.service`), installed by
  `aa 9router service-install` (or `aa daemon 9router service-install`).
- **Host-native**: `ExecStart` runs the global npm binary
  `9router --port 20128 --no-browser --skip-update`. **No Podman /
  no container.**
- Secrets/config come from `EnvironmentFile=-%h/.config/agents-arwaky/ninerouter.env`
  (do not echo its contents). Template: `config/ninerouter.env.example`.
- Port / Base URL: `http://localhost:20128/v1`
- `WorkingDirectory=%h/.9router` — the app writes its own data under
  `~/.9router/` (SQLite + config live there).
  - Authoritative SQLite database: `~/.9router/db/data.sqlite`
    (queryable read-only from the host; expect `-wal`/`-shm` siblings).
  - Logs: journald — `journalctl --user -u 9router.service`.
- Process health: `pgrep -f 9router` + HTTP probe
  `GET http://127.0.0.1:20128/api/health` (a running process may return
  `401`/`403` when auth is enabled — that still counts as alive).

Key tables in `~/.9router/db/data.sqlite`:

- `combos`: custom model route aggregations (e.g. `my9router`). Columns:
  `id`, `name`, `kind`, `models` (JSON array of provider model IDs).
- `providerConnections`: configured provider accounts & credentials.
- `providerNodes`: provider node definitions.
- `apiKeys`: keys accepted by `/v1/chat/completions`. Columns: `id`, `key`,
  `name`, `machineId`, `isActive`, `createdAt`.
- `usageHistory` / `usageDaily`: per-request token counts, cost, timestamps.
- `settings`, `kv`, `proxyPools`, `requestDetails`, `_meta`.

Open the database read-only so you never race the live writer:

```bash
DB="$HOME/.9router/db/data.sqlite"
sqlite3 "file:$DB?mode=ro" ".tables"
```

## Authentication

- `POST http://localhost:20128/v1/chat/completions` requires
  `Authorization: Bearer <NINEROUTER_KEY>`.
- Session-wide exports (written by `aa connect`):
  - `NINEROUTER_URL=http://localhost:20128`
  - `NINEROUTER_KEY` (from `~/.config/agents-arwaky/ninerouter.env` or
    Dashboard → Keys).
- Harness-side names differ per tool (e.g. Hermes:
  `HERMES_CUSTOM_9ROUTER_API_KEY`).
- List key ids (don't dump secrets into logs):
  ```bash
  sqlite3 "file:$HOME/.9router/db/data.sqlite?mode=ro" \
    "SELECT id, name, isActive FROM apiKeys;"
  ```

## Diagnostic Workflow

1. **Service status / restart**
   ```bash
   aa 9router status
   systemctl --user status 9router.service
   systemctl --user restart 9router.service
   ```

2. **Confirm API is alive**
   ```bash
   curl -s http://localhost:20128/api/health
   curl -s -H "Authorization: Bearer $NINEROUTER_KEY" \
     http://localhost:20128/v1/models | jq '.data[].id'
   ```

3. **Chat completion probe**
   ```bash
   curl -s -X POST http://localhost:20128/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $NINEROUTER_KEY" \
     -d '{"model":"my9router","messages":[{"role":"user","content":"ping"}],"max_tokens":20}'
   ```

4. **Inspect combos / usage (read-only)**
   ```bash
   sqlite3 "file:$HOME/.9router/db/data.sqlite?mode=ro" \
     "SELECT id, name, models FROM combos;"
   sqlite3 "file:$HOME/.9router/db/data.sqlite?mode=ro" \
     "SELECT timestamp, provider, model, status FROM usageHistory ORDER BY id DESC LIMIT 10;"
   ```

5. **Logs**
   ```bash
   journalctl --user -u 9router.service -n 50 --no-pager
   aa 9router logs
   ```

## Common pitfalls

- Health returning `401`/`403` while the port answers = auth on, process fine.
- Port already in use: a leftover manual `9router` process is fighting the
  unit — `kill` the manual PID, then `systemctl --user restart 9router.service`.
- First npm global install: `npm install -g 9router` (binary must be on
  `PATH` as `9router` for the unit to start).
