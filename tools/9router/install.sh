#!/usr/bin/env bash
# tools/9router/install.sh
# Installs 9Router in Hybrid Architecture:
# - Core Daemon runs in rootless Podman container (ghcr.io/decolua/9router:latest)
# - Host / Distrobox CLI wrapper installed to ~/.local/bin/9router
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

TARGET_DIR="$XDG_DATA_HOME/9router"
DATA_DIR="$TARGET_DIR/data"
DAEMON_SCRIPT="$SCRIPT_DIR/daemon/9router-daemon.sh"
LAUNCHER="$XDG_BIN_HOME/9router"
INTERNAL_BIN="$XDG_DATA_HOME/agents-arwaky/internal-bin"

echo "=========================================="
echo " Setting up 9Router (Hybrid Architecture)"
echo "=========================================="
echo ">>> Data Directory: $DATA_DIR"
mkdir -p "$DATA_DIR" "$XDG_BIN_HOME"
chmod +x "$DAEMON_SCRIPT"

echo ">>> Initializing and verifying 9Router daemon container..."
"$DAEMON_SCRIPT" start

echo ">>> Installing launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root
REPO_ROOT="${AGENTS_ARWAKY_ROOT:-}"
if [ -z "$REPO_ROOT" ]; then
  for candidate in \
    "$HOME/agents-arwaky" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/agents-arwaky" \
    "$(pwd)"; do
    if [ -f "$candidate/tools/9router/daemon/9router-daemon.sh" ]; then
      REPO_ROOT="$candidate"
      break
    fi
  done
fi

DAEMON_SCRIPT="${REPO_ROOT:-$HOME/agents-arwaky}/tools/9router/daemon/9router-daemon.sh"

if [ ! -f "$DAEMON_SCRIPT" ]; then
  echo "Error: 9Router daemon script not found at $DAEMON_SCRIPT." >&2
  exit 1
fi

if [ $# -eq 0 ]; then
  "$DAEMON_SCRIPT" status || true
  echo ""
  echo "Commands:"
  echo "  9router start     Start the daemon container"
  echo "  9router stop      Stop the daemon container"
  echo "  9router restart   Restart the daemon container"
  echo "  9router status    Check container status and API health"
  echo "  9router logs      Inspect container logs (-f to follow)"
  echo "  9router models    Discover available AI models"
  echo "  9router open      Open web dashboard in browser"
  exit 0
fi

case "$1" in
  start|stop|restart|status|logs|models|open|health)
    exec "$DAEMON_SCRIPT" "$@"
    ;;
  --help|-h|help)
    "$DAEMON_SCRIPT" help
    ;;
  *)
    exec "$DAEMON_SCRIPT" "$@"
    ;;
esac
EOF
chmod +x "$LAUNCHER"

if [ -d "$INTERNAL_BIN" ] && [ "$LAUNCHER" != "$INTERNAL_BIN/9router" ]; then
  cp "$LAUNCHER" "$INTERNAL_BIN/9router"
  chmod +x "$INTERNAL_BIN/9router"
fi

echo ">>> Successfully installed 9Router hybrid setup -> $LAUNCHER"
"$LAUNCHER" status
