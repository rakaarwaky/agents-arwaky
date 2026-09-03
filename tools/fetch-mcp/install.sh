#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/fetch-mcp"
TARGET_DIR="$XDG_DATA_HOME/fetch-mcp"
LAUNCHER="$XDG_BIN_HOME/fetch-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/fetch-mcp' first."
  exit 1
fi

echo ">>> Building Fetch-MCP into XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

cd "$VENDOR_DIR"
npm install --no-audit --no-fund
npm run build

echo ">>> Installing runtime to $TARGET_DIR..."
rm -rf "${TARGET_DIR:?}"/*
cp -r dist "$TARGET_DIR/"
cp package.json "$TARGET_DIR/"
if [ -d "node_modules" ]; then
  cp -r node_modules "$TARGET_DIR/"
fi

echo ">>> Installing launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fetch-mcp"
exec node "$DATA_DIR/dist/index.js" "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed fetch-mcp -> $LAUNCHER"
