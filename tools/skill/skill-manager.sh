#!/usr/bin/env bash
# tools/skill/skill-manager.sh
# AI Agent Skill Discovery, Inspection & Provisioning Orchestrator
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

# --- Colors ---
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  GREEN="\033[0;32m"
  CYAN="\033[0;36m"
  YELLOW="\033[0;33m"
  RED="\033[0;31m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  GREEN=""
  CYAN=""
  YELLOW=""
  RED=""
  RESET=""
fi

# --- Helper: Extract description from SKILL.md frontmatter ---
extract_description() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "No description available"
    return
  fi

  local desc
  desc="$(awk '
    BEGIN { in_fm=0 }
    /^---$/ { in_fm++; next }
    in_fm == 1 && /^description:/ {
      sub(/^description:[ \t]*/, "")
      gsub(/^["\x27]|["\x27]$/, "")
      print
      exit
    }
    in_fm >= 2 { exit }
  ' "$file")"

  if [ -n "$desc" ]; then
    echo "$desc"
  else
    # Fallback to first non-heading paragraph
    awk '
      /^#/ { next }
      /^---/ { next }
      /^[a-zA-Z]/ { print; exit }
    ' "$file" | head -n1
  fi
}

# --- Canonical Skill Resolver ---
# Resolves a skill name/tool alias to its canonical source SKILL.md
resolve_skill_file() {
  local query="$1"

  # 1. Direct match in registry mapping
  case "$query" in
    vision|vision-arwaky)
      echo "$REPO_ROOT/internal/vision-arwaky/SKILL.md"
      return 0
      ;;
    qwen-web|qwen-web-arwaky)
      echo "$REPO_ROOT/internal/qwen-web-arwaky/SKILL.md"
      return 0
      ;;
    blender|blender-arwaky)
      echo "$REPO_ROOT/internal/blender-arwaky/SKILL.md"
      return 0
      ;;
    lint|lint-arwaky)
      echo "$REPO_ROOT/tools/lint/SKILL.md"
      return 0
      ;;
    fetch|fetch-mcp)
      echo "$REPO_ROOT/tools/fetch-mcp/SKILL.md"
      return 0
      ;;
    anytype|anytype-mcp)
      echo "$REPO_ROOT/tools/anytype-mcp/SKILL.md"
      return 0
      ;;
    anytype-daemon)
      echo "$REPO_ROOT/tools/anytype-mcp/daemon/SKILL.md"
      return 0
      ;;
    codegraph|codegraph-mcp)
      echo "$REPO_ROOT/tools/codegraph/SKILL.md"
      return 0
      ;;
    context7|context7-mcp)
      echo "$REPO_ROOT/vendor/context7/skills/context7-mcp/SKILL.md"
      return 0
      ;;
    context7-cli)
      echo "$REPO_ROOT/vendor/context7/skills/context7-cli/SKILL.md"
      return 0
      ;;
    lean-ctx)
      echo "$REPO_ROOT/vendor/lean-ctx/skills/lean-ctx/SKILL.md"
      return 0
      ;;
    ponytail|ponytail-mcp)
      echo "$REPO_ROOT/vendor/ponytail/skills/ponytail/SKILL.md"
      return 0
      ;;
    ponytail-audit)
      echo "$REPO_ROOT/vendor/ponytail/skills/ponytail-audit/SKILL.md"
      return 0
      ;;
    9router)
      echo "$REPO_ROOT/vendor/9router/skills/9router/SKILL.md"
      return 0
      ;;
    9router-chat)
      echo "$REPO_ROOT/vendor/9router/skills/9router-chat/SKILL.md"
      return 0
      ;;
    9router-web-search)
      echo "$REPO_ROOT/vendor/9router/skills/9router-web-search/SKILL.md"
      return 0
      ;;
  esac

  # 2. Dynamic check under tools/<query>/SKILL.md
  if [ -f "$REPO_ROOT/tools/$query/SKILL.md" ]; then
    echo "$REPO_ROOT/tools/$query/SKILL.md"
    return 0
  fi

  # 3. Dynamic check under internal/<query>/SKILL.md
  if [ -f "$REPO_ROOT/internal/$query/SKILL.md" ]; then
    echo "$REPO_ROOT/internal/$query/SKILL.md"
    return 0
  fi

  # 4. Dynamic check under vendor/<query>/skills/<query>/SKILL.md
  if [ -f "$REPO_ROOT/vendor/$query/skills/$query/SKILL.md" ]; then
    echo "$REPO_ROOT/vendor/$query/skills/$query/SKILL.md"
    return 0
  fi

  # 5. Search any SKILL.md matching the directory name
  local found
  found="$(find "$REPO_ROOT/tools" "$REPO_ROOT/internal" "$REPO_ROOT/vendor" -type f -name "SKILL.md" 2>/dev/null | grep -E "/${query}/SKILL.md|/${query}-arwaky/SKILL.md|/${query}-mcp/SKILL.md" | head -n1 || true)"
  if [ -n "$found" ] && [ -f "$found" ]; then
    echo "$found"
    return 0
  fi

  return 1
}

