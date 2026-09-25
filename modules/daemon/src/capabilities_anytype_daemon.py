#!/usr/bin/env python3
"""Anytype daemon manager (Python) — replaces anytype-daemon.sh.

AES port of tools/daemons/anytype_daemon.py: body kept as-is; only the
imports are swapped to their AES equivalents (paths/xdg/envfile) and
constants defined locally in the original stay local as-is instead of
being pulled from modules.shared.src.taxonomy_common_constant.
"""
from __future__ import annotations

import atexit
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.taxonomy_common_vo import (
    agents_arwaky_config_dir,
)
from modules.shared.src.taxonomy_daemon_constant import (
    ANYTYPE_CONFIG_DIR,
    CONTAINER_NAME,
    DATA_DIR,
    DATA_ROOT,
    DOT_ANYTYPE,
    IMAGE_NAME,
    LOCAL_BIN,
    PID_FILE,
    ROOT,
    SHARE_DIR,
    UNIT_DIR,
)
from modules.shared.src.taxonomy_daemon_constant import (
    ANYTYPE_PORT as PORT,
)
from modules.shared.src.taxonomy_daemon_constant import (
    ANYTYPE_SCRIPT_DIR as SCRIPT_DIR,
)
from modules.shared.src.taxonomy_daemon_constant import (
    ANYTYPE_UNIT_FILE as UNIT_FILE,
)
from modules.shared.src.taxonomy_daemon_vo import DaemonStatus, ExitCode
from modules.shared.src.utility_envfile_parser import update_env_file
from modules.shared.src.utility_process_runner import cmd_out as out
from modules.shared.src.utility_process_runner import run_cmd as run


# ─── Block 1: Class Definition & Constructor ──────────────
class AnytypeDaemonManager(IDaemonProtocol):
    """AES facade: exposes the original script actions via IDaemonProtocol.

    Block 1 — constructor (stateless, no DI needed beyond module globals).
    Block 2 — protocol contract (execute) + lifecycle/unit methods it routes to.
    Block 3 — legacy action facades, factories, and helpers retained as-is.
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
        """Dispatch a protocol op to the matching action method.

        Args:
            op: protocol verb; unknown values raise ValueError.
            name: optional target name (e.g. auth account or space link).
            unit: accepted but unused for this capability.
        """
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
        if op == "auth-create":
            return ExitCode(self.auth_create(name or "agent"))
        if op == "auth-key":
            return ExitCode(self.auth_key(name or "arwaky-agent-key"))
        if op == "space-join":
            return ExitCode(self.space_join(name or ""))
        if op == "space-list":
            return ExitCode(self.space_list())
        if op == "help":
            return ExitCode(self.help())
        raise ValueError(f"Unknown daemon op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def start(self) -> ExitCode:
        """Start the daemon container (or native fallback) and wait for API."""
        return ExitCode(cmd_start())

    def stop(self) -> ExitCode:
        """Stop the running daemon container or native process."""
        return ExitCode(cmd_stop())

    def restart(self) -> ExitCode:
        """Restart the daemon by stopping then starting it again."""
        return ExitCode(cmd_restart())

    def status(self) -> DaemonStatus:
        """Probe container state and API readiness into a DaemonStatus."""
        # Probe once, print once — the legacy cmd_status path re-probed the
        # API up to three times with backoff and stalled `aa anytype status`.
        running = container_running()
        exists = container_exists() if not running else True
        ready = api_ready(timeout=3)
        print("==========================================")
        print(" Anytype Headless Daemon Status")
        print("==========================================")
        if has_podman():
            if running:
                print(" Container: RUNNING")
            elif exists:
                print(" Container: STOPPED (exists)")
            else:
                print(" Container: NOT FOUND")
        if ready:
            print(f" API: OK (http://127.0.0.1:{PORT})")
        else:
            print(" API: not ready")
        return DaemonStatus(
            container_state="running" if running else "stopped" if exists else "not-found",
            service_state="unknown",
            api_ready=ready,
            data_dir=str(DATA_ROOT),
            ok=running and ready,
            details=(),
        )

    def logs(self) -> ExitCode:
        """Show recent container or native log output."""
        return ExitCode(cmd_logs())

    def __repr__(self) -> str:
        return "AnytypeDaemonManager()"

    def auth_create(self, name: str = "agent") -> int:
        """Create a headless bot account with the given *name*."""
        return cmd_auth_create(name)

    def auth_key(self, name: str = "arwaky-agent-key") -> int:
        """Generate an API key for *name* and persist it into the .env file."""
        return cmd_auth_key(name)

    def space_join(self, link: str) -> int:
        """Join the Anytype Space identified by invite *link*."""
        return cmd_space_join(link)

    def space_list(self) -> int:
        """List all spaces joined by the daemon's bot account."""
        return cmd_space_list()

    def install_unit(self) -> ExitCode:
        """Enable and start the anytype-daemon.service systemd user unit."""
        return ExitCode(cmd_service_install())

    def unit_status(self) -> ExitCode:
        """Report systemd state of the anytype-daemon.service unit."""
        return ExitCode(cmd_service_status())

    def remove_unit(self) -> ExitCode:
        """Disable and stop the systemd service (also stops the daemon)."""
        return self.stop()

    def help(self) -> int:
        """Print usage information for the anytype daemon sub-commands."""
        return cmd_help()

    def main(self, argv) -> int:
        """Entry point: dispatch CLI args to the matching command."""
        return main(argv)


