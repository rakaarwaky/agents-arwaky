#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling mnemosyne..."
rm -f "$XDG_BIN_HOME/mnemosyne" "$XDG_BIN_HOME/mnemosyne-mcp" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/mnemosyne" 2>/dev/null || true
rm -rf "$XDG_CONFIG_HOME/mnemosyne" 2>/dev/null || true

# Remove Hermes native plugin link if present
HERMES_DIR="${XDG_DATA_HOME:-$HOME}/.hermes"
[ -d "$HOME/.hermes" ] && HERMES_DIR="$HOME/.hermes"
rm -f "$HERMES_DIR/plugins/mnemosyne" 2>/dev/null || true

echo ">>> mnemosyne uninstalled (launchers + data + config + hermes plugin link)."
