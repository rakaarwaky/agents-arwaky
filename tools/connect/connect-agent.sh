#!/usr/bin/env bash
# tools/connect/connect-agent.sh
# Bridge & Inject agents-arwaky MCP Servers & Global Skills into AI Agent Harnesses
# Supports: Antigravity, Hermes, OpenCode, Claude
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
  local skill_files=()

  # 1. Gather all skills from registered tools via skill-manager logic
  local registered_tools=("lint" "9router" "ponytail" "context7" "codegraph" "anytype" "fetch" "lean-ctx" "vision" "qwen-web" "blender" "skill")
  for tid in "${registered_tools[@]}"; do
    case "$tid" in
      lint)
        [ -f "$REPO_ROOT/tools/lint/SKILL.md" ] && skill_files+=("$REPO_ROOT/tools/lint/SKILL.md")
        while IFS= read -r f; do
          [ -f "$f" ] && skill_files+=("$f")
        done < <(find "$REPO_ROOT/internal/lint-arwaky/.agents/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
        ;;
      9router)
        while IFS= read -r f; do
          [ -f "$f" ] && skill_files+=("$f")
        done < <(find "$REPO_ROOT/vendor/9router/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
        ;;
      ponytail)
        while IFS= read -r f; do
          [ -f "$f" ] && skill_files+=("$f")
        done < <(find "$REPO_ROOT/vendor/ponytail/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
        ;;
      context7)
        while IFS= read -r f; do
          [ -f "$f" ] && skill_files+=("$f")
        done < <(find "$REPO_ROOT/vendor/context7/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
        ;;
      codegraph)
        [ -f "$REPO_ROOT/tools/codegraph/SKILL.md" ] && skill_files+=("$REPO_ROOT/tools/codegraph/SKILL.md")
        while IFS= read -r f; do
          [ -f "$f" ] && skill_files+=("$f")
        done < <(find "$REPO_ROOT/vendor/codegraph/.claude/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
        ;;
      anytype)
        [ -f "$REPO_ROOT/tools/anytype-mcp/SKILL.md" ] && skill_files+=("$REPO_ROOT/tools/anytype-mcp/SKILL.md")
        [ -f "$REPO_ROOT/tools/anytype-mcp/daemon/SKILL.md" ] && skill_files+=("$REPO_ROOT/tools/anytype-mcp/daemon/SKILL.md")
        ;;
      fetch)
        [ -f "$REPO_ROOT/tools/fetch-mcp/SKILL.md" ] && skill_files+=("$REPO_ROOT/tools/fetch-mcp/SKILL.md")
        ;;
      lean-ctx)
        [ -f "$REPO_ROOT/vendor/lean-ctx/skills/lean-ctx/SKILL.md" ] && skill_files+=("$REPO_ROOT/vendor/lean-ctx/skills/lean-ctx/SKILL.md")
        ;;
      vision)
        [ -f "$REPO_ROOT/internal/vision-arwaky/SKILL.md" ] && skill_files+=("$REPO_ROOT/internal/vision-arwaky/SKILL.md")
        ;;
      qwen-web)
        [ -f "$REPO_ROOT/internal/qwen-web-arwaky/SKILL.md" ] && skill_files+=("$REPO_ROOT/internal/qwen-web-arwaky/SKILL.md")
        ;;
      blender)
        [ -f "$REPO_ROOT/internal/blender-arwaky/SKILL.md" ] && skill_files+=("$REPO_ROOT/internal/blender-arwaky/SKILL.md")
        ;;
      skill)
        [ -f "$REPO_ROOT/tools/skill/SKILL.md" ] && skill_files+=("$REPO_ROOT/tools/skill/SKILL.md")
        ;;
    esac
  done

  # 2. Add repository root agent role & review skills (.agents/skills/*)
  if [ -d "$REPO_ROOT/.agents/skills" ]; then
    while IFS= read -r f; do
      [ -f "$f" ] && skill_files+=("$f")
    done < <(find "$REPO_ROOT/.agents/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
  fi

  # 3. Deduplicate by extracted skill name
  for sf in "${skill_files[@]}"; do
    local sname
    sname="$(extract_skill_name "$sf")"
    if [ -n "$sname" ] && [ -z "${seen_names["$sname"]:-}" ]; then
      seen_names["$sname"]=1
      echo "$sf"
    fi
  done
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

  # Handle case where destination path exists as a non-directory file (e.g. symlink/pointer)
  if [ -e "$dest_skill_dir" ] && [ ! -d "$dest_skill_dir" ]; then
    if [ "$force" = "true" ]; then
      rm -f "$dest_skill_dir"
    else
      log_skip "Destination '$dest_skill_dir' exists as a non-directory file (use --force to replace)"
      return 0
    fi
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

# ==============================================================================
# 1. Antigravity Harness Connector
# ==============================================================================
connect_antigravity() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"

  log_header "Connecting to Google Antigravity..."

  local config_dir="$HOME/.gemini/config"
  local mcp_file="$config_dir/mcp_config.json"
  local skills_dir="$config_dir/skills"

  # 1. MCP Configuration
  if [ "$skills_only" != "true" ]; then
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
      log_ok "Antigravity MCP servers configured successfully."
    fi
  fi

  # 2. Global Skills
  if [ "$mcp_only" != "true" ]; then
    log_sub "Target Global Skills: ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills for Antigravity."
  fi
}

