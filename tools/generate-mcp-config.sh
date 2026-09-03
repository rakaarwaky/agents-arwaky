#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_FILE="${1:-"$REPO_ROOT/mcp_servers.generated.json"}"

echo "Generating unified MCP client configuration..."
echo "Repository Root: $REPO_ROOT"
echo "Output File: $OUTPUT_FILE"

cat <<EOF > "$OUTPUT_FILE"
{
  "mcpServers": {
    "context7": {
      "command": "node",
      "args": [
        "$REPO_ROOT/tools/context7/dist/index.js"
      ]
    },
    "fetch": {
      "command": "node",
      "args": [
        "$REPO_ROOT/tools/fetch-mcp/dist/index.js"
      ]
    },
    "lean-ctx": {
      "command": "$HOME/.local/bin/lean-ctx",
      "args": [
        "serve"
      ]
    },
    "ponytail": {
      "command": "node",
      "args": [
        "$REPO_ROOT/tools/ponytail/dist/index.js"
      ]
    },
    "anytype": {
      "command": "node",
      "args": [
        "$REPO_ROOT/tools/anytype-mcp/dist/bin/cli.mjs"
      ],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer <YOUR_API_KEY>\", \"Anytype-Version\":\"2025-11-08\"}"
      }
    },
    "codegraph": {
      "command": "node",
      "args": [
        "$REPO_ROOT/tools/codegraph/dist/bin/codegraph.js"
      ]
    }
  }
}
EOF

echo "Generated valid JSON configuration at $OUTPUT_FILE"
