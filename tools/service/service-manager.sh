#!/usr/bin/env bash
# tools/service/service-manager.sh
# Unified Background Daemon & Service Manager for agents-arwaky
# Controls: 9Router AI Gateway, Anytype Headless Daemon, and Sandbox Runtime

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

ANYTYPE_SCRIPT="$REPO_ROOT/tools/anytype-mcp/daemon/anytype-daemon.sh"
NINEROUTER_SCRIPT="$REPO_ROOT/tools/9router/daemon/9router-daemon.sh"

# --- Colors ---
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  GREEN="\033[0;32m"
  YELLOW="\033[0;33m"
  RED="\033[0;31m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  GREEN=""
  YELLOW=""
  RED=""
  RESET=""
fi

has_podman() {
  command -v podman >/dev/null 2>&1
}

has_docker() {
  command -v docker >/dev/null 2>&1
}

get_engine() {
  if has_podman; then
    echo "podman"
  elif has_docker; then
    echo "docker"
  else
    echo ""
  fi
}

cmd_help() {
  echo -e "${BOLD}Usage:${RESET} aa service <action> [target]"
  echo ""
  echo -e "${BOLD}Actions:${RESET}"
  echo -e "  ${GREEN}status${RESET}            Display health and port status of all services"
  echo -e "  ${GREEN}start${RESET} [target]     Start service (9router, anytype, or all - default: all)"
  echo -e "  ${GREEN}stop${RESET} [target]      Stop service (9router, anytype, or all)"
  echo -e "  ${GREEN}restart${RESET} [target]   Restart service (9router, anytype, or all)"
  echo -e "  ${GREEN}logs${RESET} <target>      Follow service logs (9router or anytype)"
  echo ""
  echo -e "${BOLD}Targets:${RESET}"
  echo "  9router, anytype, all (default for start/stop/restart/status)"
}

check_service_status() {
  local engine
  engine="$(get_engine)"
  
  echo -e "${BOLD}agents-arwaky Unified Service Dashboard:${RESET}"
  echo "--------------------------------------------------------------------------------"
  printf "${BOLD}%-18s %-10s %-18s %-25s${RESET}\n" "SERVICE" "PORT" "CONTAINER" "STATUS"
  echo "--------------------------------------------------------------------------------"

  # 1. 9Router
  local r_port="${NINEROUTER_PORT:-20128}"
  local r_container="${NINEROUTER_CONTAINER_NAME:-9router}"
  local r_status="${YELLOW}Stopped${RESET}"
  local r_state="stopped"

  if [ -n "$engine" ] && "$engine" ps --format '{{.Names}}' 2>/dev/null | grep -qx "$r_container"; then
    r_state="running"
    local r_code
    r_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$r_port/" 2>/dev/null || true)"
    if [ "$r_code" = "200" ] || [ "$r_code" = "307" ] || [ "$r_code" = "302" ]; then
      r_status="${GREEN}Online (HTTP $r_code)${RESET}"
    else
      r_status="${YELLOW}Container Up (Port waiting)${RESET}"
    fi
  fi
  printf "%-18s %-10s %-18s %b\n" "9Router Gateway" "$r_port" "$r_container" "$r_status"

  # 2. Anytype Daemon
  local a_port="${ANYTYPE_PORT:-31012}"
  local a_container="${ANYTYPE_CONTAINER_NAME:-anytype-daemon}"
  local a_status="${YELLOW}Stopped${RESET}"

  if [ -n "$engine" ] && "$engine" ps --format '{{.Names}}' 2>/dev/null | grep -qx "$a_container"; then
    local a_code
    a_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$a_port/docs/openapi.json" 2>/dev/null || true)"
    if [ "$a_code" = "200" ] || [ "$a_code" = "401" ] || [ "$a_code" = "403" ]; then
      a_status="${GREEN}Online (HTTP $a_code)${RESET}"
    else
      a_status="${YELLOW}Container Up (Port waiting)${RESET}"
    fi
  fi
  printf "%-18s %-10s %-18s %b\n" "Anytype Daemon" "$a_port" "$a_container" "$a_status"

  # 3. Distrobox 'agents-env'
  local d_status="${YELLOW}Not Created${RESET}"
  if command -v distrobox >/dev/null 2>&1; then
    if distrobox list 2>/dev/null | grep -q "agents-env"; then
      d_status="${GREEN}Ready (Sandbox)${RESET}"
    fi
  fi
  printf "%-18s %-10s %-18s %b\n" "Distrobox Sandbox" "-" "agents-env" "$d_status"

  echo "--------------------------------------------------------------------------------"
  if [ "$r_state" != "running" ]; then
    echo -e "${DIM}Tip: Start all services using: 'aa service start'${RESET}"
  fi
}