# --- Canonical Skill Catalog ---
get_canonical_skills() {
  cat << 'EOF'
vision-arwaky:internal:Unified computer vision, OCR, video analysis & visual memory:internal/vision-arwaky/SKILL.md
qwen-web-arwaky:internal:Qwen AI Web Automation CLI & Playwright MCP:internal/qwen-web-arwaky/SKILL.md
blender-arwaky:internal:Headless 3D execution engine & scene automation:internal/blender-arwaky/SKILL.md
lint-arwaky:internal:AES 7-layer architecture linter for Rust, Python & TS:tools/lint/SKILL.md
anytype-daemon:internal:Anytype headless daemon lifecycle, bot accounts & space sync:tools/anytype-mcp/daemon/SKILL.md
context7-mcp:vendor:Fast Upstash documentation & context retrieval:vendor/context7/skills/context7-mcp/SKILL.md
context7-cli:vendor:Context7 CLI interface for document queries:vendor/context7/skills/context7-cli/SKILL.md
fetch-mcp:vendor:Clean web scraping, HTML-to-markdown & YouTube transcripts:tools/fetch-mcp/SKILL.md
lean-ctx:vendor:Token-lean repository indexing & context compression:vendor/lean-ctx/skills/lean-ctx/SKILL.md
ponytail:vendor:Senior-dev instructions, patterns & audit skills:vendor/ponytail/skills/ponytail/SKILL.md
codegraph:vendor:High-performance code graph engine & symbol intelligence:tools/codegraph/SKILL.md
9router:vendor:Local AI routing gateway & token saver (40+ providers):vendor/9router/skills/9router/SKILL.md
skill-manager:internal:Skill discovery, audit & provisioning orchestrator:tools/skill/SKILL.md
EOF
}

