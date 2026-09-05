#!/usr/bin/env bash
# tools/skill/skill-manager.sh
# AI Agent Skill Discovery, Inspection & Provisioning Orchestrator
# Tool-Centric Multi-Skill Architecture for internal & vendor tools
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
  ' "$file" 2>/dev/null || true)"

  if [ -n "$desc" ]; then
    echo "$desc"
  else
    # Fallback to first non-heading paragraph
    awk '
      /^#/ { next }
      /^---/ { next }
      /^[a-zA-Z]/ { print; exit }
    ' "$file" 2>/dev/null | head -n1 || echo "No description available"
  fi
}

# --- Helper: Extract clean skill name from SKILL.md ---
extract_skill_name() {
  local file="$1"
  local name
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
  ' "$file" 2>/dev/null || true)"

  if [ -n "$name" ]; then
    echo "$name"
    return 0
  fi

  local pdir
  pdir="$(basename "$(dirname "$file")")"
  case "$pdir" in
    skills|.agents|internal|tools|vendor)
      local grand
      grand="$(basename "$(dirname "$(dirname "$file")")")"
      echo "$grand"
      ;;
    daemon)
      echo "anytype-daemon"
      ;;
    *)
      echo "$pdir"
      ;;
  esac
}

# --- Normalize Tool Name or Alias to Canonical Tool ID ---
normalize_tool_id() {
  local query="$1"
  case "$query" in
    lint|lint-arwaky|la|lac) echo "lint" ;;
    9router) echo "9router" ;;
    ponytail|ponytail-mcp) echo "ponytail" ;;
    context7|context7-mcp) echo "context7" ;;
    codegraph|codegraph-mcp) echo "codegraph" ;;
    anytype|anytype-mcp|anytype-daemon) echo "anytype" ;;
    fetch|fetch-mcp) echo "fetch" ;;
    lean-ctx) echo "lean-ctx" ;;
    vision|vision-arwaky|va) echo "vision" ;;
    qwen-web|qwen-web-arwaky|qwa|qwc) echo "qwen-web" ;;
    blender|blender-arwaky|ba) echo "blender" ;;
    skill|skills|skill-manager) echo "skill" ;;
    *)
      # Lookup in manifest.json
      if [ -f "$MANIFEST_FILE" ]; then
        local found
        found="$(jq -r --arg q "$query" '.tools[] | select(.id == $q or .binary == $q or (.alias? != null and .alias == $q)) | .id' "$MANIFEST_FILE" 2>/dev/null | head -n1 || true)"
        if [ -n "$found" ] && [ "$found" != "null" ]; then
          echo "$found"
          return 0
        fi
      fi
      return 1
      ;;
  esac
}

# --- Return All SKILL.md Files for a Given Tool ID ---
get_tool_skills() {
  local tool_id="$1"
  local files=()

  case "$tool_id" in
    lint)
      [ -f "$REPO_ROOT/tools/lint/SKILL.md" ] && files+=("$REPO_ROOT/tools/lint/SKILL.md")
      while IFS= read -r f; do
        [ -f "$f" ] && files+=("$f")
      done < <(find "$REPO_ROOT/internal/lint-arwaky/.agents/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
      ;;
    9router)
      while IFS= read -r f; do
        [ -f "$f" ] && files+=("$f")
      done < <(find "$REPO_ROOT/vendor/9router/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
      ;;
    ponytail)
      while IFS= read -r f; do
        [ -f "$f" ] && files+=("$f")
      done < <(find "$REPO_ROOT/vendor/ponytail/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
      ;;
    context7)
      while IFS= read -r f; do
        [ -f "$f" ] && files+=("$f")
      done < <(find "$REPO_ROOT/vendor/context7/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
      ;;
    codegraph)
      [ -f "$REPO_ROOT/tools/codegraph/SKILL.md" ] && files+=("$REPO_ROOT/tools/codegraph/SKILL.md")
      while IFS= read -r f; do
        [ -f "$f" ] && files+=("$f")
      done < <(find "$REPO_ROOT/vendor/codegraph/.claude/skills" -type f -name "SKILL.md" 2>/dev/null | sort)
      ;;
    anytype)
      [ -f "$REPO_ROOT/tools/anytype-mcp/SKILL.md" ] && files+=("$REPO_ROOT/tools/anytype-mcp/SKILL.md")
      [ -f "$REPO_ROOT/tools/anytype-mcp/daemon/SKILL.md" ] && files+=("$REPO_ROOT/tools/anytype-mcp/daemon/SKILL.md")
      ;;
    fetch)
      [ -f "$REPO_ROOT/tools/fetch-mcp/SKILL.md" ] && files+=("$REPO_ROOT/tools/fetch-mcp/SKILL.md")
      ;;
    lean-ctx)
      [ -f "$REPO_ROOT/vendor/lean-ctx/skills/lean-ctx/SKILL.md" ] && files+=("$REPO_ROOT/vendor/lean-ctx/skills/lean-ctx/SKILL.md")
      ;;
    vision)
      [ -f "$REPO_ROOT/internal/vision-arwaky/SKILL.md" ] && files+=("$REPO_ROOT/internal/vision-arwaky/SKILL.md")
      ;;
    qwen-web)
      [ -f "$REPO_ROOT/internal/qwen-web-arwaky/SKILL.md" ] && files+=("$REPO_ROOT/internal/qwen-web-arwaky/SKILL.md")
      ;;
    blender)
      [ -f "$REPO_ROOT/internal/blender-arwaky/SKILL.md" ] && files+=("$REPO_ROOT/internal/blender-arwaky/SKILL.md")
      ;;
    skill)
      [ -f "$REPO_ROOT/tools/skill/SKILL.md" ] && files+=("$REPO_ROOT/tools/skill/SKILL.md")
      ;;
  esac

  for f in "${files[@]}"; do
    echo "$f"
  done
}

