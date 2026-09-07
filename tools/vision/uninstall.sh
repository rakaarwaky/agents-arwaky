#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling vision-arwaky..."
for BIN in vision-arwaky vision-arwaky-cli va vision-arwaky-mcp; do
  rm -f "$XDG_BIN_HOME/$BIN" 2>/dev/null || true
done
rm -rf "$XDG_DATA_HOME/vision-arwaky" 2>/dev/null || true
rm -rf "$XDG_CONFIG_HOME/vision-arwaky" 2>/dev/null || true
echo ">>> vision-arwaky uninstalled (binaries + data + config)."
