#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling google-workspace-mcp..."
rm -f "$XDG_BIN_HOME/workspace-mcp" "$XDG_BIN_HOME/google-workspace-mcp" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/google-workspace-mcp" 2>/dev/null || true
rm -rf "$XDG_CONFIG_HOME/google-workspace-mcp" 2>/dev/null || true
echo ">>> google-workspace-mcp uninstalled (launchers + data + config)."
