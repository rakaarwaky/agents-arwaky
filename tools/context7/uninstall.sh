#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling context7..."
rm -f "$XDG_BIN_HOME/context7-mcp" "$XDG_BIN_HOME/ctx7" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/context7" 2>/dev/null || true
echo ">>> context7 uninstalled (launchers + data)."
