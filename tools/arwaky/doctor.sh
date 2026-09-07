#!/usr/bin/env bash
# tools/arwaky/doctor.sh
# All-In-One Ecosystem Health & Diagnostic Engine for agents-arwaky
# Probes container sandbox, background daemons, MCP server stdio ping, and harness sync

set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

TARGET_BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
MCP_CONFIG_FILE="$REPO_ROOT/mcp_servers.generated.json"

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

print_header() {
  echo -e "${CYAN}${BOLD}   ___                           _          ${RESET}"
  echo -e "${CYAN}${BOLD}  / _ | _______    _____ _ / /____ __   ${RESET}"
  echo -e "${CYAN}${BOLD} / __ |/ __/ _ \/\/ _ \`/  '_/ // /   ${RESET}"
  echo -e "${CYAN}${BOLD}/_/ |_/_/  \_/\_/\_,_/_/\_\\_, /    ${RESET}"
  echo -e "${CYAN}${BOLD}                           /___/     ${RESET}"
  echo -e "${DIM} agents-arwaky All-In-One Diagnostic Doctor v2.0${RESET}"
  echo ""
}

main() {
  print_header

  local passed=0
  local warnings=0
  local errors=0

  # ==========================================================
  # 1. Environment & Container Sandbox
  # ==========================================================
  echo -e "${BOLD}[1/5] Environment & Container Sandbox${RESET}"
  echo "------------------------------------------------------"

  if is_inside_container; then
    echo -e "  Context:             ${GREEN}[OK] Running INSIDE Distrobox container${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  Context:             ${BLUE}[INFO] Running on HOST OS${RESET}"
  fi

  if [[ ":$PATH:" == *":$TARGET_BIN_DIR:"* ]]; then
    echo -e "  User PATH:           ${GREEN}[OK] $TARGET_BIN_DIR is present in PATH${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  User PATH:           ${YELLOW}[WARN] $TARGET_BIN_DIR is NOT in PATH${RESET}"
    echo -e "                       Add 'export PATH=\"\$HOME/.local/bin:\$PATH\"' to ~/.bashrc or ~/.zshrc"
    warnings=$((warnings + 1))
  fi

  if ! is_inside_container; then
    if command -v podman >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
      local engine_path
      engine_path="$(command -v podman || command -v docker)"
      echo -e "  Container Engine:    ${GREEN}[OK] $engine_path${RESET}"
      passed=$((passed + 1))
    else
      echo -e "  Container Engine:    ${RED}[FAIL] Neither Podman nor Docker found (Run 'aa setup')${RESET}"
      errors=$((errors + 1))
    fi

    if command -v distrobox >/dev/null 2>&1; then
      echo -e "  Distrobox:           ${GREEN}[OK] $(distrobox --version 2>&1 | head -n1)${RESET}"
      if check_distrobox_container; then
        echo -e "  Sandbox Container:   ${GREEN}[OK] 'agents-env' container ready${RESET}"
        passed=$((passed + 2))
      else
        echo -e "  Sandbox Container:   ${YELLOW}[WARN] 'agents-env' not initialized (Run 'aa install')${RESET}"
        warnings=$((warnings + 1))
      fi
    else
      echo -e "  Distrobox:           ${YELLOW}[WARN] Distrobox not found on host (Run 'aa setup')${RESET}"
      warnings=$((warnings + 1))
    fi
  fi

  for util in git jq curl python3; do
    if command -v "$util" >/dev/null 2>&1; then
      echo -e "  Utility ($util):       ${GREEN}[OK] $(command -v "$util")${RESET}"
      passed=$((passed + 1))
    else
      echo -e "  Utility ($util):       ${RED}[FAIL] $util is required${RESET}"
      errors=$((errors + 1))
    fi
  done
  echo ""

  # ==========================================================
  # 2. Background Daemons & Services
  # ==========================================================
  echo -e "${BOLD}[2/5] Background Daemons & Network Ports${RESET}"
  echo "------------------------------------------------------"
  
  # 9Router
  local r_port="${NINEROUTER_PORT:-20128}"
  local r_code
  r_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$r_port/" 2>/dev/null || true)"
  if [ "$r_code" = "200" ] || [ "$r_code" = "307" ] || [ "$r_code" = "302" ]; then
    echo -e "  9Router AI Gateway:  ${GREEN}[OK] Online on port $r_port (HTTP $r_code)${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  9Router AI Gateway:  ${YELLOW}[STANDBY] Port $r_port not responding (Run 'aa service start 9router')${RESET}"
    warnings=$((warnings + 1))
  fi

  # Anytype Daemon
  local a_port="${ANYTYPE_PORT:-31012}"
  local a_code
  a_code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$a_port/docs/openapi.json" 2>/dev/null || true)"
  if [ "$a_code" = "200" ] || [ "$a_code" = "401" ] || [ "$a_code" = "403" ]; then
    echo -e "  Anytype Daemon:      ${GREEN}[OK] Online on port $a_port (REST API Healthy)${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  Anytype Daemon:      ${YELLOW}[STANDBY] Port $a_port not responding (Run 'aa service start anytype')${RESET}"
    warnings=$((warnings + 1))
  fi
  echo ""

  # ==========================================================
  # 3. Model Context Protocol (MCP) Health & Ping
  # ==========================================================
  echo -e "${BOLD}[3/5] MCP Server Readiness & JSON-RPC Probing${RESET}"
  echo "------------------------------------------------------"

  if [ ! -f "$MCP_CONFIG_FILE" ]; then
    echo -e "  ${YELLOW}Unified manifest missing. Generating now...${RESET}"
    "$REPO_ROOT/tools/mcp/generate-config.sh" >/dev/null 2>&1 || true
  fi

  if command -v python3 >/dev/null 2>&1 && [ -f "$MCP_CONFIG_FILE" ]; then
    local mcp_probe_out
    mcp_probe_out="$(python3 - "$MCP_CONFIG_FILE" << 'PYEOF'
import json, subprocess, time, os, concurrent.futures, sys

mcp_file = sys.argv[1] if len(sys.argv) > 1 else ""
if not mcp_file or not os.path.exists(mcp_file):
    sys.exit(0)

with open(mcp_file) as f:
    data = json.load(f)

servers = data.get("mcpServers", {})

def check_server(item):
    name, conf = item
    cmd = conf.get("command", "")
    args = conf.get("args", [])
    
    bin_path = os.path.expanduser(f"~/.local/bin/{cmd}")
    if not os.path.exists(bin_path):
        import shutil
        bin_path = shutil.which(cmd)
        
    if not bin_path or not os.path.exists(bin_path):
        return (name, "NOT_FOUND", 0, f"Binary not found ({cmd})")
        
    t0 = time.time()
    init_msg = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"aa-doctor","version":"1.0"}}}) + "\n"
    
    env = os.environ.copy()
    if "env" in conf:
        env.update(conf["env"])
        
    try:
        proc = subprocess.Popen([bin_path] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        stdout, stderr = proc.communicate(input=init_msg, timeout=4.0)
        dt = int((time.time() - t0) * 1000)
        if "jsonrpc" in stdout or proc.returncode == 0:
            return (name, "OK", dt, f"Responded in {dt}ms")
        return (name, "WARN", dt, f"Code {proc.returncode} ({dt}ms)")
    except subprocess.TimeoutExpired:
        proc.kill()
        return (name, "TIMEOUT", 4000, "Ping timed out (>4s)")
    except Exception as e:
        return (name, "ERROR", 0, str(e))

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(check_server, servers.items()))

