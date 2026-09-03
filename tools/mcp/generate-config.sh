#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

OUTPUT_FILE="${1:-"$REPO_ROOT/mcp_servers.generated.json"}"

echo "Generating unified MCP client configuration..."
echo "Target: $OUTPUT_FILE"

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
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer <YOUR_API_KEY>\", \"Anytype-Version\":\"2025-11-08\"}"
      }
    },
    "codegraph": {
      "command": "codegraph-mcp"
    }
  }
}
EOF

echo ">>> Distributing per-vendor client config templates to individual XDG dirs:"
for vendor in context7 fetch-mcp lean-ctx ponytail anytype-mcp codegraph; do
  conf_dir="$(xdg_config_dir "$vendor")"
  cp "$OUTPUT_FILE" "$conf_dir/mcp_servers.json"
  echo "  - $conf_dir/mcp_servers.json"
done

echo "Generated valid JSON configuration at $OUTPUT_FILE and distributed to ~/.config/<vendor>/"
