#!/usr/bin/env bash
# tools/9router/daemon/9router-daemon.sh
# Manages the 9Router Core Gateway container (Podman / Docker)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

# Resolve and load configuration file
ENV_FILE="${AGENTS_ARWAKY_9ROUTER_ENV:-}"
if [ -z "$ENV_FILE" ]; then
  for candidate in \
    "$SCRIPT_DIR/../env" \
    "$SCRIPT_DIR/../.env" \
    "$REPO_ROOT/tools/9router/env" \
    "$REPO_ROOT/tools/9router/.env" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/9router/env" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/9router/.env"; do
    if [ -f "$candidate" ]; then
      ENV_FILE="$candidate"
      break
    fi
  done
fi

if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r key val || [ -n "$key" ]; do
    [[ "$key" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${key// }" ]] && continue
    key="$(echo "$key" | xargs)"
    val="$(echo "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")"
    if [ -n "$key" ] && [ -z "${!key:-}" ]; then
      export "$key"="$val"
    fi
  done < "$ENV_FILE"
fi

CONTAINER_NAME="${NINEROUTER_CONTAINER_NAME:-9router}"
IMAGE_NAME="${NINEROUTER_IMAGE_NAME:-ghcr.io/decolua/9router:latest}"
PORT="${NINEROUTER_PORT:-20128}"
DATA_DIR="${NINEROUTER_DATA_DIR:-$XDG_DATA_HOME/9router/data}"
INITIAL_PASSWORD="${INITIAL_PASSWORD:-}"

mkdir -p "$DATA_DIR"

has_podman() {
  command -v podman >/dev/null 2>&1
}

has_docker() {
  command -v docker >/dev/null 2>&1
}

get_engine() {
  if has_podman; then
    echo "podman"
  elif has_docker; then
    echo "docker"
  else
    echo ""
  fi
}

container_is_running() {
  local engine
  engine="$(get_engine)"
  [ -n "$engine" ] && "$engine" ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
}

container_exists() {
  local engine
  engine="$(get_engine)"
  [ -n "$engine" ] && "$engine" ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
}

check_api_ready() {
  local max_attempts=20
  local attempt=1
  while [ $attempt -le $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/api/health" 2>/dev/null | grep -q "200"; then
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  return 1
}

cmd_start() {
  local engine
  engine="$(get_engine)"
  if [ -z "$engine" ]; then
    echo "Error: Neither podman nor docker was found. Please install podman." >&2
    exit 1
  fi

  if container_is_running; then
    echo ">>> 9Router daemon container '$CONTAINER_NAME' is already running."
    cmd_status
    return 0
  fi

  local env_args=()
  if [ -n "$INITIAL_PASSWORD" ]; then
    env_args+=(-e "INITIAL_PASSWORD=$INITIAL_PASSWORD")
  fi

  if container_exists; then
    local running_env
    running_env="$("$engine" inspect "$CONTAINER_NAME" --format '{{json .Config.Env}}' 2>/dev/null || true)"
    if [ -n "$INITIAL_PASSWORD" ] && [[ "$running_env" != *"INITIAL_PASSWORD=$INITIAL_PASSWORD"* ]]; then
      echo ">>> Detected updated configuration. Recreating container '$CONTAINER_NAME'..."
      "$engine" rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
    else
      echo ">>> Starting existing container '$CONTAINER_NAME' with $engine..."
      "$engine" start "$CONTAINER_NAME"
    fi
  fi

  if ! container_is_running; then
    echo ">>> Starting 9Router container '$CONTAINER_NAME' ($IMAGE_NAME) on port $PORT..."
    "$engine" run -d \
      --name "$CONTAINER_NAME" \
      -p "$PORT:20128" \
      -v "$DATA_DIR:/app/data:Z" \
      -e DATA_DIR=/app/data \
      -e PORT=20128 \
      -e HOSTNAME=0.0.0.0 \
      "${env_args[@]}" \
      --restart unless-stopped \
      "$IMAGE_NAME"
  fi

  echo ">>> Waiting for 9Router API to be ready at http://127.0.0.1:$PORT..."
  if check_api_ready; then
    echo ">>> [OK] 9Router daemon is active and healthy!"
    echo ">>> Web Dashboard: http://localhost:$PORT"
    echo ">>> REST API Base: http://localhost:$PORT/v1"
    echo ">>> Data Storage:  $DATA_DIR"
  else
    echo "Warning: 9Router container started but API health check timed out." >&2
    echo "Check container logs with: $0 logs" >&2
  fi
}

cmd_stop() {
  local engine
  engine="$(get_engine)"
  if [ -z "$engine" ]; then
    echo "Error: No container engine found." >&2
    exit 1
  fi

  if container_is_running; then
    echo ">>> Stopping container '$CONTAINER_NAME'..."
    "$engine" stop "$CONTAINER_NAME"
    echo ">>> Container '$CONTAINER_NAME' stopped."
  else
    echo ">>> Container '$CONTAINER_NAME' is not running."
  fi
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start
}

cmd_status() {
  local engine
  engine="$(get_engine)"
  echo "=========================================="
  echo " 9Router Service Status"
  echo "=========================================="
  echo "Container Engine: ${engine:-none}"
  echo "Container Name:   $CONTAINER_NAME"
  echo "Target Port:      $PORT"
  echo "Data Directory:   $DATA_DIR"

  if [ -z "$engine" ]; then
    echo "Status:           Engine Not Found (Install Podman)"
    return 1
  fi

  if container_is_running; then
    echo "Container State:  Running"
    local health
    health="$(curl -s "http://127.0.0.1:$PORT/api/health" 2>/dev/null || echo "offline")"
    if [[ "$health" == *"\"ok\":true"* ]] || [[ "$health" == *"ok"* ]]; then
      echo "API Health:       Online (200 OK) -> http://localhost:$PORT"
    else
      echo "API Health:       Unresponsive / Initializing ($health)"
    fi
  elif container_exists; then
    echo "Container State:  Stopped"
    echo "API Health:       Offline (Run '$0 start')"
  else
    echo "Container State:  Not Created (Run '$0 start')"
    echo "API Health:       Offline"
  fi
  echo "=========================================="
}

cmd_logs() {
  local engine
  engine="$(get_engine)"
  if [ -z "$engine" ]; then
    echo "Error: No container engine found." >&2
    exit 1
  fi
  if container_exists; then
    "$engine" logs "${@:-$CONTAINER_NAME}"
  else
    echo "Container '$CONTAINER_NAME' does not exist."
  fi
}

cmd_models() {
  local url="http://127.0.0.1:$PORT/v1/models"
  local key="${NINEROUTER_KEY:-}"
  local auth_header=()
  [ -n "$key" ] && auth_header=(-H "Authorization: Bearer $key")

  local resp
  resp="$(curl -s -w "\n%{http_code}" "${auth_header[@]}" "$url" 2>/dev/null || echo "offline")"
  local http_code
  http_code="$(echo "$resp" | tail -n1)"
  local body
  body="$(echo "$resp" | sed '$d')"

  if [ "$http_code" = "200" ]; then
    if command -v jq >/dev/null 2>&1; then
      echo "$body" | jq -r '.data[] | "\(.id) [\(.owned_by // "default")]"'
    else
      echo "$body"
    fi
  elif [ "$http_code" = "401" ]; then
    echo "Notice: 9Router requires an API key." >&2
    echo "Provide it via: NINEROUTER_KEY=\"sk-...\" $0 models" >&2
    echo "Or obtain/create one at: http://localhost:$PORT (Dashboard -> Keys)" >&2
  else
    echo "Error: 9Router returned HTTP $http_code." >&2
    echo "$body" >&2
  fi
}

cmd_open() {
  local url="http://localhost:$PORT"
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url"
  else
    echo "Dashboard URL: $url"
  fi
}

cmd_key() {
  local sub="${1:-list}"
  shift || true
  case "$sub" in
    list)
      echo "=== 9Router API Keys ==="
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const keys = db.prepare('SELECT id, name, key, isActive, createdAt FROM apiKeys').all();
        if (keys.length === 0) {
          console.log('No API keys found. Add one with: 9router key add <name> [key]');
        } else {
          keys.forEach(k => console.log(\`- \${k.name || 'Unnamed'}: \${k.key} [id: \${k.id}] (\${k.isActive ? 'active' : 'inactive'})\`));
        }
      "
      ;;
    add)
      local name="${1:-}"
      local key="${2:-}"
      if [ -z "$name" ]; then
        echo "Error: Key name is required. Usage: $0 key add <name> [key]" >&2
        exit 1
      fi
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const crypto = require('crypto');
        const name = process.argv[1];
        let key = process.argv[2];
        if (!key) {
          key = 'sk-' + crypto.randomBytes(16).toString('hex');
        }
        const id = crypto.randomUUID();
        const now = new Date().toISOString();
        db.prepare('INSERT INTO apiKeys (id, key, name, machineId, isActive, createdAt) VALUES (?, ?, ?, ?, 1, ?)').run(id, key, name, 'local', now);
        console.log('>>> Successfully created API Key!');
        console.log('Name: ' + name);
        console.log('Key:  ' + key);
        console.log('ID:   ' + id);
      " "$name" "$key"
      ;;
    delete|remove|rm)
      local target="${1:-}"
      if [ -z "$target" ]; then
        echo "Error: Target is required. Usage: $0 key delete <id|name|key>" >&2
        exit 1
      fi
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const target = process.argv[1];
        const res = db.prepare('DELETE FROM apiKeys WHERE id = ? OR name = ? OR key = ?').run(target, target, target);
        console.log(\`Deleted \${res.changes} key(s).\`);
      " "$target"
      ;;
    *)
      echo "Usage: $0 key <list|add|delete> [args...]"
      ;;
  esac
}

cmd_provider() {
  local sub="${1:-list}"
  shift || true
  case "$sub" in
    list)
      echo "=== 9Router Upstream Providers ==="
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const rows = db.prepare('SELECT id, provider, name, isActive, data FROM providerConnections').all();
        if (rows.length === 0) {
          console.log('No providers configured. Add one with: 9router provider add <provider> <api-key> [name]');
        } else {
          rows.forEach(r => {
            let masked = '***';
            try {
              const d = JSON.parse(r.data);
              if (d.apiKey) masked = d.apiKey.substring(0, 6) + '...' + d.apiKey.slice(-4);
            } catch {}
            console.log(\`- [\${r.provider}] \${r.name || r.provider}: \${masked} [id: \${r.id}] (\${r.isActive ? 'active' : 'inactive'})\`);
          });
        }
      "
      ;;
    add)
      local provider="${1:-}"
      local apiKey="${2:-}"
      local name="${3:-$provider}"
      if [ -z "$provider" ] || [ -z "$apiKey" ]; then
        echo "Error: Provider and apiKey are required." >&2
        echo "Usage: $0 provider add <provider> <api-key> [name]" >&2
        echo "Example: $0 provider add openrouter sk-or-v1-abc 'OpenRouter Primary'" >&2
        exit 1
      fi
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const crypto = require('crypto');
        const provider = process.argv[1].toLowerCase();
        const apiKey = process.argv[2];
        const name = process.argv[3] || provider;
        const id = crypto.randomUUID();
        const now = new Date().toISOString();
        db.prepare(\`
          INSERT INTO providerConnections (id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt)
          VALUES (?, ?, 'apikey', ?, NULL, 1, 1, ?, ?, ?)
        \`).run(id, provider, name, JSON.stringify({ apiKey }), now, now);
        console.log('>>> Successfully configured provider!');
        console.log('Provider: ' + provider);
        console.log('Name:     ' + name);
        console.log('ID:       ' + id);
      " "$provider" "$apiKey" "$name"
      ;;
    sync)
      local file_arg="${1:-}"
      local sync_file=""

      if [ -n "$file_arg" ] && [ -f "$file_arg" ]; then
        sync_file="$file_arg"
      else
        for candidate in \
          "$SCRIPT_DIR/../providers.json" \
          "$SCRIPT_DIR/../provider.json" \
          "$REPO_ROOT/tools/9router/providers.json" \
          "$REPO_ROOT/tools/9router/provider.json" \
          "${XDG_CONFIG_HOME:-$HOME/.config}/9router/providers.json" \
          "${XDG_CONFIG_HOME:-$HOME/.config}/9router/provider.json"; do
          if [ -f "$candidate" ]; then
            sync_file="$candidate"
            break
          fi
        done
      fi

      if [ -z "$sync_file" ] || [ ! -f "$sync_file" ]; then
        if [ -n "$file_arg" ]; then
          echo "Error: Providers file not found at: $file_arg" >&2
          exit 1
        fi
        echo ">>> Notice: No providers.json found (template: tools/9router/providers.example.json)."
        echo ">>> To auto-configure providers, copy providers.example.json to providers.json and populate your keys."
        return 0
      fi

      if ! container_is_running; then
        echo "Error: 9Router container is not running. Start it first with: $0 start" >&2
        exit 1
      fi

      echo ">>> Syncing providers from $sync_file into 9Router..."
      podman exec -i "$CONTAINER_NAME" node -e '
        const fs = require("fs");
        const crypto = require("crypto");
        const Database = require("better-sqlite3");
        const db = new Database("/app/data/db/data.sqlite");

        const raw = fs.readFileSync(0, "utf8");
        let list;
        try {
          list = JSON.parse(raw);
        } catch (e) {
          console.error("Error: Invalid JSON syntax in providers file:", e.message);
          process.exit(1);
        }

        if (!Array.isArray(list)) {
          if (list && Array.isArray(list.providers)) list = list.providers;
          else if (list && typeof list === "object") list = [list];
          else list = [];
        }

        const expanded = [];
        for (const item of list) {
          if (!item || typeof item !== "object") continue;
          const rawKeys = item.apiKeys || item.api_keys || item.apiKey || item.api_key || item.key || "";
          if (Array.isArray(rawKeys) && rawKeys.length > 0) {
            rawKeys.forEach((k, idx) => {
              let itemKey = String(k).trim();
              let itemName = item.name || item.label || item.provider || "Provider";
              if (itemKey.includes("|")) {
                const parts = itemKey.split("|");
                itemName = parts[0].trim() || itemName;
                itemKey = parts.slice(1).join("|").trim();
              } else if (rawKeys.length > 1) {
                itemName = `${itemName} (Key ${idx + 1})`;
              }
              expanded.push({
                ...item,
                name: itemName,
                apiKey: itemKey,
                priority: item.priority !== undefined ? (Number(item.priority) + idx) : (idx + 1)
              });
            });
          } else {
            let itemKey = String(rawKeys).trim();
            let itemName = item.name || item.label || item.provider || "Provider";
            if (itemKey.includes("|")) {
              const parts = itemKey.split("|");
              itemName = parts[0].trim() || itemName;
              itemKey = parts.slice(1).join("|").trim();
            }
            expanded.push({
              ...item,
              name: itemName,
              apiKey: itemKey,
              priority: item.priority !== undefined ? Number(item.priority) : 1
            });
          }
        }

        const now = new Date().toISOString();
        let syncedCount = 0;

        for (const item of expanded) {
          const name = item.name || item.label || item.displayName || "Custom Provider";
          let provider = (item.provider || item.type || "custom").toLowerCase().trim();
          const apiKey = item.apiKey || "";
          const priority = Number(item.priority) || 1;
          const url = item.url || item.baseUrl || item.base_url || "";
          let models = item.models || item.model || [];
          if (typeof models === "string") models = [models];

          const isCustom = provider === "custom" || provider === "openai-compatible" ||
            (!["gemini","openrouter","openai","anthropic","deepseek","groq","cerebras","mistral","cohere","together","perplexity","xai","github","novita","sambanova"].includes(provider) && url);

          if (isCustom) {
            const slug = name.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "") || "custom";
            const nodeId = "openai-compatible-" + slug;

            // 1. providerNodes
            const nodeData = JSON.stringify({
              prefix: slug,
              apiType: "chat",
              baseUrl: url || "http://localhost:11434/v1"
            });
            db.prepare(`INSERT INTO providerNodes(id, type, name, data, createdAt, updatedAt)
              VALUES(?, ?, ?, ?, ?, ?)
              ON CONFLICT(id) DO UPDATE SET
                type=excluded.type, name=excluded.name, data=excluded.data, updatedAt=excluded.updatedAt`).run(
              nodeId, "openai-compatible", name, nodeData, now, now
            );

            // 2. providerConnections
            const existing = db.prepare("SELECT id FROM providerConnections WHERE provider = ? AND name = ?").get(nodeId, name);
            const connId = existing ? existing.id : crypto.randomUUID();
            const connData = JSON.stringify({
              apiKey: apiKey || "none",
              priority: priority,
              providerSpecificData: {
                prefix: slug,
                apiType: "chat",
                baseUrl: url || "http://localhost:11434/v1",
                nodeName: name,
                models: models,
                connectionProxyEnabled: false,
                connectionProxyUrl: "",
                connectionNoProxy: ""
              },
              testStatus: "unknown"
            });

            db.prepare(`INSERT INTO providerConnections(id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(id) DO UPDATE SET
                provider=excluded.provider, authType=excluded.authType, name=excluded.name,
                email=excluded.email, priority=excluded.priority, isActive=excluded.isActive,
                data=excluded.data, updatedAt=excluded.updatedAt`).run(
              connId, nodeId, "apikey", name, null, priority, 1, connData, now, now
            );

            // 3. Register custom models in kv if any
            for (const m of models) {
              const mid = typeof m === "string" ? m : m.id;
              const mname = typeof m === "string" ? m : (m.name || m.id);
              const k = nodeId + "|" + mid + "|llm";
              const val = JSON.stringify({ id: mid, name: mname, providerAlias: nodeId, type: "llm" });
              db.prepare("INSERT OR REPLACE INTO kv(scope, key, value) VALUES(?, ?, ?)").run("customModels", k, val);
            }
            console.log(`  [OK] Custom Provider: ${name} -> ${nodeId} (priority ${priority}, ${models.length} model(s))`);
            syncedCount++;
          } else {
            const existing = db.prepare("SELECT id FROM providerConnections WHERE provider = ? AND name = ?").get(provider, name);
            const connId = existing ? existing.id : crypto.randomUUID();
            const specificData = {
              connectionProxyEnabled: false,
              connectionProxyUrl: "",
              connectionNoProxy: ""
            };
            if (url) specificData.baseUrl = url;
            if (models.length > 0) specificData.models = models;

            const connData = JSON.stringify({
              apiKey: apiKey,
              priority: priority,
              globalPriority: null,
              defaultModel: null,
              providerSpecificData: specificData,
              testStatus: "unknown"
            });

            db.prepare(`INSERT INTO providerConnections(id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(id) DO UPDATE SET
                provider=excluded.provider, authType=excluded.authType, name=excluded.name,
                email=excluded.email, priority=excluded.priority, isActive=excluded.isActive,
                data=excluded.data, updatedAt=excluded.updatedAt`).run(
              connId, provider, "apikey", name, null, priority, 1, connData, now, now
            );

            for (const m of models) {
              const mid = typeof m === "string" ? m : m.id;
              const mname = typeof m === "string" ? m : (m.name || m.id);
              const k = provider + "|" + mid + "|llm";
              const val = JSON.stringify({ id: mid, name: mname, providerAlias: provider, type: "llm" });
              db.prepare("INSERT OR REPLACE INTO kv(scope, key, value) VALUES(?, ?, ?)").run("customModels", k, val);
            }
            console.log(`  [OK] Standard Provider: ${name} -> ${provider} (priority ${priority})`);
            syncedCount++;
          }
        }
        console.log(`>>> Provider synchronization completed: ${syncedCount} provider(s) active.`);
      ' < "$sync_file"
      ;;
    delete|remove|rm)
      local target="${1:-}"
      if [ -z "$target" ]; then
        echo "Error: Target is required. Usage: $0 provider delete <id|provider|name>" >&2
        exit 1
      fi
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const target = process.argv[1];
        const res = db.prepare('DELETE FROM providerConnections WHERE id = ? OR provider = ? OR name = ?').run(target, target, target);
        console.log(\`Deleted \${res.changes} provider connection(s).\`);
      " "$target"
      ;;
    *)
      echo "Usage: $0 provider <list|add|delete|sync> [args...]"
      ;;
  esac
}

cmd_password() {
  local sub="${1:-show}"
  shift || true
  case "$sub" in
    show)
      local env_file="${ENV_FILE:-$SCRIPT_DIR/../.env}"
      echo "=========================================="
      echo " 9Router Admin Dashboard Authentication"
      echo "=========================================="
      if [ -n "$INITIAL_PASSWORD" ]; then
        echo "Initial Password: $INITIAL_PASSWORD"
        echo "Config File:      $env_file"
      else
        echo "Initial Password: [Not set - using default 123456]"
        echo "To set one:       $0 password set <your-password>"
      fi
      echo "Web Dashboard:    http://localhost:$PORT"
      echo "=========================================="
      ;;
    set)
      local new_pass="${1:-}"
      if [ -z "$new_pass" ]; then
        echo "Error: Password cannot be empty. Usage: $0 password set <new_password>" >&2
        exit 1
      fi
      local env_file="${ENV_FILE:-$SCRIPT_DIR/../.env}"
      mkdir -p "$(dirname "$env_file")"
      if [ -f "$env_file" ] && grep -q "^INITIAL_PASSWORD=" "$env_file"; then
        sed -i "s|^INITIAL_PASSWORD=.*|INITIAL_PASSWORD=\"$new_pass\"|" "$env_file"
      else
        echo "INITIAL_PASSWORD=\"$new_pass\"" >> "$env_file"
      fi
      export INITIAL_PASSWORD="$new_pass"
      echo ">>> Updated INITIAL_PASSWORD in $env_file"
      echo ">>> Applying new password to 9Router container..."
      local engine
      engine="$(get_engine)"
      if container_exists; then
        "$engine" rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
      fi
      cmd_start
      ;;
    reset)
      echo ">>> Resetting dashboard authentication to INITIAL_PASSWORD..."
      podman exec "$CONTAINER_NAME" node -e "
        const db = require('better-sqlite3')('/app/data/db/data.sqlite');
        const row = db.prepare('SELECT data FROM settings WHERE id = 1').get();
        if (row) {
          const s = JSON.parse(row.data);
          delete s.password;
          db.prepare('UPDATE settings SET data = ? WHERE id = 1').run(JSON.stringify(s));
          console.log('Saved password hash cleared.');
        }
      " 2>/dev/null || true
      cmd_password show
      ;;
    *)
      echo "Usage: $0 password <show|set|reset> [new_password]"
      ;;
  esac
}

cmd_help() {
  cat <<EOF
Usage: $(basename "$0") <command> [args...]

Commands:
  start                     Start the 9Router Podman container in background
  stop                      Stop the 9Router container
  restart                   Restart the 9Router container
  status                    Show container status and API health check
  logs                      Follow container logs (-f to stream)
  models                    List available AI models from the running gateway
  password [show|set|reset] Manage Admin Dashboard password
  key list                  List 9Router consumer API keys
  key add <name> [key]      Create a new API key (or import an existing key)
  key delete <id|name|key>  Delete an API key
  provider list             List configured AI providers
  provider add <p> <k> [n]  Add provider connection (e.g. openrouter sk-...)
  provider delete <target>  Delete provider connection
  provider sync [file]      Sync providers from providers.json into database
  open                      Open web dashboard in browser (http://localhost:$PORT)
  help                      Show this help message
EOF
}

ACTION="${1:-help}"
shift || true

case "$ACTION" in
  start)    cmd_start "$@" ;;
  stop)     cmd_stop "$@" ;;
  restart)  cmd_restart "$@" ;;
  status)   cmd_status "$@" ;;
  logs)     cmd_logs "$@" ;;
  models)   cmd_models "$@" ;;
  password) cmd_password "$@" ;;
  key|keys) cmd_key "$@" ;;
  provider|providers) cmd_provider "$@" ;;
  open)     cmd_open "$@" ;;
  help|-h)  cmd_help ;;
  *)
    cmd_help
    exit 1
    ;;
esac