for name, status, dt, desc in results:
    print(f"{name}\t{status}\t{desc}")
PYEOF
    )"

    while IFS=$'\t' read -r s_name s_status s_desc; do
      [ -n "$s_name" ] || continue
      case "$s_status" in
        OK)
          echo -e "  MCP Server [${s_name}]:\t${GREEN}[OK] ${s_desc}${RESET}"
          passed=$((passed + 1))
          ;;
        WARN)
          echo -e "  MCP Server [${s_name}]:\t${YELLOW}[WARN] ${s_desc}${RESET}"
          warnings=$((warnings + 1))
          ;;
        TIMEOUT)
          echo -e "  MCP Server [${s_name}]:\t${YELLOW}[TIMEOUT] ${s_desc}${RESET}"
          warnings=$((warnings + 1))
          ;;
        *)
          echo -e "  MCP Server [${s_name}]:\t${RED}[FAIL] ${s_desc}${RESET}"
          errors=$((errors + 1))
          ;;
      esac
    done <<< "$mcp_probe_out"
  else
    echo -e "  ${YELLOW}[SKIP] Python3 not available for parallel MCP probing.${RESET}"
  fi
  echo ""

  # ==========================================================
  # 4. Agent Harness Integration
  # ==========================================================
  echo -e "${BOLD}[4/5] Agent Harness Integrations${RESET}"
  echo "------------------------------------------------------"

  # Antigravity
  local agy_dir="$HOME/.gemini/antigravity-cli"
  if [ -d "$agy_dir" ]; then
    echo -e "  Google Antigravity:  ${GREEN}[OK] Harness directory present ($agy_dir)${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  Google Antigravity:  ${BLUE}[INFO] Harness directory not found (Run 'aa connect --antigravity')${RESET}"
  fi

  # Hermes
  local hermes_dir="$HOME/.hermes"
  if [ -d "$hermes_dir" ]; then
    echo -e "  Hermes Agent:        ${GREEN}[OK] Harness directory present ($hermes_dir)${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  Hermes Agent:        ${BLUE}[INFO] Harness directory not found (Run 'aa connect --hermes')${RESET}"
  fi

  # OpenCode
  local opencode_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  if [ -d "$opencode_dir" ]; then
    echo -e "  OpenCode Interpreter:${GREEN}[OK] Harness directory present ($opencode_dir)${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  OpenCode Interpreter:${BLUE}[INFO] Harness directory not found (Run 'aa connect --opencode')${RESET}"
  fi
  echo ""

  # ==========================================================
  # 5. Secrets & Environment Readiness
  # ==========================================================
  echo -e "${BOLD}[5/5] Credentials & Configurations${RESET}"
  echo "------------------------------------------------------"

  # Anytype API Key
  local anytype_env="$REPO_ROOT/tools/anytype-mcp/.env"
  if [ -f "$anytype_env" ] && grep -q "ANYTYPE_API_KEY=" "$anytype_env" 2>/dev/null; then
    echo -e "  Anytype Auth Key:    ${GREEN}[CONFIGURED] Present in tools/anytype-mcp/.env${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  Anytype Auth Key:    ${YELLOW}[MISSING] Run 'aa anytype auth-key' to pair${RESET}"
    warnings=$((warnings + 1))
  fi

  # 9Router Env
  local nr_env="$REPO_ROOT/tools/9router/.env"
  if [ -f "$nr_env" ]; then
    echo -e "  9Router Config:      ${GREEN}[CONFIGURED] Present in tools/9router/.env${RESET}"
    passed=$((passed + 1))
  else
    echo -e "  9Router Config:      ${BLUE}[DEFAULT] Using container standard configuration${RESET}"
  fi

  echo "------------------------------------------------------"
  if [ "$errors" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ Diagnostic Complete:${RESET} ${passed} checks passed, ${warnings} notices. Ecosystem is healthy!"
  else
    echo -e "${RED}${BOLD}✗ Diagnostic Complete:${RESET} ${errors} failed, ${warnings} notices, ${passed} passed."
    echo -e "Run ${BOLD}'aa sync'${RESET} or ${BOLD}'aa install'${RESET} to resolve missing components."
  fi
}

main "$@"
