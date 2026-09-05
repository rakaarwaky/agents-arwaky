#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

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
if command -v bun >/dev/null 2>&1; then
  bun install
  bun run build
elif command -v npm >/dev/null 2>&1; then
  npm install --no-audit --no-fund
  npm run build
else
  echo "Error: Neither bun nor npm found."
  exit 1
fi

echo ">>> Installing runtime to $TARGET_DIR..."
rm -rf "${TARGET_DIR:?}"/*
cp -r dist "$TARGET_DIR/"
cp package.json "$TARGET_DIR/"
if [ -d "node_modules" ]; then
  cp -r node_modules "$TARGET_DIR/"
fi

echo ">>> Installing dual MCP/CLI launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fetch-mcp"
export NODE_PATH="$DATA_DIR/node_modules:${NODE_PATH:-}"

# Check if first argument is a CLI subcommand or help flag
CLI_COMMANDS=" html markdown readable txt json youtube "

if [ $# -gt 0 ] && { [[ "$CLI_COMMANDS" =~ [[:space:]]"$1"[[:space:]] ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--version" ]] || [[ "$1" == "-v" ]]; }; then
  exec node "$DATA_DIR/dist/cli.js" "$@"
else
  exec node "$DATA_DIR/dist/index.js" "$@"
fi
EOF
chmod +x "$LAUNCHER"
ln -sf "$LAUNCHER" "$XDG_BIN_HOME/mcp-fetch"

echo ">>> Successfully installed fetch-mcp -> $LAUNCHER (and $XDG_BIN_HOME/mcp-fetch)"
