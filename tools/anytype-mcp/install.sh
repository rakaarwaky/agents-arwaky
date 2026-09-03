#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/xdg.sh"

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
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/anytype-mcp"
exec node "$DATA_DIR/bin/cli.mjs" "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed anytype-mcp -> $LAUNCHER"
