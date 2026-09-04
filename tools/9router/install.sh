#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/9router"
TARGET_DIR="$XDG_DATA_HOME/9router"
LAUNCHER="$XDG_BIN_HOME/9router"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/9router' first."
  exit 1
fi

echo ">>> Building 9router into XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

cd "$VENDOR_DIR"

if command -v npm >/dev/null 2>&1; then
  echo ">>> Installing upstream dependencies..."
  npm install --no-audit --no-fund

  echo ">>> Compiling Next.js standalone application..."
  npm run build

  echo ">>> Bundling CLI launcher..."
  cd "$VENDOR_DIR/cli"
  npm install --no-audit --no-fund
  node scripts/build-cli.js

  echo ">>> Staging runtime to $TARGET_DIR..."
  rm -rf "${TARGET_DIR:?}"/*
  cp -r "$VENDOR_DIR/cli/cli.js" "$TARGET_DIR/"
  cp -r "$VENDOR_DIR/cli/package.json" "$TARGET_DIR/"
  cp -r "$VENDOR_DIR/cli/src" "$TARGET_DIR/"
  cp -r "$VENDOR_DIR/cli/hooks" "$TARGET_DIR/"
  if [ -d "$VENDOR_DIR/cli/app" ]; then
    cp -r "$VENDOR_DIR/cli/app" "$TARGET_DIR/"
  fi
  if [ -d "$VENDOR_DIR/cli/node_modules" ]; then
    cp -r "$VENDOR_DIR/cli/node_modules" "$TARGET_DIR/"
  fi
else
  echo "Error: npm is required to build 9router." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/data"

echo ">>> Installing launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
ROUTER_RUNTIME="${XDG_DATA_HOME:-$HOME/.local/share}/9router"
export DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/9router/data"
exec node "$ROUTER_RUNTIME/cli.js" "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed 9router -> $LAUNCHER"
