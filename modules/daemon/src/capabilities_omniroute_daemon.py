#!/usr/bin/env python3
"""OmniRoute daemon manager (Python) — host-native, no container.

Runs the OmniRoute gateway directly on the host via the `omniroute` CLI
(pnpm/npm global install), with a systemd user service for 24/7 operation.
No Docker, no Podman.

Port 7777 is a deliberate choice: dashboard and API share it because the
existing ``~/.omniroute/.env`` sets neither ``API_PORT`` nor
``DASHBOARD_PORT``, and upstream falls both back to ``PORT``
(``opts.port ?? process.env.PORT ?? "20128"`` in
``bin/cli/commands/serve.mjs`` of the pinned checkout). The systemd unit sets
``PORT`` rather than passing flags.

The upstream ``.env`` lives at ``~/.omniroute/.env`` — the one documented
exception to the per-tool XDG rule, because upstream reads it from its own
working directory. ``STORAGE_ENCRYPTION_KEY`` there decrypts every provider
credential in ``storage.sqlite``; never regenerate it.
"""
from __future__ import annotations

import os
import secrets
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
    OMNIROUTE_DATA_DIR,
    OMNIROUTE_ENV_FILE,
    OMNIROUTE_ENV_TEMPLATE,
    OMNIROUTE_HOST,
    OMNIROUTE_PORT,
    OMNIROUTE_UNIT_FILE,
    ROOT,
)
from modules.shared.src.taxonomy_daemon_vo import DaemonStatus, DaemonUnit, ExitCode
from modules.shared.src.taxonomy_tools_constant import OMNIROUTE_ENV_FILENAME
from modules.shared.src.utility_process_runner import cmd_out, run_cmd

#: Written only when neither the repo copy nor the repo template exists.
#: `STORAGE_ENCRYPTION_KEY` encrypts the provider credentials in storage.sqlite,
#: so this is a genuine last resort and never replaces a key that already
#: decrypts an existing database.


# ─── Block 1: Class Definition & Constructor ──────────────
class OmnirouteDaemonManager(IDaemonProtocol):
    """AES facade: exposes OmniRoute host-native daemon actions via IDaemonProtocol.

    No container engine required.
    """

    def __init__(self, root=None, daemons: object | None = None) -> None:
        pass

    # ─── Block 2: Protocol Method Implementation ──────────────
    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        """Enable and start the omniroute.service systemd user unit."""
        del unit  # OmniRoute owns a single unit; the caller passes it for routing
        return ExitCode(cmd_service_install())

    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        """Disable and remove the omniroute.service systemd user unit."""
        del unit  # OmniRoute owns a single unit; the caller passes it for routing
        return ExitCode(cmd_service_uninstall())

    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        """Report the state of the omniroute.service systemd unit."""
        del unit  # OmniRoute owns a single unit; the caller passes it for routing
        return ExitCode(cmd_service_status())

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def start(self) -> ExitCode:
        """Bring the gateway up via systemd or a detached host process."""
        return ExitCode(cmd_start())

    def stop(self) -> ExitCode:
        """Stop the running gateway service or process."""
        return ExitCode(cmd_stop())

    def restart(self) -> ExitCode:
        """Restart the gateway, waiting for API readiness after stop."""
        return ExitCode(cmd_restart())

    def status(self) -> DaemonStatus:
        """Probe process, systemd, and API state into a DaemonStatus."""
        cmd_status()
        running = process_running()
        ready = api_ready(timeout=3)
        return DaemonStatus(
            container_state="running" if running else "stopped",
            service_state="active" if service_active() else "inactive" if service_installed() else "not-installed",
            api_ready=ready,
            data_dir=str(OMNIROUTE_DATA_DIR),
            ok=running and ready,
            details=(),
        )

    def logs(self) -> ExitCode:
        """Show recent gateway logs via journalctl."""
        return ExitCode(cmd_logs())

    def __repr__(self) -> str:
        return "OmnirouteDaemonManager()"

    def models(self) -> int:
        """List AI model endpoints exposed at /v1/models."""
        return cmd_models()

    def help(self) -> ExitCode:
        """Print usage information for daemon sub-commands."""
        return ExitCode(cmd_help())


def _run(cmd, **kw):
    return run_cmd(cmd, **kw)