# --- Resolve Single Skill File by Exact Name or Alias ---
resolve_single_skill_file() {
  local query="$1"

  # 1. Check tools/<query>/SKILL.md
  if [ -f "$REPO_ROOT/tools/$query/SKILL.md" ]; then
    echo "$REPO_ROOT/tools/$query/SKILL.md"
    return 0
  fi

  # 2. Check internal/<query>/SKILL.md
  if [ -f "$REPO_ROOT/internal/$query/SKILL.md" ]; then
    echo "$REPO_ROOT/internal/$query/SKILL.md"
    return 0
  fi

  # 3. Dynamic search across skill directories
  local found
  found="$(find "$REPO_ROOT/tools" "$REPO_ROOT/internal" "$REPO_ROOT/vendor" -type f -name "SKILL.md" 2>/dev/null | grep -E "/${query}/SKILL.md|/${query}-arwaky/SKILL.md|/${query}-mcp/SKILL.md" | head -n1 || true)"
  if [ -n "$found" ] && [ -f "$found" ]; then
    echo "$found"
    return 0
  fi

  return 1
}

# --- Get Canonical Tool List ---
get_registered_tool_ids() {
  cat << 'EOF'
lint:internal:AES 7-layer architecture linter & 38 generation/remediation skills
9router:vendor:Local AI routing gateway for 40+ providers & multimodal skills
ponytail:vendor:Senior-dev instructions, technical debt analysis & code review
context7:vendor:Fast Upstash documentation & context retrieval
codegraph:vendor:Rust-powered code graph engine & symbol intelligence
anytype:vendor:Anytype local-first knowledge graph & background daemon
fetch:vendor:Web scraping, clean HTML-to-markdown & YouTube transcripts
lean-ctx:vendor:Token-lean repository indexing & context compression
vision:internal:Unified computer vision, OCR, video intelligence & visual memory
qwen-web:internal:Qwen AI Web Automation CLI & Playwright MCP
blender:internal:Headless 3D execution engine & scene automation
skill:internal:Skill discovery, audit & workspace provisioner
EOF
}

# --- Copy a Single SKILL.md to Target Workspace ---
copy_single_skill_file() {
  local source_file="$1"
  local target_dir="$2"
  local custom_dest="$3"
  local force="$4"

  if [ ! -f "$source_file" ]; then
    echo -e "${RED}Error: Source file not found: $source_file${RESET}" >&2
    return 1
  fi

  local clean_name
  clean_name="$(extract_skill_name "$source_file")"

  # If custom destination is provided
  if [ -n "$custom_dest" ]; then
    local dest_file="$custom_dest/$clean_name/SKILL.md"
    if [[ "$custom_dest" == *".md" ]]; then
      dest_file="$custom_dest"
    fi
    mkdir -p "$(dirname "$dest_file")"
    if [ -f "$dest_file" ] && [ "$force" != "true" ]; then
      echo -e "  ${YELLOW}[SKIP]${RESET} Already exists: $dest_file (use --force to overwrite)"
      return 0
    fi
    cp "$source_file" "$dest_file"
    echo -e "  ${GREEN}[OK]${RESET} Provisioned: $dest_file"
    return 0
  fi

  # Standard provisioning: Exclusively to .agents/skills/
  local dest="$target_dir/.agents/skills/$clean_name/SKILL.md"

  mkdir -p "$(dirname "$dest")"

  if [ -f "$dest" ] && [ "$force" != "true" ]; then
    echo -e "  ${YELLOW}[SKIP]${RESET} Already exists: $dest"
  else
    cp "$source_file" "$dest"
    echo -e "  ${GREEN}[OK]${RESET} Provisioned: $dest"
  fi

  return 0
}

