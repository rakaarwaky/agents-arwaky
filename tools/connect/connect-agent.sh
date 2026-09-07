#!/usr/bin/env bash
# tools/connect/connect-agent.sh
# Bridge & Inject agents-arwaky MCP Servers & Global Skills into AI Agent Harnesses
# Supports: Antigravity, Hermes, OpenCode
# Compliant with Linux XDG Base Directory Specification & AES standards

set -euo pipefail

# --- Self-resolve Repository Root ---
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

MANIFEST_FILE="$REPO_ROOT/tools/arwaky/manifest.json"
MCP_GENERATED_FILE="$REPO_ROOT/mcp_servers.generated.json"

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

# --- Logging Helpers ---
log_header() {
  echo -e "${BOLD}${CYAN}==>${RESET} ${BOLD}$1${RESET}"
}

log_sub() {
  echo -e "  ${BLUE}->${RESET} $1"
}

log_ok() {
  echo -e "  ${GREEN}✓${RESET} $1"
}

log_skip() {
  echo -e "  ${YELLOW}↷${RESET} $1"
}

log_warn() {
  echo -e "  ${YELLOW}⚠${RESET} $1"
}

log_err() {
  echo -e "  ${RED}✗${RESET} $1" >&2
}

# --- Ensure Unified MCP Config Exists & Up-to-Date ---
ensure_mcp_config() {
  if [ ! -f "$MCP_GENERATED_FILE" ] || [ "$MANIFEST_FILE" -nt "$MCP_GENERATED_FILE" ]; then
    log_sub "Regenerating unified MCP configuration..."
    "$REPO_ROOT/tools/mcp/generate-config.sh" "$MCP_GENERATED_FILE" >/dev/null
  fi
}

# --- Extract Skill Name from SKILL.md ---
extract_skill_name() {
  local file="$1"
  local name=""
  if [ -f "$file" ]; then
    name="$(awk '
      BEGIN { in_fm=0 }
      /^---$/ { in_fm++; next }
      in_fm == 1 && /^name:/ {
        sub(/^name:[ \t]*/, "")
        gsub(/^["\x27]|["\x27]$/, "")
        print
        exit
      }
      in_fm >= 2 { exit }
    ' "$file")"
  fi
  if [ -z "$name" ]; then
    name="$(basename "$(dirname "$file")")"
  fi
  echo "$name"
}

# --- Collect All Available Skills in agents-arwaky ---
# Returns one absolute path to SKILL.md per line (deduplicated by skill name)
get_all_skill_files() {
  local -A seen_names=()
  local sf sname

  while IFS= read -r sf; do
    [ -f "$sf" ] || continue
    sname="$(extract_skill_name "$sf")"
    if [ -n "$sname" ] && [ -z "${seen_names["$sname"]:-}" ]; then
      seen_names["$sname"]=1
      echo "$sf"
    fi
  done < <(find "$REPO_ROOT/tools" "$REPO_ROOT/internal" "$REPO_ROOT/vendor" \
    -name "node_modules" -prune -o \
    -name ".venv" -prune -o \
    -name "venv" -prune -o \
    -name "target" -prune -o \
    -name ".git" -prune -o \
    -name "*copy*" -prune -o \
    -type f -name "SKILL.md" -print 2>/dev/null | sort)
}

# --- Copy Skill Directory Safely ---
copy_skill_to_dir() {
  local src_skill_file="$1"
  local dest_base_dir="$2"
  local force="${3:-false}"
  local dry_run="${4:-false}"

  local sname
  sname="$(extract_skill_name "$src_skill_file")"
  local src_dir
  src_dir="$(dirname "$src_skill_file")"
  local dest_skill_dir="$dest_base_dir/$sname"
  local dest_skill_file="$dest_skill_dir/SKILL.md"

  if [ "$dry_run" = "true" ]; then
    log_sub "[DRY-RUN] Would install skill '$sname' -> $dest_skill_file"
    return 0
  fi

  if [ -f "$dest_skill_file" ] && [ "$force" != "true" ]; then
    log_skip "Skill '$sname' already exists (use --force to overwrite)"
    return 0
  fi

  # Handle case where destination path exists as a non-directory file (e.g. broken pointer/symlink)
  if [ -e "$dest_skill_dir" ] && [ ! -d "$dest_skill_dir" ]; then
    rm -f "$dest_skill_dir"
  fi

  mkdir -p "$dest_skill_dir"
  cp "$src_skill_file" "$dest_skill_file"

  # Copy optional companion assets if present in source skill folder
  for extra in scripts references resources examples; do
    if [ -d "$src_dir/$extra" ]; then
      rm -rf "${dest_skill_dir:?}/$extra"
      cp -r "$src_dir/$extra" "$dest_skill_dir/"
    fi
  done

  log_ok "Skill '$sname' provisioned"
}

# --- 9Router Credentials & Environment Injection Helpers ---
get_9router_credentials() {
  local router_url=""
  local router_key=""

  # 1. Search candidate env files for 9Router configuration
  local env_file=""
  for candidate in \
    "$REPO_ROOT/tools/9router/.env" \
    "$REPO_ROOT/tools/9router/env" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/9router/.env"; do
    if [ -f "$candidate" ]; then
      env_file="$candidate"
      break
    fi
  done

  if [ -n "$env_file" ] && [ -f "$env_file" ]; then
    local port
    router_url="$(grep "^NINEROUTER_URL=" "$env_file" 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d "\"'" || true)"
    port="$(grep -E "^(NINEROUTER_PORT|PORT)=" "$env_file" 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d "\"'" || true)"
    router_key="$(grep "^NINEROUTER_KEY=" "$env_file" 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d "\"'" || true)"
    if [ -z "$router_url" ] && [ -n "$port" ]; then
      router_url="http://localhost:$port"
    fi
  fi

  [ -z "$router_url" ] && router_url="http://127.0.0.1:20128"

  # 2. If key is missing from .env, query active key from 9Router DB via container
  if [ -z "$router_key" ]; then
    local engine=""
    command -v podman >/dev/null 2>&1 && engine="podman"
    [ -z "$engine" ] && command -v docker >/dev/null 2>&1 && engine="docker"
    if [ -n "$engine" ]; then
      router_key="$("$engine" exec 9router node -e "
        try {
          const db = require('better-sqlite3')('/app/data/db/data.sqlite');
          const k = db.prepare('SELECT key FROM apiKeys WHERE isActive = 1 ORDER BY createdAt DESC LIMIT 1').get();
          if (k) process.stdout.write(k.key);
        } catch {}
      " 2>/dev/null || true)"
    fi
  fi

  echo "$router_url|$router_key"
}

