#!/usr/bin/env bash
# =============================================================================
# agents-arwaky — Installer (wajib semua, non-interactive)
# =============================================================================
# Menginstal launcher `agents-arwaky` (alias `aa`) DAN semua prerequisite
# yang dibutuhkan oleh seluruh toolchain. Tidak ada yang optional.
#
# Usage:
#   ./install.sh              # install semua, non-interactive
#   ./install.sh --check      # dry-run: hanya report mana yang missing
# =============================================================================
set -euo pipefail

# --- Colors ------------------------------------------------------------------
if [[ -n "${NO_COLOR:-}" ]] || [[ ! -t 1 ]]; then
  R="" G="" Y="" B="" C="" RST="" BOLD=""
else
  R="\033[0;31m" G="\033[0;32m" Y="\033[0;33m" B="\033[0;34m"
  C="\033[0;36m" RST="\033[0m" BOLD="\033[1m"
fi
info()  { printf "${C}[INFO]${RST}  %s\n" "$*"; }
ok()    { printf "${G}[ OK ]${RST}  %s\n" "$*"; }
warn()  { printf "${Y}[WARN]${RST}  %s\n" "$*" >&2; }
err()   { printf "${R}[FAIL]${RST}  %s\n" "$*" >&2; }
step()  { printf "\n${BOLD}${B}>>> %s${RST}\n" "$*"; }
die()   { err "$@"; exit 1; }

# --- Resolve repo root -------------------------------------------------------
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
ROOT="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# --- Parse flags -------------------------------------------------------------
CHECK_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=true ;;
    --help|-h)
      echo "Usage: $0 [--check]"
      echo "  --check   Dry-run: only report missing prerequisites"
      exit 0 ;;
  esac
done

# =============================================================================
# SECTION 1: Detect Package Manager
# =============================================================================
detect_pkg_manager() {
  if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
    PKG_INSTALL="sudo apt-get install -y"
    PKG_UPDATE="sudo apt-get update -qq"
  elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
    PKG_INSTALL="sudo dnf install -y"
    PKG_UPDATE="sudo dnf check-update || true"
  elif command -v yum &>/dev/null; then
    PKG_MGR="yum"
    PKG_INSTALL="sudo yum install -y"
    PKG_UPDATE="sudo yum check-update || true"
  elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
    PKG_INSTALL="sudo pacman -S --noconfirm"
    PKG_UPDATE="sudo pacman -Sy"
  elif command -v apk &>/dev/null; then
    PKG_MGR="apk"
    PKG_INSTALL="sudo apk add"
    PKG_UPDATE="sudo apk update"
  else
    PKG_MGR="none"
    PKG_INSTALL=""
    PKG_UPDATE=""
  fi
}

# =============================================================================
# SECTION 2: Semua Prerequisite (WAJIB)
# =============================================================================
# System packages via package manager (semua wajib ada)
SYS_PACKAGES=(git curl wget python3 nodejs npm jq)

# System libraries untuk vision-arwaky
VISION_LIBS=(libgl1 tesseract-ocr ffmpeg)

# =============================================================================
# SECTION 3: Check + Install Functions
# =============================================================================
MISSING=()

check_tool() {
  local tool="$1"
  if command -v "$tool" &>/dev/null; then
    ok "$tool: $(command -v "$tool")"
    return 0
  else
    err "$tool tidak ditemukan"
    MISSING+=("$tool")
    return 1
  fi
}

check_python_version() {
  if ! command -v python3 &>/dev/null; then return; fi
  local ver
  ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  local major="${ver%%.*}"
  local minor="${ver#*.}"
  if (( major >= 3 && minor >= 10 )); then
    ok "Python $ver (>= 3.10)"
  else
    err "Python $ver ditemukan tapi >= 3.10 wajib"
    die "Upgrade Python ke 3.10+ lalu jalankan ulang: sudo apt-get install python3.12"
  fi
}

check_node_version() {
  if ! command -v node &>/dev/null; then return; fi
  local ver
  ver="$(node -v 2>/dev/null || echo "v0.0.0")"
  ok "Node.js $ver"
}

