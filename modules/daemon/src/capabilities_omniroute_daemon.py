#!/usr/bin/env python3
"""OmniRoute daemon manager (Python) — host-native, no container.

Replaces the 9router PodmanDaemonManager. Runs the OmniRoute gateway
directly on the host via the `omniroute` CLI (npm global install),
with a systemd user service for 24/7 operation. No Podman required.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from modules.shared.src.contract_daemon_protocol import IDaemonManager
from modules.shared.src.taxonomy_daemon_vo import DaemonStatus
from modules.shared.src.utility_paths_resolver import repo_root
from modules.shared.src.taxonomy_common_vo import (
    config_home,
    data_home,
)

ROOT = repo_root()

PORT = os.environ.get("OMNIROUTE_PORT", "7777")
DATA_DIR = data_home() / "omniroute"
UNIT_DIR = config_home() / "systemd/user"
UNIT_FILE = UNIT_DIR / "omniroute.service"

WEAK_PASSWORDS = {"change-me-to-a-strong-password", "", "password", "admin"}


def run(cmd, **kw):
    return subprocess.run(cmd, check=False, **kw)


def out(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kw).stdout.strip()


def _omniroute_binary() -> str | None:
    """Find the omniroute CLI on PATH or in the XDG bin dir."""
    found = shutil.which("omniroute")
    if found:
        return found
    candidates = [
        config_home() / "omniroute" / "bin" / "omniroute",
        data_home() / "omniroute" / "bin" / "omniroute",
        data_home() / "local" / "bin" / "omniroute",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def process_running() -> bool:
    """Check if an omniroute process is active or port is listening."""
    pid_out = out(["pgrep", "-f", "omniroute.*serve"])
    if pid_out.strip():
        return True
    # Fall back to checking whether the port is listening
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", int(PORT))) == 0
    except Exception:
        return False


def api_ready(timeout=90) -> bool:
    url = f"http://127.0.0.1:{PORT}/v1/models"
    deadline = time.time() + timeout
    delay = 1.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                return True
        except urllib.error.HTTPError as e:
            # 401/403 = auth required (normal state), server is up
            if e.code in (401, 403):
                return True
            # any other response proves the HTTP layer is alive
            return True
        except (OSError, ValueError):
            pass
        time.sleep(delay)
        delay = min(delay * 2, 10.0)
    return False


def service_installed() -> bool:
    return UNIT_FILE.exists()


def service_active() -> bool:
    return out(["systemctl", "--user", "is-active", "omniroute.service"]) == "active"


def read_env() -> dict:
    env = {}
    secret_dir = config_home() / "omniroute"
    for cand in (
        secret_dir / "omniroute.env",
        secret_dir / ".env",
    ):
        if cand.exists():
            for line in cand.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    pwd = env.get("INITIAL_PASSWORD", "")
    if pwd in WEAK_PASSWORDS and pwd:
        print("  ⚠ Warning: INITIAL_PASSWORD is a known-weak/placeholder value.", file=sys.stderr)
        print("    Set a strong password in $XDG_CONFIG_HOME/omniroute/omniroute.env", file=sys.stderr)
    return env


# ─── PodmanDaemonManager class (retained for API compatibility) ──────────
class PodmanDaemonManager(IDaemonManager):
    """AES facade: exposes OmniRoute host-native daemon verbs via IDaemonManager.

    No container engine required.
    """

    def __init__(self, root=None, daemons: object | None = None) -> None:
        pass

    # ─── Protocol ABC methods ──────────────────────────────────
    def start(self) -> int:
        return cmd_start()

    def stop(self) -> int:
        return cmd_stop()

    def restart(self) -> int:
        return cmd_restart()

    def status(self) -> DaemonStatus:
        cmd_status()
        return DaemonStatus(
            container_state="running" if process_running() else "stopped",
            service_state="active" if service_active() else "inactive" if service_installed() else "not-installed",
            api_ready=api_ready(timeout=3),
            data_dir=str(DATA_DIR),
            ok=process_running() and api_ready(timeout=3),
            details=(),
        )

    def logs(self) -> int:
        return cmd_logs()

    # ─── Legacy verb facades ───────────────────────────────────
    def models(self) -> int:
        return cmd_models()

    def service_install(self) -> int:
        return cmd_service_install()

    def service_status(self) -> int:
        return cmd_service_status()

    def service_uninstall(self) -> int:
        return cmd_service_uninstall()

    def help(self) -> int:
        return cmd_help()

    def main(self, argv) -> int:
        return main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


def cmd_service_install():
    binary = _omniroute_binary()
    if binary is None:
        print("Error: 'omniroute' binary not found on PATH. Install with:", file=sys.stderr)
        print("  npm install -g omniroute", file=sys.stderr)
        return 1
    UNIT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    src = ROOT / "modules/daemon/deploy/omniroute.service"
    if src.exists():
        shutil.copy2(src, UNIT_FILE)
    else:
        # Write a minimal unit file in-place
        unit_content = f"""\
[Unit]
Description=OmniRoute AI Gateway (host-native, no container)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HOME=%h
EnvironmentFile=-%h/.config/omniroute/omniroute.env
WorkingDirectory=%h/.omniroute
ExecStart={binary} serve --port {PORT} --no-open
Restart=always
RestartSec=5s

