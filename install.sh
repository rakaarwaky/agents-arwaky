#!/usr/bin/env bash
# =============================================================================
# agents-arwaky — Installer (all required, latest versions, non-interactive)
# =============================================================================
# Installs ALL prerequisites at latest versions + launcher `aa`.
# Nothing is optional, no prompts.
#
# Usage:
#   ./install.sh              # install everything
#   ./install.sh --check      # dry-run only
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
# SECTION 2: System packages via apt/dnf (base OS deps only)
# =============================================================================
SYS_PACKAGES=(git curl wget ca-certificates gnupg jq)
VISION_LIBS=(libgl1 tesseract-ocr ffmpeg)

install_pkg() {
  local pkg="$1"
  case "$PKG_MGR" in
    apt)     dpkg -s "$pkg" &>/dev/null 2>&1 && ok "$pkg (already installed)" && return 0 ;;
    dnf|yum) rpm -q "$pkg" &>/dev/null 2>&1 && ok "$pkg (already installed)" && return 0 ;;
    pacman)  pacman -Qi "$pkg" &>/dev/null 2>&1 && ok "$pkg (already installed)" && return 0 ;;
    apk)     apk info -e "$pkg" &>/dev/null 2>&1 && ok "$pkg (already installed)" && return 0 ;;
  esac
  if [[ -z "$PKG_INSTALL" ]]; then return 1; fi
  info "Installing $pkg..."
  $PKG_INSTALL "$pkg" &>/dev/null && ok "Installed $pkg" || warn "Failed to install $pkg"
}

# =============================================================================
# SECTION 3: Python (latest via deadsnakes PPA / system)
# =============================================================================
install_python() {
  step "Python (latest)"
  # Check if already >= 3.10
  if command -v python3 &>/dev/null; then
    local ver
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    local major="${ver%%.*}"
    local minor="${ver#*.}"
    if (( major >= 3 && minor >= 10 )); then
      ok "Python $ver (already meets requirement)"
      return 0
    fi
  fi

  # Install latest via deadsnakes PPA (Ubuntu/Debian)
  if [[ "$PKG_MGR" == "apt" ]]; then
    info "Installing latest Python via deadsnakes PPA..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
    $PKG_UPDATE || true
    for py in python3.13 python3.12 python3.11 python3.10; do
      if $PKG_INSTALL "$py" 2>/dev/null; then
        ok "Installed $py"
        # Point python3 to the new version
        sudo update-alternatives --install /usr/bin/python3 python3 "/usr/bin/$py" 1 2>/dev/null || true
        return 0
      fi
    done
  fi

  # Fallback: install via system package
  case "$PKG_MGR" in
    dnf|yum) $PKG_INSTALL python3 && ok "Installed python3" && return 0 ;;
    pacman)  $PKG_INSTALL python && ok "Installed python" && return 0 ;;
    apk)     $PKG_INSTALL python3 && ok "Installed python3" && return 0 ;;
  esac

  die "Failed to install Python >= 3.10"
}

# =============================================================================
# SECTION 4: Node.js (latest LTS via NodeSource)
# =============================================================================
install_nodejs() {
  step "Node.js (latest LTS via NodeSource)"

  # Check if already >= 18
  if command -v node &>/dev/null; then
    local ver
    ver="$(node -v 2>/dev/null | sed 's/v//')"
    local major="${ver%%.*}"
    if (( major >= 18 )); then
      ok "Node.js v$ver (already meets requirement)"
      return 0
    fi
    warn "Node.js v$ver is too old, upgrading..."
  fi

  # Install via NodeSource (Debian/Ubuntu)
  if [[ "$PKG_MGR" == "apt" ]]; then
    info "Setting up NodeSource repository..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | \
      sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg 2>/dev/null || true
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | \
      sudo tee /etc/apt/sources.list.d/nodesource.list >/dev/null
    $PKG_UPDATE || true
    $PKG_INSTALL nodejs && ok "Installed Node.js 22.x (latest LTS)" && return 0
  fi

  # Fallback: nvm (cross-distro)
  info "Installing Node.js via nvm..."
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  if [[ ! -d "$NVM_DIR" ]]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  fi
  [[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"
  if command -v nvm &>/dev/null; then
    nvm install --lts && ok "Installed Node.js $(node -v) via nvm" && return 0
  fi

  # Fallback: system package (may be outdated)
  case "$PKG_MGR" in
    dnf|yum) $PKG_INSTALL nodejs && ok "Installed nodejs" && return 0 ;;
    pacman)  $PKG_INSTALL nodejs npm && ok "Installed nodejs + npm" && return 0 ;;
  esac

  die "Failed to install Node.js. Manual: curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs"
}

