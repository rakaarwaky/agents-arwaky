#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling qwen-web-arwaky..."
for BIN in qwen-web-arwaky qwa qwen-web-cli qwen-web-mcp qwc; do
  rm -f "$XDG_BIN_HOME/$BIN" 2>/dev/null || true
done
rm -rf "$XDG_DATA_HOME/qwen-web" 2>/dev/null || true
rm -rf "$XDG_CONFIG_HOME/qwen-web" 2>/dev/null || true
echo ">>> qwen-web-arwaky uninstalled (binaries + data + config)."