[Install]
WantedBy=default.target
"""
        UNIT_FILE.write_text(unit_content, encoding="utf-8")
    if shutil.which("loginctl"):
        run(["loginctl", "enable-linger", os.environ.get("USER", "raka")])
    run(["systemctl", "--user", "daemon-reload"])
    run(["systemctl", "--user", "enable", "--now", "omniroute.service"])
    print(f">>> Waiting for OmniRoute API to be ready at http://127.0.0.1:{PORT}...")
    if api_ready():
        print(f">>> [OK] OmniRoute daemon installed and active: omniroute.service (port {PORT})")
        print(f">>> Web Dashboard: http://localhost:{PORT}")
        return 0
    print(">>> [WARN] Service enabled, but API is still initializing. Check 'aa omniroute logs'.", file=sys.stderr)
    return 2


def cmd_service_uninstall():
    if UNIT_FILE.exists():
        print(">>> Disabling and stopping omniroute.service...")
        run(["systemctl", "--user", "disable", "--now", "omniroute.service"])
        UNIT_FILE.unlink(missing_ok=True)
        run(["systemctl", "--user", "daemon-reload"])
        print(">>> OmniRoute systemd user service removed.")
    else:
        print(">>> OmniRoute systemd service is not installed.")
    return 0


def cmd_service_status():
    if service_installed():
        return run(["systemctl", "--user", "status", "omniroute.service"]).returncode
    print("OmniRoute systemd service is not installed (run 'aa omniroute service-install').")
    return 0


def cmd_start():
    if service_installed():
        print(f">>> Starting OmniRoute via systemd service (omniroute.service, port {PORT})...")
        run(["systemctl", "--user", "start", "omniroute.service"])
        print(f">>> Waiting for OmniRoute API to be ready at http://127.0.0.1:{PORT}...")
        if api_ready():
            print(f">>> [OK] OmniRoute daemon is active and healthy!")
            print(f">>> Web Dashboard: http://localhost:{PORT}")
            return 0
        print(f"Warning: OmniRoute service started but API health check timed out. Check 'aa omniroute logs'.", file=sys.stderr)
        return 2
    binary = _omniroute_binary()
    if binary is None:
        print("Error: 'omniroute' binary not found. Install with: npm install -g omniroute", file=sys.stderr)
        return 1
    if process_running():
        print(f">>> OmniRoute is already running (port {PORT}).")
        return cmd_status()
    print(f">>> Starting OmniRoute host-native on port {PORT}...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [binary, "serve", "--port", PORT, "--no-open"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(f">>> Process PID: {proc.pid}")
    print(f">>> Waiting for OmniRoute API to be ready at http://127.0.0.1:{PORT}...")
    if api_ready():
        print(f">>> [OK] OmniRoute daemon is active and healthy!")
        print(f">>> Web Dashboard: http://localhost:{PORT}")
        return 0
    print(f"Warning: API health check timed out. Check logs in {DATA_DIR / 'logs'}.", file=sys.stderr)
    return 2


def cmd_stop():
    if service_installed():
        print(">>> Stopping OmniRoute via systemd service...")
        run(["systemctl", "--user", "stop", "omniroute.service"])
        print(">>> OmniRoute service stopped.")
        return 0
    if process_running():
        print(">>> Stopping OmniRoute process...")
        run(["pkill", "-f", "omniroute.*serve"])
        time.sleep(2)
        print(">>> OmniRoute stopped.")
    else:
        print(">>> OmniRoute is not running.")
    return 0


def cmd_restart():
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_status():
    print(f"OmniRoute Status (port {PORT}):")
    if process_running():
        print("  Process: RUNNING")
    else:
        print("  Process: STOPPED")
    if service_installed():
        print(f"  systemd: {'ACTIVE' if service_active() else 'INACTIVE'} (omniroute.service)")
    if api_ready(timeout=10):
        print(f"  API: OK (http://127.0.0.1:{PORT})")
    else:
        print("  API: not ready")
    print(f"  Data: {DATA_DIR}")
    return 0


def cmd_logs():
    if service_installed():
        return run(["systemctl", "--user", "status", "omniroute.service", "-n", "200"]).returncode
    log_file = DATA_DIR / "logs" / "omniroute.log"
    if log_file.exists():
        print(log_file.read_text(encoding="utf-8", errors="replace")[-20000:])
        return 0
    print("OmniRoute is not installed/running. No log file found.")
    return 1


def cmd_models():
    url = f"http://127.0.0.1:{PORT}/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            print(r.read().decode("utf-8", errors="replace"))
        return 0
    except (OSError, ValueError) as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        return 1


def cmd_help():
    print(f"Usage: aa omniroute <command> [args...]  (port {PORT})")
    print()
    print("Commands:")
    print("  start              Start OmniRoute daemon (host-native)")
    print("  stop               Stop OmniRoute daemon")
    print("  restart           Restart OmniRoute daemon")
    print("  status            Show process status and API health")
    print("  logs              Show service logs")
    print("  models            List available AI models")
    print("  service-install   Enable 24/7 systemd user service")
    print("  service-status    Show systemd service status")
    print("  service-uninstall Disable and remove systemd user service")
    print("  help              Show this help")
    return 0


def main(argv):
    if not argv or argv[0] in ("help", "-h", "--help"):
        return cmd_help()
    action = argv[0]
    dispatch = {
        "start": cmd_start, "stop": cmd_stop, "restart": cmd_restart,
        "status": cmd_status, "logs": cmd_logs, "models": cmd_models,
        "service-install": cmd_service_install, "service-status": cmd_service_status,
        "service-uninstall": cmd_service_uninstall,
    }
    handler = dispatch.get(action)
    if not handler:
        print(f"Unknown omniroute command: {action}", file=sys.stderr)
        return cmd_help()
    return handler()