# --- Install All Skills for a Tool ---
install_tool_skills() {
  local tool_id="$1"
  local target_dir="$2"
  local custom_dest="$3"
  local force="$4"

  local skill_files=()
  while IFS= read -r f; do
    [ -n "$f" ] && skill_files+=("$f")
  done < <(get_tool_skills "$tool_id")

  local total="${#skill_files[@]}"
  if [ "$total" -eq 0 ]; then
    echo -e "${RED}Error: No skills found for tool '$tool_id'.${RESET}" >&2
    return 1
  fi

  if [ "$total" -eq 1 ]; then
    echo -e "${BOLD}Provisioning skill for tool '${CYAN}$tool_id${RESET}'...${RESET}"
  else
    echo -e "${BOLD}Installing all ${CYAN}$total skills${RESET} for tool '${CYAN}$tool_id${RESET}'...${RESET}"
  fi
  echo -e "Target Workspace: ${BLUE}$target_dir${RESET}"
  echo "------------------------------------------------------------------"

  local success=0
  for sf in "${skill_files[@]}"; do
    if copy_single_skill_file "$sf" "$target_dir" "$custom_dest" "$force"; then
      success=$((success + 1))
    fi
  done

  echo "------------------------------------------------------------------"
  echo -e "${GREEN}Successfully provisioned $success skill(s) for tool '$tool_id'.${RESET}"
  return 0
}

cmd_help() {
  echo -e "${BOLD}agents-arwaky Skill Manager (${CYAN}aa skill${RESET}${BOLD})${RESET}"
  echo -e "${DIM}Discover, inspect and provision AI agent skills across internal and vendor tools.${RESET}"
  echo ""
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  aa skill <command> [arguments...]"
  echo ""
  echo -e "${BOLD}COMMANDS:${RESET}"
  echo -e "  ${GREEN}list, ls${RESET} [tool]             List all tools and their associated skills"
  echo -e "  ${GREEN}install, get, copy${RESET} <name>   Install ALL skills for a tool (or a specific individual skill)"
  echo -e "  ${GREEN}install all, sync${RESET}           Provision ALL skills for ALL tools in the ecosystem"
  echo -e "  ${GREEN}show${RESET} <name>                 Display the content of a skill's SKILL.md in terminal"
  echo -e "  ${GREEN}check${RESET}                       Audit SKILL.md coverage across all registered tools"
  echo -e "  ${GREEN}help${RESET}                        Show this help screen"
  echo ""
  echo -e "${BOLD}TOOL-CENTRIC INSTALLATION EXAMPLES:${RESET}"
  echo -e "  ${CYAN}aa skill install lint${RESET}       # Installs ALL 39 AES skills for lint-arwaky"
  echo -e "  ${CYAN}aa skill install 9router${RESET}     # Installs ALL 9 skills for 9router (chat, search, voice, etc.)"
  echo -e "  ${CYAN}aa skill install ponytail${RESET}    # Installs ALL 6 skills for ponytail (audit, debt, review)"
  echo -e "  ${CYAN}aa skill install blender${RESET}     # Installs blender-arwaky 3D headless skill"
  echo -e "  ${CYAN}aa skill install fetch${RESET}       # Installs fetch-mcp scraping skill"
  echo -e "  ${CYAN}aa skill install all${RESET}         # Installs ALL 68 skills across the entire ecosystem"
  echo ""
  echo -e "${BOLD}INDIVIDUAL SKILL INSTALLATION:${RESET}"
  echo -e "  ${CYAN}aa skill install lint-arwaky-python${RESET}  # Installs only the Python AES scanner skill"
  echo -e "  ${CYAN}aa skill install 9router-web-search${RESET}  # Installs only the web search skill"
  echo ""
  echo -e "${BOLD}OPTIONS FOR INSTALL:${RESET}"
  echo -e "  ${CYAN}--target <dir>${RESET}              Base directory to install into (default: current directory .)"
  echo -e "  ${CYAN}--dest <path>${RESET}               Exact custom destination folder for the skill"
  echo -e "  ${CYAN}--force, -f${RESET}                 Overwrite existing SKILL.md file if present"
  echo ""
}

