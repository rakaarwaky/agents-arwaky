#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

echo ">>> Uninstalling 9Router..."
DAEMON_SCRIPT="$SCRIPT_DIR/daemon/9router-daemon.sh"

# Stop & remove systemd user service if installed
if command -v systemctl >/dev/null 2>&1; then
  if systemctl --user list-unit-files 9router.service >/dev/null 2>&1; then
    systemctl --user disable --now 9router.service 2>/dev/null || true
  fi
  if [ -x "$DAEMON_SCRIPT" ]; then
    "$DAEMON_SCRIPT" service-uninstall >/dev/null 2>&1 || true
  fi
  systemctl --user daemon-reload 2>/dev/null || true
fi
rm -f "$HOME/.config/systemd/user/9router.service" 2>/dev/null || true

rm -f "$XDG_BIN_HOME/9router" 2>/dev/null || true
rm -f "$XDG_DATA_HOME/agents-arwaky/internal-bin/9router" 2>/dev/null || true
rm -rf "$XDG_DATA_HOME/9router" 2>/dev/null || true

echo ">>> 9router uninstalled (daemon service, launchers, data)."
