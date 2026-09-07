#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling ponytail..."
rm -f "$XDG_BIN_HOME/ponytail-mcp" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/ponytail" 2>/dev/null || true
echo ">>> ponytail uninstalled (launcher + data)."
