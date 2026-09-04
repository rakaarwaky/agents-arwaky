#!/usr/bin/env bash
# tools/arwaky/arwaky-cli.sh
# Core Orchestration Engine for agents-arwaky

set -euo pipefail

# --- Self-resolve Repository Root (handling symlinks) ---
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MANIFEST_FILE="$SCRIPT_DIR/manifest.json"
TARGET_BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

# --- Colors ---
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  GREEN="\033[0;32m"
  BLUE="\033[0;34m"
  CYAN="\033[0;36m"
  YELLOW="\033[0;33m"
  RED="\033[0;31m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  GREEN=""
  BLUE=""
  CYAN=""
  YELLOW=""
  RED=""
  RESET=""
fi

# --- Helper Functions ---
print_banner() {
  echo -e "${CYAN}${BOLD}   ___                           _          ${RESET}"
  echo -e "${CYAN}${BOLD}  / _ | _______    _____ _ / /____ __   ${RESET}"
  echo -e "${CYAN}${BOLD} / __ |/ __/ _ \/\/ _ \`/  '_/ // /   ${RESET}"
  echo -e "${CYAN}${BOLD}/_/ |_/_/  \_/\_/\_,_/_/\_\\_, /    ${RESET}"
  echo -e "${CYAN}${BOLD}                           /___/     ${RESET}"
  echo -e "${DIM} agents-arwaky Unified Tool Orchestrator v1.0${RESET}"
  echo ""
}

is_inside_container() {
  [ -f /.dockerenv ] || [ -n "${CONTAINER_ID:-}" ]
}

check_distrobox_container() {
  if command -v distrobox >/dev/null 2>&1; then
    distrobox list 2>/dev/null | grep -q "agents-env"
  else
    return 1
  fi
}

cmd_help() {
  print_banner
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  arwaky <command> [arguments...]"
  echo ""
  echo -e "${BOLD}COMMANDS:${RESET}"
  echo -e "  ${GREEN}status${RESET}             Check health, submodule and binary installation status"
  echo -e "  ${GREEN}doctor${RESET}             Diagnose runtime environment, container sandbox & PATH"
  echo -e "  ${GREEN}list${RESET}               List all registered tools (vendor & internal)"
  echo -e "  ${GREEN}run${RESET} <tool> [args]  Execute any registered tool (auto-dispatches host/container)"
  echo -e "  ${GREEN}anytype${RESET} [action]    Manage Anytype headless daemon, bot accounts & keys"
  echo -e "  ${GREEN}mcp${RESET} [action]       Manage MCP configurations (list, generate, show)"
  echo -e "  ${GREEN}install${RESET} [tool]     Install full ecosystem or a specific tool from source"
  echo -e "  ${GREEN}shell${RESET}              Enter the Distrobox 'agents-env' sandbox shell"
  echo -e "  ${GREEN}help${RESET}               Show this help message"
  echo ""
  echo -e "${BOLD}EXAMPLES:${RESET}"
  echo -e "  arwaky status"
  echo -e "  arwaky doctor"
  echo -e "  arwaky install"
  echo -e "  arwaky install 9router"
  echo -e "  arwaky run context7 --help"
  echo -e "  arwaky run codegraph index ."
  echo -e "  arwaky run lint --help"
  echo -e "  arwaky mcp generate"
  echo ""
}

cmd_doctor() {
  print_banner
  echo -e "${BOLD}Running Environment Diagnostics...${RESET}"
  echo "------------------------------------------------------"

  # 1. Execution Context
  if is_inside_container; then
    echo -e " Context:         ${GREEN}[OK] Running INSIDE Distrobox container${RESET}"
  else
    echo -e " Context:         ${BLUE}[INFO] Running on HOST OS${RESET}"
  fi

  # 2. PATH Verification
  if [[ ":$PATH:" == *":$TARGET_BIN_DIR:"* ]]; then
    echo -e " User PATH:       ${GREEN}[OK] $TARGET_BIN_DIR is present in PATH${RESET}"
  else
    echo -e " User PATH:       ${YELLOW}[WARN] $TARGET_BIN_DIR is NOT in PATH${RESET}"
    echo -e "                  Add 'export PATH=\"\$HOME/.local/bin:\$PATH\"' to your ~/.bashrc or ~/.zshrc"
  fi

  # 3. Host Prerequisites (if on host)
  if ! is_inside_container; then
    if command -v podman >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
      echo -e " Container Engine: ${GREEN}[OK] $(command -v podman || command -v docker)${RESET}"
    else
      echo -e " Container Engine: ${RED}[FAIL] Podman or Docker not found (Run 'make setup')${RESET}"
    fi

    if command -v distrobox >/dev/null 2>&1; then
      echo -e " Distrobox:       ${GREEN}[OK] $(distrobox --version 2>&1 | head -n1)${RESET}"
      if check_distrobox_container; then
        echo -e " Sandbox Container:${GREEN}[OK] 'agents-env' exists and ready${RESET}"
      else
        echo -e " Sandbox Container:${YELLOW}[WARN] 'agents-env' not yet created (Run 'make install')${RESET}"
      fi
    else
      echo -e " Distrobox:       ${YELLOW}[WARN] Distrobox not found on host (Run 'make setup')${RESET}"
    fi
  fi

  # 4. Utilities
  for util in git jq curl; do
    if command -v "$util" >/dev/null 2>&1; then
      echo -e " Utility ($util):   ${GREEN}[OK] $(command -v "$util")${RESET}"
    else
      echo -e " Utility ($util):   ${RED}[FAIL] $util is required${RESET}"
    fi
  done

  echo "------------------------------------------------------"
  echo -e "${GREEN}Diagnostics complete.${RESET}"
}