def _out(cmd, **kw) -> str:
    return cmd_out(cmd, **kw)


def _omniroute_binary() -> str | None:
    """Locate the omniroute launcher on PATH or inside an XDG node prefix."""
    found = shutil.which("omniroute")
    if found:
        return found
    for candidate in (
        OMNIROUTE_DATA_DIR / "bin" / "omniroute",
        config_home() / "omniroute" / "bin" / "omniroute",
        data_home() / "omniroute" / "bin" / "omniroute",
        data_home() / "local" / "bin" / "omniroute",
    ):
        if candidate.exists():
            return str(candidate)
    return None


def base_url() -> str:
    """Gateway base URL for the allocated dashboard port."""
    return f"http://{OMNIROUTE_HOST}:{OMNIROUTE_PORT}"


def process_running() -> bool:
    """True when the OmniRoute server is up (port listens or CLI process lives).

    The port is authoritative: `pgrep -f omniroute` also matches this module's
    own command line and the daemon CLI helpers, so it is only a fallback.
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", int(OMNIROUTE_PORT))) == 0:
                return True
    except OSError:
        pass
    return bool(_out(["pgrep", "-f", r"bin/omniroute( |$)"]).strip())


def api_ready(timeout=90) -> bool:
    """Poll the dashboard until it answers or *timeout* seconds elapse.

    Any HTTP response proves the server is up; 401/403 just means auth is on.
    """
    deadline = time.time() + timeout
    delay = 1.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base_url(), timeout=3):
                return True
        except urllib.error.HTTPError:
            # Any status code proves the HTTP layer is alive.
            return True
        except (OSError, ValueError):
            pass
        time.sleep(delay)
        delay = min(delay * 2, 10.0)
    return False


def service_installed() -> bool:
    """True when the omniroute.service unit file is present on disk."""
    return OMNIROUTE_UNIT_FILE.exists()


def service_active() -> bool:
    """True when the omniroute.service systemd user unit is currently active."""
    return _out(["systemctl", "--user", "is-active", "omniroute.service"]) == "active"


def read_env() -> dict:
    """Load OmniRoute env vars from the XDG env file (empty when absent)."""
    env: dict[str, str] = {}
    if not OMNIROUTE_ENV_FILE.exists():
        return env
    for line in OMNIROUTE_ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def seed_env() -> None:
    """Provision ``~/.omniroute/.env`` from the repo copy, never clobbering one.

    Sources, in order:
      1. ``config/omniroute.env``          — the operator's working copy
      2. ``config/omniroute.env.example``  — the committed template
      3. a generated minimal file           — last resort

    An existing target is left alone, always. Its ``STORAGE_ENCRYPTION_KEY``
    decrypts every provider credential in ``storage.sqlite``; regenerating it
    would leave the database unreadable while still looking like a healthy
    install, which is the worst possible failure mode here.
    """
    if OMNIROUTE_ENV_FILE.exists():
        return
    OMNIROUTE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    repo_env = ROOT / "config" / OMNIROUTE_ENV_FILENAME
    repo_example = ROOT / "config" / f"{OMNIROUTE_ENV_FILENAME}.example"
    if repo_env.exists():
        shutil.copy2(repo_env, OMNIROUTE_ENV_FILE)
        origin = f"your config/{OMNIROUTE_ENV_FILENAME}"
    elif repo_example.exists():
        shutil.copy2(repo_example, OMNIROUTE_ENV_FILE)
        origin = f"the template config/{OMNIROUTE_ENV_FILENAME}.example"
    else:
        OMNIROUTE_ENV_FILE.write_text(
            OMNIROUTE_ENV_TEMPLATE.format(
                storage_encryption_key=secrets.token_hex(32),
                port=OMNIROUTE_PORT,
            ),
            encoding="utf-8",
        )
        origin = "a generated file"
    try:
        OMNIROUTE_ENV_FILE.chmod(0o600)
    except OSError:
        pass
    print(f">>> Env: copied {origin} -> {OMNIROUTE_ENV_FILE}")
    print(">>>      Add provider keys with `omniroute setup`, then: aa omniroute restart")


def _unit_content(binary: str) -> str:
    """Render the systemd user unit for the host-native OmniRoute process."""
    node_bin = data_home() / "nodejs"
    node_path = f"{node_bin}/node-v24.11.0-linux-x64/bin" if node_bin.exists() else ""
    path_parts = [p for p in (node_path, "%h/.local/bin", "/usr/local/bin", "/usr/bin") if p]
    return f"""\
