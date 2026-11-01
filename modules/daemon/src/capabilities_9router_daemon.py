#!/usr/bin/env python3
"""9router daemon manager (Python) — host-native, no container.

Runs the 9router gateway directly on the host via the `9router` CLI
(npm global install), with a systemd user service for 24/7 operation.
No Docker, no Podman.

Port 20128 is the 9router default (`-p/--port`). The systemd unit sets
`PORT` rather than passing flags. The upstream `.env` lives at
``$XDG_CONFIG_HOME/agents-arwaky/ninerouter.env``; the runtime keeps its
working directory at ``~/.9router`` and reads ``server.log`` from there.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from modules.shared.src.common.taxonomy_common_vo import (
    config_home,
    data_home,
)
from modules.shared.src.common.utility_process_runner import cmd_out, run_cmd
from modules.shared.src.daemon.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.daemon.taxonomy_daemon_constant import (
    NINEROUTER_DATA_DIR,
    NINEROUTER_PORT,
    NINEROUTER_UNIT_FILE,
    ROOT,
)
from modules.shared.src.daemon.taxonomy_daemon_vo import (
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)

__all__ = [
    "NinerouterDaemonManager",
]

#: Written only when neither the repo copy nor the repo template exists.
#: `STORAGE_ENCRYPTION_KEY` encrypts provider credentials; this is a genuine
#: last resort and never replaces a key that already decrypts an existing database.

# ─── Block 1: Class Definition & Constructor ──────────────
class NinerouterDaemonManager(IDaemonProtocol):
    """AES facade: exposes 9router host-native daemon actions via IDaemonProtocol.

    No container engine required.
    """

    def __init__(self, root=None, daemons: object | None = None, import_omni=None) -> None:
        self._import_omni = import_omni

    # ─── Block 2: Protocol Method Implementation ──────────────
    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        """Enable and start the 9router.service systemd user unit."""
        del unit  # 9router owns a single unit; the caller passes it for routing
        return ExitCode(cmd_service_install())

    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        """Disable and remove the 9router.service systemd user unit."""
        del unit  # 9router owns a single unit; the caller passes it for routing
        return ExitCode(cmd_service_uninstall())

    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        """Report the state of the 9router.service systemd unit."""
        del unit  # 9router owns a single unit; the caller passes it for routing
        return ExitCode(cmd_service_status())

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
            service_state=("not-installed" if not service_installed()
                           else ("active" if service_active() else "inactive")),
            api_ready=ready,
            data_dir=str(NINEROUTER_DATA_DIR),
            ok=running and ready,
            details=(),
        )

    def logs(self) -> ExitCode:
        """Show recent gateway logs via journalctl."""
        return ExitCode(cmd_logs())

    def models(self) -> int:
        """List AI model endpoints exposed at /v1/models."""
        return cmd_models()

    def help(self) -> ExitCode:
        """Print usage information for daemon sub-commands."""
        return ExitCode(cmd_help())

    def import_omniroute(self, argv: list[str]) -> ExitCode:
        """Migrate OmniRoute provider credentials into 9router."""
        if self._import_omni is None:
            print("import-omniroute requires the import capability to be wired in the container.", file=sys.stderr)
            return ExitCode(2)
        return ExitCode(self._import_omni.run_import(argv, cmd_stop, cmd_start))

    def __repr__(self) -> str:
        return "NinerouterDaemonManager()"


# ─── Block 3: Constructors, Std Traits, Helpers ───────────
def _run(cmd, **kw):
    return run_cmd(cmd, **kw)


def _out(cmd, **kw) -> str:
    return cmd_out(cmd, **kw)


def _is_9router_wrapper(path: Path) -> bool:
    """True when *path* is this repo's `aa 9router` wrapper, not the real CLI.

    The installer drops a Python shim at ``~/.local/bin/9router`` that only
    implements the ``aa`` sub-commands — it forwards to the composition root's
    ``modules.root_cli_entry.cmd_9router`` and understands nothing else.
    Handing that shim to systemd's ``ExecStart=... serve`` produces an
    immediate ``ModuleNotFoundError`` exit, and with ``Restart=always`` the unit
    crash-loops forever while the real gateway is nowhere in sight.
    """
    try:
        head = path.read_bytes()[:512]
    except OSError:
        return False
    return b"arwaky-installer" in head or b"surface_daemon_command" in head


def _9router_binary() -> str | None:
    """Locate the real 9router CLI (the one that accepts `serve`).

    ``shutil.which`` alone is not enough: ``~/.local/bin/9router`` is this
    repo's ``aa`` wrapper and shadows the genuine npm launcher. Resolve the
    node prefix first, then PATH, skipping the wrapper in both.
    """
    candidates: list[Path] = []
    nodejs = data_home() / "nodejs"
    if nodejs.exists():
        candidates += sorted(nodejs.glob("node-v*/bin/9router"), reverse=True)
    candidates += [
        NINEROUTER_DATA_DIR / "bin" / "9router",
        config_home() / "9router" / "bin" / "9router",
        data_home() / "9router" / "bin" / "9router",
    ]
    on_path = shutil.which("9router")
    if on_path:
        candidates.append(Path(on_path))
    for candidate in candidates:
        if candidate.is_file() and not _is_9router_wrapper(candidate):
            return str(candidate)
    return None


def base_url() -> str:
    """Gateway base URL for the allocated dashboard port."""
    return f"http://127.0.0.1:{NINEROUTER_PORT}"


def _systemd_main_pids() -> set[str]:
    """PIDs systemd currently tracks for 9router.service (empty when inactive)."""
    raw = _out(["systemctl", "--user", "show", "9router.service", "-p", "MainPID", "--value"])
    pids = set()
    for token in raw.split():
        if token.isdigit() and token != "0":
            pids.add(token)
    return pids


def _stray_daemons() -> list[str]:
    """PIDs of `9router serve` processes that systemd does not own.

    These are the ones a `systemctl stop` cannot reach, so `cmd_stop` has to
    sweep them explicitly.
    """
    owned = _systemd_main_pids()
    found = []
    for pid in _out(["pgrep", "-f", r"bin/9router( |$)"]).split():
        if pid.isdigit() and pid not in owned:
            found.append(pid)
    return found


def process_running() -> bool:
    """True when the 9router server is up (port listens or CLI process lives).

    The port is authoritative: `pgrep -f 9router` also matches this module's
    own command line and the daemon CLI helpers, so it is only a fallback.
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", int(NINEROUTER_PORT))) == 0:
                return True
    except OSError:
        pass
    return bool(_out(["pgrep", "-f", r"bin/9router( |$)"]).strip())


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
    """True when the 9router.service unit file is present on disk."""
    return NINEROUTER_UNIT_FILE.exists()


