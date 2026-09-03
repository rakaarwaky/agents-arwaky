#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/context7"
TARGET_DIR="$XDG_DATA_HOME/context7"
LAUNCHER="$XDG_BIN_HOME/context7-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/context7' first."
  exit 1
fi

echo ">>> Building Context7..."
cd "$VENDOR_DIR"
pnpm install --ignore-scripts
pnpm --filter @upstash/context7-mcp build

echo ">>> Setting up XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

echo ">>> Installing launcher to $LAUNCHER..."
cat <<EOF > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
exec node "$VENDOR_DIR/packages/mcp/dist/index.js" "\$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed context7-mcp -> $LAUNCHER"