cmd_start() {
  local target="${1:-all}"
  case "$target" in
    9router)
      echo -e "${BOLD}>>> Starting 9Router Gateway...${RESET}"
      "$NINEROUTER_SCRIPT" start
      ;;
    anytype|anytype-daemon)
      echo -e "${BOLD}>>> Starting Anytype Daemon...${RESET}"
      "$ANYTYPE_SCRIPT" start
      ;;
    all)
      echo -e "${BOLD}>>> Starting all background services...${RESET}"
      "$NINEROUTER_SCRIPT" start || true
      echo ""
      "$ANYTYPE_SCRIPT" start || true
      ;;
    *)
      echo -e "${RED}Unknown service target: $target${RESET}"
      echo "Valid targets: 9router, anytype, all"
      exit 1
      ;;
  esac
}

cmd_stop() {
  local target="${1:-all}"
  case "$target" in
    9router)
      echo -e "${BOLD}>>> Stopping 9Router Gateway...${RESET}"
      "$NINEROUTER_SCRIPT" stop
      ;;
    anytype|anytype-daemon)
      echo -e "${BOLD}>>> Stopping Anytype Daemon...${RESET}"
      "$ANYTYPE_SCRIPT" stop
      ;;
    all)
      echo -e "${BOLD}>>> Stopping all background services...${RESET}"
      "$NINEROUTER_SCRIPT" stop || true
      "$ANYTYPE_SCRIPT" stop || true
      ;;
    *)
      echo -e "${RED}Unknown service target: $target${RESET}"
      echo "Valid targets: 9router, anytype, all"
      exit 1
      ;;
  esac
}

cmd_restart() {
  local target="${1:-all}"
  case "$target" in
    9router)
      echo -e "${BOLD}>>> Restarting 9Router Gateway...${RESET}"
      "$NINEROUTER_SCRIPT" restart
      ;;
    anytype|anytype-daemon)
      echo -e "${BOLD}>>> Restarting Anytype Daemon...${RESET}"
      "$ANYTYPE_SCRIPT" restart
      ;;
    all)
      echo -e "${BOLD}>>> Restarting all background services...${RESET}"
      "$NINEROUTER_SCRIPT" restart || true
      "$ANYTYPE_SCRIPT" restart || true
      ;;
    *)
      echo -e "${RED}Unknown service target: $target${RESET}"
      echo "Valid targets: 9router, anytype, all"
      exit 1
      ;;
  esac
}

cmd_logs() {
  local target="${1:-}"
  if [ -z "$target" ]; then
    echo -e "${RED}Error: Missing service target for logs.${RESET}"
    echo "Usage: aa service logs <9router|anytype>"
    exit 1
  fi
  shift || true

  case "$target" in
    9router)
      "$NINEROUTER_SCRIPT" logs "$@"
      ;;
    anytype|anytype-daemon)
      "$ANYTYPE_SCRIPT" logs "$@"
      ;;
    *)
      echo -e "${RED}Unknown service target: $target${RESET}"
      echo "Valid targets: 9router, anytype"
      exit 1
      ;;
  esac
}

main() {
  local action="${1:-status}"
  shift || true

  case "$action" in
    status|list)
      check_service_status
      ;;
    start)
      cmd_start "${1:-all}"
      ;;
    stop)
      cmd_stop "${1:-all}"
      ;;
    restart)
      cmd_restart "${1:-all}"
      ;;
    logs)
      cmd_logs "$@"
      ;;
    help|-h|--help)
      cmd_help
      ;;
    *)
      echo -e "${RED}Unknown service action: $action${RESET}"
      cmd_help
      exit 1
      ;;
  esac
}

main "$@"