def service_active() -> bool:
    """True when the 9router.service systemd user unit is currently active."""
    return _out(["systemctl", "--user", "is-active", "9router.service"]) == "active"


def read_env() -> dict:
    """Load 9router env vars from the XDG env file (empty when absent)."""
    env: dict[str, str] = {}
    env_file = NINEROUTER_DATA_DIR / ".env"
    if not env_file.exists():
        return env
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def seed_env() -> None:
    """Provision ``~/.9router/.env`` from the repo copy, never clobbering one.

    Sources, in order:
      1. ``config/ninerouter.env``          — the operator's working copy
      2. ``config/ninerouter.env.example``  — the committed template
      3. a generated minimal file           — last resort

    An existing target is left alone, always.
    """
    env_file = NINEROUTER_DATA_DIR / ".env"
    if env_file.exists():
        return
    NINEROUTER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    repo_env = ROOT / "config" / "ninerouter.env"
    repo_example = ROOT / "config" / "ninerouter.env.example"
    if repo_env.exists():
        shutil.copy2(repo_env, env_file)
        origin = "your config/ninerouter.env"
    elif repo_example.exists():
        shutil.copy2(repo_example, env_file)
        origin = "the template config/ninerouter.env.example"
    else:
        env_file.write_text(
            f"# 9router — generated by `aa tool install 9router` for a fresh install.\nPORT={NINEROUTER_PORT}\n",
            encoding="utf-8",
        )
        origin = "a generated file"
    try:
        env_file.chmod(0o600)
    except OSError:
        pass
    print(f">>> Env: copied {origin} -> {env_file}")
    print(">>>      Add provider keys with `9router setup`, then: aa 9router restart")


def _unit_content(binary: str) -> str:
    """Render the systemd user unit for the host-native 9router process."""
    node_bin = data_home() / "nodejs"
    node_path = f"{node_bin}/node-v24.11.0-linux-x64/bin" if node_bin.exists() else ""
    path_parts = [p for p in (node_path, "%h/.local/bin", "/usr/local/bin", "/usr/bin") if p]
    return f"""\
[Unit]
Description=9router AI Gateway (host-native, no container)
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
Environment=HOME=%h
Environment=NODE_ENV=production
Environment=PATH={":".join(path_parts)}
EnvironmentFile=-%h/.9router/.env
WorkingDirectory=%h/.9router
ExecStart={binary} --port {NINEROUTER_PORT} --no-browser --skip-update
Restart=always
RestartSec=5s
TimeoutStopSec=30

[Install]
WantedBy=default.target
"""


