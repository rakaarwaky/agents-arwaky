#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/google-workspace-mcp"
TARGET_DIR="$XDG_DATA_HOME/google-workspace-mcp"
CONFIG_DIR="$XDG_CONFIG_HOME/google-workspace-mcp"
CREDENTIALS_DIR="$TARGET_DIR/credentials"
VENV_DIR="$TARGET_DIR/venv"
LAUNCHER="$XDG_BIN_HOME/workspace-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/pyproject.toml" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/google-workspace-mcp' first."
  exit 1
fi

echo ">>> Setting up Google Workspace MCP directories..."
mkdir -p "$TARGET_DIR" "$CONFIG_DIR" "$CREDENTIALS_DIR" "$XDG_BIN_HOME"

echo ">>> Creating Python virtual environment at $VENV_DIR..."
if command -v uv >/dev/null 2>&1; then
  if [ ! -d "$VENV_DIR" ]; then
    uv venv "$VENV_DIR" --python 3.11 2>/dev/null || uv venv "$VENV_DIR"
  fi
  uv pip install --python "$VENV_DIR/bin/python" -e "$VENDOR_DIR"
elif command -v python3 >/dev/null 2>&1; then
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -e "$VENDOR_DIR"
else
  echo "Error: Neither uv nor python3 found."
  exit 1
fi

echo ">>> Installing unified launcher to $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/google-workspace-mcp"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/google-workspace-mcp"
CREDENTIALS_DIR="$DATA_DIR/credentials"
VENV_DIR="$DATA_DIR/venv"
VENV_PY="$VENV_DIR/bin/python"
CLIENT_SECRET_FILE="$CONFIG_DIR/client_secret.json"

if [ ! -x "$VENV_PY" ]; then
  echo "Error: Python runtime not found at $VENV_PY" >&2
  echo "Please run: aa install workspace" >&2
  exit 1
fi

mkdir -p "$CONFIG_DIR" "$CREDENTIALS_DIR"

export GOOGLE_CLIENT_SECRET_PATH="${GOOGLE_CLIENT_SECRET_PATH:-$CLIENT_SECRET_FILE}"
export WORKSPACE_MCP_CREDENTIALS_DIR="${WORKSPACE_MCP_CREDENTIALS_DIR:-$CREDENTIALS_DIR}"
export USER_GOOGLE_EMAIL="${USER_GOOGLE_EMAIL:-arwaky90@gmail.com}"

run_setup() {
  echo "================================================================="
  echo " Google Workspace MCP - Setup & Onboarding Wizard"
  echo "================================================================="
  if [ -f "$CLIENT_SECRET_FILE" ]; then
    echo "✓ client_secret.json sudah ada di: $CLIENT_SECRET_FILE"
  else
    echo "(!) client_secret.json belum ditemukan di: $CLIENT_SECRET_FILE"
    echo ">>> Membuka Google Cloud Console di browser Anda..."
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "https://console.cloud.google.com/apis/credentials" 2>/dev/null &
    fi
    echo ""
    echo "Langkah cepat:"
    echo " 1. Di browser yang baru terbuka, klik '+ Create Credentials' -> 'OAuth client ID'."
    echo " 2. Pilih Application type: 'Desktop app' -> klik 'Create'."
    echo " 3. Unduh file JSON credentials ke folder Downloads."
    echo ""
    
    downloaded_file="$(find "$HOME/Downloads" -maxdepth 1 -name "client_secret*.json" 2>/dev/null | head -n1 || true)"
    if [ -n "$downloaded_file" ] && [ -f "$downloaded_file" ]; then
      echo ">>> Menemukan file kredensial di Downloads: $downloaded_file"
      cp "$downloaded_file" "$CLIENT_SECRET_FILE"
      echo "✓ Berhasil menyalin ke $CLIENT_SECRET_FILE"
    else
      echo "Silakan letakkan file JSON credentials tersebut di:"
      echo "  $CLIENT_SECRET_FILE"
      echo ""
      read -rp "Tekan Enter setelah file ditaruh di sana untuk melanjutkan..."
      downloaded_file="$(find "$HOME/Downloads" -maxdepth 1 -name "client_secret*.json" 2>/dev/null | head -n1 || true)"
      if [ -n "$downloaded_file" ] && [ -f "$downloaded_file" ] && [ ! -f "$CLIENT_SECRET_FILE" ]; then
        cp "$downloaded_file" "$CLIENT_SECRET_FILE"
        echo "✓ Berhasil menyalin ke $CLIENT_SECRET_FILE"
      fi
    fi
  fi

  if [ -f "$CLIENT_SECRET_FILE" ]; then
    echo "✓ client_secret.json siap."
    echo ">>> Memulai pemicu login Google OAuth..."
    if [ -x "$VENV_DIR/bin/workspace-mcp" ]; then
      exec "$VENV_DIR/bin/workspace-mcp" --single-user
    else
      exec "$VENV_PY" -m workspace_mcp --single-user
    fi
  else
    echo "Error: File $CLIENT_SECRET_FILE masih belum ditemukan. Setup dibatalkan." >&2
    exit 1
  fi
}

if [ "${1:-}" = "setup" ] || [ "${1:-}" = "auth" ]; then
  run_setup
fi

# Graceful SIGTERM shutdown handler (prevents exit code 143 / signal: terminated on reload)
exec "$VENV_PY" -c "
import signal, sys
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
from main import main
args = sys.argv[1:]
if not args:
    args = ['--single-user']
sys.argv = ['workspace-mcp'] + args
main()
" "$@"
EOF

chmod +x "$LAUNCHER"
ln -sf "$LAUNCHER" "$XDG_BIN_HOME/google-workspace-mcp"

echo ">>> Successfully installed workspace-mcp -> $LAUNCHER (and $XDG_BIN_HOME/google-workspace-mcp)"
