#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling codegraph..."
rm -f "$XDG_BIN_HOME/codegraph-mcp" "$XDG_BIN_HOME/codegraph" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/codegraph" 2>/dev/null || true
echo ">>> codegraph uninstalled (launchers + data)."