update_env_file() {
  local file="$1"
  local key="$2"
  local val="$3"
  local dry_run="${4:-false}"

  if [ "$dry_run" = "true" ]; then
    log_sub "[DRY-RUN] Would set $key in $file"
    return 0
  fi

  mkdir -p "$(dirname "$file")"
  touch "$file"
  chmod 600 "$file" 2>/dev/null || true

  if grep -q "^${key}=" "$file" 2>/dev/null; then
    local escaped_val
    escaped_val="$(printf '%s\n' "$val" | sed -e 's/[\/&]/\\&/g')"
    sed -i "s|^${key}=.*|${key}=\"${escaped_val}\"|" "$file"
  else
    echo "${key}=\"${val}\"" >> "$file"
  fi
}

inject_9router_env() {
  local target="$1"
  local dry_run="${2:-false}"

  local creds
  creds="$(get_9router_credentials)"
  local router_url="${creds%%|*}"
  local router_key="${creds#*|}"

  if [ -z "$router_key" ]; then
    log_skip "No active 9Router API Key found in .env or database; skipping env injection for $target."
    return 0
  fi

  case "$target" in
    antigravity)
      log_sub "Target Environment: ${BLUE}~/.gemini/config/.env & ~/.gemini/antigravity-cli/.env${RESET}"
      update_env_file "$HOME/.gemini/config/.env" "NINEROUTER_URL" "$router_url" "$dry_run"
      update_env_file "$HOME/.gemini/config/.env" "NINEROUTER_KEY" "$router_key" "$dry_run"
      if [ -d "$HOME/.gemini/antigravity-cli" ]; then
        update_env_file "$HOME/.gemini/antigravity-cli/.env" "NINEROUTER_URL" "$router_url" "$dry_run"
        update_env_file "$HOME/.gemini/antigravity-cli/.env" "NINEROUTER_KEY" "$router_key" "$dry_run"
      fi
      log_ok "Injected NINEROUTER_URL and NINEROUTER_KEY into Antigravity environment."
      ;;
    hermes)
      local hermes_env="${XDG_DATA_HOME:-$HOME}/.hermes/.env"
      [ -d "$HOME/.hermes" ] && hermes_env="$HOME/.hermes/.env"
      log_sub "Target Environment: ${BLUE}$hermes_env${RESET}"
      update_env_file "$hermes_env" "NINEROUTER_URL" "$router_url" "$dry_run"
      update_env_file "$hermes_env" "NINEROUTER_KEY" "$router_key" "$dry_run"
      log_ok "Injected NINEROUTER_URL and NINEROUTER_KEY into Hermes main environment."

      # Multi-profile support: inject into all Hermes profile environments
      local hermes_profiles_dir="${hermes_env%/.env}/profiles"
      if [ -d "$hermes_profiles_dir" ]; then
        for pdir in "$hermes_profiles_dir"/*; do
          if [ -d "$pdir" ]; then
            local pname
            pname="$(basename "$pdir")"
            local penv="$pdir/.env"
            update_env_file "$penv" "NINEROUTER_URL" "$router_url" "$dry_run"
            update_env_file "$penv" "NINEROUTER_KEY" "$router_key" "$dry_run"
            log_ok "Injected NINEROUTER_URL and NINEROUTER_KEY into Hermes profile '$pname' environment."
          fi
        done
      fi
      ;;
    opencode)
      local opencode_env="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/.env"
      log_sub "Target Environment: ${BLUE}$opencode_env${RESET}"
      update_env_file "$opencode_env" "NINEROUTER_URL" "$router_url" "$dry_run"
      update_env_file "$opencode_env" "NINEROUTER_KEY" "$router_key" "$dry_run"
      if [ -d "$HOME/.opencode" ]; then
        update_env_file "$HOME/.opencode/.env" "NINEROUTER_URL" "$router_url" "$dry_run"
        update_env_file "$HOME/.opencode/.env" "NINEROUTER_KEY" "$router_key" "$dry_run"
      fi
      log_ok "Injected NINEROUTER_URL and NINEROUTER_KEY into OpenCode environment."
      ;;
    qwencode|qwen)
      local qwen_env="${QWEN_HOME:-$HOME/.qwen}/.env"
      log_sub "Target Environment: ${BLUE}$qwen_env${RESET}"
      update_env_file "$qwen_env" "NINEROUTER_URL" "$router_url" "$dry_run"
      update_env_file "$qwen_env" "NINEROUTER_KEY" "$router_key" "$dry_run"
      log_ok "Injected NINEROUTER_URL and NINEROUTER_KEY into Qwen Code environment."
      ;;
    session)
      local env_d="${XDG_CONFIG_HOME:-$HOME/.config}/environment.d/9router.conf"
      log_sub "Target Session Environment: ${BLUE}$env_d${RESET}"
      update_env_file "$env_d" "NINEROUTER_URL" "$router_url" "$dry_run"
      update_env_file "$env_d" "NINEROUTER_KEY" "$router_key" "$dry_run"
      log_ok "Injected NINEROUTER_URL and NINEROUTER_KEY into user session environment.d."
      ;;
  esac
}

# --- Ensure Shared Mnemosyne Memory DB Path across Environments ---
inject_mnemosyne_env() {
  local target="$1"
  local dry_run="${2:-false}"
  local data_dir="${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne"

  case "$target" in
    antigravity)
      log_sub "Target Environment (Mnemosyne): ${BLUE}~/.gemini/config/.env & ~/.gemini/antigravity-cli/.env${RESET}"
      update_env_file "$HOME/.gemini/config/.env" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      if [ -d "$HOME/.gemini/antigravity-cli" ]; then
        update_env_file "$HOME/.gemini/antigravity-cli/.env" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      fi
      log_ok "Injected MNEMOSYNE_DATA_DIR into Antigravity environment."
      ;;
    hermes)
      local hermes_env="${XDG_DATA_HOME:-$HOME}/.hermes/.env"
      [ -d "$HOME/.hermes" ] && hermes_env="$HOME/.hermes/.env"
      log_sub "Target Environment (Mnemosyne): ${BLUE}$hermes_env${RESET}"
      update_env_file "$hermes_env" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      local hermes_profiles_dir="${hermes_env%/.env}/profiles"
      if [ -d "$hermes_profiles_dir" ]; then
        for pdir in "$hermes_profiles_dir"/*; do
          if [ -d "$pdir" ]; then
            local pname
            pname="$(basename "$pdir")"
            local penv="$pdir/.env"
            update_env_file "$penv" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
            log_ok "Injected MNEMOSYNE_DATA_DIR into Hermes profile '$pname' environment."
          fi
        done
      fi
      log_ok "Injected MNEMOSYNE_DATA_DIR into Hermes main environment."
      ;;
    opencode)
      local opencode_env="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/.env"
      log_sub "Target Environment (Mnemosyne): ${BLUE}$opencode_env${RESET}"
      update_env_file "$opencode_env" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      if [ -d "$HOME/.opencode" ]; then
        update_env_file "$HOME/.opencode/.env" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      fi
      log_ok "Injected MNEMOSYNE_DATA_DIR into OpenCode environment."
      ;;
    qwencode|qwen)
      local qwen_env="${QWEN_HOME:-$HOME/.qwen}/.env"
      log_sub "Target Environment (Mnemosyne): ${BLUE}$qwen_env${RESET}"
      update_env_file "$qwen_env" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      log_ok "Injected MNEMOSYNE_DATA_DIR into Qwen Code environment."
      ;;
    session)
      local env_d="${XDG_CONFIG_HOME:-$HOME/.config}/environment.d/mnemosyne.conf"
      log_sub "Target Session Environment (Mnemosyne): ${BLUE}$env_d${RESET}"
      update_env_file "$env_d" "MNEMOSYNE_DATA_DIR" "$data_dir" "$dry_run"
      log_ok "Injected MNEMOSYNE_DATA_DIR into user session environment.d."
      ;;
  esac
}


# ==============================================================================
# 1. Antigravity Harness Connector
# ==============================================================================
connect_antigravity() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"
  local env_only="${5:-false}"

  log_header "Connecting to Google Antigravity..."

  local config_dir="$HOME/.gemini/config"
  local mcp_file="$config_dir/mcp_config.json"
  local skills_dir="$config_dir/skills"

  # 1. MCP Configuration
  if [ "$skills_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target MCP Config: ${BLUE}$mcp_file${RESET}"
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would merge MCP servers into $mcp_file"
    else
      mkdir -p "$config_dir"
      if [ ! -f "$mcp_file" ] || [ ! -s "$mcp_file" ] || ! jq empty "$mcp_file" 2>/dev/null; then
        echo '{"mcpServers":{}}' > "$mcp_file"
      fi

      local tmp_file
      tmp_file="$(mktemp)"
      if [ "$force" = "true" ]; then
        jq --slurpfile src "$MCP_GENERATED_FILE" '
          .mcpServers = ((.mcpServers // {}) + $src[0].mcpServers)
        ' "$mcp_file" > "$tmp_file"
      else
        jq --slurpfile src "$MCP_GENERATED_FILE" '
          .mcpServers = ($src[0].mcpServers + (.mcpServers // {}))
        ' "$mcp_file" > "$tmp_file"
      fi
      mv "$tmp_file" "$mcp_file"
      # Ensure compatibility with both ~/.gemini/config, ~/.gemini/antigravity-cli, and ~/.gemini/antigravity
      if [ -d "$HOME/.gemini/antigravity-cli" ]; then
        ln -sf "$mcp_file" "$HOME/.gemini/antigravity-cli/mcp_config.json"
      fi
      if [ -d "$HOME/.gemini/antigravity" ]; then
        ln -sf "$mcp_file" "$HOME/.gemini/antigravity/mcp_config.json"
      fi
      log_ok "Antigravity MCP servers configured successfully."
    fi
  fi

  # 2. Global Skills
  if [ "$mcp_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target Global Skills: ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    if [ -d "$HOME/.gemini/antigravity-cli" ]; then
      ln -sfn "$skills_dir" "$HOME/.gemini/antigravity-cli/skills" 2>/dev/null || true
    fi
    if [ -d "$HOME/.gemini/antigravity" ]; then
      ln -sfn "$skills_dir" "$HOME/.gemini/antigravity/skills" 2>/dev/null || true
    fi
    log_ok "Processed $count skills for Antigravity."
  fi


  # 4. Environment Variables (NINEROUTER_URL, NINEROUTER_KEY, MNEMOSYNE_DATA_DIR)
  if [ "$mcp_only" != "true" ] && [ "$skills_only" != "true" ] || [ "$env_only" = "true" ]; then
    inject_9router_env "antigravity" "$dry_run"
    inject_mnemosyne_env "antigravity" "$dry_run"
  fi
}

# ==============================================================================
# 2. Hermes Harness Connector (Main & Multi-Profiles)
# NOTE: User rule: Save strictly in ~/.hermes/skills/ (or profile skills), NOT in shared-skills!
# ==============================================================================
connect_hermes_instance() {
  local target_dir="$1"
  local profile_label="$2"
  local force="$3"
  local dry_run="$4"
  local mcp_only="$5"
  local skills_only="$6"
  local env_only="$7"
  local hermes_root="$8"

  local config_file="$target_dir/config.yaml"
  local skills_dir="$target_dir/skills"

  log_header "Connecting to Hermes ($profile_label)..."

  # 1. MCP Configuration in config.yaml
  if [ "$skills_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target MCP Config: ${BLUE}$config_file${RESET}"
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would merge MCP servers into $config_file (mcp_servers: section)"
    else
      mkdir -p "$target_dir"
      if [ ! -f "$config_file" ]; then
        echo "mcp_servers: {}" > "$config_file"
      fi

      # Determine Python interpreter (prefer Hermes venv with ruamel.yaml for comment preservation)
      local python_cmd=""
      if [ -x "$hermes_root/hermes-agent/venv/bin/python" ]; then
        python_cmd="$hermes_root/hermes-agent/venv/bin/python"
      elif command -v python3 >/dev/null 2>&1; then
        python_cmd="python3"
      fi

      if [ -n "$python_cmd" ]; then
        "$python_cmd" - "$config_file" "$MCP_GENERATED_FILE" "$force" << 'EOF'
import sys, json
from pathlib import Path

config_path = Path(sys.argv[1])
mcp_path = Path(sys.argv[2])
force = sys.argv[3].lower() == "true"

with open(mcp_path, "r", encoding="utf-8") as f:
    servers = json.load(f).get("mcpServers", {})

try:
    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.load(f) or {}
except Exception:
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    yaml_fallback = True
else:
    yaml_fallback = False

if "mcp_servers" not in data or data["mcp_servers"] is None:
    data["mcp_servers"] = {}

for name, srv in servers.items():
    entry = {"command": srv["command"], "enabled": True}
    if "args" in srv:
        entry["args"] = srv["args"]
    if "env" in srv:
        entry["env"] = srv["env"]
    data["mcp_servers"][name] = entry

with open(config_path, "w", encoding="utf-8") as f:
    if yaml_fallback:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    else:
        yaml.dump(data, f)
EOF
        log_ok "Hermes MCP servers configured in $config_file."
      else
        log_warn "Python interpreter not available; skipping automated YAML merge."
      fi
    fi
  fi

  # 2. Global Skills strictly in <target_dir>/skills/
  if [ "$mcp_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target Global Skills (strictly $skills_dir): ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills for Hermes ($profile_label)."
  fi

}

connect_hermes() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"
  local env_only="${5:-false}"

  log_header "Connecting to Hermes Agent (Main & Multi-Profiles)..."

  local hermes_home="${XDG_DATA_HOME:-$HOME}/.hermes"
  [ -d "$HOME/.hermes" ] && hermes_home="$HOME/.hermes"

  # 1. Connect Default/Main Hermes Instance
  connect_hermes_instance "$hermes_home" "Main Profile" "$force" "$dry_run" "$mcp_only" "$skills_only" "$env_only" "$hermes_home"

  # 2. Connect All Multi-Profiles under ~/.hermes/profiles/
  local profiles_dir="$hermes_home/profiles"
  if [ -d "$profiles_dir" ]; then
    local p_count=0
    for pdir in "$profiles_dir"/*; do
      if [ -d "$pdir" ]; then
        local pname
        pname="$(basename "$pdir")"
        connect_hermes_instance "$pdir" "Profile: $pname" "$force" "$dry_run" "$mcp_only" "$skills_only" "$env_only" "$hermes_home"
        p_count=$((p_count + 1))
      fi
    done
    log_ok "Synchronized all $p_count Hermes multi-profiles."
  fi

  # 3. Environment Variables (NINEROUTER_URL, NINEROUTER_KEY, MNEMOSYNE_DATA_DIR) for Main & Profiles
  if [ "$env_only" = "true" ] || { [ "$mcp_only" != "true" ] && [ "$skills_only" != "true" ]; }; then
    inject_9router_env "hermes" "$dry_run"
    inject_mnemosyne_env "hermes" "$dry_run"
  fi
}

# ==============================================================================
# 3. OpenCode Harness Connector
# ==============================================================================
connect_opencode() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"
  local env_only="${5:-false}"

  log_header "Connecting to OpenCode..."

  local config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  local config_file="$config_dir/opencode.jsonc"
  local skills_dir="$config_dir/skills"

  # 1. MCP Configuration & Skills Path in opencode.jsonc
  if [ "$skills_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target OpenCode Config: ${BLUE}$config_file${RESET}"
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would update .mcp and .skills.paths in $config_file"
    else
      mkdir -p "$config_dir"
      if [ ! -f "$config_file" ] || [ ! -s "$config_file" ] || ! jq empty "$config_file" 2>/dev/null; then
        # shellcheck disable=SC2016
        echo '{"$schema": "https://opencode.ai/config.json"}' > "$config_file"
      fi

      local tmp_file
      tmp_file="$(mktemp)"
      if [ "$force" = "true" ]; then
        jq --arg sdir "$skills_dir" --slurpfile src "$MCP_GENERATED_FILE" '
          .mcp = ((.mcp // {}) + ($src[0].mcpServers | to_entries | map({
            key: .key,
            value: {
              type: "local",
              command: ([.value.command] + (.value.args // [])),
              environment: (.value.env // {}),
              enabled: true
            }
            | if (.value.environment | length == 0) then del(.value.environment) else . end
          }) | from_entries))
          | .skills = ((.skills // {}) * {
              paths: (((.skills.paths // []) + [$sdir]) | unique)
            })
          | .permission = ((.permission // {}) + {
              "bash": "deny",
              "glob": "deny",
              "grep": "deny",
              "read": "deny"
            })
        ' "$config_file" > "$tmp_file"
      else
        jq --arg sdir "$skills_dir" --slurpfile src "$MCP_GENERATED_FILE" '
          .mcp = (($src[0].mcpServers | to_entries | map({
            key: .key,
            value: {
              type: "local",
              command: ([.value.command] + (.value.args // [])),
              environment: (.value.env // {}),
              enabled: true
            }
            | if (.value.environment | length == 0) then del(.value.environment) else . end
          }) | from_entries) + (.mcp // {}))
          | .skills = ((.skills // {}) * {
              paths: (((.skills.paths // []) + [$sdir]) | unique)
            })
          | .permission = ((.permission // {}) + {
              "bash": "deny",
              "glob": "deny",
              "grep": "deny",
              "read": "deny"
            })
        ' "$config_file" > "$tmp_file"
      fi
      mv "$tmp_file" "$config_file"
      log_ok "OpenCode MCP servers, shadow permissions & skill search paths configured successfully."
    fi
  fi

  # 2. Global Skills in ~/.config/opencode/skills/
  if [ "$mcp_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target Global Skills: ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills for OpenCode."
  fi


  # 4. Environment Variables (NINEROUTER_URL, NINEROUTER_KEY, MNEMOSYNE_DATA_DIR)
  if [ "$env_only" = "true" ] || { [ "$mcp_only" != "true" ] && [ "$skills_only" != "true" ]; }; then
    inject_9router_env "opencode" "$dry_run"
    inject_mnemosyne_env "opencode" "$dry_run"
  fi
}

# ==============================================================================
# 4. Qwen Code (qwencode) Harness Connector
# ==============================================================================
connect_qwencode() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"
  local env_only="${5:-false}"

  log_header "Connecting to Qwen Code (qwencode)..."

  local qwen_home="${QWEN_HOME:-$HOME/.qwen}"
  local settings_file="$qwen_home/settings.json"
  local skills_dir="$qwen_home/skills"

  # 1. MCP Configuration in settings.json
  if [ "$skills_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target MCP Config: ${BLUE}$settings_file${RESET}"
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would merge MCP servers into $settings_file (mcpServers: section)"
    else
      mkdir -p "$qwen_home"
      if [ ! -f "$settings_file" ] || [ ! -s "$settings_file" ] || ! jq empty "$settings_file" 2>/dev/null; then
        echo '{"mcpServers":{}}' > "$settings_file"
      fi

      local tmp_file
      tmp_file="$(mktemp)"
      if [ "$force" = "true" ]; then
        jq --slurpfile src "$MCP_GENERATED_FILE" '
          .mcpServers = ((.mcpServers // {}) + $src[0].mcpServers)
        ' "$settings_file" > "$tmp_file"
      else
        jq --slurpfile src "$MCP_GENERATED_FILE" '
          .mcpServers = ($src[0].mcpServers + (.mcpServers // {}))
        ' "$settings_file" > "$tmp_file"
      fi
      mv "$tmp_file" "$settings_file"
      log_ok "Qwen Code MCP servers configured successfully."
    fi
  fi

  # 2. Global Skills in ~/.qwen/skills/
  if [ "$mcp_only" != "true" ] && [ "$env_only" != "true" ]; then
    log_sub "Target Global Skills: ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills for Qwen Code."
  fi


  # 4. Environment Variables (NINEROUTER_URL, NINEROUTER_KEY, MNEMOSYNE_DATA_DIR)
  if [ "$env_only" = "true" ] || { [ "$mcp_only" != "true" ] && [ "$skills_only" != "true" ]; }; then
    inject_9router_env "qwencode" "$dry_run"
    inject_mnemosyne_env "qwencode" "$dry_run"
  fi
}


# ==============================================================================
# Disconnect (Unconnect) Connectors — reverse of connect_* above
# Removes agents-arwaky MCP servers, provisioned skills, and injected env vars
# from each agent harness. Safe: only touches keys/entries that agents-arwaky
# itself injected (driven by MCP_GENERATED_FILE or the static fallback list).
# ==============================================================================

# --- Resolve the list of MCP server names owned by agents-arwaky ---
get_arwaky_mcp_server_names() {
  local names=""
  if [ -f "$MCP_GENERATED_FILE" ]; then
    names="$(jq -r '.mcpServers | keys[]' "$MCP_GENERATED_FILE" 2>/dev/null || true)"
  fi
  if [ -z "$names" ]; then
    # Static fallback mirroring tools/mcp/generate-config.sh
    names="context7
fetch
ponytail
anytype
codegraph
vision
qwen-web
blender
lint
workspace
mnemosyne"
  fi
  printf '%s\n' "$names"
}

# --- Remove one env key from a .env file ---
remove_env_key() {
  local file="$1"
  local key="$2"
  local dry_run="${3:-false}"
  [ -f "$file" ] || return 0
  if [ "$dry_run" = "true" ]; then
    log_sub "[DRY-RUN] Would remove $key from $file"
    return 0
  fi
  sed -i "/^${key}=/d" "$file" 2>/dev/null || true
  log_ok "Removed $key from $file"
}

# --- Remove provisioned skills that came from agents-arwaky ---
remove_provisioned_skills() {
  local dest_base_dir="$1"
  local dry_run="${2:-false}"
  [ -d "$dest_base_dir" ] || return 0
  local sname dest
  while IFS= read -r sf; do
    [ -n "$sf" ] || continue
    sname="$(extract_skill_name "$sf")"
    [ -n "$sname" ] || continue
    dest="$dest_base_dir/$sname"
    if [ -d "$dest" ]; then
      if [ "$dry_run" = "true" ]; then
        log_sub "[DRY-RUN] Would remove skill '$sname' from $dest_base_dir"
      else
        rm -rf "$dest"
        log_ok "Removed skill '$sname' from $dest_base_dir"
      fi
    fi
  done < <(get_all_skill_files)
}

# --- Remove agents-arwaky MCP servers from a JSON mcpServers map ---
remove_mcp_servers_json() {
  local file="$1"
  local key="$2"          # top-level key holding the server map ("mcpServers" or "mcp")
  local dry_run="${3:-false}"
  [ -f "$file" ] || return 0
  local names
  names="$(get_arwaky_mcp_server_names)"
  if [ "$dry_run" = "true" ]; then
    log_sub "[DRY-RUN] Would remove agents-arwaky servers from $file"
    return 0
  fi
  local tmp
  tmp="$(mktemp)"
  cp "$file" "$tmp"
  local n
  for n in $names; do
    jq --arg n "$n" "del(.${key}[\$n])" "$tmp" > "$tmp.$$" 2>/dev/null && mv "$tmp.$$" "$tmp" || true
  done
  mv "$tmp" "$file"
  log_ok "Removed agents-arwaky MCP servers from $file"
}

# --- 1. Antigravity Disconnect ---
disconnect_antigravity() {
  local dry_run="${1:-false}"
  log_header "Disconnecting from Google Antigravity..."
  local config_dir="$HOME/.gemini/config"
  local mcp_file="$config_dir/mcp_config.json"
  local skills_dir="$config_dir/skills"

  remove_mcp_servers_json "$mcp_file" "mcpServers" "$dry_run"
  remove_provisioned_skills "$skills_dir" "$dry_run"

  # Remove env keys injected by agents-arwaky
  remove_env_key "$config_dir/.env" "NINEROUTER_URL" "$dry_run"
  remove_env_key "$config_dir/.env" "NINEROUTER_KEY" "$dry_run"
  remove_env_key "$config_dir/.env" "MNEMOSYNE_DATA_DIR" "$dry_run"
  if [ -d "$HOME/.gemini/antigravity-cli" ]; then
    remove_mcp_servers_json "$HOME/.gemini/antigravity-cli/mcp_config.json" "mcpServers" "$dry_run"
    remove_env_key "$HOME/.gemini/antigravity-cli/.env" "NINEROUTER_URL" "$dry_run"
    remove_env_key "$HOME/.gemini/antigravity-cli/.env" "NINEROUTER_KEY" "$dry_run"
    remove_env_key "$HOME/.gemini/antigravity-cli/.env" "MNEMOSYNE_DATA_DIR" "$dry_run"
  fi
  log_ok "Antigravity disconnect complete."
}

# --- 2. Hermes Disconnect (Main + Multi-Profiles) ---
disconnect_hermes_instance() {
  local target_dir="$1"
  local profile_label="$2"
  local dry_run="$3"
  local config_file="$target_dir/config.yaml"
  local skills_dir="$target_dir/skills"

  log_header "Disconnecting from Hermes ($profile_label)..."
  if [ -f "$config_file" ]; then
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would remove agents-arwaky MCP servers from $config_file"
    else
      local names
      names="$(get_arwaky_mcp_server_names | tr '\n' ' ')"
      local python_cmd=""
      if [ -x "${XDG_DATA_HOME:-$HOME}/.hermes/hermes-agent/venv/bin/python" ]; then
        python_cmd="${XDG_DATA_HOME:-$HOME}/.hermes/hermes-agent/venv/bin/python"
      elif command -v python3 >/dev/null 2>&1; then
        python_cmd="python3"
      fi
      if [ -n "$python_cmd" ]; then
        # shellcheck disable=SC2086
        "$python_cmd" - "$config_file" $names << 'PYEOF'
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
to_remove = set(sys.argv[2:])

try:
    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.load(f) or {}
    yaml_fallback = False
except Exception:
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    yaml_fallback = True

if isinstance(data, dict) and isinstance(data.get("mcp_servers"), dict):
    for name in list(to_remove):
        data["mcp_servers"].pop(name, None)
    if not data["mcp_servers"]:
        data.pop("mcp_servers", None)

with open(config_path, "w", encoding="utf-8") as f:
    if yaml_fallback:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    else:
        yaml.dump(data, f)
PYEOF
        log_ok "Removed agents-arwaky MCP servers from $config_file"
      else
        log_warn "Python interpreter not available; skipping YAML cleanup."
      fi
    fi
  fi

  remove_provisioned_skills "$skills_dir" "$dry_run"

  remove_env_key "$target_dir/.env" "NINEROUTER_URL" "$dry_run"
  remove_env_key "$target_dir/.env" "NINEROUTER_KEY" "$dry_run"
  remove_env_key "$target_dir/.env" "MNEMOSYNE_DATA_DIR" "$dry_run"
}

disconnect_hermes() {
  local dry_run="${1:-false}"
  log_header "Disconnecting from Hermes Agent (Main & Multi-Profiles)..."
  local hermes_home="${XDG_DATA_HOME:-$HOME}/.hermes"
  [ -d "$HOME/.hermes" ] && hermes_home="$HOME/.hermes"

  disconnect_hermes_instance "$hermes_home" "Main Profile" "$dry_run"

  local profiles_dir="$hermes_home/profiles"
  if [ -d "$profiles_dir" ]; then
    local p_count=0
    for pdir in "$profiles_dir"/*; do
      if [ -d "$pdir" ]; then
        local pname
        pname="$(basename "$pdir")"
        disconnect_hermes_instance "$pdir" "Profile: $pname" "$dry_run"
        p_count=$((p_count + 1))
      fi
    done
    log_ok "Disconnected all $p_count Hermes multi-profiles."
  fi
  log_ok "Hermes disconnect complete."
}

# --- 3. OpenCode Disconnect ---
disconnect_opencode() {
  local dry_run="${1:-false}"
  log_header "Disconnecting from OpenCode..."
  local config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  local config_file="$config_dir/opencode.jsonc"
  local skills_dir="$config_dir/skills"

  remove_mcp_servers_json "$config_file" "mcp" "$dry_run"
  remove_provisioned_skills "$skills_dir" "$dry_run"

  remove_env_key "$config_dir/.env" "NINEROUTER_URL" "$dry_run"
  remove_env_key "$config_dir/.env" "NINEROUTER_KEY" "$dry_run"
  remove_env_key "$config_dir/.env" "MNEMOSYNE_DATA_DIR" "$dry_run"
  if [ -d "$HOME/.opencode" ]; then
    remove_env_key "$HOME/.opencode/.env" "NINEROUTER_URL" "$dry_run"
    remove_env_key "$HOME/.opencode/.env" "NINEROUTER_KEY" "$dry_run"
    remove_env_key "$HOME/.opencode/.env" "MNEMOSYNE_DATA_DIR" "$dry_run"
  fi
  log_ok "OpenCode disconnect complete."
}

# --- 4. Qwen Code Disconnect ---
disconnect_qwencode() {
  local dry_run="${1:-false}"
  log_header "Disconnecting from Qwen Code (qwencode)..."
  local qwen_home="${QWEN_HOME:-$HOME/.qwen}"
  local settings_file="$qwen_home/settings.json"
  local skills_dir="$qwen_home/skills"

  remove_mcp_servers_json "$settings_file" "mcpServers" "$dry_run"
  remove_provisioned_skills "$skills_dir" "$dry_run"

  remove_env_key "$qwen_home/.env" "NINEROUTER_URL" "$dry_run"
  remove_env_key "$qwen_home/.env" "NINEROUTER_KEY" "$dry_run"
  remove_env_key "$qwen_home/.env" "MNEMOSYNE_DATA_DIR" "$dry_run"
  log_ok "Qwen Code disconnect complete."
}

# --- Disconnect All Harnesses ---
disconnect_all() {
  local dry_run="${1:-false}"
  log_header "Disconnecting agents-arwaky from ALL agent harnesses..."
  echo "------------------------------------------------------------------"
  disconnect_antigravity "$dry_run"
  echo ""
  disconnect_hermes "$dry_run"
  echo ""
  disconnect_opencode "$dry_run"
  echo ""
  disconnect_qwencode "$dry_run"
  echo "------------------------------------------------------------------"
  echo -e "${GREEN}${BOLD}Disconnect complete.${RESET} agents-arwaky entries removed from all harnesses."
}


# ==============================================================================
# Legacy lean-ctx remnant cleanup (post-uninstall lean-ctx)
# Removes leftover lean-ctx MCP entries, skill dirs, HERMES.md blocks and the
# 97MB binary that older installs dropped into harnesses and internal-bin.
# ==============================================================================
disconnect_legacy_lean_ctx() {
  local dry_run="${1:-false}"
  log_header "Cleaning up legacy lean-ctx remnants..."

  # 1. Hermes config.yaml (mcp_servers.lean-ctx)
  local hermes_home="${XDG_DATA_HOME:-$HOME}/.hermes"
  [ -d "$HOME/.hermes" ] && hermes_home="$HOME/.hermes"
  local config_file="$hermes_home/config.yaml"
  if [ -f "$config_file" ]; then
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would remove lean-ctx from $config_file"
    else
      local python_cmd="python3"
      [ -x "$hermes_home/hermes-agent/venv/bin/python" ] && python_cmd="$hermes_home/hermes-agent/venv/bin/python"
      "$python_cmd" - "$config_file" << 'PYEOF' || true
import sys
from pathlib import Path
try:
    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(Path(sys.argv[1]), "r", encoding="utf-8") as f:
        data = yaml.load(f) or {}
    fb = False
except Exception:
    import yaml
    with open(Path(sys.argv[1]), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    fb = True
if isinstance(data, dict) and isinstance(data.get("mcp_servers"), dict):
    data["mcp_servers"].pop("lean-ctx", None)
    if not data["mcp_servers"]:
        data.pop("mcp_servers", None)
with open(Path(sys.argv[1]), "w", encoding="utf-8") as f:
    if fb:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    else:
        yaml.dump(data, f)
PYEOF
      log_ok "Removed lean-ctx from $config_file"
    fi
  fi

  # 2. HERMES.md lean-ctx blocks (main + profiles)
  local hmd
  for hmd in "$hermes_home/HERMES.md" "$hermes_home"/profiles/*/HERMES.md; do
    [ -f "$hmd" ] || continue
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would strip lean-ctx blocks from $hmd"
    else
      python3 - "$hmd" << 'PYEOF' || true
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
before = s
s = re.sub(r"(?s)<!--\s*lean-ctx-rules\s*-->.*?<!--\s*/lean-ctx-rules\s*-->\n?", "", s)
s = re.sub(r"(?s)<!--\s*lean-ctx-compression\s*-->.*?<!--\s*/lean-ctx-compression\s*-->\n?", "", s)
s = re.sub(r"(?s)<!--\s*lean-ctx-solution\s*-->.*?<!--\s*/lean-ctx-solution\s*-->\n?", "", s)
s = re.sub(r"(?s)<!--\s*lean-ctx\s*-->.*?<!--\s*/lean-ctx\s*-->\n?", "", s)
s = re.sub(r"(?s)#\s*Lean-CTX.*?(?=\n# |\Z)", "", s, flags=re.I)
if s != before:
    open(p, "w", encoding="utf-8").write(s)
