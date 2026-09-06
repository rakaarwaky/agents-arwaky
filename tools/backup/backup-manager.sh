#!/usr/bin/env bash
# tools/backup/backup-manager.sh
# Unified Backup & Restore Adapter for agents-arwaky (aa backup / aa restore)
# Exclusively backs up essential runtime state, databases, credentials & login sessions.
# Compliant with Linux XDG Base Directory Specification & AES standards.

set -euo pipefail

# Self-resolve Repository Root
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source XDG helper
# shellcheck source=/dev/null
[ -f "$REPO_ROOT/tools/lib/xdg.sh" ] && source "$REPO_ROOT/tools/lib/xdg.sh"

BACKUP_STORE="${XDG_DATA_HOME:-$HOME/.local/share}/backups"
GDRIVE_HELPER="$SCRIPT_DIR/gdrive.py"
WORKSPACE_PY="${XDG_DATA_HOME:-$HOME/.local/share}/google-workspace-mcp/venv/bin/python"

TMP_DIRS=()
cleanup_all_tmp() {
  for d in "${TMP_DIRS[@]:-}"; do
    if [ -n "$d" ] && [ -d "$d" ]; then
      rm -rf "$d"
    fi
  done
}
trap cleanup_all_tmp EXIT

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

log_info()  { echo -e "${CYAN}==>${RESET} ${BOLD}$1${RESET}"; }
log_sub()   { echo -e "  ${BLUE}->${RESET} $1"; }
log_ok()    { echo -e "  ${GREEN}✓${RESET} $1"; }
log_warn()  { echo -e "  ${YELLOW}⚠${RESET} $1"; }
log_err()   { echo -e "  ${RED}✗${RESET} $1" >&2; }

normalize_tool_name() {
  local query="$1"
  case "$query" in
    mnemosyne|mnemo|memory) echo "mnemosyne" ;;
    9router|router) echo "9router" ;;
    qwen-web|qwen|qwen-web-arwaky) echo "qwen-web" ;;
    workspace|google-workspace|google-workspace-mcp) echo "workspace" ;;
    anytype|anytype-mcp|anytype-daemon) echo "anytype" ;;
    all) echo "all" ;;
    *) echo "$query" ;;
  esac
}

check_gdrive_support() {
  if [ ! -x "$WORKSPACE_PY" ]; then
    log_err "Google Workspace runtime not found at $WORKSPACE_PY"
    log_err "Please run: aa install workspace"
    exit 1
  fi
  local creds_dir="${XDG_DATA_HOME:-$HOME/.local/share}/google-workspace-mcp/credentials"
  if [ ! -d "$creds_dir" ] || [ -z "$(find "$creds_dir" -maxdepth 1 -name "*.json" ! -name "oauth_states.json" 2>/dev/null)" ]; then
    log_err "Google Workspace credentials not found in $creds_dir"
    log_err "Please run: workspace-mcp setup"
    exit 1
  fi
}

safe_copy_container_dir() {
  local src="$1"
  local dest="$2"
  [ -d "$src" ] || return 0
  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  if cp -ra "$src" "$dest" 2>/dev/null; then
    return 0
  elif command -v podman >/dev/null 2>&1; then
    podman unshare bash -c "rm -rf '$dest' && cp -ra '$src' '$dest' && chown -R 0:0 '$dest'" 2>/dev/null || true
    return 0
  fi
}

safe_restore_container_dir() {
  local src="$1"
  local dest="$2"
  [ -d "$src" ] || return 0
  mkdir -p "$(dirname "$dest")"
  if rm -rf "$dest" 2>/dev/null && cp -ra "$src" "$dest" 2>/dev/null; then
    return 0
  elif command -v podman >/dev/null 2>&1; then
    podman unshare bash -c "rm -rf '$dest' && cp -ra '$src' '$dest'" 2>/dev/null || true
  fi
}