cmd_list() {
  local tool_filter="${1:-}"

  # If a specific tool was asked to list (e.g. aa skill list lint)
  if [ -n "$tool_filter" ] && [ "$tool_filter" != "--all" ]; then
    local tool_id
    if ! tool_id="$(normalize_tool_id "$tool_filter")"; then
      echo -e "${RED}Error: Tool '$tool_filter' not found in manifest.${RESET}"
      exit 1
    fi

    echo -e "${BOLD}Skills associated with tool '${CYAN}$tool_id${RESET}':${RESET}"
    echo "------------------------------------------------------------------------------------------------"
    printf "${BOLD}%-28s %-65s${RESET}\n" "SKILL NAME" "DESCRIPTION"
    echo "------------------------------------------------------------------------------------------------"

    while IFS= read -r sf; do
      local sname sdesc
      sname="$(extract_skill_name "$sf")"
      sdesc="$(extract_description "$sf")"
      printf "%-28s %-65s\n" "$sname" "$sdesc"
    done < <(get_tool_skills "$tool_id")
    echo "------------------------------------------------------------------------------------------------"
    echo -e "${DIM}Install all skills for this tool using 'aa skill install $tool_id'.${RESET}"
    return 0
  fi

  echo -e "${BOLD}Available Tools & Associated Skills in agents-arwaky:${RESET}"
  echo "------------------------------------------------------------------------------------------------"
  printf "${BOLD}%-14s %-10s %-14s %-50s${RESET}\n" "TOOL ID" "CATEGORY" "SKILLS COUNT" "DESCRIPTION"
  echo "------------------------------------------------------------------------------------------------"

  local total_skills=0
  while IFS=: read -r tid cat desc; do
    [ -z "$tid" ] && continue
    local scount
    scount="$(get_tool_skills "$tid" | wc -l)"
    total_skills=$((total_skills + scount))

    local cat_color="$CYAN"
    [ "$cat" = "internal" ] && cat_color="$GREEN"

    printf "%-14s ${cat_color}%-10s${RESET} ${BOLD}%-14s${RESET} %-50s\n" "$tid" "$cat" "$scount skill(s)" "$desc"
  done < <(get_registered_tool_ids)

  echo "------------------------------------------------------------------------------------------------"
  echo -e "Total Tools: ${BOLD}12${RESET} | Total Ecosystem Skills: ${GREEN}${BOLD}$total_skills${RESET}"
  echo -e "${DIM}Run 'aa skill install <tool-id>' to install all skills for that tool.${RESET}"
  echo -e "${DIM}Run 'aa skill list <tool-id>' to see every individual skill in that tool.${RESET}"
}

cmd_check() {
  echo -e "${BOLD}Auditing SKILL.md Readiness across Registered Tools:${RESET}"
  echo "------------------------------------------------------------------------------------------------"
  printf "${BOLD}%-15s %-10s %-12s %-14s %-35s${RESET}\n" "TOOL ID" "CATEGORY" "STATUS" "SKILLS COUNT" "SAMPLE PATH"
  echo "------------------------------------------------------------------------------------------------"

  local total_tools=0
  local total_ready=0
  local total_missing=0
  local total_skills=0

  while IFS=: read -r tid cat _desc; do
    [ -z "$tid" ] && continue
    total_tools=$((total_tools + 1))

    local skills=()
    while IFS= read -r sf; do
      [ -n "$sf" ] && skills+=("$sf")
    done < <(get_tool_skills "$tid")

    local count="${#skills[@]}"
    total_skills=$((total_skills + count))

    if [ "$count" -gt 0 ]; then
      total_ready=$((total_ready + 1))
      local sample="${skills[0]#"$REPO_ROOT"/}"
      printf "%-15s %-10s ${GREEN}%-12s${RESET} %-14s %-35s\n" "$tid" "$cat" "FOUND" "$count skill(s)" "$sample"
    else
      total_missing=$((total_missing + 1))
      printf "%-15s %-10s ${RED}%-12s${RESET} %-14s %-35s\n" "$tid" "$cat" "MISSING" "0 skills" "None"
    fi
  done < <(get_registered_tool_ids)

  echo "------------------------------------------------------------------------------------------------"
  echo -e "Total Tools: ${BOLD}$total_tools${RESET} | Ready: ${GREEN}$total_ready${RESET} | Missing: ${RED}$total_missing${RESET} | Total Skills: ${CYAN}$total_skills${RESET}"
}