# =============================================================================
# SECTION 5: Rust (latest via rustup)
# =============================================================================
install_rust() {
  step "Rust (latest via rustup)"
  if command -v cargo &>/dev/null; then
    ok "cargo: $(cargo --version)"
    return 0
  fi
  # Check if rustup is installed but not on PATH
  if [[ -f "$HOME/.cargo/bin/cargo" ]]; then
    export PATH="$HOME/.cargo/bin:$PATH"
    ok "cargo: $(cargo --version)"
    return 0
  fi
  info "Installing Rust..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
  CARGO_ENV="$HOME/.cargo/env"
  [[ -f "$CARGO_ENV" ]] && source "$CARGO_ENV"  # shellcheck disable=SC1090
  command -v cargo &>/dev/null && ok "Rust: $(cargo --version)" && return 0
  die "Failed to install Rust"
}

# =============================================================================
# SECTION 6: uv (latest via official installer)
# =============================================================================
install_uv() {
  step "uv (latest)"
  if command -v uv &>/dev/null; then
    ok "uv: $(uv --version)"
    return 0
  fi
  info "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv &>/dev/null && ok "uv: $(uv --version)" && return 0
  die "Failed to install uv"
}

# =============================================================================
# SECTION 7: bun (latest via official installer)
# =============================================================================
install_bun() {
  step "bun (latest)"
  if command -v bun &>/dev/null; then
    ok "bun: $(bun --version)"
    return 0
  fi
  info "Installing bun..."
  curl -fsSL https://bun.sh/install | bash
  export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
  command -v bun &>/dev/null && ok "bun: $(bun --version)" && return 0
  die "Failed to install bun"
}

# =============================================================================
# SECTION 8: pnpm (latest via corepack/npm)
# =============================================================================
install_pnpm() {
  step "pnpm (latest)"
  if command -v pnpm &>/dev/null; then
    ok "pnpm: $(pnpm -v)"
    return 0
  fi
  info "Installing pnpm..."
  if command -v corepack &>/dev/null; then
    corepack enable && corepack prepare pnpm@latest --activate && ok "pnpm: $(pnpm -v)" && return 0
  fi
  if command -v npm &>/dev/null; then
    npm install -g pnpm@latest && ok "pnpm: $(pnpm -v)" && return 0
  fi
  die "Failed to install pnpm"
}

# =============================================================================
# SECTION 9: npm (usually bundled with Node.js)
# =============================================================================
install_npm() {
  step "npm"
  if command -v npm &>/dev/null; then
    ok "npm: $(npm -v)"
    return 0
  fi
  # npm is usually included with NodeSource install
  case "$PKG_MGR" in
    apt)    $PKG_INSTALL npm 2>/dev/null ;;
    dnf|yum) $PKG_INSTALL npm 2>/dev/null ;;
    pacman) $PKG_INSTALL npm 2>/dev/null ;;
  esac
  command -v npm &>/dev/null && ok "npm: $(npm -v)" && return 0
  warn "npm not found — may already be bundled with nodejs"
}

# =============================================================================
# SECTION 10: Install all
# =============================================================================
install_all() {
  # System packages (base OS)
  step "System packages"
  if [[ "$PKG_MGR" != "none" ]]; then
    # Suppress GPG warnings from broken third-party repos (e.g. Brave)
    $PKG_UPDATE 2>/dev/null || true
    for pkg in "${SYS_PACKAGES[@]}"; do
      install_pkg "$pkg"
    done
  fi

  # System libraries
  step "System libraries"
  for pkg in "${VISION_LIBS[@]}"; do
    install_pkg "$pkg"
  done

  # Runtimes — all via official latest installers
  install_python
  install_nodejs
  install_npm
  install_rust
  install_uv
  install_bun
  install_pnpm

  # Podman
  step "Podman"
  if command -v podman &>/dev/null; then
    # Suppress storage driver warning by setting overlay driver
    local podman_conf="${XDG_CONFIG_HOME:-$HOME/.config}/containers/storage.conf"
    if [[ ! -f "$podman_conf" ]]; then
      mkdir -p "$(dirname "$podman_conf")"
      printf '[storage]\ndriver = "overlay"\n' > "$podman_conf"
    fi
    ok "podman: $(podman --version)"
  else
    install_pkg podman || warn "podman not available"
  fi
}

