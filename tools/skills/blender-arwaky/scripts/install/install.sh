#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
XDG_BIN_HOME="${XDG_BIN_HOME:-${HOME}/.local/bin}"
XDG_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
INSTALL_DIR="${XDG_BIN_HOME}"
APP_ID="blender-arwaky"
VENV_DIR="${XDG_DATA_HOME}/${APP_ID}/venv"
CONFIG_DIR="${XDG_CONFIG_HOME}/${APP_ID}"

cmds=(blender-arwaky ba blender-mcp)

ensure_uv_or_pip() {
  if [[ -d "${VENV_DIR}" && ! -x "${VENV_DIR}/bin/python3" ]]; then
    echo "[!] Detected broken venv at ${VENV_DIR}; recreating..."
    rm -rf "${VENV_DIR}"
  fi

  if [[ ! -d "${VENV_DIR}" ]]; then
    echo "[*] Creating virtual environment at ${VENV_DIR} ..."
    mkdir -p "$(dirname "${VENV_DIR}")"
    python3 -m venv "${VENV_DIR}"
  fi

  if command -v uv >/dev/null 2>&1; then
    echo "[*] Using uv for install from ${PROJECT_ROOT}"
    (cd "${PROJECT_ROOT}" && uv pip install --python "${VENV_DIR}/bin/python3" -e .)
    return
  fi
  if [[ -x "${VENV_DIR}/bin/pip" ]]; then
    echo "[*] Using venv pip for install from ${PROJECT_ROOT}"
    "${VENV_DIR}/bin/pip" install -e "${PROJECT_ROOT}"
    return
  fi
  echo "[!] No usable installer found."
  return 1
}

ensure_install_dir() {
  mkdir -p "${INSTALL_DIR}"
}

ensure_config_dir() {
  mkdir -p "${CONFIG_DIR}"
}

write_wrapper() {
  local name="$1"
  local target="${VENV_DIR}/bin/${name}"
  local wrapper="${INSTALL_DIR}/${name}"

  if [[ ! -x "${target}" ]]; then
    echo "[!] Missing entrypoint: ${target}"
    return 1
  fi

  cat > "${wrapper}" <<EOF
#!/usr/bin/env bash
exec "${target}" "\$@"
EOF
  chmod +x "${wrapper}"
  echo "[+] Installed ${wrapper} -> ${target}"
}

warn_path() {
  case ":${PATH}:" in
    *:${INSTALL_DIR}:*)
      ;;
    *)
      echo "[!] ${INSTALL_DIR} is not on PATH."
      echo "    Add this to ~/.bashrc or ~/.zshrc:"
      echo "    export PATH=\"${INSTALL_DIR}:\$PATH\""
      ;;
  esac
}

main() {
  echo "=== Blender Arwaky Installer ==="
  echo "Project Root: ${PROJECT_ROOT}"
  echo "Install Dir:  ${INSTALL_DIR}"
  echo "Venv Dir:     ${VENV_DIR}"
  echo "Config Dir:   ${CONFIG_DIR}"
  echo "XDG Data:     ${XDG_DATA_HOME}"
  echo

  ensure_uv_or_pip
  ensure_install_dir
  ensure_config_dir

  for cmd in "${cmds[@]}"; do
    write_wrapper "${cmd}"
  done

  # Ensure IDE auto-symlink to XDG venv
  for symlink_name in ".venv" "venv"; do
    local link_target="${PROJECT_ROOT}/${symlink_name}"
    if [[ -L "${link_target}" ]] || [[ ! -e "${link_target}" ]]; then
      ln -sfn "${VENV_DIR}" "${link_target}"
      echo "[+] IDE symlink created: ${link_target} -> ${VENV_DIR}"
    fi
  done

  echo
  echo "=== Installation Complete ==="
  echo "You can now run:"
  printf '  %s --help\n' "${cmds[@]}"
  warn_path
}

main "$@"