# ==============================================================================
# 2. Hermes Harness Connector
# NOTE: User rule: Save strictly in ~/.hermes/skills/, NOT in shared-skills!
# ==============================================================================
connect_hermes() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"

  log_header "Connecting to Hermes Agent..."

  local hermes_home="${XDG_DATA_HOME:-$HOME}/.hermes"
  [ -d "$HOME/.hermes" ] && hermes_home="$HOME/.hermes"
  local config_file="$hermes_home/config.yaml"
  local skills_dir="$hermes_home/skills"

  # 1. MCP Configuration in config.yaml
  if [ "$skills_only" != "true" ]; then
    log_sub "Target MCP Config: ${BLUE}$config_file${RESET}"
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would merge MCP servers into $config_file (mcp_servers: section)"
    else
      mkdir -p "$hermes_home"
      if [ ! -f "$config_file" ]; then
        echo "mcp_servers: {}" > "$config_file"
      fi

      # Determine Python interpreter (prefer Hermes venv with ruamel.yaml for comment preservation)
      local python_cmd=""
      if [ -x "$hermes_home/hermes-agent/venv/bin/python" ]; then
        python_cmd="$hermes_home/hermes-agent/venv/bin/python"
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

  # 2. Global Skills strictly in ~/.hermes/skills/
  if [ "$mcp_only" != "true" ]; then
    log_sub "Target Global Skills (strictly ~/.hermes/skills): ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills for Hermes."
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

  log_header "Connecting to OpenCode..."

  local config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  local config_file="$config_dir/opencode.jsonc"
  local skills_dir="$config_dir/skills"

  # 1. MCP Configuration & Skills Path in opencode.jsonc
  if [ "$skills_only" != "true" ]; then
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
        ' "$config_file" > "$tmp_file"
      fi
      mv "$tmp_file" "$config_file"
      log_ok "OpenCode MCP servers & skill search paths configured successfully."
    fi
  fi

  # 2. Global Skills in ~/.config/opencode/skills/
  if [ "$mcp_only" != "true" ]; then
    log_sub "Target Global Skills: ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills for OpenCode."
  fi
}

