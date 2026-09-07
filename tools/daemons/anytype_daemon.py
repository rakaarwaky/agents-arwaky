#!/usr/bin/env python3
"""Anytype daemon manager (Python) — pengganti anytype-daemon.sh."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import config_home, data_home  # noqa: E402

CONTAINER_NAME = "anytype-daemon"
IMAGE_NAME = "localhost/anytype-daemon:latest"
PORT = os.environ.get("ANYTYPE_API_BASE_URL", "http://127.0.0.1:31012").split(":")[-1].strip("/")
DATA_DIR = data_home() / "anytype-mcp"
DOT_ANYTYPE = data_home() / "anytype"
CONFIG_DIR = config_home() / "anytype"
SHARE_DIR = data_home() / "anytype" / "share"
LOCAL_BIN = data_home() / "anytype-mcp/bin"
SCRIPT_DIR = Path(__file__).resolve().parent
UNIT_DIR = config_home() / "systemd/user"
UNIT_FILE = UNIT_DIR / "anytype-daemon.service"
DATA_ROOT = data_home() / "anytype-mcp"


def run(cmd, **kw):
    return subprocess.run(cmd, **kw)


def out(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw).stdout.strip()


def has_podman():
    return shutil.which("podman") is not None


def container_running():
    return out(["podman", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME]) == "true"


def container_exists():
    return out(["podman", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"]) == CONTAINER_NAME


def api_ready(timeout=90):
    url = f"http://127.0.0.1:{PORT}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status < 400:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def build_image():
    print(">>> Building Anytype daemon image...")
    cwd = SCRIPT_DIR
    code = run(["podman", "build", "-t", IMAGE_NAME, "."], cwd=cwd).returncode
    if code != 0:
        print("Error: failed to build image", file=sys.stderr)
        sys.exit(1)


def ensure_dirs():
    for d in (DATA_DIR, DOT_ANYTYPE, CONFIG_DIR, SHARE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def cmd_start():
    if has_podman():
        if container_running():
            print(f">>> Anytype daemon container '{CONTAINER_NAME}' is already running.")
            return 0
        ensure_dirs()
        if container_exists():
            print(f">>> Starting existing Anytype container '{CONTAINER_NAME}'...")
            run(["podman", "start", CONTAINER_NAME])
        else:
            if out(["podman", "image", "exists", IMAGE_NAME]) != "":
                build_image()
            print(f">>> Launching Anytype daemon container '{CONTAINER_NAME}' on port {PORT}...")
            run(["podman", "run", "-d", "--name", CONTAINER_NAME, "--network", "host",
                 "--restart", "unless-stopped",
                 "-v", f"{DATA_DIR}:/data:Z",
                 "-v", f"{DOT_ANYTYPE}:/root/.anytype:Z",
                 "-v", f"{CONFIG_DIR}:/root/.config/anytype:Z",
                 "-v", f"{SHARE_DIR}:/root/.local/share/anytype:Z",
                 IMAGE_NAME])
        print(f">>> Waiting for Anytype API on port {PORT}...")
        if api_ready():
            print(f">>> [OK] Anytype daemon is ready at http://127.0.0.1:{PORT}")
        else:
            print(">>> [WARN] Container started, but API is still initializing. Check 'aa anytype logs'.")
        return 0
    # native fallback
    print(">>> Podman not found. Falling back to native background execution...")
    anytype_bin = LOCAL_BIN / "anytype"
    if not anytype_bin.exists():
        print("Error: local anytype binary not found.", file=sys.stderr)
        return 1
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    log_file = DATA_ROOT / "daemon.log"
    with log_file.open("ab") as f:
        p = subprocess.Popen([str(anytype_bin), "serve", "--listen-address", f"127.0.0.1:{PORT}"],
                             stdout=f, stderr=f, start_new_session=True)
    print(f">>> Started local Anytype daemon (PID: {p.pid}). Logs: {log_file}")
    return 0


def cmd_stop():
    if has_podman() and container_exists():
        print(f">>> Stopping Anytype daemon container '{CONTAINER_NAME}'...")
        run(["podman", "stop", CONTAINER_NAME])
        return 0
    subprocess.run(["pkill", "-f", "anytype serve"])
    print(">>> Anytype daemon stopped.")
    return 0


def cmd_restart():
    cmd_stop()
    time.sleep(1)
    return cmd_start()


def cmd_status():
    print("==========================================")
    print(" Anytype Headless Daemon Status")
    print("==========================================")
    if has_podman():
        if container_running():
            print(" Container: RUNNING")
        elif container_exists():
            print(" Container: STOPPED (exists)")
        else:
            print(" Container: NOT FOUND")
    if api_ready(timeout=10):
        print(f" API: OK (http://127.0.0.1:{PORT})")
    else:
        print(f" API: not ready")
    return 0


def cmd_logs():
    if has_podman() and container_exists():
        return run(["podman", "logs", "-f", "--tail", "200", CONTAINER_NAME]).returncode
    log = DATA_ROOT / "daemon.log"
    if log.exists():
        return run(["tail", "-f", "-n", "200", str(log)]).returncode
    print("Anytype daemon is not running.")
    return 1


def cmd_exec_anytype(args):
    if has_podman() and container_running():
        return run(["podman", "exec", CONTAINER_NAME, "anytype", *args]).returncode
    anytype_bin = LOCAL_BIN / "anytype"
    if anytype_bin.exists():
        return run([str(anytype_bin), *args]).returncode
    print("Error: Anytype daemon not running and local binary not found.", file=sys.stderr)
    return 1


def cmd_auth_create(name="agent"):
    return cmd_exec_anytype(["account", "create", "--name", name])


def cmd_auth_key(name="arwaky-agent-key"):
    code = cmd_exec_anytype(["account", "api-key", "create", "--name", name])
    if code != 0:
        return code
    return 0


def cmd_space_join(link):
    if not link:
        print("Error: Missing invite link.", file=sys.stderr)
        return 1
    return cmd_exec_anytype(["space", "join", link])


def cmd_space_list():
    return cmd_exec_anytype(["space", "list"])


def cmd_service_install():
    if not has_podman():
        print("Error: Podman is required to install the systemd container service.", file=sys.stderr)
        return 1
    UNIT_DIR.mkdir(parents=True, exist_ok=True)
    src = SCRIPT_DIR / "anytype-daemon.service"
    if src.exists():
        shutil.copy2(src, UNIT_FILE)
    run(["systemctl", "--user", "daemon-reload"])
    run(["systemctl", "--user", "enable", "--now", "anytype-daemon.service"])
    print(">>> Anytype daemon installed and started as user systemd service: anytype-daemon.service")
    return 0


def cmd_service_status():
    return run(["systemctl", "--user", "status", "anytype-daemon.service"]).returncode


def cmd_help():
    print("Usage: aa anytype <command> [arguments...]")
    print()
    print("Commands:")
    print("  start              Start Anytype daemon")
    print("  stop               Stop Anytype daemon")
    print("  restart            Restart Anytype daemon")
    print("  status             Check health and API accessibility")
    print("  logs               Tail daemon logs")
    print("  auth-create [name] Create a headless bot account")
    print("  auth-key [name]    Generate API key for MCP")
    print("  space-join <link>  Join an Anytype Space via invite link")
    print("  space-list         List spaces joined by the bot")
    print("  service-install    Enable auto-start via systemd user unit")
    print("  service-status     Check systemd user service status")
    print("  help               Show this help")
    return 0


def main(argv):
    if not argv or argv[0] in ("help", "-h", "--help"):
        return cmd_help()
    action = argv[0]
    rest = argv[1:]
    if action == "start":
        return cmd_start()
    if action == "stop":
        return cmd_stop()
    if action == "restart":
        return cmd_restart()
    if action == "status":
        return cmd_status()
    if action == "logs":
        return cmd_logs()
    if action == "auth-create":
        return cmd_auth_create(rest[0] if rest else "agent")
    if action == "auth-key":
        return cmd_auth_key(rest[0] if rest else "arwaky-agent-key")
    if action == "space-join":
        return cmd_space_join(rest[0] if rest else "")
    if action == "space-list":
        return cmd_space_list()
    if action == "service-install":
        return cmd_service_install()
    if action == "service-status":
        return cmd_service_status()
    print(f"Unknown anytype command: {action}", file=sys.stderr)
    return cmd_help()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
