#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

OUTPUT_FILE="${1:-"$REPO_ROOT/mcp_servers.generated.json"}"

echo "Generating unified MCP client configuration..."
echo "Target: $OUTPUT_FILE"

# Load environment if .env exists
ENV_FILE="${AGENTS_ARWAKY_ENV:-}"
if [ -z "$ENV_FILE" ]; then
  for candidate in \
    "$REPO_ROOT/tools/anytype-mcp/.env" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/anytype-mcp/.env" \
    "$REPO_ROOT/.env"; do
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
    if [ -n "$key" ]; then
      export "$key"="$val"
    fi
  done < "$ENV_FILE"
fi

ANYTYPE_BASE="${ANYTYPE_API_BASE_URL:-http://127.0.0.1:31012}"
ANYTYPE_KEY="${ANYTYPE_API_KEY:-<YOUR_API_KEY>}"

cat <<EOF > "$OUTPUT_FILE"
{
  "mcpServers": {
    "context7": {
      "command": "context7-mcp"
    },
    "fetch": {
      "command": "fetch-mcp"
    },
    "lean-ctx": {
      "command": "lean-ctx",
      "args": [
        "serve"
      ]
    },
    "ponytail": {
      "command": "ponytail-mcp"
    },
    "anytype": {
      "command": "anytype-mcp",
      "env": {
        "ANYTYPE_API_BASE_URL": "$ANYTYPE_BASE",
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer $ANYTYPE_KEY\", \"Anytype-Version\":\"2025-11-08\"}"
      }
    },
    "codegraph": {
      "command": "codegraph-mcp"
    },
    "vision": {
      "command": "vision-arwaky-mcp"
    },
    "qwen-web": {
      "command": "qwen-web-mcp"
    },
    "blender": {
      "command": "blender-mcp"
    }
  }
}
EOF

echo ">>> Distributing client config templates to individual XDG config dirs:"
for tool in context7 fetch-mcp lean-ctx ponytail anytype-mcp codegraph vision-arwaky qwen-web blender-arwaky; do
  conf_dir="$(xdg_config_dir "$tool")"
  cp "$OUTPUT_FILE" "$conf_dir/mcp_servers.json"
  echo "  - $conf_dir/mcp_servers.json"
done

echo "Generated valid JSON configuration at $OUTPUT_FILE and distributed to ~/.config/<vendor>/"