PYEOF
      log_ok "Stripped lean-ctx blocks from $hmd"
    fi
  done

  # 3. Skill dirs named lean-ctx (Hermes main + profiles, Zed, OpenCode, etc.)
  local skill_root
  for skill_root in "$hermes_home/skills" "$hermes_home"/profiles/*/skills; do
    [ -d "$skill_root/lean-ctx" ] || continue
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would remove skill dir $skill_root/lean-ctx"
    else
      rm -rf "$skill_root/lean-ctx"
      log_ok "Removed skill dir $skill_root/lean-ctx"
    fi
  done

  # 4. Zed settings.json lean-ctx block
  local zed_cfg="$HOME/.config/zed/settings.json"
  if [ -f "$zed_cfg" ]; then
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would remove lean-ctx from $zed_cfg"
    else
      if jq 'del(.mcp["lean-ctx"]) // del(.mcpServers["lean-ctx"])' "$zed_cfg" > "$zed_cfg.$$" 2>/dev/null; then
        mv "$zed_cfg.$$" "$zed_cfg"
      else
        rm -f "$zed_cfg.$$"
      fi
      log_ok "Removed lean-ctx from $zed_cfg"
    fi
  fi

  # 5. mcp_servers.json templates that reference lean-ctx
  local tpl
  for tpl in "$HOME"/.config/*/mcp_servers.json; do
    [ -f "$tpl" ] || continue
    if grep -q '"lean-ctx"' "$tpl" 2>/dev/null; then
      if [ "$dry_run" = "true" ]; then
        log_sub "[DRY-RUN] Would remove lean-ctx from $tpl"
      else
        if jq 'del(.mcpServers["lean-ctx"])' "$tpl" > "$tpl.$$" 2>/dev/null; then
          mv "$tpl.$$" "$tpl"
        else
          rm -f "$tpl.$$"
        fi
        log_ok "Removed lean-ctx from $tpl"
      fi
    fi
  done

  # 6. Binary remnants in internal-bin
  local ibin="${XDG_DATA_HOME:-$HOME/.local/share}/agents-arwaky/internal-bin"
  for b in lean-ctx _lc _lc_compress; do
    if [ -e "$ibin/$b" ]; then
      if [ "$dry_run" = "true" ]; then
        log_sub "[DRY-RUN] Would remove binary $ibin/$b"
      else
        rm -f "$ibin/$b"
        log_ok "Removed binary $ibin/$b"
      fi
    fi
  done

  log_ok "Legacy lean-ctx cleanup complete."
}
# --- Disconnect Usage Help ---
cmd_disconnect_help() {
  echo -e "${BOLD}agents-arwaky Harness Disconnector (${CYAN}aa disconnect${RESET}${BOLD})${RESET}"
  echo -e "${DIM}Remove agents-arwaky MCP servers, provisioned skills and env vars from agent harnesses.${RESET}"
  echo ""
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  aa disconnect <agent-harness...> [options]"
  echo ""
  echo -e "${BOLD}TARGET AGENT HARNESSES:${RESET}"
  echo -e "  ${GREEN}--antigravity, antigravity${RESET}  Google Antigravity (~/.gemini/config/)"
  echo -e "  ${GREEN}--hermes, hermes${RESET}            Hermes Agent (Main & all profiles under ~/.hermes/profiles/)"
  echo -e "  ${GREEN}--opencode, opencode${RESET}        OpenCode (~/.config/opencode/opencode.jsonc)"
  echo -e "  ${GREEN}--qwencode, qwencode${RESET}        Qwen Code (~/.qwen/settings.json)"
  echo -e "  ${GREEN}--all, all${RESET}                  Disconnect from ALL 4 agent harnesses"
  echo -e "  ${GREEN}--lean-ctx${RESET}                 Remove legacy lean-ctx remnants (Hermes, Zed, mcp templates, binary)"
  echo ""
  echo -e "${BOLD}OPTIONS:${RESET}"
  echo -e "  ${CYAN}--dry-run${RESET}                   Preview modifications without writing to disk"
  echo -e "  ${CYAN}--help, -h${RESET}                  Show this help screen"
  echo ""
}

