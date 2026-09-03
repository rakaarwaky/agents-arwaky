#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/ponytail"
TARGET_DIR="$XDG_DATA_HOME/ponytail"
LAUNCHER="$XDG_BIN_HOME/ponytail-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/ponytail-mcp/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/ponytail' first."
  exit 1
fi

echo ">>> Building Ponytail into XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

cd "$VENDOR_DIR/ponytail-mcp"
npm install --no-audit --no-fund

echo ">>> Installing runtime to $TARGET_DIR..."
rm -rf "${TARGET_DIR:?}"/*
cp -r index.js instructions.js package.json "$TARGET_DIR/"
if [ -d "node_modules" ]; then
  cp -r node_modules "$TARGET_DIR/"
fi
if [ -d "$VENDOR_DIR/hooks" ]; then cp -r "$VENDOR_DIR/hooks" "$TARGET_DIR/"; fi
if [ -d "$VENDOR_DIR/skills" ]; then cp -r "$VENDOR_DIR/skills" "$TARGET_DIR/"; fi

echo ">>> Installing launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/ponytail"
exec node "$DATA_DIR/index.js" "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed ponytail-mcp -> $LAUNCHER"