[Unit]
Description=OmniRoute AI Gateway (host-native, no container)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HOME=%h
Environment=NODE_ENV=production
Environment=PATH={":".join(path_parts)}
EnvironmentFile=-{OMNIROUTE_ENV_FILE}
WorkingDirectory={OMNIROUTE_DATA_DIR}
ExecStart={binary} serve --port {OMNIROUTE_PORT} --no-open --no-tray
Restart=always
RestartSec=5s

[Install]
WantedBy=default.target
"""


def cmd_service_install():
    """Install the systemd user unit, enable linger, and start the gateway."""
    binary = _omniroute_binary()
    if binary is None:
        print("Error: 'omniroute' launcher not found on PATH. Install it with:", file=sys.stderr)
        print("  aa tool install omniroute", file=sys.stderr)
        print("  (or manually: npm install -g omniroute)", file=sys.stderr)
        return 1
    seed_env()
    OMNIROUTE_UNIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OMNIROUTE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    src = ROOT / "modules/daemon/deploy/omniroute.service"
    if src.exists():
        # Keep the checked-in template authoritative but substitute the binary
        # path and ports resolved on this host.
        template = src.read_text(encoding="utf-8")
        template = template.replace("@@EXEC_BINARY@@", binary)
        template = template.replace("@@PORT@@", str(OMNIROUTE_PORT))
        template = template.replace("@@API_PORT@@", str(OMNIROUTE_PORT))
        template = template.replace("@@WS_PORT@@", str(OMNIROUTE_PORT))
        template = template.replace("@@HOST@@", OMNIROUTE_HOST)
        OMNIROUTE_UNIT_FILE.write_text(template, encoding="utf-8")
    else:
        OMNIROUTE_UNIT_FILE.write_text(_unit_content(binary), encoding="utf-8")
    if shutil.which("loginctl"):
        _run(["loginctl", "enable-linger", os.environ.get("USER", "raka")])
    _run(["systemctl", "--user", "daemon-reload"])
    _run(["systemctl", "--user", "enable", "--now", "omniroute.service"])
    print(f">>> Waiting for OmniRoute to be ready at {base_url()}...")
    if api_ready():
        print(f">>> [OK] OmniRoute daemon installed and active: omniroute.service (port {OMNIROUTE_PORT})")
        print(f">>> Web Dashboard: {base_url()}")
        return 0
    print(">>> [WARN] Service enabled, but the gateway is still initializing.", file=sys.stderr)
    print(">>>        Check 'aa omniroute logs'.", file=sys.stderr)
    return 2


def cmd_service_uninstall():
    """Disable and remove the omniroute.service systemd user unit."""
    if OMNIROUTE_UNIT_FILE.exists():
        print(">>> Disabling and stopping omniroute.service...")
        _run(["systemctl", "--user", "disable", "--now", "omniroute.service"])
        OMNIROUTE_UNIT_FILE.unlink(missing_ok=True)
        _run(["systemctl", "--user", "daemon-reload"])
        print(">>> OmniRoute systemd user service removed.")
    else:
        print(">>> OmniRoute systemd service is not installed.")
    return 0


def cmd_service_status():
    """Show systemd state of omniroute.service; 0 when not installed."""
    if service_installed():
        return _run(["systemctl", "--user", "status", "omniroute.service"]).returncode
    print("OmniRoute systemd service is not installed (run 'aa omniroute service-install').")
    return 0


def cmd_start():
    """Start the gateway via systemd or a detached host process."""
    if service_installed():
        print(f">>> Starting OmniRoute via systemd service (omniroute.service, port {OMNIROUTE_PORT})...")
        _run(["systemctl", "--user", "start", "omniroute.service"])
        print(f">>> Waiting for OmniRoute to be ready at {base_url()}...")
        if api_ready():
            print(">>> [OK] OmniRoute daemon is active and healthy!")
            print(f">>> Web Dashboard: {base_url()}")
            return 0
        print("Warning: service started but readiness timed out. Check 'aa omniroute logs'.", file=sys.stderr)
        return 2
    binary = _omniroute_binary()
    if binary is None:
        print("Error: 'omniroute' launcher not found. Install with: aa tool install omniroute", file=sys.stderr)
        return 1
    if process_running():
        print(f">>> OmniRoute is already running (port {OMNIROUTE_PORT}).")
        return cmd_status()
    seed_env()
    print(f">>> Starting OmniRoute host-native on port {OMNIROUTE_PORT}...")
    OMNIROUTE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **read_env()}
    proc = subprocess.Popen(
        [binary, "serve", "--port", str(OMNIROUTE_PORT), "--no-open", "--no-tray"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(f">>> Process PID: {proc.pid}")
    print(f">>> Waiting for OmniRoute to be ready at {base_url()}...")
    if api_ready():
        print(">>> [OK] OmniRoute daemon is active and healthy!")
        print(f">>> Web Dashboard: {base_url()}")
        return 0
    print(f"Warning: readiness timed out. Check logs in {OMNIROUTE_DATA_DIR / 'logs'}.", file=sys.stderr)
    return 2


def cmd_stop():
    """Stop the running gateway via systemd or pkill."""
    if service_installed():
        print(">>> Stopping OmniRoute via systemd service...")
        _run(["systemctl", "--user", "stop", "omniroute.service"])
        print(">>> OmniRoute service stopped.")
        return 0
    if process_running():
        print(">>> Stopping OmniRoute process...")
        _run(["pkill", "-f", r"bin/omniroute( |$)"])
        time.sleep(2)
        print(">>> OmniRoute stopped.")
    else:
        print(">>> OmniRoute is not running.")
    return 0


def cmd_restart():
    """Stop then start the gateway, giving the process time to exit."""
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_status():
    """Print process, systemd, and API health status of the gateway."""
    print(f"OmniRoute Status (port {OMNIROUTE_PORT}):")
    print(f"  Process: {'RUNNING' if process_running() else 'STOPPED'}")
    if service_installed():
        print(f"  systemd: {'ACTIVE' if service_active() else 'INACTIVE'} (omniroute.service)")
    print(f"  API: {'OK' if api_ready(timeout=10) else 'not ready'} ({base_url()})")
    print(f"  Port: {OMNIROUTE_PORT} (dashboard + API share it)")
    print(f"  Data: {OMNIROUTE_DATA_DIR}")
    print(f"  Config: {OMNIROUTE_ENV_FILE}")
    return 0


def cmd_logs():
    """Show journalctl output for the gateway (last 200 lines)."""
    if service_installed():
        return _run(["systemctl", "--user", "status", "omniroute.service", "-n", "200"]).returncode
    log_file = OMNIROUTE_DATA_DIR / "logs" / "omniroute.log"
    if log_file.exists():
        print(log_file.read_text(encoding="utf-8", errors="replace")[-20000:])
        return 0
    print("OmniRoute is not installed/running. No log file found.")
    return 1


def cmd_models():
    """Fetch and print the /v1/models response from the gateway."""
    url = f"{base_url()}/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            print(r.read().decode("utf-8", errors="replace"))
        return 0
    except (OSError, ValueError) as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        return 1


def cmd_help():
    """Print usage and list available sub-commands for the omniroute daemon."""
    print(f"Usage: aa omniroute <command> [args...]  (dashboard port {OMNIROUTE_PORT})")
    print()
    print("Commands:")
    print("  start              Start OmniRoute daemon (host-native)")
    print("  stop               Stop OmniRoute daemon")
    print("  restart            Restart OmniRoute daemon")
    print("  status             Show process status and API health")
    print("  logs               Show service logs")
    print("  models             List available AI models")
    print("  service-install    Enable 24/7 systemd user service")
    print("  service-status     Show systemd service status")
    print("  service-uninstall  Disable and remove systemd user service")
    print("  help               Show this help")
    print()
    print(f"Dashboard: {base_url()}")
    print(f"Port: {OMNIROUTE_PORT} (dashboard and API share it unless API_PORT/DASHBOARD_PORT are split)")
    print(f"Config: {OMNIROUTE_ENV_FILE}  — edit this file directly; `aa omniroute restart` reloads it")
    return 0


def main(argv):
    """Dispatch CLI args to the matching sub-command handler."""
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
