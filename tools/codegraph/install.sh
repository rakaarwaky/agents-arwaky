#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/codegraph"
TARGET_DIR="$XDG_DATA_HOME/codegraph"
LAUNCHER="$XDG_BIN_HOME/codegraph-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/codegraph' first."
  exit 1
fi

echo ">>> Building CodeGraph into XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"
cd "$VENDOR_DIR"

echo ">>> Installing dependencies..."
npm install --no-audit --no-fund

echo ">>> Compiling TypeScript and assets..."
npm run build

echo ">>> Staging build output to $TARGET_DIR..."
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
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/codegraph"
if [ $# -eq 0 ]; then
  exec node "$DATA_DIR/dist/bin/codegraph.js" serve --mcp
else
  exec node "$DATA_DIR/dist/bin/codegraph.js" "$@"
fi
EOF
chmod +x "$LAUNCHER"
ln -sf "$LAUNCHER" "$XDG_BIN_HOME/codegraph"

echo ">>> Successfully installed codegraph-mcp -> $LAUNCHER (and $XDG_BIN_HOME/codegraph)"