cmd_list() {
  print_banner
  echo -e "${BOLD}Registered Tools in agents-arwaky:${RESET}"
  echo "--------------------------------------------------------------------------------"
  printf "${BOLD}%-14s %-10s %-8s %-45s${RESET}\n" "TOOL ID" "CATEGORY" "MCP?" "DESCRIPTION"
  echo "--------------------------------------------------------------------------------"

  local count
  count="$(jq '.tools | length' "$MANIFEST_FILE")"
  for ((i=0; i<count; i++)); do
    local id category isMcp desc
    id="$(jq -r ".tools[$i].id" "$MANIFEST_FILE")"
    category="$(jq -r ".tools[$i].category" "$MANIFEST_FILE")"
    isMcp="$(jq -r ".tools[$i].isMcp" "$MANIFEST_FILE")"
    desc="$(jq -r ".tools[$i].description" "$MANIFEST_FILE")"

    local mcp_label="No"
    [ "$isMcp" = "true" ] && mcp_label="Yes"

    local cat_color="$CYAN"
    [ "$category" = "internal" ] && cat_color="$GREEN"

    printf "%-14s ${cat_color}%-10s${RESET} %-8s %-45s\n" "$id" "$category" "$mcp_label" "$desc"
  done
  echo "--------------------------------------------------------------------------------"
}

cmd_status() {
  print_banner
  echo -e "${BOLD}System & Tool Health Status:${RESET}"
  echo "--------------------------------------------------------------------------------"
  printf "${BOLD}%-14s %-10s %-20s %-25s${RESET}\n" "TOOL" "CATEGORY" "TARGET BINARY" "STATUS"
  echo "--------------------------------------------------------------------------------"

  local count
  count="$(jq '.tools | length' "$MANIFEST_FILE")"
  for ((i=0; i<count; i++)); do
    local id category bin subpath
    id="$(jq -r ".tools[$i].id" "$MANIFEST_FILE")"
    category="$(jq -r ".tools[$i].category" "$MANIFEST_FILE")"
    bin="$(jq -r ".tools[$i].binary" "$MANIFEST_FILE")"
    subpath="$(jq -r ".tools[$i].path" "$MANIFEST_FILE")"

    local cat_color="$CYAN"
    [ "$category" = "internal" ] && cat_color="$GREEN"

    local status_str
    # Check submodule presence
    if [ ! -d "$REPO_ROOT/$subpath" ] || [ ! -e "$REPO_ROOT/$subpath/.git" ]; then
      status_str="${RED}Submodule Missing${RESET}"
    elif command -v "$bin" >/dev/null 2>&1; then
      status_str="${GREEN}Installed ($bin)${RESET}"
    elif [ -x "$TARGET_BIN_DIR/$bin" ]; then
      status_str="${GREEN}Ready ($TARGET_BIN_DIR)${RESET}"
    elif [ "$category" = "internal" ]; then
      status_str="${BLUE}Source Ready (Internal)${RESET}"
    else
      status_str="${YELLOW}Not Installed${RESET}"
    fi

    printf "%-14s ${cat_color}%-10s${RESET} %-20s %b\n" "$id" "$category" "$bin" "$status_str"
  done
  echo "--------------------------------------------------------------------------------"
}

cmd_mcp() {
  local action="${1:-list}"
  case "$action" in
    list)
      echo -e "${BOLD}MCP-Enabled Tools:${RESET}"
      jq -r '.tools[] | select(.isMcp == true) | "  - \(.id) [\(.category)]: \(.description)"' "$MANIFEST_FILE"
      ;;
    generate)
      "$REPO_ROOT/tools/mcp/generate-config.sh"
      ;;
    show|path)
      local cfg="$REPO_ROOT/mcp_servers.generated.json"
      if [ -f "$cfg" ]; then
        echo -e "${BOLD}Path:${RESET} $cfg"
        echo ""
        cat "$cfg"
      else
        echo -e "${YELLOW}Configuration file not found. Generating now...${RESET}"
        "$REPO_ROOT/tools/mcp/generate-config.sh"
      fi
      ;;
    *)
      echo -e "${RED}Unknown MCP action: $action${RESET}"
      echo "Valid actions: list, generate, show"
      exit 1
      ;;
  esac
}

