---
name: 9router-gateway
description: Use when managing, configuring, or debugging the local 9Router AI Gateway service (localhost:20128).
---

# 9Router AI Gateway (localhost:20128)

## Architecture Facts

- Runs as systemd user service `9router.service` (`~/.config/systemd/user/9router.service`).
- Binary: `/home/raka/.local/bin/9router --tray --skip-update`
- Port / Base URL: `http://localhost:20128/v1`
- Data directory: `~/.9router/`
  - Authoritative SQLite database: `~/.9router/db/data.sqlite`
  - Logs: `~/.9router/logs/`
- Key tables in `~/.9router/db/data.sqlite`:
  - `combos`: Custom model route aggregations (e.g. `my9router`, `9vision`). Columns: `id`, `name`, `kind`, `models` (JSON array of provider model IDs).
  - `providerConnections`: Configured accounts & credentials for providers (Bai, KGW, OpenCode, etc.).
  - `providerNodes`: External/internal provider node definitions.
  - `apiKeys`: 9Router API keys accepted by `/v1/chat/completions`.
  - `usageHistory` & `usageDaily`: Per-request token counts, cost, timestamps, and model stats.
  - `settings`: Global configuration options in JSON format.
  - `kv`: Key-value scoped configurations.

## Authentication

- Requests to `http://localhost:20128/v1/chat/completions` require an API Key Bearer header:
  `Authorization: Bearer <API_KEY>`
- Environment variable used across Hermes profiles: `HERMES_CUSTOM_9ROUTER_API_KEY`.
- Keys can be inspected in the database:
  ```bash
  sqlite3 ~/.9router/db/data.sqlite "SELECT id, name, key, isActive FROM apiKeys;"
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
   sqlite3 ~/.9router/db/data.sqlite "SELECT id, name, models FROM combos;"
   ```

5. **Inspect Recent Error Logs / Requests:**
   ```bash
   sqlite3 ~/.9router/db/data.sqlite \
     "SELECT timestamp, provider, model, status, promptTokens, completionTokens FROM usageHistory ORDER BY id DESC LIMIT 10;"
   ```
   Or journalctl logs:
   ```bash
   journalctl --user -u 9router.service -n 50 --no-pager
   ```