# =============================================================================
# SECTION 11: Check only
# =============================================================================
pkg_installed() {
  local pkg="$1"
  case "$PKG_MGR" in
    apt)     dpkg -s "$pkg" &>/dev/null 2>&1 ;;
    dnf|yum) rpm -q "$pkg" &>/dev/null 2>&1 ;;
    pacman)  pacman -Qi "$pkg" &>/dev/null 2>&1 ;;
    apk)     apk info -e "$pkg" &>/dev/null 2>&1 ;;
    *)       command -v "$pkg" &>/dev/null ;;
  esac
}

check_only() {
  step "Checking all prerequisites"
  local fail=0

  # System packages (check via package manager, not command -v)
  for pkg in "${SYS_PACKAGES[@]}"; do
    pkg_installed "$pkg" && ok "$pkg" || { err "$pkg not found"; ((fail++)); }
  done
  for pkg in "${VISION_LIBS[@]}"; do
    pkg_installed "$pkg" && ok "$pkg" || { err "$pkg not found"; ((fail++)); }
  done

  # Python
  if command -v python3 &>/dev/null; then
    local pyver
    pyver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    local pyminor="${pyver#*.}"
    (( pyminor >= 10 )) && ok "Python $pyver" || { err "Python $pyver (requires >= 3.10)"; ((fail++)); }
  else
    err "python3 not found"; ((fail++))
  fi

  # Node.js
  if command -v node &>/dev/null; then
    local nver
    nver="$(node -v | sed 's/v//' | cut -d. -f1)"
    (( nver >= 18 )) && ok "Node.js $(node -v)" || { err "Node.js $(node -v) (requires >= 18)"; ((fail++)); }
  else
    err "node not found"; ((fail++))
  fi

  # Toolchains
  for tool in npm cargo uv bun pnpm podman; do
    command -v "$tool" &>/dev/null && ok "$tool" || { err "$tool not found"; ((fail++)); }
  done

  echo
  (( fail == 0 )) && ok "All prerequisites installed!" || err "$fail prerequisites not installed"
  return $fail
}

# =============================================================================
# SECTION 12: Launcher + submodules
# =============================================================================
setup_launcher() {
  step "Setting up launcher"
  BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
  mkdir -p "$BIN_DIR"
  LAUNCHER="$BIN_DIR/agents-arwaky"
  rm -f "$LAUNCHER"
  cat > "$LAUNCHER" <<EOL
#!/usr/bin/env bash
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
  [[ ":$PATH:" != *":$BIN_DIR:"* ]] && warn "$BIN_DIR is not on your PATH — add to ~/.bashrc"
}

init_submodules() {
  step "Initializing submodules"
  [[ -d "$ROOT/.git" ]] && git -C "$ROOT" submodule update --init --recursive vendor/ internal/ && ok "Submodules ready" || warn "Skipped"
}

print_summary() {
  echo
  step "Installation complete!"
  echo
  printf "  ${BOLD}Launcher:${RST} %s (alias: aa)\n" "$BIN_DIR/agents-arwaky"
  printf "  ${BOLD}Repo:${RST}     %s\n" "$ROOT"
  echo
  echo "  Next: source ~/.bashrc && aa doctor && aa install --yes"
  echo
}

# =============================================================================
# MAIN
# =============================================================================
main() {
  step "agents-arwaky Installer"
  echo "  Repo: $ROOT"
  detect_pkg_manager
  info "Package manager: $PKG_MGR"

  $CHECK_ONLY && { check_only; exit $?; }

  install_all
  setup_launcher
  init_submodules
  print_summary
}

main