# --- Main Dispatcher for disconnect subcommand ---
cmd_disconnect() {
  local targets=()
  local dry_run="false"
  local lean_ctx_only="false"

  while [ $# -gt 0 ]; do
    case "$1" in
      --antigravity|antigravity|agy)
        targets+=("antigravity"); shift ;;
      --hermes|hermes)
        targets+=("hermes"); shift ;;
      --opencode|opencode)
        targets+=("opencode"); shift ;;
      --qwencode|qwencode|--qwen|qwen|qwen-code)
        targets+=("qwencode"); shift ;;
      --lean-ctx|lean-ctx|lean_ctx)
        lean_ctx_only="true"; shift ;;
      --all|all)
        targets=("antigravity" "hermes" "opencode" "qwencode"); shift ;;
      --dry-run)
        dry_run="true"; shift ;;
      --help|-h|help)
        cmd_disconnect_help; exit 0 ;;
      *)
        log_err "Unknown target or option: $1"; echo ""; cmd_disconnect_help; exit 1 ;;
    esac
  done

  # Legacy lean-ctx cleanup only (used by aa uninstall --all / aa reset)
  if [ "$lean_ctx_only" = "true" ]; then
    disconnect_legacy_lean_ctx "$dry_run"
    exit 0
  fi

  if [ "${#targets[@]}" -eq 0 ]; then
    log_err "No target agent harness specified."
    echo ""
    cmd_disconnect_help
    exit 1
  fi

  # Deduplicate targets
  local -A unique_targets=()
  for t in "${targets[@]}"; do
    unique_targets["$t"]=1
  done

  echo -e "${BOLD}Disconnecting agents-arwaky from agent harnesses...${RESET}"
  echo "------------------------------------------------------------------"

  for target in "${!unique_targets[@]}"; do
    case "$target" in
      antigravity) disconnect_antigravity "$dry_run" ;;
      hermes)      disconnect_hermes "$dry_run" ;;
      opencode)    disconnect_opencode "$dry_run" ;;
      qwencode)    disconnect_qwencode "$dry_run" ;;
    esac
    echo ""
  done

  echo "------------------------------------------------------------------"
  echo -e "${GREEN}${BOLD}Disconnect complete.${RESET} agents-arwaky entries removed from selected harnesses."
}
# --- Show Usage Help ---
cmd_help() {
  echo -e "${BOLD}agents-arwaky Harness Connector (${CYAN}aa connect${RESET}${BOLD})${RESET}"
  echo -e "${DIM}Inject agents-arwaky MCP servers and global skills into external agent harnesses.${RESET}"
  echo ""
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  aa connect <agent-harness...> [options]"
  echo -e "  aa disconnect <agent-harness...>   (unconnect / remove agents-arwaky entries)"
  echo ""
  echo -e "${BOLD}TARGET AGENT HARNESSES:${RESET}"
  echo -e "  ${GREEN}--antigravity, antigravity${RESET}  Google Antigravity (~/.gemini/config/)"
  echo -e "  ${GREEN}--hermes, hermes${RESET}            Hermes Agent (Main & all profiles under ~/.hermes/profiles/)"
  echo -e "  ${GREEN}--opencode, opencode${RESET}        OpenCode (~/.config/opencode/opencode.jsonc)"
  echo -e "  ${GREEN}--qwencode, qwencode${RESET}        Qwen Code (~/.qwen/settings.json)"
  echo -e "  ${GREEN}--all, all${RESET}                  Connect to ALL 4 agent harnesses"
  echo ""
  echo -e "${BOLD}OPTIONS:${RESET}"
  echo -e "  ${CYAN}--force, -f${RESET}                 Overwrite existing skill files and update existing MCP entries"
  echo -e "  ${CYAN}--dry-run${RESET}                   Preview modifications without writing to disk"
  echo -e "  ${CYAN}--mcp-only${RESET}                  Only configure MCP servers (skip skills & env provisioning)"
  echo -e "  ${CYAN}--skills-only${RESET}               Only provision global skills (skip MCP & env configuration)"
  echo -e "  ${CYAN}--env-only${RESET}                  Only inject environment variables (NINEROUTER_URL/KEY)"
  echo -e "  ${CYAN}--help, -h${RESET}                  Show this help screen"
  echo ""
  echo -e "${BOLD}EXAMPLES:${RESET}"
  echo -e "  aa connect --antigravity"
  echo -e "  aa connect hermes"
  echo -e "  aa connect --opencode"
  echo -e "  aa connect qwencode"
  echo -e "  aa connect --all"
  echo -e "  aa connect antigravity hermes qwencode --force"
  echo ""
}

