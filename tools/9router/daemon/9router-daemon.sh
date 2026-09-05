#!/usr/bin/env bash
# tools/9router/daemon/9router-daemon.sh
# Manages the 9Router Core Gateway container (Podman / Docker)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

CONTAINER_NAME="${NINEROUTER_CONTAINER_NAME:-9router}"
IMAGE_NAME="${NINEROUTER_IMAGE_NAME:-ghcr.io/decolua/9router:latest}"
PORT="${NINEROUTER_PORT:-20128}"
DATA_DIR="${NINEROUTER_DATA_DIR:-$XDG_DATA_HOME/9router/data}"

mkdir -p "$DATA_DIR"

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

container_is_running() {
  local engine
  engine="$(get_engine)"
  [ -n "$engine" ] && "$engine" ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
}

container_exists() {
  local engine
  engine="$(get_engine)"
  [ -n "$engine" ] && "$engine" ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
}

check_api_ready() {
  local max_attempts=20
  local attempt=1
  while [ $attempt -le $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/api/health" 2>/dev/null | grep -q "200"; then
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  return 1
}

cmd_start() {
  local engine
  engine="$(get_engine)"
  if [ -z "$engine" ]; then
    echo "Error: Neither podman nor docker was found. Please install podman." >&2
    exit 1
  fi

  if container_is_running; then
    echo ">>> 9Router daemon container '$CONTAINER_NAME' is already running."
    cmd_status
    return 0
  fi

  if container_exists; then
    echo ">>> Starting existing container '$CONTAINER_NAME' with $engine..."
    "$engine" start "$CONTAINER_NAME"
  else
    echo ">>> Starting 9Router container '$CONTAINER_NAME' ($IMAGE_NAME) on port $PORT..."
    "$engine" run -d \
      --name "$CONTAINER_NAME" \
      -p "$PORT:20128" \
      -v "$DATA_DIR:/app/data:Z" \
      -e DATA_DIR=/app/data \
      -e PORT=20128 \
      -e HOSTNAME=0.0.0.0 \
      --restart unless-stopped \
      "$IMAGE_NAME"
  fi

  echo ">>> Waiting for 9Router API to be ready at http://127.0.0.1:$PORT..."
  if check_api_ready; then
    echo ">>> [OK] 9Router daemon is active and healthy!"
    echo ">>> Web Dashboard: http://localhost:$PORT"
    echo ">>> REST API Base: http://localhost:$PORT/v1"
    echo ">>> Data Storage:  $DATA_DIR"
  else
    echo "Warning: 9Router container started but API health check timed out." >&2
    echo "Check container logs with: $0 logs" >&2
  fi
}

cmd_stop() {
  local engine
  engine="$(get_engine)"
  if [ -z "$engine" ]; then
    echo "Error: No container engine found." >&2
    exit 1
  fi

  if container_is_running; then
    echo ">>> Stopping container '$CONTAINER_NAME'..."
    "$engine" stop "$CONTAINER_NAME"
    echo ">>> Container '$CONTAINER_NAME' stopped."
  else
    echo ">>> Container '$CONTAINER_NAME' is not running."
  fi
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start
}

cmd_status() {
  local engine
  engine="$(get_engine)"
  echo "=========================================="
  echo " 9Router Service Status"
  echo "=========================================="
  echo "Container Engine: ${engine:-none}"
  echo "Container Name:   $CONTAINER_NAME"
  echo "Target Port:      $PORT"
  echo "Data Directory:   $DATA_DIR"

  if [ -z "$engine" ]; then
    echo "Status:           Engine Not Found (Install Podman)"
    return 1
  fi

  if container_is_running; then
    echo "Container State:  Running"
    local health
    health="$(curl -s "http://127.0.0.1:$PORT/api/health" 2>/dev/null || echo "offline")"
    if [[ "$health" == *"\"ok\":true"* ]] || [[ "$health" == *"ok"* ]]; then
      echo "API Health:       Online (200 OK) -> http://localhost:$PORT"
    else
      echo "API Health:       Unresponsive / Initializing ($health)"
    fi
  elif container_exists; then
    echo "Container State:  Stopped"
    echo "API Health:       Offline (Run '$0 start')"
  else
    echo "Container State:  Not Created (Run '$0 start')"
    echo "API Health:       Offline"
  fi
  echo "=========================================="
}

cmd_logs() {
  local engine
  engine="$(get_engine)"
  if [ -z "$engine" ]; then
    echo "Error: No container engine found." >&2
    exit 1
  fi
  if container_exists; then
    "$engine" logs "${@:-$CONTAINER_NAME}"
  else
    echo "Container '$CONTAINER_NAME' does not exist."
  fi
}

cmd_models() {
  local url="http://127.0.0.1:$PORT/v1/models"
  local key="${NINEROUTER_KEY:-}"
  local auth_header=()
  [ -n "$key" ] && auth_header=(-H "Authorization: Bearer $key")

  local resp
  resp="$(curl -s -w "\n%{http_code}" "${auth_header[@]}" "$url" 2>/dev/null || echo "offline")"
  local http_code
  http_code="$(echo "$resp" | tail -n1)"
  local body
  body="$(echo "$resp" | sed '$d')"

  if [ "$http_code" = "200" ]; then
    if command -v jq >/dev/null 2>&1; then
      echo "$body" | jq -r '.data[] | "\(.id) [\(.owned_by // "default")]"'
    else
      echo "$body"
    fi
  elif [ "$http_code" = "401" ]; then
    echo "Notice: 9Router requires an API key." >&2
    echo "Provide it via: NINEROUTER_KEY=\"sk-...\" $0 models" >&2
    echo "Or obtain/create one at: http://localhost:$PORT (Dashboard -> Keys)" >&2
  else
    echo "Error: 9Router returned HTTP $http_code." >&2
    echo "$body" >&2
  fi
}

cmd_open() {
  local url="http://localhost:$PORT"
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url"
  else
    echo "Dashboard URL: $url"
  fi
}

cmd_help() {
  cat <<EOF
Usage: $(basename "$0") <command> [args...]

Commands:
  start     Start the 9Router Podman container in background
  stop      Stop the 9Router container
  restart   Restart the 9Router container
  status    Show container status and API health check
  logs      Follow container logs (-f to stream)
  models    List available AI models from the running gateway
  open      Open web dashboard in browser (http://localhost:$PORT)
  help      Show this help message
EOF
}

ACTION="${1:-help}"
shift || true

case "$ACTION" in
  start)    cmd_start "$@" ;;
  stop)     cmd_stop "$@" ;;
  restart)  cmd_restart "$@" ;;
  status)   cmd_status "$@" ;;
  logs)     cmd_logs "$@" ;;
  models)   cmd_models "$@" ;;
  open)     cmd_open "$@" ;;
  help|-h)  cmd_help ;;
  *)
    cmd_help
    exit 1
    ;;
esac
