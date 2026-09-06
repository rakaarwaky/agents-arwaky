#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/anytype-mcp"
TARGET_DIR="$XDG_DATA_HOME/anytype-mcp"
LAUNCHER="$XDG_BIN_HOME/anytype-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/anytype-mcp' first."
  exit 1
fi

echo ">>> Building Anytype-MCP into XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

cd "$VENDOR_DIR"
npm install --no-audit --no-fund
npm run build

echo ">>> Installing runtime to $TARGET_DIR..."
rm -rf "${TARGET_DIR:?}"/*
mkdir -p "$TARGET_DIR/bin"
cp bin/cli.mjs "$TARGET_DIR/bin/"
cp package.json "$TARGET_DIR/"

echo ">>> Installing launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail

# Auto-load .env if OPENAPI_MCP_HEADERS or ANYTYPE_API_KEY is not defined
ENV_FILE="${AGENTS_ARWAKY_ENV:-}"
if [ -z "$ENV_FILE" ]; then
  for candidate in \
    "$HOME/agents-arwaky/tools/anytype-mcp/.env" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/anytype-mcp/.env" \
    "$HOME/agents-arwaky/.env" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/agents-arwaky/.env"; do
    if [ -f "$candidate" ]; then
      ENV_FILE="$candidate"
      break
    fi
  done
fi

if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$ENV_FILE"
  set +a
fi

export ANYTYPE_API_BASE_URL="${ANYTYPE_API_BASE_URL:-http://127.0.0.1:31012}"

if [ -z "${OPENAPI_MCP_HEADERS:-}" ] && [ -n "${ANYTYPE_API_KEY:-}" ]; then
  export OPENAPI_MCP_HEADERS="{\"Authorization\":\"Bearer ${ANYTYPE_API_KEY}\", \"Anytype-Version\":\"2025-11-08\"}"
fi

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/anytype-mcp"
exec node "$DATA_DIR/bin/cli.mjs" "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed anytype-mcp -> $LAUNCHER"
