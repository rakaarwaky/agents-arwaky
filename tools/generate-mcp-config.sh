#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/xdg.sh"

OUTPUT_FILE="${1:-"$XDG_CONFIG_HOME/agents-arwaky/mcp_servers.json"}"
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Generating unified MCP client configuration..."
echo "Target XDG Config: $OUTPUT_FILE"

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
    },
    "graphify": {
      "command": "graphify-mcp"
    }
  }
}
EOF

# Also create local convenience link if in repository
if [ "$OUTPUT_FILE" != "$REPO_ROOT/mcp_servers.generated.json" ]; then
  cp "$OUTPUT_FILE" "$REPO_ROOT/mcp_servers.generated.json"
fi

echo "Generated valid JSON configuration at $OUTPUT_FILE (and $REPO_ROOT/mcp_servers.generated.json)"