cmd_install() {
  local target_name="${1:-}"
  local target_dir="."
  local custom_dest=""
  local force="false"

  if [ -z "$target_name" ]; then
    echo -e "${RED}Error: Missing tool or skill name.${RESET}"
    echo "Usage: aa skill install <tool-name|skill-name|all> [--target <dir>] [--force]"
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
        shift
        ;;
    esac
  done

  target_dir="$(cd "$target_dir" 2>/dev/null && pwd || echo "$target_dir")"

  # Case 1: Install ALL skills for ALL tools
  if [ "$target_name" = "all" ]; then
    echo -e "${BOLD}Provisioning ALL skills for ALL tools into target workspace: $target_dir${RESET}"
    echo "------------------------------------------------------------------"
    local total_installed=0
    while IFS=: read -r tid _cat _desc; do
      [ -z "$tid" ] && continue
      while IFS= read -r sf; do
        if copy_single_skill_file "$sf" "$target_dir" "$custom_dest" "$force"; then
          total_installed=$((total_installed + 1))
        fi
      done < <(get_tool_skills "$tid")
    done < <(get_registered_tool_ids)
    echo "------------------------------------------------------------------"
    echo -e "${GREEN}All $total_installed ecosystem skills provisioned successfully.${RESET}"
    return 0
  fi

  # Case 2: Target is a registered Tool (install ALL its skills)
  local matched_tool_id=""
  if matched_tool_id="$(normalize_tool_id "$target_name")"; then
    install_tool_skills "$matched_tool_id" "$target_dir" "$custom_dest" "$force"
    return 0
  fi

  # Case 3: Target is a specific individual skill
  local single_skill_file=""
  if single_skill_file="$(resolve_single_skill_file "$target_name")"; then
    echo -e "${BOLD}Provisioning individual skill '$target_name'...${RESET}"
    copy_single_skill_file "$single_skill_file" "$target_dir" "$custom_dest" "$force"
    return 0
  fi

  echo -e "${RED}Error: Neither tool nor skill named '$target_name' could be found.${RESET}"
  echo "Run 'aa skill list' to see all available tools and skills."
  exit 1
}

cmd_show() {
  local query="${1:-}"
  if [ -z "$query" ]; then
    echo -e "${RED}Error: Missing tool or skill name.${RESET}"
    echo "Usage: aa skill show <tool-name|skill-name>"
    exit 1
  fi

  # If it is a tool ID
  local matched_tool_id=""
  if matched_tool_id="$(normalize_tool_id "$query")"; then
    local skills=()
    while IFS= read -r sf; do
      [ -n "$sf" ] && skills+=("$sf")
    done < <(get_tool_skills "$matched_tool_id")

    if [ "${#skills[@]}" -gt 1 ]; then
      echo -e "${BOLD}Tool '${CYAN}$matched_tool_id${RESET}' contains ${CYAN}${#skills[@]} skills${RESET}.${RESET}"
      echo -e "${DIM}Displaying primary canonical skill:${RESET} ${skills[0]}"
      echo "------------------------------------------------------------------"
      cat "${skills[0]}"
      echo "------------------------------------------------------------------"
      echo -e "${BOLD}Other skills in '$matched_tool_id':${RESET}"
      for ((i=1; i<${#skills[@]}; i++)); do
        echo "  - $(extract_skill_name "${skills[$i]}")"
      done
      echo -e "\n${DIM}View any specific skill using 'aa skill show <skill-name>'.${RESET}"
      return 0
    elif [ "${#skills[@]}" -eq 1 ]; then
      echo -e "${BOLD}Source:${RESET} ${skills[0]}"
      echo "------------------------------------------------------------------"
      cat "${skills[0]}"
      return 0
    fi
  fi

  # Fallback to single skill search
  local sf=""
  if sf="$(resolve_single_skill_file "$query")"; then
    echo -e "${BOLD}Source:${RESET} $sf"
    echo "------------------------------------------------------------------"
    cat "$sf"
    return 0
  fi

  echo -e "${RED}Error: Skill or tool '$query' not found.${RESET}"
  exit 1
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
