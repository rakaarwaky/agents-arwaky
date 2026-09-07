#!/usr/bin/env bash
# tools/sync/sync-all.sh
# One-shot ecosystem synchronizer & update orchestrator for agents-arwaky
# Syncs submodules, validates binaries, regenerates MCP configurations, and reconnects harnesses

set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=/dev/null
[ -f "$REPO_ROOT/tools/lib/xdg.sh" ] && source "$REPO_ROOT/tools/lib/xdg.sh"

# --- Colors ---
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD="\033[1m"
  GREEN="\033[0;32m"
  BLUE="\033[0;34m"
  CYAN="\033[0;36m"
  YELLOW="\033[0;33m"
  RED="\033[0;31m"
  RESET="\033[0m"
else
  BOLD=""
  GREEN=""
  BLUE=""
  CYAN=""
  YELLOW=""
  RED=""
  RESET=""
fi

log_step() {
  echo -e "${BOLD}${CYAN}[$1]${RESET} ${BOLD}$2${RESET}"
}

cmd_help() {
  echo -e "${BOLD}Usage:${RESET} aa sync [options]"
  echo ""
  echo -e "${BOLD}Options:${RESET}"
  echo -e "  ${GREEN}--pull${RESET}        Pull latest git commits before syncing submodules"
  echo -e "  ${GREEN}--build${RESET}       Trigger full rebuild of all tools (aa install)"
  echo -e "  ${GREEN}--no-connect${RESET}  Skip re-connecting agent harnesses"
  echo -e "  ${GREEN}--help${RESET}        Show this help message"
}

main() {
  local do_pull="false"
  local do_build="false"
  local do_connect="true"

  while [ $# -gt 0 ]; do
    case "$1" in
      --pull)
        do_pull="true"
        shift
        ;;
      --build)
        do_build="true"
        shift
        ;;
      --no-connect)
        do_connect="false"
        shift
        ;;
      --help|-h)
        cmd_help
        exit 0
        ;;
      *)
        echo -e "${RED}Unknown option: $1${RESET}"
        cmd_help
        exit 1
        ;;
    esac
  done

  echo -e "${BOLD}======================================================${RESET}"
  echo -e "${CYAN}${BOLD}   agents-arwaky Unified Ecosystem Synchronizer       ${RESET}"
  echo -e "${BOLD}======================================================${RESET}"

  # Step 1: Git pull (if requested)
  if [ "$do_pull" = "true" ]; then
    log_step "1/5" "Pulling latest repository commits..."
    git -C "$REPO_ROOT" pull --ff-only || {
      echo -e "${YELLOW}Warning: git pull failed or has diverged. Continuing with local sync...${RESET}"
    }
  else
    log_step "1/5" "Skipping git pull (use 'aa sync --pull' to pull latest changes)"
  fi

  # Step 2: Submodules Sync
  log_step "2/5" "Synchronizing and initializing git submodules..."
  git -C "$REPO_ROOT" submodule update --init --recursive vendor/ internal/
  echo -e "  ${GREEN}✓${RESET} Submodules up to date."

  # Step 3: Build or Validate Host Binaries
  if [ "$do_build" = "true" ]; then
    log_step "3/5" "Rebuilding all tools..."
    "$REPO_ROOT/agents-arwaky" install
  else
    log_step "3/5" "Verifying installed toolchain binaries..."
    local missing=0
    for bin in git jq curl; do
      if ! command -v "$bin" >/dev/null 2>&1; then
        echo -e "  ${RED}✗${RESET} Missing core tool: $bin"
        missing=$((missing + 1))
      fi
    done
    if [ "$missing" -eq 0 ]; then
      echo -e "  ${GREEN}✓${RESET} Core toolchain verified."
    else
      echo -e "  ${RED}✗${RESET} $missing core tool(s) missing — run 'aa install' to build tools."
    fi
  fi

  # Step 4: MCP Configuration & Harness Sync
  log_step "4/5" "Regenerating unified MCP manifests..."
  "$REPO_ROOT/tools/mcp/generate-config.sh" >/dev/null
  echo -e "  ${GREEN}✓${RESET} Unified MCP manifest generated."

  if [ "$do_connect" = "true" ]; then
    echo -e "  ${BLUE}->${RESET} Reconnecting agent harnesses (--all)..."
    "$REPO_ROOT/tools/connect/connect-agent.sh" --all >/dev/null 2>&1 || {
      echo -e "  ${YELLOW}↷${RESET} Note: Harness connector finished with warnings (normal if some harnesses not installed)."
    }
    echo -e "  ${GREEN}✓${RESET} Agent harnesses synchronized."
  fi

  # Step 5: Integrity Verification
  log_step "5/5" "Running ecosystem verification check..."
  "$REPO_ROOT/tools/ci/verify.sh"

  echo ""
  echo -e "${GREEN}${BOLD}✓ Ecosystem Sync Complete!${RESET} Everything is aligned and ready to run."
}

main "$@"