def cmd_service_install():
    """Install the systemd user unit, enable linger, and start the gateway."""
    binary = _9router_binary()
    if binary is None:
        print("Error: '9router' launcher not found on PATH. Install it with:", file=sys.stderr)
        print("  aa tool install 9router", file=sys.stderr)
        print("  (or manually: npm install -g 9router)", file=sys.stderr)
        return 1
    seed_env()
    NINEROUTER_UNIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    NINEROUTER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    src = ROOT / "modules/daemon/deploy/9router.service"
    if src.exists():
        # Keep the checked-in template authoritative but substitute the binary
        # path and ports resolved on this host.
        template = src.read_text(encoding="utf-8")
        template = template.replace("@@EXEC_BINARY@@", binary)
        template = template.replace("@@PORT@@", str(NINEROUTER_PORT))
        template = template.replace("@@API_PORT@@", str(NINEROUTER_PORT))
        template = template.replace("@@WS_PORT@@", str(NINEROUTER_PORT))
        template = template.replace("@@HOST@@", "127.0.0.1")
        NINEROUTER_UNIT_FILE.write_text(template, encoding="utf-8")
    else:
        NINEROUTER_UNIT_FILE.write_text(_unit_content(binary), encoding="utf-8")
    if shutil.which("loginctl"):
        _run(["loginctl", "enable-linger", os.environ.get("USER", "raka")])
    _run(["systemctl", "--user", "daemon-reload"])
    _run(["systemctl", "--user", "enable", "--now", "9router.service"])
    print(f">>> Waiting for 9router to be ready at {base_url()}...")
    if api_ready():
        print(f">>> [OK] 9router daemon installed and active: 9router.service (port {NINEROUTER_PORT})")
        print(f">>> Web Dashboard: {base_url()}")
        return 0
    print(">>> [WARN] Service enabled, but the gateway is still initializing.", file=sys.stderr)
    print(">>>        Check 'aa 9router logs'.", file=sys.stderr)
    return 2


def cmd_service_uninstall():
    """Disable and remove the 9router.service systemd user unit."""
    if NINEROUTER_UNIT_FILE.exists():
        print(">>> Disabling and stopping 9router.service...")
        _run(["systemctl", "--user", "disable", "--now", "9router.service"])
        NINEROUTER_UNIT_FILE.unlink(missing_ok=True)
        _run(["systemctl", "--user", "daemon-reload"])
        print(">>> 9router systemd user service removed.")
    else:
        print(">>> 9router systemd service is not installed.")
    return 0


def cmd_service_status():
    """Show systemd state of 9router.service; 0 when not installed."""
    if service_installed():
        return _run(["systemctl", "--user", "status", "9router.service"]).returncode
    print("9router systemd service is not installed (run 'aa 9router service-install').")
    return 0


