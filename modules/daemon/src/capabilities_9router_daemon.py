#!/usr/bin/env python3
"""9Router daemon manager (Python) — host-native, no container.

Runs the 9Router gateway directly on the host via the `9router` CLI
(npm global install), with a systemd user service for 24/7 operation.
No Podman required.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.taxonomy_common_vo import (
    config_home,
    data_home,
)
from modules.shared.src.taxonomy_daemon_constant import (
    DATA_DIR,
    PORT,
    ROOT,
    UNIT_DIR,
    UNIT_FILE,
    WEAK_PASSWORDS,
)
from modules.shared.src.taxonomy_daemon_vo import DaemonStatus, ExitCode
from modules.shared.src.utility_process_runner import cmd_out, run_cmd


def _run(cmd, **kw):
    return run_cmd(cmd, **kw)


def _out(cmd, **kw) -> str:
    return cmd_out(cmd, **kw)


# ─── Block 1: Class Definition & Constructor ──────────────
class NinerouterDaemonManager(IDaemonProtocol):
    """AES facade: exposes 9Router host-native daemon actions via IDaemonProtocol.

    No container engine required.
    """

    def __init__(self, root=None, daemons: object | None = None) -> None:
        pass

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        name: str | None = None,
        unit: str | None = None,
    ) -> DaemonStatus | ExitCode:
        if op == "start":
            return self.start()
        if op == "stop":
            return self.stop()
        if op == "restart":
            return self.restart()
        if op == "status":
            return self.status()
        if op == "logs":
            return self.logs()
        if op == "install_unit":
            return self.install_unit()
        if op == "remove_unit":
            return self.remove_unit()
        if op == "unit_status":
            return self.unit_status()
        if op == "models":
            return ExitCode(self.models())
        if op == "help":
            return self.help()
        raise ValueError(f"Unknown daemon op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def start(self) -> ExitCode:
        return ExitCode(cmd_start())

    def stop(self) -> ExitCode:
        return ExitCode(cmd_stop())

    def restart(self) -> ExitCode:
        return ExitCode(cmd_restart())

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

    def logs(self) -> ExitCode:
        return ExitCode(cmd_logs())

    def __repr__(self) -> str:
        return "NinerouterDaemonManager()"

    def models(self) -> int:
        return cmd_models()

    def install_unit(self) -> ExitCode:
        return ExitCode(cmd_service_install())

    def unit_status(self) -> ExitCode:
        return ExitCode(cmd_service_status())

    def remove_unit(self) -> ExitCode:
        return ExitCode(cmd_service_uninstall())

    def help(self) -> ExitCode:
        return ExitCode(cmd_help())

    def main(self, argv) -> int:
        return main(argv)


def _9router_binary() -> str | None:
    """Find the 9router CLI on PATH or in the XDG bin dir."""
    found = shutil.which("9router")
    if found:
        return found
    candidates = [
        config_home() / "9router" / "bin" / "9router",
        data_home() / "9router" / "bin" / "9router",
        data_home() / "local" / "bin" / "9router",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def process_running() -> bool:
    """True when the 9router server is up (port listens or CLI process lives).

    Prefer the port: `pgrep -f 9router` also matches status shells and this
    module's own command line, so it is only a secondary signal.
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", int(PORT))) == 0:
                return True
    except OSError:
        pass
    pid_out = _out(["pgrep", "-f", r"bin/9router( |$)"])
    return bool(pid_out.strip())


def api_ready(timeout=90) -> bool:
    url = f"http://127.0.0.1:{PORT}/api/health"
    deadline = time.time() + timeout
    delay = 1.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):
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
    return _out(["systemctl", "--user", "is-active", "9router.service"]) == "active"