# --- Main Dispatcher ---
main() {
  if [ $# -eq 0 ]; then
    cmd_help
    exit 0
  fi

  # Support 'aa disconnect' subcommand (unconnect harnesses)
  if [ "${1:-}" = "disconnect" ] || [ "${1:-}" = "unconnect" ]; then
    shift || true
    cmd_disconnect "$@"
    exit 0
  fi

  local targets=()
  local force="false"
  local dry_run="false"
  local mcp_only="false"
  local skills_only="false"
  local env_only="false"

  while [ $# -gt 0 ]; do
    case "$1" in
      --antigravity|antigravity|agy)
        targets+=("antigravity")
        shift
        ;;
      --hermes|hermes)
        targets+=("hermes")
        shift
        ;;
      --opencode|opencode)
        targets+=("opencode")
        shift
        ;;
      --qwencode|qwencode|--qwen|qwen|qwen-code)
        targets+=("qwencode")
        shift
        ;;
      --all|all)
        targets=("antigravity" "hermes" "opencode" "qwencode")
        shift
        ;;
      --force|-f)
        force="true"
        shift
        ;;
      --dry-run)
        dry_run="true"
        shift
        ;;
      --mcp-only)
        mcp_only="true"
        shift
        ;;
      --skills-only)
        skills_only="true"
        shift
        ;;
      --env-only)
        env_only="true"
        shift
        ;;
      --help|-h|help)
        cmd_help
        exit 0
        ;;
      *)
        log_err "Unknown target or option: $1"
        echo ""
        cmd_help
        exit 1
        ;;
    esac
  done

  if [ "${#targets[@]}" -eq 0 ]; then
    log_err "No target agent harness specified."
    echo ""
    cmd_help
    exit 1
  fi

  # Deduplicate targets
  local -A unique_targets=()
  for t in "${targets[@]}"; do
    unique_targets["$t"]=1
  done

  if [ "$skills_only" != "true" ] && [ "$env_only" != "true" ]; then
    ensure_mcp_config
  fi

  echo -e "${BOLD}Connecting agents-arwaky to agent harnesses...${RESET}"
  echo "------------------------------------------------------------------"

  for target in "${!unique_targets[@]}"; do
    case "$target" in
      antigravity)
        connect_antigravity "$force" "$dry_run" "$mcp_only" "$skills_only" "$env_only"
        ;;
      hermes)
        connect_hermes "$force" "$dry_run" "$mcp_only" "$skills_only" "$env_only"
        ;;
      opencode)
        connect_opencode "$force" "$dry_run" "$mcp_only" "$skills_only" "$env_only"
        ;;
      qwencode)
        connect_qwencode "$force" "$dry_run" "$mcp_only" "$skills_only" "$env_only"
        ;;
    esac
    echo ""
  done

  # Inject user session environment for GUI and shell consistency
  if [ "$env_only" = "true" ] || { [ "$mcp_only" != "true" ] && [ "$skills_only" != "true" ]; }; then
    inject_9router_env "session" "$dry_run"
    inject_mnemosyne_env "session" "$dry_run"
    echo ""
  fi

  echo "------------------------------------------------------------------"
  echo -e "${GREEN}${BOLD}Connection complete.${RESET} Agent harnesses are now synchronized with agents-arwaky."
}

main "$@"