is_installed_pkg() {
  local pkg="$1"
  case "$PKG_MGR" in
    apt)     dpkg -s "$pkg" &>/dev/null 2>&1 ;;
    dnf|yum) rpm -q "$pkg" &>/dev/null 2>&1 ;;
    pacman)  pacman -Qi "$pkg" &>/dev/null 2>&1 ;;
    apk)     apk info -e "$pkg" &>/dev/null 2>&1 ;;
    *)       false ;;
  esac
}

install_pkg() {
  local pkg="$1"
  if is_installed_pkg "$pkg"; then
    ok "$pkg (sudah terpasang)"
    return 0
  fi
  if [[ -z "$PKG_INSTALL" ]]; then
    err "Tidak bisa auto-install $pkg (package manager tidak dikenal)"
    return 1
  fi
  info "Installing $pkg..."
  if $PKG_INSTALL "$pkg" &>/dev/null; then
    ok "Installed $pkg"
  else
    warn "Gagal install $pkg — mungkin namanya berbeda, install manual"
  fi
}

install_all_prereqs() {
  # --- System packages via package manager ---
  step "System packages (wajib)"
  if [[ "$PKG_MGR" == "none" ]]; then
    err "Package manager tidak dikenal. Install manual: ${SYS_PACKAGES[*]}"
    exit 1
  fi
  $PKG_UPDATE || true
  for pkg in "${SYS_PACKAGES[@]}"; do
    install_pkg "$pkg"
  done

  # --- System libraries untuk vision-arwaky ---
  step "System libraries (vision-arwaky)"
  for pkg in "${VISION_LIBS[@]}"; do
    install_pkg "$pkg"
  done

  # --- uv (Python package manager, wajib untuk internal tools) ---
  step "uv (Python package manager)"
  if command -v uv &>/dev/null; then
    ok "uv: $(command -v uv)"
  else
    info "Installing uv..."
    if command -v curl &>/dev/null; then
      curl -LsSf https://astral.sh/uv/install.sh | sh
      # Update PATH untuk sesi ini
      export PATH="$HOME/.local/bin:$PATH"
      if command -v uv &>/dev/null; then
        ok "uv installed"
      else
        die "Gagal install uv. Run manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
      fi
    else
      die "curl tidak ada, tidak bisa install uv"
    fi
  fi

  # --- bun (wajib untuk fetch-mcp, anytype-mcp) ---
  step "bun (JS runtime)"
  if command -v bun &>/dev/null; then
    ok "bun: $(command -v bun)"
  else
    info "Installing bun..."
    if command -v curl &>/dev/null; then
      curl -fsSL https://bun.sh/install | bash
      export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
      if command -v bun &>/dev/null; then
        ok "bun installed"
      else
        die "Gagal install bun. Run manually: curl -fsSL https://bun.sh/install | bash"
      fi
    else
      die "curl tidak ada, tidak bisa install bun"
    fi
  fi

  # --- pnpm (wajib untuk context7) ---
  step "pnpm (package manager)"
  if command -v pnpm &>/dev/null; then
    ok "pnpm: $(command -v pnpm)"
  else
    info "Installing pnpm..."
    if command -v npm &>/dev/null; then
      npm install -g pnpm && ok "pnpm installed" || die "Gagal install pnpm"
    elif command -v corepack &>/dev/null; then
      corepack enable && corepack prepare pnpm@latest --activate && ok "pnpm installed" || die "Gagal install pnpm"
    else
      die "npm/corepack tidak ada, tidak bisa install pnpm"
    fi
  fi

  # --- Rust toolchain (wajib untuk lint-arwaky) ---
  step "Rust toolchain (cargo + rustc)"
  if command -v cargo &>/dev/null; then
    ok "cargo: $(cargo --version)"
  elif command -v rustc &>/dev/null; then
    ok "rustc: $(rustc --version) — cargo missing, installing..."
    rustup component add cargo 2>/dev/null && ok "cargo added" || die "Gagal tambah cargo"
  else
    info "Installing Rust via rustup..."
    if command -v curl &>/dev/null; then
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
      # Source cargo env
      CARGO_ENV="$HOME/.cargo/env"
      if [[ -f "$CARGO_ENV" ]]; then
        # shellcheck disable=SC1090
        source "$CARGO_ENV"
      fi
      if command -v cargo &>/dev/null; then
        ok "Rust toolchain installed"
      else
        die "Gagal install Rust"
      fi
    else
      die "curl tidak ada, tidak bisa install Rust"
    fi
  fi

  # --- Podman (wajib untuk daemon container) ---
  step "Podman (container engine)"
  if command -v podman &>/dev/null; then
    ok "podman: $(command -v podman)"
  else
    install_pkg podman || warn "podman tidak tersedia — daemon container tidak akan jalan"
  fi
}

