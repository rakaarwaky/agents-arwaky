#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/mnemosyne"
TARGET_DIR="$XDG_DATA_HOME/mnemosyne"
CONFIG_DIR="$XDG_CONFIG_HOME/mnemosyne"
VENV_DIR="$TARGET_DIR/venv"
VENV_PY="$VENV_DIR/bin/python"
LAUNCHER="$XDG_BIN_HOME/mnemosyne"
MCP_LAUNCHER="$XDG_BIN_HOME/mnemosyne-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/pyproject.toml" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/mnemosyne' first."
  exit 1
fi

echo ">>> Setting up Mnemosyne directories..."
mkdir -p "$TARGET_DIR" "$CONFIG_DIR" "$XDG_BIN_HOME"

echo ">>> Creating Python virtual environment at $VENV_DIR..."
if command -v uv >/dev/null 2>&1; then
  if [ ! -d "$VENV_DIR" ]; then
    uv venv "$VENV_DIR" --python 3.11 2>/dev/null || uv venv "$VENV_DIR"
  fi
  echo ">>> Installing mnemosyne-memory with MCP & embeddings via uv..."
  uv pip install --python "$VENV_PY" -e "${VENDOR_DIR}[mcp,embeddings]"
  if [ -d "$VENDOR_DIR/integrations/hermes" ]; then
    uv pip install --python "$VENV_PY" --no-deps -e "$VENDOR_DIR/integrations/hermes" || true
  fi
elif command -v python3 >/dev/null 2>&1; then
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/pip" install --upgrade pip
  echo ">>> Installing mnemosyne-memory with MCP & embeddings via pip..."
  "$VENV_DIR/bin/pip" install -e "${VENDOR_DIR}[mcp,embeddings]"
  if [ -d "$VENDOR_DIR/integrations/hermes" ]; then
    "$VENV_DIR/bin/pip" install --no-deps -e "$VENDOR_DIR/integrations/hermes" || true
  fi
else
  echo "Error: Neither uv nor python3 found."
  exit 1
fi

echo ">>> Installing CLI launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mnemosyne"
VENV_PY="$DATA_DIR/venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "Error: Mnemosyne Python runtime not found at $VENV_PY" >&2
  echo "Please run: aa install mnemosyne" >&2
  exit 1
fi

mkdir -p "$DATA_DIR" "$CONFIG_DIR"
export MNEMOSYNE_DATA_DIR="${MNEMOSYNE_DATA_DIR:-$DATA_DIR}"

exec "$VENV_PY" -m mnemosyne.cli "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Installing MCP launcher to $MCP_LAUNCHER..."
cat <<'EOF' > "$MCP_LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mnemosyne"
VENV_PY="$DATA_DIR/venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "Error: Mnemosyne Python runtime not found at $VENV_PY" >&2
  echo "Please run: aa install mnemosyne" >&2
  exit 1
fi

mkdir -p "$DATA_DIR" "$CONFIG_DIR"
export MNEMOSYNE_DATA_DIR="${MNEMOSYNE_DATA_DIR:-$DATA_DIR}"

# Graceful SIGTERM shutdown handler (prevents exit code 143 / signal: terminated on reload)
exec "$VENV_PY" -c "
import signal, sys
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
from mnemosyne.cli import run_cli
sys.argv = ['mnemosyne', 'mcp'] + sys.argv[1:]
run_cli()
" "$@"
EOF
chmod +x "$MCP_LAUNCHER"

# --- Hermes Native Plugin & Shared DB Setup ---
HERMES_DIR="${XDG_DATA_HOME:-$HOME}/.hermes"
[ -d "$HOME/.hermes" ] && HERMES_DIR="$HOME/.hermes"

if [ -d "$HERMES_DIR" ]; then
  echo ">>> Configuring Hermes integration for shared memory..."
  mkdir -p "$HERMES_DIR/plugins"

  # Link provider plugin into Hermes plugins directory
  if [ -d "$VENDOR_DIR/hermes_memory_provider" ]; then
    rm -rf "$HERMES_DIR/plugins/mnemosyne"
    ln -sf "$VENDOR_DIR/hermes_memory_provider" "$HERMES_DIR/plugins/mnemosyne"
    echo "✓ Linked Hermes plugin: $HERMES_DIR/plugins/mnemosyne -> $VENDOR_DIR/hermes_memory_provider"
  fi

  # Install package in Hermes virtualenv if present
  HERMES_VENV="$HERMES_DIR/hermes-agent/venv"
  if [ -x "$HERMES_VENV/bin/python" ]; then
    echo ">>> Installing mnemosyne into Hermes venv ($HERMES_VENV)..."
    if command -v uv >/dev/null 2>&1; then
      uv pip install --python "$HERMES_VENV/bin/python" -e "$VENDOR_DIR" || true
      uv pip install --python "$HERMES_VENV/bin/python" --no-deps -e "$VENDOR_DIR/integrations/hermes" || true
    else
      "$HERMES_VENV/bin/pip" install -e "$VENDOR_DIR" || true
      "$HERMES_VENV/bin/pip" install --no-deps -e "$VENDOR_DIR/integrations/hermes" || true
    fi
  fi
fi

echo ">>> Successfully installed Mnemosyne memory system:"
echo "  - CLI: $LAUNCHER"
echo "  - MCP: $MCP_LAUNCHER"
echo "  - Shared Data: $TARGET_DIR"