# ==============================================================================
# 4. Claude Harness Connector (Claude Desktop & Claude Code CLI)
# ==============================================================================
connect_claude() {
  local force="$1"
  local dry_run="$2"
  local mcp_only="$3"
  local skills_only="$4"

  log_header "Connecting to Claude (Desktop & Code CLI)..."

  local desktop_config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/Claude"
  local desktop_config_file="$desktop_config_dir/claude_desktop_config.json"
  local cli_config_file="$HOME/.claude.json"
  local commands_dir="$HOME/.claude/commands"
  local skills_dir="$HOME/.claude/skills"

  # 1. Claude Desktop Config
  if [ "$skills_only" != "true" ]; then
    log_sub "Target Claude Desktop Config: ${BLUE}$desktop_config_file${RESET}"
    if [ "$dry_run" = "true" ]; then
      log_sub "[DRY-RUN] Would merge MCP servers into $desktop_config_file"
    else
      mkdir -p "$desktop_config_dir"
      if [ ! -f "$desktop_config_file" ] || [ ! -s "$desktop_config_file" ] || ! jq empty "$desktop_config_file" 2>/dev/null; then
        echo '{"mcpServers":{}}' > "$desktop_config_file"
      fi
      local tmp_file
      tmp_file="$(mktemp)"
      if [ "$force" = "true" ]; then
        jq --slurpfile src "$MCP_GENERATED_FILE" '
          .mcpServers = ((.mcpServers // {}) + $src[0].mcpServers)
        ' "$desktop_config_file" > "$tmp_file"
      else
        jq --slurpfile src "$MCP_GENERATED_FILE" '
          .mcpServers = ($src[0].mcpServers + (.mcpServers // {}))
        ' "$desktop_config_file" > "$tmp_file"
      fi
      mv "$tmp_file" "$desktop_config_file"
      log_ok "Claude Desktop MCP configuration updated."
    fi

    # 2. Claude Code CLI Config (if .claude.json exists or ~/.claude directory exists)
    if [ -f "$cli_config_file" ] || [ -d "$HOME/.claude" ]; then
      log_sub "Target Claude Code CLI Config: ${BLUE}$cli_config_file${RESET}"
      if [ "$dry_run" = "true" ]; then
        log_sub "[DRY-RUN] Would merge MCP servers into $cli_config_file"
      else
        if [ ! -f "$cli_config_file" ] || [ ! -s "$cli_config_file" ] || ! jq empty "$cli_config_file" 2>/dev/null; then
          echo '{"mcpServers":{}}' > "$cli_config_file"
        fi
        local tmp_cli
        tmp_cli="$(mktemp)"
        if [ "$force" = "true" ]; then
          jq --slurpfile src "$MCP_GENERATED_FILE" '
            .mcpServers = ((.mcpServers // {}) + $src[0].mcpServers)
          ' "$cli_config_file" > "$tmp_cli"
        else
          jq --slurpfile src "$MCP_GENERATED_FILE" '
            .mcpServers = ($src[0].mcpServers + (.mcpServers // {}))
          ' "$cli_config_file" > "$tmp_cli"
        fi
        mv "$tmp_cli" "$cli_config_file"
        log_ok "Claude Code CLI MCP configuration updated."
      fi
    fi
  fi

  # 3. Claude Slash Commands & Skills
  if [ "$mcp_only" != "true" ]; then
    log_sub "Target Claude Commands: ${BLUE}$commands_dir${RESET}"
    log_sub "Target Claude Skills: ${BLUE}$skills_dir${RESET}"
    local count=0
    while IFS= read -r sf; do
      [ -n "$sf" ] || continue
      local sname
      sname="$(extract_skill_name "$sf")"

      if [ "$dry_run" = "true" ]; then
        log_sub "[DRY-RUN] Would provision Claude command: $commands_dir/$sname.md"
      else
        mkdir -p "$commands_dir"
        if [ ! -f "$commands_dir/$sname.md" ] || [ "$force" = "true" ]; then
          cp "$sf" "$commands_dir/$sname.md"
        fi
        copy_skill_to_dir "$sf" "$skills_dir" "$force" "$dry_run"
      fi
      count=$((count + 1))
    done < <(get_all_skill_files)
    log_ok "Processed $count skills/commands for Claude."
  fi
}

# --- Show Usage Help ---
cmd_help() {
  echo -e "${BOLD}agents-arwaky Harness Connector (${CYAN}aa connect${RESET}${BOLD})${RESET}"
  echo -e "${DIM}Inject agents-arwaky MCP servers and global skills into external agent harnesses.${RESET}"
  echo ""
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  aa connect <agent-harness...> [options]"
  echo ""
  echo -e "${BOLD}TARGET AGENT HARNESSES:${RESET}"
  echo -e "  ${GREEN}--antigravity, antigravity${RESET}  Google Antigravity (~/.gemini/config/)"
  echo -e "  ${GREEN}--hermes, hermes${RESET}            Hermes Agent (~/.hermes/config.yaml & ~/.hermes/skills/)"
  echo -e "  ${GREEN}--opencode, opencode${RESET}        OpenCode (~/.config/opencode/opencode.jsonc)"
  echo -e "  ${GREEN}--claude, claude${RESET}            Claude Desktop & Claude Code CLI"
  echo -e "  ${GREEN}--all, all${RESET}                  Connect to ALL 4 agent harnesses"
  echo ""
  echo -e "${BOLD}OPTIONS:${RESET}"
  echo -e "  ${CYAN}--force, -f${RESET}                 Overwrite existing skill files and update existing MCP entries"
  echo -e "  ${CYAN}--dry-run${RESET}                   Preview modifications without writing to disk"
  echo -e "  ${CYAN}--mcp-only${RESET}                  Only configure MCP servers (skip skills provisioning)"
  echo -e "  ${CYAN}--skills-only${RESET}               Only provision global skills (skip MCP configuration)"
  echo -e "  ${CYAN}--help, -h${RESET}                  Show this help screen"
  echo ""
  echo -e "${BOLD}EXAMPLES:${RESET}"
  echo -e "  aa connect --antigravity"
  echo -e "  aa connect hermes"
  echo -e "  aa connect --opencode"
  echo -e "  aa connect --claude"
  echo -e "  aa connect --all"
  echo -e "  aa connect antigravity hermes --force"
  echo ""
}

# --- Main Dispatcher ---
main() {
  if [ $# -eq 0 ]; then
    cmd_help
    exit 0
  fi

  local targets=()
  local force="false"
  local dry_run="false"
  local mcp_only="false"
  local skills_only="false"

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
      --claude|claude)
        targets+=("claude")
        shift
        ;;
      --all|all)
        targets=("antigravity" "hermes" "opencode" "claude")
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

  ensure_mcp_config

  echo -e "${BOLD}Connecting agents-arwaky to agent harnesses...${RESET}"
  echo "------------------------------------------------------------------"

  for target in "${!unique_targets[@]}"; do
    case "$target" in
      antigravity)
        connect_antigravity "$force" "$dry_run" "$mcp_only" "$skills_only"
        ;;
      hermes)
        connect_hermes "$force" "$dry_run" "$mcp_only" "$skills_only"
        ;;
      opencode)
        connect_opencode "$force" "$dry_run" "$mcp_only" "$skills_only"
        ;;
      claude)
        connect_claude "$force" "$dry_run" "$mcp_only" "$skills_only"
        ;;
    esac
    echo ""
  done

  echo "------------------------------------------------------------------"
  echo -e "${GREEN}${BOLD}Connection complete.${RESET} Agent harnesses are now synchronized with agents-arwaky."
}

main "$@"
