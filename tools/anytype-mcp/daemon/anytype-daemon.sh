#!/usr/bin/env bash
# tools/anytype-daemon/anytype-daemon.sh
# Manages the Anytype Headless Daemon inside Podman (or local fallback)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

CONTAINER_NAME="${ANYTYPE_CONTAINER_NAME:-anytype-daemon}"
IMAGE_NAME="${ANYTYPE_IMAGE_NAME:-anytype-daemon:latest}"
PORT="${ANYTYPE_PORT:-31012}"
DATA_ROOT="$XDG_DATA_HOME/anytype-daemon"
DATA_DIR="$DATA_ROOT/data"
CONFIG_DIR="$DATA_ROOT/config"
SHARE_DIR="$DATA_ROOT/share"
LOCAL_BIN="$DATA_ROOT/bin"
DOT_ANYTYPE_DIR="$DATA_ROOT/dot-anytype"
ENV_FILE="${AGENTS_ARWAKY_ANYTYPE_ENV:-"$TOOL_DIR/.env"}"

mkdir -p "$DATA_DIR" "$CONFIG_DIR" "$SHARE_DIR" "$LOCAL_BIN" "$DOT_ANYTYPE_DIR"

has_podman() {
  command -v podman >/dev/null 2>&1
}

container_is_running() {
  has_podman && podman ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
}

container_exists() {
  has_podman && podman ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER_NAME"
}