def has_podman():
    """True when the podman CLI is available on PATH."""
    return shutil.which("podman") is not None


def container_running():
    """True when the Anytype daemon container is currently up."""
    return out(
        ["podman", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME]
    ) == "true"


def container_exists():
    """True when a container with CONTAINER_NAME exists (running or stopped)."""
    return out(
        ["podman", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"]
    ) == CONTAINER_NAME


def api_ready(timeout=90):
    """Poll the daemon HTTP port until it answers or *timeout* seconds elapse."""
    url = f"http://127.0.0.1:{PORT}"
    deadline = time.time() + timeout
    delay = 1.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status < 400:
                    return True
        except urllib.error.HTTPError as e:
            # Any HTTP status (even 404 on /) proves the daemon answered.
            if e.code < 500:
                return True
        except (OSError, ValueError):
            pass
        # Exponential backoff: 1s, 2s, 4s, 8s... capped at 10s
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(delay, remaining))
        delay = min(delay * 2, 10.0)
    return False


def image_exists() -> bool:
    """True when the Anytype daemon Podman image is already pulled."""
    return subprocess.run(
        ["podman", "image", "exists", IMAGE_NAME],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def build_image():
    """Build the Anytype daemon container image from the deploy script."""
    print(">>> Building Anytype daemon image...")
    cwd = SCRIPT_DIR
    code = run(["podman", "build", "-t", IMAGE_NAME, "."], cwd=cwd).returncode
    if code != 0:
        print("Error: failed to build image", file=sys.stderr)
        sys.exit(1)


def ensure_dirs():
    """Create all XDG data and config directories required by the daemon."""
    for d in (DATA_DIR, DOT_ANYTYPE, ANYTYPE_CONFIG_DIR, SHARE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _write_pid(pid: int) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _read_pid():
    """Read the Anytype daemon PID from the PID file, returning None on failure."""
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def _cleanup_pid() -> None:
    PID_FILE.unlink(missing_ok=True)


def _extract_api_key(stdout: str) -> str:
    """Return first token-shaped line (API key), else last non-empty line."""
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    for ln in lines:
        m = re.search(r"[A-Za-z0-9_\-\.]{20,}", ln)
        if m:
            return m.group(0)
    return lines[-1] if lines else ""


def cmd_start():
    """Start the daemon via Podman or native fallback and wait for API readiness."""
    if has_podman():
        if container_running():
            print(f">>> Anytype daemon container '{CONTAINER_NAME}' is already running.")
            return 0
        ensure_dirs()
        if container_exists():
            print(f">>> Starting existing Anytype container '{CONTAINER_NAME}'...")
            run(["podman", "start", CONTAINER_NAME])
        else:
            if not image_exists():
                build_image()
            print(
                f">>> Launching Anytype daemon container '{CONTAINER_NAME}' on port {PORT}..."
            )
            run([
                "podman", "run", "-d", "--name", CONTAINER_NAME, "--network", "host",
                "--restart", "unless-stopped",
                "-v", f"{DATA_DIR}:/data:Z",
                "-v", f"{DOT_ANYTYPE}:/root/.anytype:Z",
                "-v", f"{ANYTYPE_CONFIG_DIR}:/root/.config/anytype:Z",
                "-v", f"{SHARE_DIR}:/root/.local/share/anytype:Z",
                IMAGE_NAME,
            ])
        print(f">>> Waiting for Anytype API on port {PORT}...")
        if api_ready():
            print(f">>> [OK] Anytype daemon is ready at http://127.0.0.1:{PORT}")
            return 0
        print(
            ">>> [WARN] Container started, but API is still initializing."
            " Check 'aa anytype logs'.",
            file=sys.stderr,
        )
        return 2
    # native fallback
    print(">>> Podman not found. Falling back to native background execution...")
    anytype_bin = LOCAL_BIN / "anytype"
    if not anytype_bin.exists():
        print("Error: local anytype binary not found.", file=sys.stderr)
        return 1
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    log_file = DATA_ROOT / "daemon.log"
    with log_file.open("ab") as f:
        p = subprocess.Popen(
            [str(anytype_bin), "serve", "--listen-address", f"127.0.0.1:{PORT}"],
            stdout=f,
            stderr=f,
            start_new_session=True,
        )
    _write_pid(p.pid)
    atexit.register(_cleanup_pid)
    print(f">>> Started local Anytype daemon (PID: {p.pid}). Logs: {log_file}")
    return 0


def cmd_stop():
    """Stop the daemon container or native process, cleaning up the PID file."""
    if has_podman() and container_exists():
        print(f">>> Stopping Anytype daemon container '{CONTAINER_NAME}'...")
        run(["podman", "stop", CONTAINER_NAME])
        return 0
    # Native mode: use PID file (targeted, not pkill)
    pid = _read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f">>> Sent SIGTERM to Anytype daemon (PID: {pid}).")
        except ProcessLookupError:
            print(">>> Anytype daemon process not found (stale PID file).")
        _cleanup_pid()
    elif shutil.which("pkill"):
        subprocess.run(
            ["pkill", "-f", "anytype serve"], capture_output=True, check=False
        )
        print(">>> Anytype daemon stopped.")
    else:
        print(">>> No Anytype daemon PID found and pkill unavailable.")
    return 0


def cmd_restart():
    """Stop then start the daemon, waiting 1s for the process to exit."""
    cmd_stop()
    time.sleep(1)
    return cmd_start()


def cmd_status():
    """Print container, API, and data-dir status of the daemon."""
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
        print(" API: not ready")
    return 0


def cmd_logs():
    """Tail the container journal or native log file (last 200 lines)."""
    if has_podman() and container_exists():
        return run(["podman", "logs", "-f", "--tail", "200", CONTAINER_NAME]).returncode
    log = DATA_ROOT / "daemon.log"
    if log.exists():
        return run(["tail", "-f", "-n", "200", str(log)]).returncode
    print("Anytype daemon is not running.")
    return 1


def cmd_exec_anytype(args):
    """Run an anytype subcommand inside the running container or local binary."""
    if has_podman() and container_running():
        return run(["podman", "exec", CONTAINER_NAME, "anytype", *args]).returncode
    anytype_bin = LOCAL_BIN / "anytype"
    if anytype_bin.exists():
        return run([str(anytype_bin), *args]).returncode
    print("Error: Anytype daemon not running and local binary not found.", file=sys.stderr)
    return 1


def cmd_auth_create(name="agent"):
    """Create a headless bot account with the given *name*."""
    # anytype-cli >=0.3: 'auth create <name>' (was 'account create --name')
    return cmd_exec_anytype(["auth", "create", name])


def cmd_auth_key(name="arwaky-agent-key"):
    """Generate API key and update .env with ANYTYPE_API_KEY (parse output)."""
    if has_podman() and container_running():
        result = subprocess.run(
            ["podman", "exec", CONTAINER_NAME, "anytype",
             "auth", "apikey", "create", name],
            capture_output=True, text=True, check=False,
        )
    elif (LOCAL_BIN / "anytype").exists():
        result = subprocess.run(
            [str(LOCAL_BIN / "anytype"), "auth", "apikey",
             "create", name],
            capture_output=True, text=True, check=False,
        )
    else:
        print("Error: Anytype daemon not running and local binary not found.", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return result.returncode

    # Parse API key from output (token-shaped regex)
    api_key = _extract_api_key(result.stdout)
    if not api_key:
        print("Error: could not extract API key from daemon output.", file=sys.stderr)
        return 1

    # Update .env (canonical $XDG_CONFIG_HOME/agents-arwaky + repo config placeholder)
    env_candidates = [
        agents_arwaky_config_dir() / "anytype.env",
        ROOT / "config/anytype.env",
    ]
    for env_path in env_candidates:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        update_env_file(env_path, "ANYTYPE_API_KEY", api_key)
        print(f"  \u2713 Updated ANYTYPE_API_KEY in {env_path}")

    print(f"  \u2713 API key generated: {name}")
    return 0


def cmd_space_join(link):
    """Join the Anytype Space identified by the invite *link*."""
    if not link:
        print("Error: Missing invite link.", file=sys.stderr)
        return 1
    return cmd_exec_anytype(["space", "join", link])


def cmd_space_list():
    """List all Anytype Spaces joined by the daemon's bot account."""
    return cmd_exec_anytype(["space", "list"])


def cmd_service_install():
    """Create and enable the anytype-daemon.service systemd user unit."""
    if not has_podman():
        print(
            "Error: Podman is required to install the systemd container service.",
            file=sys.stderr,
        )
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
    """Show systemd state of the anytype-daemon.service unit."""
    return run(["systemctl", "--user", "status", "anytype-daemon.service"]).returncode


def cmd_help():
    """Print usage and list available sub-commands for the Anytype daemon."""
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
    """Dispatch CLI args to the matching sub-command handler."""
    if not argv or argv[0] in ("help", "-h", "--help"):
        return cmd_help()
    action = argv[0]
    rest = argv[1:]
    dispatch = {
        "start": lambda: cmd_start(),
        "stop": lambda: cmd_stop(),
        "restart": lambda: cmd_restart(),
        "status": lambda: cmd_status(),
        "logs": lambda: cmd_logs(),
        "auth-create": lambda: cmd_auth_create(rest[0] if rest else "agent"),
        "auth-key": lambda: cmd_auth_key(rest[0] if rest else "arwaky-agent-key"),
        "space-join": lambda: cmd_space_join(rest[0] if rest else ""),
        "space-list": lambda: cmd_space_list(),
        "service-install": lambda: cmd_service_install(),
        "service-status": lambda: cmd_service_status(),
    }
    handler = dispatch.get(action)
    if handler:
        return handler()
    print(f"Unknown anytype command: {action}", file=sys.stderr)
    return cmd_help()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
