#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/graphify"
TARGET_DIR="$XDG_DATA_HOME/graphify"
LAUNCHER="$XDG_BIN_HOME/graphify"
LAUNCHER_MCP="$XDG_BIN_HOME/graphify-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/pyproject.toml" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/graphify' first."
  exit 1
fi

echo ">>> Setting up Graphify in XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

if command -v uv >/dev/null 2>&1; then
  if [ ! -d "$TARGET_DIR/venv" ]; then
    uv venv "$TARGET_DIR/venv"
  fi
  echo ">>> Installing Graphify into virtual environment via uv..."
  uv pip install --quiet -e "$VENDOR_DIR" --python "$TARGET_DIR/venv"
else
  echo "Error: uv is not installed. Please install uv or run 'curl -LsSf https://astral.sh/uv/install.sh | sh'."
  exit 1
fi

echo ">>> Installing launchers..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/graphify"
exec "$DATA_DIR/venv/bin/graphify" "$@"
EOF
chmod +x "$LAUNCHER"

cp "$LAUNCHER" "$LAUNCHER_MCP"

echo ">>> Successfully installed graphify -> $LAUNCHER and $LAUNCHER_MCP"