# --- Collect File Items for a Single Tool ---
# Populates temporary staging directory with 'data' and 'config'
stage_tool_data() {
  local tool="$1"
  local stage_dir="$2"

  mkdir -p "$stage_dir/data" "$stage_dir/config"

  case "$tool" in
    mnemosyne)
      local mnemo_data="${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne"
      local mnemo_conf="${XDG_CONFIG_HOME:-$HOME/.config}/mnemosyne"
      
      if [ -f "$mnemo_data/mnemosyne.db" ]; then
        log_sub "Capturing SQLite database: $mnemo_data/mnemosyne.db"
        if command -v sqlite3 >/dev/null 2>&1; then
          sqlite3 "$mnemo_data/mnemosyne.db" ".backup '$stage_dir/data/mnemosyne.db'"
        else
          cp -a "$mnemo_data/mnemosyne.db"* "$stage_dir/data/" 2>/dev/null || true
        fi
      fi
      [ -d "$mnemo_data/banks" ] && cp -ra "$mnemo_data/banks" "$stage_dir/data/" || true
      [ -d "$mnemo_data/history" ] && cp -ra "$mnemo_data/history" "$stage_dir/data/" || true
      [ -d "$mnemo_conf" ] && cp -ra "$mnemo_conf"/* "$stage_dir/config/" 2>/dev/null || true
      ;;

    9router)
      local router_data="${XDG_DATA_HOME:-$HOME/.local/share}/9router"
      local router_env_d="${XDG_CONFIG_HOME:-$HOME/.config}/environment.d/9router.conf"
      local router_prov="$REPO_ROOT/tools/9router/providers.json"
      local router_dot_env="$REPO_ROOT/vendor/9router/.env"

      if [ -d "$router_data/data" ]; then
        log_sub "Capturing 9Router databases & keys: $router_data/data"
        safe_copy_container_dir "$router_data/data" "$stage_dir/data/data"
      fi
      [ -f "$router_prov" ] && cp "$router_prov" "$stage_dir/config/providers.json" || true
      [ -f "$router_env_d" ] && cp "$router_env_d" "$stage_dir/config/9router.conf" || true
      [ -f "$router_dot_env" ] && cp "$router_dot_env" "$stage_dir/config/dot-env" || true
      ;;

    qwen-web)
      local qwen_data="${XDG_DATA_HOME:-$HOME/.local/share}/qwen-web"
      local qwen_conf="${XDG_CONFIG_HOME:-$HOME/.config}/qwen-web"

      if [ -d "$qwen_data/qwen_session" ]; then
        log_sub "Capturing Playwright browser session & cookies: $qwen_data/qwen_session"
        cp -ra "$qwen_data/qwen_session" "$stage_dir/data/"
      fi
      [ -d "$qwen_conf" ] && cp -ra "$qwen_conf"/* "$stage_dir/config/" 2>/dev/null || true
      ;;

    workspace)
      local ws_data="${XDG_DATA_HOME:-$HOME/.local/share}/google-workspace-mcp/credentials"
      local ws_conf="${XDG_CONFIG_HOME:-$HOME/.config}/google-workspace-mcp"

      if [ -d "$ws_data" ]; then
        log_sub "Capturing OAuth tokens: $ws_data"
        cp -ra "$ws_data" "$stage_dir/data/credentials"
      fi
      if [ -f "$ws_conf/client_secret.json" ]; then
        log_sub "Capturing OAuth client_secret.json"
        cp "$ws_conf/client_secret.json" "$stage_dir/config/"
      fi
      ;;

    anytype)
      local any_vault="${XDG_DATA_HOME:-$HOME/.local/share}/anytype-daemon/dot-anytype"
      local any_env="${XDG_CONFIG_HOME:-$HOME/.config}/anytype-mcp/.env"
      local any_tools_env="$REPO_ROOT/tools/anytype-mcp/.env"

      if [ -d "$any_vault" ]; then
        log_sub "Capturing Anytype encrypted vault & keys: $any_vault"
        safe_copy_container_dir "$any_vault" "$stage_dir/data/dot-anytype"
      fi
      [ -f "$any_env" ] && cp "$any_env" "$stage_dir/config/anytype-mcp.env" || true
      [ -f "$any_tools_env" ] && cp "$any_tools_env" "$stage_dir/config/tools-anytype.env" || true
      ;;

    *)
      log_err "Unsupported tool for backup: $tool"
      log_err "Supported tools: mnemosyne, 9router, qwen-web, workspace, anytype, all"
      return 1
      ;;
  esac
}

# --- Restore Staged Items for a Single Tool ---
restore_tool_data() {
  local tool="$1"
  local stage_dir="$2"

  case "$tool" in
    mnemosyne)
      local target_data="${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne"
      local target_conf="${XDG_CONFIG_HOME:-$HOME/.config}/mnemosyne"
      mkdir -p "$target_data" "$target_conf"

      if [ -f "$stage_dir/data/mnemosyne.db" ]; then
        [ -f "$target_data/mnemosyne.db" ] && cp "$target_data/mnemosyne.db" "$target_data/mnemosyne.db.bak"
        cp -a "$stage_dir/data/mnemosyne.db"* "$target_data/"
        log_ok "Restored Mnemosyne database: $target_data/mnemosyne.db"
      fi
      if [ -d "$stage_dir/data/banks" ]; then
        cp -ra "$stage_dir/data/banks" "$target_data/"
        log_ok "Restored memory banks"
      fi
      if [ -d "$stage_dir/config" ] && [ "$(ls -A "$stage_dir/config" 2>/dev/null)" ]; then
        cp -ra "$stage_dir/config"/* "$target_conf/"
        log_ok "Restored Mnemosyne configuration"
      fi
      ;;

    9router)
      local target_data="${XDG_DATA_HOME:-$HOME/.local/share}/9router"
      local target_env_d="${XDG_CONFIG_HOME:-$HOME/.config}/environment.d/9router.conf"
      local target_prov="$REPO_ROOT/tools/9router/providers.json"
      local target_dot_env="$REPO_ROOT/vendor/9router/.env"

      mkdir -p "$target_data" "$(dirname "$target_env_d")" "$(dirname "$target_prov")"

      if [ -d "$stage_dir/data/data" ]; then
        safe_restore_container_dir "$stage_dir/data/data" "$target_data/data"
        log_ok "Restored 9Router persistent database"
      fi
      if [ -f "$stage_dir/config/providers.json" ]; then
        [ -f "$target_prov" ] && cp "$target_prov" "$target_prov.bak"
        cp "$stage_dir/config/providers.json" "$target_prov"
        log_ok "Restored 9Router provider configuration: $target_prov"
      fi
      if [ -f "$stage_dir/config/9router.conf" ]; then
        cp "$stage_dir/config/9router.conf" "$target_env_d"
        log_ok "Restored user session env: $target_env_d"
      fi
      if [ -f "$stage_dir/config/dot-env" ]; then
        cp "$stage_dir/config/dot-env" "$target_dot_env"
        log_ok "Restored 9Router .env"
      fi
      ;;

    qwen-web)
      local target_data="${XDG_DATA_HOME:-$HOME/.local/share}/qwen-web"
      local target_conf="${XDG_CONFIG_HOME:-$HOME/.config}/qwen-web"
      mkdir -p "$target_data" "$target_conf"

      if [ -d "$stage_dir/data/qwen_session" ]; then
        rm -rf "$target_data/qwen_session"
        cp -ra "$stage_dir/data/qwen_session" "$target_data/"
        chmod -R 700 "$target_data/qwen_session"
        log_ok "Restored Qwen Web browser session & cookies: $target_data/qwen_session"
      fi
      if [ -d "$stage_dir/config" ] && [ "$(ls -A "$stage_dir/config" 2>/dev/null)" ]; then
        cp -ra "$stage_dir/config"/* "$target_conf/"
        log_ok "Restored Qwen Web configuration"
      fi
      ;;

    workspace)
      local target_data="${XDG_DATA_HOME:-$HOME/.local/share}/google-workspace-mcp/credentials"
      local target_conf="${XDG_CONFIG_HOME:-$HOME/.config}/google-workspace-mcp"
      mkdir -p "$target_data" "$target_conf"

      if [ -d "$stage_dir/data/credentials" ]; then
        cp -ra "$stage_dir/data/credentials"/* "$target_data/" 2>/dev/null || true
        chmod -R 700 "$target_data"
        chmod -R 600 "$target_data"/*.json 2>/dev/null || true
        log_ok "Restored Google Workspace OAuth credentials: $target_data"
      fi
      if [ -f "$stage_dir/config/client_secret.json" ]; then
        cp "$stage_dir/config/client_secret.json" "$target_conf/client_secret.json"
        chmod 600 "$target_conf/client_secret.json"
        log_ok "Restored client_secret.json: $target_conf/client_secret.json"
      fi
      ;;

    anytype)
      local target_vault="${XDG_DATA_HOME:-$HOME/.local/share}/anytype-daemon/dot-anytype"
      local target_env="${XDG_CONFIG_HOME:-$HOME/.config}/anytype-mcp/.env"
      local target_tools_env="$REPO_ROOT/tools/anytype-mcp/.env"
      mkdir -p "$(dirname "$target_vault")" "$(dirname "$target_env")"

      if [ -d "$stage_dir/data/dot-anytype" ]; then
        safe_restore_container_dir "$stage_dir/data/dot-anytype" "$target_vault"
        chmod -R 700 "$target_vault" 2>/dev/null || true
        log_ok "Restored Anytype encrypted vault: $target_vault"
      fi
      if [ -f "$stage_dir/config/anytype-mcp.env" ]; then
        cp "$stage_dir/config/anytype-mcp.env" "$target_env"
        log_ok "Restored Anytype MCP .env: $target_env"
      fi
      if [ -f "$stage_dir/config/tools-anytype.env" ]; then
        cp "$stage_dir/config/tools-anytype.env" "$target_tools_env"
        log_ok "Restored tools/anytype-mcp/.env"
      fi
      ;;

    *)
      log_err "Unknown tool: $tool"
      return 1
      ;;
  esac
}

# --- Action: Backup ---
cmd_backup() {
  local tool_raw="${1:-}"
  shift || true

  case "$tool_raw" in
    help|-h|--help)
      cmd_help
      return 0
      ;;
    list|ls)
      cmd_list "$@"
      return 0
      ;;
    "")
      log_err "Missing tool name."
      echo "Usage: aa backup <tool|all> [destination_path] [--gdrive]"
      exit 1
      ;;
  esac

  local tool
  tool="$(normalize_tool_name "$tool_raw")"

  local dest_path=""
  local use_gdrive=false

  while [ $# -gt 0 ]; do
    case "$1" in
      --gdrive|-g)
        use_gdrive=true
        shift
        ;;
      *)
        if [ -z "$dest_path" ]; then
          dest_path="$1"
        fi
        shift
        ;;
    esac
  done

  if [ "$use_gdrive" = "true" ]; then
    check_gdrive_support
  fi

  local timestamp
  timestamp="$(date +'%Y%m%d_%H%M%S')"

  local output_dir="$BACKUP_STORE"
  local output_file=""

  if [ -n "$dest_path" ]; then
    if [[ "$dest_path" == *.tar.gz ]] || [[ "$dest_path" == *.tgz ]]; then
      output_file="$dest_path"
      output_dir="$(dirname "$output_file")"
    else
      output_dir="$dest_path"
    fi
  fi

  mkdir -p "$output_dir"
  if [ -z "$output_file" ]; then
    output_file="$output_dir/agents-arwaky-${tool}-${timestamp}.tar.gz"
  fi

  log_info "Starting backup for: ${BOLD}$tool${RESET}"

  local staging_dir
  staging_dir="$(mktemp -d)"
  TMP_DIRS+=("$staging_dir")

  local tools_to_backup=()
  if [ "$tool" = "all" ]; then
    tools_to_backup=("mnemosyne" "9router" "qwen-web" "workspace" "anytype")
  else
    tools_to_backup=("$tool")
  fi

  for t in "${tools_to_backup[@]}"; do
    log_sub "Processing $t..."
    mkdir -p "$staging_dir/$t"
    stage_tool_data "$t" "$staging_dir/$t"
  done

  # Create metadata manifest
  cat <<EOF > "$staging_dir/manifest.json"
{
  "tool": "$tool",
  "tools_included": $(printf '%s\n' "${tools_to_backup[@]}" | jq -R . | jq -s .),
  "timestamp": "$timestamp",
  "version": "1.0",
  "backup_type": "sensitive_data_only"
}
EOF

  log_sub "Packaging archive to: ${BLUE}$output_file${RESET}"
  tar -czf "$output_file" -C "$staging_dir" .

  local archive_size
  archive_size="$(du -h "$output_file" | cut -f1)"
  log_ok "Local backup archive ready (${archive_size}): $output_file"

  # Google Drive upload
  if [ "$use_gdrive" = "true" ]; then
    log_info "Uploading backup to Google Drive (folder: 'Agents-Arwaky-Backups')..."
    local upload_res
    upload_res="$("$WORKSPACE_PY" "$GDRIVE_HELPER" upload "$output_file")"
    
    local file_id web_link
    file_id="$(echo "$upload_res" | jq -r '.file_id // empty')"
    web_link="$(echo "$upload_res" | jq -r '.web_view_link // empty')"

    if [ -n "$file_id" ]; then
      log_ok "Successfully uploaded to Google Drive!"
      echo -e "    ${BOLD}Drive File ID:${RESET} $file_id"
      echo -e "    ${BOLD}Direct Link:${RESET}   $web_link"
    else
      log_err "Failed to parse Google Drive upload result: $upload_res"
      exit 1
    fi
  fi
}

# --- Action: Restore ---
cmd_restore() {
  local tool_raw="${1:-}"
  shift || true

  case "$tool_raw" in
    help|-h|--help)
      cmd_help
      return 0
      ;;
    "")
      log_err "Missing tool name."
      echo "Usage: aa restore <tool|all> <source_path_or_gdrive_query> [--gdrive]"
      exit 1
      ;;
  esac

  local tool
  tool="$(normalize_tool_name "$tool_raw")"

  local src_path=""
  local use_gdrive=false

  while [ $# -gt 0 ]; do
    case "$1" in
      --gdrive|-g)
        use_gdrive=true
        shift
        ;;
      *)
        if [ -z "$src_path" ]; then
          src_path="$1"
        fi
        shift
        ;;
    esac
  done

  if [ -z "$src_path" ]; then
    log_err "Missing backup source path or Google Drive query/ID."
    exit 1
  fi

  local local_archive="$src_path"
  local tmp_download_dir=""

  if [ "$use_gdrive" = "true" ]; then
    check_gdrive_support
    log_info "Fetching backup from Google Drive matching: ${BOLD}$src_path${RESET}..."
    tmp_download_dir="$(mktemp -d)"
    TMP_DIRS+=("$tmp_download_dir")

    local dl_res
    dl_res="$("$WORKSPACE_PY" "$GDRIVE_HELPER" download "$src_path" "$tmp_download_dir")"
    local dl_path
    dl_path="$(echo "$dl_res" | jq -r '.local_path // empty')"
    if [ -z "$dl_path" ] || [ ! -f "$dl_path" ]; then
      log_err "Failed to download backup archive from Google Drive: $dl_res"
      exit 1
    fi
    local_archive="$dl_path"
    log_ok "Downloaded archive to: $local_archive"
  fi

  if [ ! -f "$local_archive" ]; then
    log_err "Backup file not found: $local_archive"
    exit 1
  fi

  log_info "Inspecting backup archive: $local_archive"
  local extract_dir
  extract_dir="$(mktemp -d)"
  TMP_DIRS+=("$extract_dir")

  tar -xzf "$local_archive" -C "$extract_dir"

  if [ ! -f "$extract_dir/manifest.json" ]; then
    log_err "Invalid backup archive: missing manifest.json"
    exit 1
  fi

  local archive_tool
  archive_tool="$(jq -r '.tool // empty' "$extract_dir/manifest.json")"
  log_sub "Archive target tool: $archive_tool"

  local tools_to_restore=()
  if [ "$tool" = "all" ]; then
    if [ "$archive_tool" = "all" ]; then
      while IFS= read -r t; do
        tools_to_restore+=("$t")
      done < <(jq -r '.tools_included[]?' "$extract_dir/manifest.json")
    else
      tools_to_restore=("$archive_tool")
    fi
  else
    tools_to_restore=("$tool")
  fi

  for t in "${tools_to_restore[@]}"; do
    if [ -d "$extract_dir/$t" ]; then
      log_info "Restoring component: ${BOLD}$t${RESET}..."
      restore_tool_data "$t" "$extract_dir/$t"
    elif [ -d "$extract_dir/data" ] && [ "$archive_tool" = "$t" ]; then
      # Single tool archive where data is at root
      log_info "Restoring single component: ${BOLD}$t${RESET}..."
      restore_tool_data "$t" "$extract_dir"
    else
      log_warn "No data found in archive for: $t (skipping)"
    fi
  done

  log_ok "Restore completed successfully for $tool."
}

# --- Action: List ---
cmd_list() {
  local use_gdrive=false
  while [ $# -gt 0 ]; do
    case "$1" in
      --gdrive|-g) use_gdrive=true; shift ;;
      *) shift ;;
    esac
  done

  log_info "Local Backups in ${BLUE}$BACKUP_STORE${RESET}:"
  if [ -d "$BACKUP_STORE" ]; then
    local count=0
    for f in "$BACKUP_STORE"/*.tar.gz; do
      if [ -f "$f" ]; then
        local sz
        sz="$(du -h "$f" | cut -f1)"
        local dt
        dt="$(date -r "$f" +'%Y-%m-%d %H:%M:%S')"
        echo -e "  ${GREEN}•${RESET} $(basename "$f") ${DIM}(Size: $sz, Modified: $dt)${RESET}"
        count=$((count + 1))
      fi
    done
    [ "$count" -eq 0 ] && echo "  (no local backups found)"
  else
    echo "  (directory does not exist)"
  fi

  if [ "$use_gdrive" = "true" ]; then
    echo ""
    log_info "Google Drive Backups (folder: 'Agents-Arwaky-Backups'):"
    check_gdrive_support
    local list_json
    list_json="$("$WORKSPACE_PY" "$GDRIVE_HELPER" list)"
    local gcount
    gcount="$(echo "$list_json" | jq '. | length')"
    if [ "$gcount" -gt 0 ]; then
      echo "$list_json" | jq -r '.[] | "  • \(.name) (ID: \(.id), Created: \(.createdTime))"'
    else
      echo "  (no backups found in Google Drive folder)"
    fi
  fi
}

cmd_help() {
  echo -e "${BOLD}agents-arwaky Unified Backup & Restore Adapter${RESET}"
  echo -e "${DIM}Securely backup and restore sensitive credentials, databases & login sessions.${RESET}"
  echo ""
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  aa backup <tool|all> [destination] [--gdrive]"
  echo -e "  aa restore <tool|all> <source_or_query> [--gdrive]"
  echo -e "  aa backup list [--gdrive]"
  echo ""
  echo -e "${BOLD}SUPPORTED TOOLS:${RESET}"
  echo -e "  ${GREEN}mnemosyne${RESET}   SQLite database, banks, and memories (~/.local/share/mnemosyne/)"
  echo -e "  ${GREEN}9router${RESET}     Providers, API keys, and cache db (~/.local/share/9router/, tools/9router/)"
  echo -e "  ${GREEN}qwen-web${RESET}    Browser session, cookies, and storage state (~/.local/share/qwen-web/)"
  echo -e "  ${GREEN}workspace${RESET}   Google Workspace OAuth credentials & client_secret.json"
  echo -e "  ${GREEN}anytype${RESET}     Encrypted vault & P2P keys (~/.local/share/anytype-daemon/dot-anytype/)"
  echo -e "  ${GREEN}all${RESET}         All of the above bundled in a single secure archive"
  echo ""
  echo -e "${BOLD}FLAGS:${RESET}"
  echo -e "  ${CYAN}--gdrive, -g${RESET}  Upload to or download from Google Drive ('Agents-Arwaky-Backups' folder)"
  echo ""
  echo -e "${BOLD}EXAMPLES:${RESET}"
  echo -e "  aa backup mnemosyne                     # Local backup to ~/.local/share/backups/"
  echo -e "  aa backup all --gdrive                  # Backup everything and upload to Google Drive"
  echo -e "  aa restore mnemosyne /path/to/file.tar.gz"
  echo -e "  aa restore qwen-web qwen-backup --gdrive # Download from Google Drive and restore login session"
}

# --- Main Dispatcher ---
main() {
  local action="${1:-help}"
  shift || true

  case "$action" in
    backup)  cmd_backup "$@" ;;
    restore) cmd_restore "$@" ;;
    list)    cmd_list "$@" ;;
    help|-h|--help) cmd_help ;;
    *)
      # Allow shorthand `backup-manager.sh mnemosyne` or `backup-manager.sh list`
      if [ "$action" = "mnemosyne" ] || [ "$action" = "9router" ] || [ "$action" = "qwen-web" ] || [ "$action" = "workspace" ] || [ "$action" = "anytype" ] || [ "$action" = "all" ]; then
        cmd_backup "$action" "$@"
      else
        log_err "Unknown backup action: $action"
        cmd_help
        exit 1
      fi
      ;;
  esac
}

main "$@"