cmd_run() {
  if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Missing tool name.${RESET}"
    echo "Usage: arwaky run <tool-name> [args...]"
    exit 1
  fi

  local tool_input="$1"
  shift

  # Find tool in manifest by id or alias
  local tool_info
  tool_info="$(jq -r --arg q "$tool_input" '.tools[] | select(.id == $q or .alias == $q)' "$MANIFEST_FILE")"

  if [ -z "$tool_info" ]; then
    echo -e "${RED}Error: Tool '$tool_input' not found in manifest.${RESET}"
    echo "Run 'arwaky list' to see all available tools."
    exit 1
  fi

  local id category bin subpath
  id="$(echo "$tool_info" | jq -r '.id')"
  category="$(echo "$tool_info" | jq -r '.category')"
  bin="$(echo "$tool_info" | jq -r '.binary')"
  subpath="$(echo "$tool_info" | jq -r '.path')"

  # 1. If executable binary exists in PATH or TARGET_BIN_DIR, execute it
  if command -v "$bin" >/dev/null 2>&1; then
    exec "$bin" "$@"
  elif [ -x "$TARGET_BIN_DIR/$bin" ]; then
    exec "$TARGET_BIN_DIR/$bin" "$@"
  fi

  # 2. If running on host and binary is inside Distrobox container
  if ! is_inside_container && check_distrobox_container; then
    local internal_bin="$HOME/.local/share/agents-arwaky/internal-bin/$bin"
    if distrobox enter agents-env -- test -x "$internal_bin" 2>/dev/null; then
      exec distrobox enter agents-env -- "$internal_bin" "$@"
    fi
  fi

  # 3. For internal tools with specific runners
  if [ "$category" = "internal" ]; then
    local tool_dir="$REPO_ROOT/$subpath"
    case "$id" in
      lint)
        if command -v cargo >/dev/null 2>&1; then
          exec cargo run --quiet --manifest-path "$tool_dir/Cargo.toml" -- "$@"
        elif check_distrobox_container; then
          exec distrobox enter agents-env -- cargo run --quiet --manifest-path "$tool_dir/Cargo.toml" -- "$@"
        fi
        ;;
      vision|qwen-web|blender)
        if command -v uv >/dev/null 2>&1; then
          exec uv run --directory "$tool_dir" "$bin" "$@"
        elif command -v python3 >/dev/null 2>&1; then
          exec python3 -m "$id" "$@"
        fi
        ;;
    esac
  fi

  echo -e "${RED}Error: Binary '$bin' for tool '$id' is not installed or runnable.${RESET}"
  echo -e "Try running: ${BOLD}arwaky install $id${RESET} or ${BOLD}arwaky install${RESET}"
  exit 1
}

cmd_install() {
  local tool="${1:-}"
  if [ -z "$tool" ]; then
    echo ">>> Running full installation pipeline..."
    if is_inside_container; then
      "$REPO_ROOT/tools/build/build-all.sh"
    else
      make -C "$REPO_ROOT" install
    fi
  else
    local tool_info
    tool_info="$(jq -c --arg q "$tool" '.tools[] | select(.id == $q or .binary == $q or (.alias? != null and .alias == $q))' "$MANIFEST_FILE" 2>/dev/null | head -n1 || true)"
    
    local tool_id="$tool"
    if [ -n "$tool_info" ]; then
      tool_id="$(echo "$tool_info" | jq -r '.id')"
    fi

    echo ">>> Installing tool: $tool_id..."
    if grep -q "^host-build-${tool_id}:" "$REPO_ROOT/Makefile"; then
      make -C "$REPO_ROOT" "host-build-${tool_id}"
    elif [ -x "$REPO_ROOT/tools/$tool_id/install.sh" ]; then
      "$REPO_ROOT/tools/$tool_id/install.sh"
    elif [ -x "$REPO_ROOT/tools/${tool_id}-mcp/install.sh" ]; then
      "$REPO_ROOT/tools/${tool_id}-mcp/install.sh"
    else
      make -C "$REPO_ROOT" "host-build-$tool" || make -C "$REPO_ROOT" install
    fi
  fi
}

# --- Main Dispatcher ---
main() {
  local cmd="${1:-help}"
  shift || true

  case "$cmd" in
    status)          cmd_status "$@" ;;
    doctor)          cmd_doctor "$@" ;;
    list|ls)         cmd_list "$@" ;;
    run)             cmd_run "$@" ;;
    install)         cmd_install "$@" ;;
    anytype)         "$REPO_ROOT/tools/anytype-mcp/daemon/anytype-daemon.sh" "$@" ;;
    mcp)             cmd_mcp "$@" ;;
    shell|enter)     make -C "$REPO_ROOT" shell ;;
    help|-h|--help)  cmd_help ;;
    *)
      echo -e "${RED}Unknown command: $cmd${RESET}"
      echo ""
      cmd_help
      exit 1
      ;;
  esac
}

main "$@"
