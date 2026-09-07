#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling fetch-mcp..."
rm -f "$XDG_BIN_HOME/fetch-mcp" "$XDG_BIN_HOME/mcp-fetch" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/fetch-mcp" 2>/dev/null || true
echo ">>> fetch-mcp uninstalled (launchers + data)."