def read_env() -> dict:
    env = {}
    secret_dir = config_home() / "9router"
    for cand in (
        config_home() / "agents-arwaky" / "ninerouter.env",
        secret_dir / "9router.env",
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
        print("    Set a strong password in $XDG_CONFIG_HOME/agents-arwaky/ninerouter.env", file=sys.stderr)
    return env


def cmd_service_install():
    binary = _9router_binary()
    if binary is None:
        print("Error: '9router' binary not found on PATH. Install with:", file=sys.stderr)
        print("  npm install -g 9router", file=sys.stderr)
        return 1
    UNIT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    src = ROOT / "modules/daemon/deploy/9router.service"
    if src.exists():
        shutil.copy2(src, UNIT_FILE)
    else:
        # Write a minimal unit file in-place
        unit_content = f"""\
[Unit]
Description=9Router AI Gateway (host-native, no container)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HOME=%h
Environment=PORT={PORT}
Environment=HOSTNAME=0.0.0.0
Environment=NODE_ENV=production
Environment=PATH=%h/.local/share/nodejs/node-v24.11.0-linux-x64/bin:%h/.local/bin:/usr/local/bin:/usr/bin
EnvironmentFile=-%h/.config/agents-arwaky/ninerouter.env
WorkingDirectory=%h/.9router
ExecStart={binary} --port {PORT} --no-browser --skip-update
Restart=always
RestartSec=5s

[Install]
WantedBy=default.target
"""
        UNIT_FILE.write_text(unit_content, encoding="utf-8")
    if shutil.which("loginctl"):
        _run(["loginctl", "enable-linger", os.environ.get("USER", "raka")])
    _run(["systemctl", "--user", "daemon-reload"])
    _run(["systemctl", "--user", "enable", "--now", "9router.service"])
    print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{PORT}...")
    if api_ready():
        print(f">>> [OK] 9Router daemon installed and active: 9router.service (port {PORT})")
        print(f">>> Web Dashboard: http://localhost:{PORT}")
        return 0
    print(">>> [WARN] Service enabled, but API is still initializing. Check 'aa 9router logs'.", file=sys.stderr)
    return 2


def cmd_service_uninstall():
    if UNIT_FILE.exists():
        print(">>> Disabling and stopping 9router.service...")
        _run(["systemctl", "--user", "disable", "--now", "9router.service"])
        UNIT_FILE.unlink(missing_ok=True)
        _run(["systemctl", "--user", "daemon-reload"])
        print(">>> 9Router systemd user service removed.")
    else:
        print(">>> 9Router systemd service is not installed.")
    return 0


def cmd_service_status():
    if service_installed():
        return _run(["systemctl", "--user", "status", "9router.service"]).returncode
    print("9Router systemd service is not installed (run 'aa 9router service-install').")
    return 0


def cmd_start():
    if service_installed():
        print(f">>> Starting 9Router via systemd service (9router.service, port {PORT})...")
        _run(["systemctl", "--user", "start", "9router.service"])
        print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{PORT}...")
        if api_ready():
            print(">>> [OK] 9Router daemon is active and healthy!")
            print(f">>> Web Dashboard: http://localhost:{PORT}")
            return 0
        print("Warning: 9Router service started but API health check timed out. Check 'aa 9router logs'.", file=sys.stderr)
        return 2
    binary = _9router_binary()
    if binary is None:
        print("Error: '9router' binary not found. Install with: npm install -g 9router", file=sys.stderr)
        return 1
    if process_running():
        print(f">>> 9Router is already running (port {PORT}).")
        return cmd_status()
    print(f">>> Starting 9Router host-native on port {PORT}...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [binary, "--port", PORT, "--no-browser", "--skip-update"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(f">>> Process PID: {proc.pid}")
    print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{PORT}...")
    if api_ready():
        print(">>> [OK] 9Router daemon is active and healthy!")
        print(f">>> Web Dashboard: http://localhost:{PORT}")
        return 0
    print(f"Warning: API health check timed out. Check logs in {DATA_DIR / 'logs'}.", file=sys.stderr)
    return 2


def cmd_stop():
    if service_installed():
        print(">>> Stopping 9Router via systemd service...")
        _run(["systemctl", "--user", "stop", "9router.service"])
        print(">>> 9Router service stopped.")
        return 0
    if process_running():
        print(">>> Stopping 9Router process...")
        # Match the real binary only — bare "9router" also hits this shell.
        _run(["pkill", "-f", r"bin/9router( |$)"])
        time.sleep(2)
        print(">>> 9Router stopped.")
    else:
        print(">>> 9Router is not running.")
    return 0


def cmd_restart():
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_status():
    print(f"9Router Status (port {PORT}):")
    if process_running():
        print("  Process: RUNNING")
    else:
        print("  Process: STOPPED")
    if service_installed():
        print(f"  systemd: {'ACTIVE' if service_active() else 'INACTIVE'} (9router.service)")
    if api_ready(timeout=10):
        print(f"  API: OK (http://127.0.0.1:{PORT})")
    else:
        print("  API: not ready")
    print(f"  Data: {DATA_DIR}")
    return 0


def cmd_logs():
    if service_installed():
        return _run(["systemctl", "--user", "status", "9router.service", "-n", "200"]).returncode
    log_file = DATA_DIR / "logs" / "9router.log"
    if log_file.exists():
        print(log_file.read_text(encoding="utf-8", errors="replace")[-20000:])
        return 0
    print("9Router is not installed/running. No log file found.")
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
    print(f"Usage: aa 9router <command> [args...]  (port {PORT})")
    print()
    print("Commands:")
    print("  start              Start 9Router daemon (host-native)")
    print("  stop               Stop 9Router daemon")
    print("  restart           Restart 9Router daemon")
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
        print(f"Unknown 9router command: {action}", file=sys.stderr)
        return cmd_help()
    return handler()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
