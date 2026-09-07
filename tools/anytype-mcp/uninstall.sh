#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling anytype-mcp..."

# Remove systemd user service if installed
if command -v systemctl >/dev/null 2>&1 && systemctl --user list-unit-files anytype-daemon.service >/dev/null 2>&1; then
  systemctl --user disable --now anytype-daemon.service 2>/dev/null || true
  systemctl --user daemon-reload 2>/dev/null || true
fi
rm -f "$HOME/.config/systemd/user/anytype-daemon.service" 2>/dev/null || true

rm -f "$XDG_BIN_HOME/anytype-mcp" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/anytype-mcp" 2>/dev/null || true
rm -rf "$XDG_CONFIG_HOME/anytype-mcp" 2>/dev/null || true
echo ">>> anytype-mcp uninstalled (service + launcher + data + config)."
