#!/usr/bin/env bash
# agents-arwaky installer
# Membuat binary `agents-arwaky` (+ alias `aa`) di local bin sehingga bisa
# dipanggil dari terminal manapun.
set -euo pipefail

# --- resolve repo root (ikuti symlink) ---------------------------------------
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
ROOT="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# --- prasyarat ----------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 diperlukan." >&2
  exit 1
fi
if [ ! -f "$ROOT/tools/cli/arwaky.py" ]; then
  echo "Error: struktur repo tidak ditemukan di $ROOT (tools/cli/arwaky.py tidak ada)." >&2
  exit 1
fi

# --- lokasi instalasi ---------------------------------------------------------
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"

LAUNCHER="$BIN_DIR/agents-arwaky"

# --- tulis launcher dengan ROOT yang sudah di-bake-in -------------------------
# Hapus dulu symlink lama (jika ada) agar tidak menembus target repo.
rm -f "$LAUNCHER"
cat > "$LAUNCHER" <<EOL
#!/usr/bin/env bash
# agents-arwaky - Main Orchestrator Entrypoint (alias: aa)
# Dipasang oleh install.sh — menunjuk ke $ROOT
set -euo pipefail

ROOT="$ROOT"

export AGENTS_ARWAKY_ROOT="\$ROOT"
export PYTHONPATH="\$ROOT/tools/lib\${PYTHONPATH:+:\${PYTHONPATH}}"

exec python3 "\$ROOT/tools/cli/arwaky.py" "\$@"
EOL
chmod +x "$LAUNCHER"

# --- alias aa ----------------------------------------------------------------
ln -sf "$LAUNCHER" "$BIN_DIR/aa"

echo "Installed: $LAUNCHER"
echo "Alias:     $BIN_DIR/aa"

# --- hint PATH ---------------------------------------------------------------
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo
  echo "Catatan: $BIN_DIR belum ada di PATH Anda. Tambahkan dengan:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
  echo "(atau tambahkan baris itu ke ~/.bashrc)"
fi
echo
echo "Sekarang jalankan 'agents-arwaky' atau 'aa' dari terminal manapun."