# --- Canonical Skill Packs ---
get_skill_packs() {
  cat << 'EOF'
aes-python:lint-arwaky:12:AES 7-Layer Architecture & Compliance for Python:internal/lint-arwaky/.agents/skills/*-python
aes-rust:lint-arwaky:12:AES 7-Layer Architecture & Compliance for Rust:internal/lint-arwaky/.agents/skills/*-rust
aes-typescript:lint-arwaky:12:AES 7-Layer Architecture & Compliance for TypeScript:internal/lint-arwaky/.agents/skills/*-typescript
agent-roles:ecosystem:5:Multi-Agent Roles (Architect, BA, Tech Lead, Dev, QA):internal/vision-arwaky/.agents/skills/role-*
9router:9router:9:Local AI Gateway Routing, Search & Multimodal Services:vendor/9router/skills/*
ponytail:ponytail:6:Senior Dev Instructions, Debt Analysis & Code Review:vendor/ponytail/skills/*
core-tools:ecosystem:13:Canonical Tool-Usage Skills for all 13 Registered Tools:canonical
EOF
}

cmd_help() {
  echo -e "${BOLD}agents-arwaky Skill Manager (${CYAN}aa skill${RESET}${BOLD})${RESET}"
  echo -e "${DIM}Discover, inspect and provision AI agent skills across internal and vendor tools.${RESET}"
  echo ""
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  aa skill <command> [arguments...]"
  echo ""
  echo -e "${BOLD}COMMANDS:${RESET}"
  echo -e "  ${GREEN}list, ls${RESET}                  List all available internal and vendor skills"
  echo -e "  ${GREEN}pack list, pack ls${RESET}        List available multi-skill packs (AES Python, Rust, TS, Roles, etc.)"
  echo -e "  ${GREEN}pack install${RESET} <pack-name>  Install an entire skill pack to workspace"
  echo -e "  ${GREEN}install, copy, get${RESET} <name> Copy skill or pack to workspace (agents/skill/ & .agents/skills/)"
  echo -e "  ${GREEN}install all, sync${RESET}         Provision all canonical skills to current workspace"
  echo -e "  ${GREEN}show${RESET} <name>               Display the content of a skill's SKILL.md in terminal"
  echo -e "  ${GREEN}check${RESET}                     Audit SKILL.md coverage across all registered tools"
  echo -e "  ${GREEN}help${RESET}                      Show this help screen"
  echo ""
  echo -e "${BOLD}OPTIONS FOR INSTALL:${RESET}"
  echo -e "  ${CYAN}--target <dir>${RESET}            Base directory to install into (default: current directory .)"
  echo -e "  ${CYAN}--dest <path>${RESET}             Exact custom destination folder for the skill"
  echo -e "  ${CYAN}--force, -f${RESET}               Overwrite existing SKILL.md file if present"
  echo ""
  echo -e "${BOLD}EXAMPLES:${RESET}"
  echo -e "  aa skill list"
  echo -e "  aa skill pack list"
  echo -e "  aa skill pack install aes-python"
  echo -e "  aa skill install blender"
  echo -e "  aa skill install fetch --target /path/to/workspace"
  echo -e "  aa skill install all"
  echo -e "  aa skill show lint-arwaky"
  echo ""
}

cmd_list() {
  echo -e "${BOLD}Available AI Agent Skills in agents-arwaky:${RESET}"
  echo "------------------------------------------------------------------------------------------------"
  printf "${BOLD}%-20s %-10s %-10s %-50s${RESET}\n" "SKILL NAME" "CATEGORY" "STATUS" "DESCRIPTION"
  echo "------------------------------------------------------------------------------------------------"

  while IFS=: read -r skill_name category short_desc rel_path; do
    [ -z "$skill_name" ] && continue
    local full_path="$REPO_ROOT/$rel_path"
    local status_str
    if [ -f "$full_path" ]; then
      status_str="${GREEN}[Ready]${RESET}"
    else
      status_str="${YELLOW}[Missing]${RESET}"
    fi

    local cat_color="$CYAN"
    [ "$category" = "internal" ] && cat_color="$GREEN"

    printf "%-20s ${cat_color}%-10s${RESET} %-19b %-50s\n" "$skill_name" "$category" "$status_str" "$short_desc"
  done < <(get_canonical_skills)
  echo "------------------------------------------------------------------------------------------------"
  echo -e "${DIM}Use 'aa skill install <name>' to provision a skill to your active workspace.${RESET}"
}

cmd_check() {
  echo -e "${BOLD}Auditing SKILL.md Readiness across Registered Tools:${RESET}"
  echo "------------------------------------------------------------------------------------------------"
  printf "${BOLD}%-15s %-10s %-12s %-45s${RESET}\n" "TOOL ID" "CATEGORY" "SKILL STATUS" "RESOLVED PATH"
  echo "------------------------------------------------------------------------------------------------"

  local count
  count="$(jq '.tools | length' "$MANIFEST_FILE")"
  local total_ready=0
  local total_missing=0

  for ((i=0; i<count; i++)); do
    local id category
    id="$(jq -r ".tools[$i].id" "$MANIFEST_FILE")"
    category="$(jq -r ".tools[$i].category" "$MANIFEST_FILE")"

    local resolved_path=""
    if resolved_path="$(resolve_skill_file "$id")"; then
      local rel_display="${resolved_path#"$REPO_ROOT"/}"
      printf "%-15s %-10s ${GREEN}%-12s${RESET} %-45s\n" "$id" "$category" "FOUND" "$rel_display"
      total_ready=$((total_ready + 1))
    else
      printf "%-15s %-10s ${RED}%-12s${RESET} %-45s\n" "$id" "$category" "MISSING" "No SKILL.md found"
      total_missing=$((total_missing + 1))
    fi
  done
  echo "------------------------------------------------------------------------------------------------"
  echo -e "Total Tools: ${BOLD}$count${RESET} | Ready: ${GREEN}$total_ready${RESET} | Missing: ${RED}$total_missing${RESET}"
}

copy_single_skill() {
  local skill_name="$1"
  local target_dir="$2"
  local custom_dest="$3"
  local force="$4"

  local source_file
  if ! source_file="$(resolve_skill_file "$skill_name")"; then
    echo -e "${RED}Error: Skill '$skill_name' not found.${RESET}" >&2
    return 1
  fi

  if [ ! -f "$source_file" ]; then
    echo -e "${RED}Error: Source file does not exist: $source_file${RESET}" >&2
    return 1
  fi

  # Determine canonical destination skill name
  local clean_name
  clean_name="$(basename "$(dirname "$source_file")")"
  if [ "$clean_name" = "skills" ] || [ "$clean_name" = ".agents" ] || [ "$clean_name" = "daemon" ] || [ "$clean_name" = "internal" ] || [ "$clean_name" = "tools" ]; then
    clean_name="$skill_name"
  fi

  # If custom destination is provided
  if [ -n "$custom_dest" ]; then
    local dest_file="$custom_dest/SKILL.md"
    if [[ "$custom_dest" == *".md" ]]; then
      dest_file="$custom_dest"
    fi
    mkdir -p "$(dirname "$dest_file")"
    if [ -f "$dest_file" ] && [ "$force" != "true" ]; then
      echo -e "  ${YELLOW}[SKIP]${RESET} Destination exists: $dest_file (use --force to overwrite)"
      return 0
    fi
    cp "$source_file" "$dest_file"
    echo -e "  ${GREEN}[OK]${RESET} Provisioned: $dest_file"
    return 0
  fi

  # Standard provisioning: Both agents/skill/ and .agents/skills/
  local dest1="$target_dir/agents/skill/$clean_name/SKILL.md"
  local dest2="$target_dir/.agents/skills/$clean_name/SKILL.md"

  mkdir -p "$(dirname "$dest1")"
  mkdir -p "$(dirname "$dest2")"

  local copied=0
  for dest in "$dest1" "$dest2"; do
    if [ -f "$dest" ] && [ "$force" != "true" ]; then
      echo -e "  ${YELLOW}[SKIP]${RESET} Already exists: $dest"
    else
      cp "$source_file" "$dest"
      echo -e "  ${GREEN}[OK]${RESET} Provisioned: $dest"
      copied=$((copied + 1))
    fi
  done

  return 0
}

cmd_install() {
  local skill_name="${1:-}"
  local target_dir="."
  local custom_dest=""
  local force="false"

  if [ -z "$skill_name" ]; then
    echo -e "${RED}Error: Missing skill name.${RESET}"
    echo "Usage: aa skill install <skill-name|all> [--target <dir>] [--force]"
    exit 1
  fi
  shift || true

  while [ $# -gt 0 ]; do
    case "$1" in
      --target|-t)
        target_dir="$2"
        shift 2
        ;;
      --dest|-d)
        custom_dest="$2"
        shift 2
        ;;
      --force|-f)
        force="true"
        shift
        ;;
      *)
        echo -e "${YELLOW}Warning: Unknown argument '$1' ignored.${RESET}"
        shift
        ;;
    esac
  done

  target_dir="$(cd "$target_dir" 2>/dev/null && pwd || echo "$target_dir")"

  if [ "$skill_name" = "all" ]; then
    echo -e "${BOLD}Provisioning ALL skills into target workspace: $target_dir${RESET}"
    echo "------------------------------------------------------------------"
    while IFS=: read -r sname _cat _desc _path; do
      [ -z "$sname" ] && continue
      copy_single_skill "$sname" "$target_dir" "$custom_dest" "$force" || true
    done < <(get_canonical_skills)
    echo "------------------------------------------------------------------"
    echo -e "${GREEN}All available skills provisioned successfully.${RESET}"
    return 0
  fi

  echo -e "${BOLD}Provisioning skill '$skill_name'...${RESET}"
  copy_single_skill "$skill_name" "$target_dir" "$custom_dest" "$force"
}

cmd_show() {
  local skill_name="${1:-}"
  if [ -z "$skill_name" ]; then
    echo -e "${RED}Error: Missing skill name.${RESET}"
    echo "Usage: aa skill show <skill-name>"
    exit 1
  fi

  local source_file
  if ! source_file="$(resolve_skill_file "$skill_name")"; then
    echo -e "${RED}Error: Skill '$skill_name' not found.${RESET}"
    exit 1
  fi

  if [ ! -f "$source_file" ]; then
    echo -e "${RED}Error: File not found: $source_file${RESET}"
    exit 1
  fi

  echo -e "${BOLD}Source:${RESET} $source_file"
  echo "------------------------------------------------------------------"
  cat "$source_file"
}

# --- Main Dispatcher ---
main() {
  local action="${1:-help}"
  shift || true

  case "$action" in
    list|ls)
      cmd_list "$@"
      ;;
    check|audit)
      cmd_check "$@"
      ;;
    install|copy|get|add)
      cmd_install "$@"
      ;;
    sync)
      cmd_install "all" "$@"
      ;;
    show|cat|view)
      cmd_show "$@"
      ;;
    help|-h|--help)
      cmd_help
      ;;
    *)
      echo -e "${RED}Unknown skill command: $action${RESET}"
      echo ""
      cmd_help
      exit 1
      ;;
  esac
}

main "$@"