def cmd_start():
    """Start the gateway via systemd, falling back to a detached process.

    A gateway started by hand (or left over from an earlier run) already owns
    the port, so starting the unit on top of it only produces a bind conflict.
    Detect that first instead of reporting a false failure.
    """
    if process_running() and not service_active():
        print(f">>> 9router is already serving port {NINEROUTER_PORT} outside systemd.")
        print(">>> Run 'aa 9router service-install' to manage it as a unit.")
        return cmd_status()
    if service_installed():
        print(f">>> Starting 9router via systemd service (9router.service, port {NINEROUTER_PORT})...")
        _run(["systemctl", "--user", "start", "9router.service"])
        print(f">>> Waiting for 9router to be ready at {base_url()}...")
        if api_ready():
            print(">>> [OK] 9router daemon is active and healthy!")
            print(f">>> Web Dashboard: {base_url()}")
            return 0
        print("Warning: service started but readiness timed out. Check 'aa 9router logs'.", file=sys.stderr)
        return 2
    binary = _9router_binary()
    if binary is None:
        print("Error: '9router' launcher not found. Install with: aa tool install 9router", file=sys.stderr)
        return 1
    if process_running():
        print(f">>> 9router is already running (port {NINEROUTER_PORT}).")
        return cmd_status()
    seed_env()
    print(f">>> Starting 9router host-native on port {NINEROUTER_PORT}...")
    NINEROUTER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **read_env()}
    proc = subprocess.Popen(
        [binary, "--port", str(NINEROUTER_PORT), "--no-browser", "--skip-update"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(f">>> Process PID: {proc.pid}")
    print(f">>> Waiting for 9router to be ready at {base_url()}...")
    if api_ready():
        print(">>> [OK] 9router daemon is active and healthy!")
        print(f">>> Web Dashboard: {base_url()}")
        return 0
    print(f"Warning: readiness timed out. Check logs in {NINEROUTER_DATA_DIR / 'logs'}.", file=sys.stderr)
    return 2


def cmd_stop():
    """Stop the gateway via systemd, then sweep any stray detached process.

    Both paths are required: the unit file can be installed while the process
    actually serving the port was started by hand (or predates the unit), and
    stopping only systemd would silently leave that process holding the port.
    """
    if service_installed():
        print(">>> Stopping 9router via systemd service...")
        _run(["systemctl", "--user", "stop", "9router.service"])
    if _stray_daemons():
        print(">>> Stopping detached 9router process(es) not owned by systemd...")
        _run(["pkill", "-f", r"bin/9router( |$)"])
        for _ in range(20):
            if not _stray_daemons():
                break
            time.sleep(0.5)
    if not service_installed() and not _stray_daemons() and not process_running():
        print(">>> 9router is not running.")
        return 0
    print(">>> 9router stopped.")
    return 0


def cmd_restart():
    """Stop then start the gateway, giving the process time to exit."""
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_status() -> int:
    """Print process, systemd, and API health status of the gateway."""
    print(f"9router Status (port {NINEROUTER_PORT}):")
    print(f"  Process: {'RUNNING' if process_running() else 'STOPPED'}")
    if service_installed():
        print(f"  systemd: {'ACTIVE' if service_active() else 'INACTIVE'} (9router.service)")
    print(f"  API: {'OK' if api_ready(timeout=10) else 'not ready'} ({base_url()})")
    print(f"  Port: {NINEROUTER_PORT}")
    print(f"  Data: {NINEROUTER_DATA_DIR}")
    return 0


def cmd_logs():
    """Show journalctl output for the gateway (last 200 lines)."""
    if service_installed():
        return _run(["systemctl", "--user", "status", "9router.service", "-n", "200"]).returncode
    log_file = NINEROUTER_DATA_DIR / "logs" / "9router.log"
    if log_file.exists():
        print(log_file.read_text(encoding="utf-8", errors="replace")[-20000:])
        return 0
    print("9router is not installed/running. No log file found.")
    return 1


def cmd_models():
    """Fetch and print the /v1/models response from the gateway."""
    url = f"{base_url()}/v1/models"
    request = urllib.request.Request(url)
    key = read_env().get("9ROUTER_KEY") or os.environ.get("9ROUTER_KEY")
    if key:
        request.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(request, timeout=10) as r:
            print(r.read().decode("utf-8", errors="replace"))
        return 0
    except urllib.error.HTTPError as e:
        print(f"Error fetching models: HTTP {e.code} {e.reason}", file=sys.stderr)
        if e.code in (401, 403):
            print("Set 9ROUTER_KEY in ~/.9router/.env.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        return 1


def cmd_help():
    """Print usage and list available sub-commands for the 9router daemon."""
    print(f"Usage: aa 9router <command> [args...]  (port {NINEROUTER_PORT})")
    print()
    print("Commands:")
    print("  start              Start 9router daemon (host-native)")
    print("  stop               Stop 9router daemon")
    print("  restart            Restart 9router daemon")
    print("  status             Show process status and API health")
    print("  logs               Show service logs")
    print("  models             List available AI models")
    print("  service-install    Enable 24/7 systemd user service")
    print("  service-status     Show systemd service status")
    print("  service-uninstall  Disable and remove systemd user service")
    print("  import-omniroute   Migrate OmniRoute credentials into 9router [--dry-run]")
    print("  help               Show this help")
    print()
    print(f"Dashboard: {base_url()}")
    print(f"Port: {NINEROUTER_PORT}")
    print(f"Config: {NINEROUTER_DATA_DIR / '.env'}  — edit this file directly; `aa 9router restart` reloads it")
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
        print(f"Unknown 9router command: {action}", file=sys.stderr)
        return cmd_help()
    return handler()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