check_api_ready() {
  local max_attempts=15
  local attempt=1
  while [ $attempt -le $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/docs/openapi.json" 2>/dev/null | grep -q "200\|401\|403"; then
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  return 1
}

update_env_api_key() {
  local key="$1"
  [ -f "$ENV_FILE" ] || cp "$TOOL_DIR/.env.example" "$ENV_FILE"

  if grep -q "^ANYTYPE_API_KEY=" "$ENV_FILE"; then
    sed -i "s|^ANYTYPE_API_KEY=.*|ANYTYPE_API_KEY=\"$key\"|" "$ENV_FILE"
  else
    echo "ANYTYPE_API_KEY=\"$key\"" >> "$ENV_FILE"
  fi

  if ! grep -q "^ANYTYPE_API_BASE_URL=" "$ENV_FILE"; then
    echo "ANYTYPE_API_BASE_URL=\"http://127.0.0.1:$PORT\"" >> "$ENV_FILE"
  fi
  echo ">>> Successfully updated ANYTYPE_API_KEY in $ENV_FILE"
}

build_image() {
  echo ">>> Building container image '$IMAGE_NAME' using Podman..."
  podman build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Containerfile" "$SCRIPT_DIR"
}

ensure_local_binary() {
  local bin="$LOCAL_BIN/anytype"
  if [ -x "$bin" ]; then
    return 0
  fi

  echo ">>> Downloading official anytype-cli binary..."
  local version="v0.3.6"
  local arch
  case "$(uname -m)" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
  esac

  local url="https://github.com/anyproto/anytype-cli/releases/download/${version}/anytype-cli-${version}-linux-${arch}.tar.gz"
  local tmp_archive
  tmp_archive="$(mktemp "${TMPDIR:-/tmp}/anytype.XXXXXX.tar.gz")"
  curl -fsSL "$url" -o "$tmp_archive"
  tar -xzf "$tmp_archive" -C "$LOCAL_BIN"
  chmod +x "$LOCAL_BIN/anytype"
  rm -f "$tmp_archive"
  echo ">>> Installed anytype binary to $LOCAL_BIN/anytype"
}

cmd_start() {
  if has_podman; then
    if container_is_running; then
      echo ">>> Anytype daemon container '$CONTAINER_NAME' is already running."
      return 0
    fi

    if container_exists; then
      echo ">>> Starting existing Anytype container '$CONTAINER_NAME'..."
      podman start "$CONTAINER_NAME"
    else
      if ! podman image exists "$IMAGE_NAME" 2>/dev/null; then
        build_image
      fi

      echo ">>> Launching Anytype daemon container '$CONTAINER_NAME' on port $PORT..."
      podman run -d \
        --name "$CONTAINER_NAME" \
        --network host \
        --restart unless-stopped \
        -v "$DATA_DIR:/data:Z" \
        -v "$DOT_ANYTYPE_DIR:/root/.anytype:Z" \
        -v "$CONFIG_DIR:/root/.config/anytype:Z" \
        -v "$SHARE_DIR:/root/.local/share/anytype:Z" \
        "$IMAGE_NAME"
    fi

    echo ">>> Waiting for Anytype API to become responsive on port $PORT..."
    if check_api_ready; then
      echo ">>> [OK] Anytype daemon is ready at http://127.0.0.1:$PORT"
    else
      echo ">>> [WARN] Container started, but API is still initializing. Check 'arwaky anytype logs'."
    fi
  else
    echo ">>> Podman not found on host. Falling back to native background execution..."
    ensure_local_binary
    export TMPDIR="${TMPDIR:-$HOME/.tmp}"
    mkdir -p "$TMPDIR"
    nohup "$LOCAL_BIN/anytype" serve --listen-address "127.0.0.1:$PORT" > "$DATA_ROOT/daemon.log" 2>&1 &
    echo ">>> Started local Anytype daemon (PID: $!). Logs: $DATA_ROOT/daemon.log"
  fi
}

cmd_stop() {
  if has_podman && container_exists; then
    echo ">>> Stopping Anytype daemon container '$CONTAINER_NAME'..."
    podman stop "$CONTAINER_NAME" || true
  else
    pkill -f "anytype serve" || true
    echo ">>> Anytype daemon stopped."
  fi
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start
}

cmd_status() {
  echo "=========================================="
  echo " Anytype Headless Daemon Status"
  echo "=========================================="
  if has_podman; then
    if container_is_running; then
      echo " Podman Container: [RUNNING] ($CONTAINER_NAME)"
    elif container_exists; then
      echo " Podman Container: [STOPPED] ($CONTAINER_NAME)"
    else
      echo " Podman Container: [NOT CREATED]"
    fi
  else
    echo " Engine:           Native Process (Podman not installed)"
  fi

  echo " Listen Port:      127.0.0.1:$PORT"
  if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/docs/openapi.json" 2>/dev/null | grep -q "200"; then
    echo " REST API (MCP):   [HEALTHY - 200 OK]"
  else
    echo " REST API (MCP):   [UNREACHABLE / NOT READY]"
  fi

  if [ -f "$ENV_FILE" ] && grep -q "^ANYTYPE_API_KEY=" "$ENV_FILE" && ! grep -q '^ANYTYPE_API_KEY=""' "$ENV_FILE"; then
    echo " Environment:      [CONFIGURED] ANYTYPE_API_KEY is present in .env"
  else
    echo " Environment:      [ATTENTION] ANYTYPE_API_KEY is empty in .env"
  fi
  echo "=========================================="
}

cmd_logs() {
  if has_podman && container_exists; then
    podman logs -f "$CONTAINER_NAME"
  elif [ -f "$DATA_ROOT/daemon.log" ]; then
    tail -f "$DATA_ROOT/daemon.log"
  else
    echo "No log file found."
  fi
}

cmd_exec_anytype() {
  if has_podman && container_is_running; then
    podman exec -i "$CONTAINER_NAME" anytype "$@"
  else
    ensure_local_binary
    export TMPDIR="${TMPDIR:-$HOME/.tmp}"
    "$LOCAL_BIN/anytype" "$@"
  fi
}

cmd_auth_create() {
  local bot_name="${1:-arwaky-bot}"
  echo ">>> Creating bot account '$bot_name' in Anytype daemon..."
  cmd_exec_anytype auth create "$bot_name"
}

cmd_auth_key() {
  local key_name="${1:-arwaky-mcp-key}"
  echo ">>> Creating API key '$key_name' in Anytype daemon..."
  local output
  output="$(cmd_exec_anytype auth apikey create "$key_name")"
  echo "$output"

  # Extract token if output contains token
  local token
  token="$(echo "$output" | grep "^Key:" | head -n1 | sed -e 's/^Key:[[:space:]]*//' || true)"
  if [ -z "$token" ]; then
    token="$(echo "$output" | grep -oE '([a-zA-Z0-9_+/=-]{20,})' | head -n1 || true)"
  fi
  if [ -n "$token" ]; then
    update_env_api_key "$token"
    # Regenerate MCP config automatically
    "$REPO_ROOT/tools/mcp/generate-config.sh" || true
  else
    echo ">>> Note: Please copy your token above and paste into ANYTYPE_API_KEY in $ENV_FILE"
  fi
}

cmd_space_join() {
  if [ $# -lt 1 ]; then
    echo "Error: Missing invite link."
    echo "Usage: arwaky anytype space-join <invite-link>"
    exit 1
  fi
  cmd_exec_anytype space join "$1"
}

cmd_space_list() {
  cmd_exec_anytype space list
}

cmd_service_install() {
  if ! has_podman; then
    echo "Error: Podman is required to install the systemd container service." >&2
    exit 1
  fi

  local unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  cp "$SCRIPT_DIR/anytype-daemon.service" "$unit_dir/anytype-daemon.service"
  systemctl --user daemon-reload
  systemctl --user enable --now anytype-daemon.service
  echo ">>> Anytype daemon installed and started as user systemd service: anytype-daemon.service"
}

cmd_service_status() {
  systemctl --user status anytype-daemon.service
}

cmd_help() {
  echo "Usage: anytype-daemon.sh <command> [arguments...]"
  echo ""
  echo "Commands:"
  echo "  start              Start Anytype daemon (in Podman or native background)"
  echo "  stop               Stop Anytype daemon"
  echo "  restart            Restart Anytype daemon"
  echo "  status             Check health and API accessibility"
  echo "  logs               Tail daemon logs"
  echo "  auth-create [name] Create a headless bot account for the agent"
  echo "  auth-key [name]    Generate API key for MCP and update .env automatically"
  echo "  space-join <link>  Join an Anytype Space via invite link"
  echo "  space-list         List spaces joined by the bot"
  echo "  service-install    Enable auto-start on host login via systemd user unit"
  echo "  service-status     Check systemd user service status"
}

case "${1:-help}" in
  start)            cmd_start ;;
  stop)             cmd_stop ;;
  restart)          cmd_restart ;;
  status)           cmd_status ;;
  logs)             cmd_logs ;;
  auth-create)      shift; cmd_auth_create "$@" ;;
  auth-key|auth-apikey) shift; cmd_auth_key "$@" ;;
  space-join)       shift; cmd_space_join "$@" ;;
  space-list)       cmd_space_list ;;
  service-install)  cmd_service_install ;;
  service-status)   cmd_service_status ;;
  help|-h|--help)   cmd_help ;;
  *)                cmd_exec_anytype "$@" ;;
esac