# =============================================================================
# SECTION 4: Check Only (dry-run)
# =============================================================================
check_only() {
  step "Checking semua prerequisite"

  for tool in "${SYS_PACKAGES[@]}"; do
    check_tool "$tool" || true
  done

  for tool in "${VISION_LIBS[@]}"; do
    check_tool "$tool" || true
  done

  check_tool uv || true
  check_tool bun || true
  check_tool pnpm || true
  check_tool cargo || true
  check_tool podman || true

  check_python_version
  check_node_version

  echo
  if (( ${#MISSING[@]} > 0 )); then
    err "${#MISSING[@]} prerequisite belum terpasang: ${MISSING[*]}"
    echo "  Jalankan: $0  (tanpa --check) untuk install otomatis"
    return 1
  else
    ok "Semua prerequisite sudah terpasang!"
    return 0
  fi
}

# =============================================================================
# SECTION 5: XDG Setup + aa Launcher
# =============================================================================
setup_launcher() {
  step "Setup agents-arwaky launcher"

  BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
  mkdir -p "$BIN_DIR"

  LAUNCHER="$BIN_DIR/agents-arwaky"
  rm -f "$LAUNCHER"

  cat > "$LAUNCHER" <<EOL
#!/usr/bin/env bash
# agents-arwaky — Main Orchestrator (alias: aa)
# Installed by install.sh — points to $ROOT
set -euo pipefail

ROOT="$ROOT"

export AGENTS_ARWAKY_ROOT="\$ROOT"
export PYTHONPATH="\$ROOT/tools/lib\${PYTHONPATH:+:\${PYTHONPATH}}"

exec python3 "\$ROOT/tools/cli/arwaky.py" "\$@"
EOL
  chmod +x "$LAUNCHER"
  ln -sf "$LAUNCHER" "$BIN_DIR/aa"

  ok "Launcher: $LAUNCHER"
  ok "Alias:    $BIN_DIR/aa"

  if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo
    warn "$BIN_DIR belum ada di PATH."
    echo "  Tambahkan ke ~/.bashrc:"
    echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "  Lalu: source ~/.bashrc"
  fi
}

# =============================================================================
# SECTION 6: Git Submodules
# =============================================================================
init_submodules() {
  step "Init git submodules"
  if [[ -d "$ROOT/.git" ]]; then
    git -C "$ROOT" submodule update --init --recursive vendor/ internal/ && \
      ok "Submodules siap" || warn "Submodule init ada masalah"
  else
    warn "Bukan git repo — skip submodule init"
  fi
}

# =============================================================================
# SECTION 7: Summary
# =============================================================================
print_summary() {
  echo
  step "Ringkasan Instalasi"
  echo
  printf "  ${BOLD}Launcher:${RST}   %s (alias: aa)\n" "$BIN_DIR/agents-arwaky"
  printf "  ${BOLD}Repo:${RST}       %s\n" "$ROOT"
  printf "  ${BOLD}XDG Data:${RST}   %s\n" "${XDG_DATA_HOME:-$HOME/.local/share}"
  printf "  ${BOLD}XDG Config:${RST} %s\n" "${XDG_CONFIG_HOME:-$HOME/.config}"
  printf "  ${BOLD}XDG Cache:${RST}  %s\n" "${XDG_CACHE_HOME:-$HOME/.cache}"
  echo
  echo "  Selanjutnya:"
  echo "    1. Reload shell:  source ~/.bashrc"
  echo "    2. Cek kesehatan: aa doctor"
  echo "    3. Install tools: aa install --yes"
  echo
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  step "agents-arwaky Installer"
  echo "  Repository: $ROOT"
  echo

  detect_pkg_manager
  info "Package manager: $PKG_MGR"

  if $CHECK_ONLY; then
    check_only
    exit $?
  fi

  install_all_prereqs
  setup_launcher
  init_submodules
  print_summary
}

main
