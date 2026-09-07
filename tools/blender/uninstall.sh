#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling blender-arwaky..."
for BIN in blender-arwaky ba blender-mcp; do
  rm -f "$XDG_BIN_HOME/$BIN" 2>/dev/null || true
done
rm -rf "$XDG_DATA_HOME/blender-arwaky" 2>/dev/null || true
rm -rf "$XDG_CONFIG_HOME/blender-arwaky" 2>/dev/null || true
echo ">>> blender-arwaky uninstalled (binaries + data + config)."
