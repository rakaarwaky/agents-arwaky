"""Anytype daemon manager capability — port of tools/daemons/anytype_daemon.py."""
from __future__ import annotations

import atexit
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from modules.shared.src.common.taxonomy_core_constant import ANYTYPE_PORT
from modules.shared.src.daemon.contract_daemon_protocol import IDaemonManager
from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus
from modules.shared.src.envfile.utility_envfile import update_env_file
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.xdg.utility_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
    state_home,
)

CONTAINER_NAME = "anytype-daemon"
IMAGE_NAME = "localhost/anytype-daemon:latest"


def _run(cmd: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, **kw)  # noqa: S603


def _out(cmd: list[str], **kw: object) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kw).stdout.strip()  # noqa: S603


def _has_podman() -> bool:
    return shutil.which("podman") is not None


def _container_running() -> bool:
    return _out(["podman", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME]) == "true"


def _container_exists() -> bool:
    return _out(["podman", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"]) == CONTAINER_NAME


class AnytypeDaemonManager(IDaemonManager):
    """Manage the Anytype headless daemon (podman container or native fallback).

    # Block 1: Configuration & image handling
    # Block 2: Container / native lifecycle verbs
    # Block 3: Status snapshot, logs & anytype-specific verbs
    """

    # -- Block 1: Configuration & image handling --------------------------------
    def __init__(self) -> None:
        self._root = repo_root()
        self._port = os.environ.get(
            "ANYTYPE_API_BASE_URL", f"http://127.0.0.1:{ANYTYPE_PORT}"
        ).split(":")[-1].strip("/")
        self._data_dir = data_home() / "anytype-mcp"
        self._dot_anytype = data_home() / "anytype"
        self._config_dir = config_home() / "anytype"
        self._share_dir = data_home() / "anytype" / "share"
        self._local_bin = data_home() / "anytype-mcp/bin"
        self._script_dir = self._root / "tools/deploy"
        self._unit_dir = config_home() / "systemd/user"
        self._unit_file = self._unit_dir / "anytype-daemon.service"
        self._data_root = data_home() / "anytype-mcp"
        self._pid_file = state_home() / "anytype-daemon.pid"

    def _api_ready(self, timeout: int = 90) -> bool:
        url = f"http://127.0.0.1:{self._port}"
        deadline = time.time() + timeout
        delay = 1.0
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=3) as resp:  # noqa: S310
                    if resp.status < 400:
                        return True
            except (OSError, ValueError):
                pass
            time.sleep(delay)
            delay = min(delay * 2, 10.0)
        return False

    def _image_exists(self) -> bool:
        return subprocess.run(  # noqa: S603
            ["podman", "image", "exists", IMAGE_NAME],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        ).returncode == 0

    def _build_image(self) -> None:
        print(">>> Building Anytype daemon image...")
        code = _run(["podman", "build", "-t", IMAGE_NAME, "."], cwd=self._script_dir).returncode
        if code != 0:
            print("Error: failed to build image", file=sys.stderr)
            sys.exit(1)

    def _ensure_dirs(self) -> None:
        for directory in (self._data_dir, self._dot_anytype, self._config_dir, self._share_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def _write_pid(self, pid: int) -> None:
        self._pid_file.parent.mkdir(parents=True, exist_ok=True)
        self._pid_file.write_text(str(pid), encoding="utf-8")

    def _read_pid(self) -> int | None:
        if self._pid_file.exists():
            try:
                return int(self._pid_file.read_text().strip())
            except (ValueError, OSError):
                return None
        return None

    def _cleanup_pid(self) -> None:
        self._pid_file.unlink(missing_ok=True)

    @staticmethod
    def _extract_api_key(stdout: str) -> str:
        """First token-shaped line (API key), else the last non-empty line."""
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        for line in lines:
            match = re.search(r"[A-Za-z0-9_\-\.]{20,}", line)
            if match:
                return match.group(0)
        return lines[-1] if lines else ""

    # -- Block 2: Container / native lifecycle verbs ---------------------------
    def start(self) -> int:
        if _has_podman():
            if _container_running():
                print(f">>> Anytype daemon container '{CONTAINER_NAME}' is already running.")
                return 0
            self._ensure_dirs()
            if _container_exists():
                print(f">>> Starting existing Anytype container '{CONTAINER_NAME}'...")
                _run(["podman", "start", CONTAINER_NAME])
            else:
                if not self._image_exists():
                    self._build_image()
                print(f">>> Launching Anytype daemon container '{CONTAINER_NAME}' on port {self._port}...")
                _run([
                    "podman", "run", "-d", "--name", CONTAINER_NAME, "--network", "host",
                    "--restart", "unless-stopped",
                    "-v", f"{self._data_dir}:/data:Z",
                    "-v", f"{self._dot_anytype}:/root/.anytype:Z",
                    "-v", f"{self._config_dir}:/root/.config/anytype:Z",
                    "-v", f"{self._share_dir}:/root/.local/share/anytype:Z",
                    IMAGE_NAME,
                ])
            print(f">>> Waiting for Anytype API on port {self._port}...")
            if self._api_ready():
                print(f">>> [OK] Anytype daemon is ready at http://127.0.0.1:{self._port}")
                return 0
            print(">>> [WARN] Container started, but API is still initializing. "
                  "Check 'aa anytype logs'.", file=sys.stderr)
            return 2
        # native fallback
        print(">>> Podman not found. Falling back to native background execution...")
        anytype_bin = self._local_bin / "anytype"
        if not anytype_bin.exists():
            print("Error: local anytype binary not found.", file=sys.stderr)
            return 1
        self._data_root.mkdir(parents=True, exist_ok=True)
        log_file = self._data_root / "daemon.log"
        with log_file.open("ab") as handle:
            proc = subprocess.Popen(  # noqa: S603, S607
                [str(anytype_bin), "serve", "--listen-address", f"127.0.0.1:{self._port}"],
                stdout=handle, stderr=handle, start_new_session=True,
            )
        self._write_pid(proc.pid)
        atexit.register(self._cleanup_pid)
        print(f">>> Started local Anytype daemon (PID: {proc.pid}). Logs: {log_file}")
        return 0

    def stop(self) -> int:
        if _has_podman() and _container_exists():
            print(f">>> Stopping Anytype daemon container '{CONTAINER_NAME}'...")
            _run(["podman", "stop", CONTAINER_NAME])
            return 0
        pid = self._read_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f">>> Sent SIGTERM to Anytype daemon (PID: {pid}).")
            except ProcessLookupError:
                print(">>> Anytype daemon process not found (stale PID file).")
            self._cleanup_pid()
        elif shutil.which("pkill"):
            subprocess.run(["pkill", "-f", "anytype serve"], capture_output=True, check=False)  # noqa: S603
            print(">>> Anytype daemon stopped.")
        else:
            print(">>> No Anytype daemon PID found and pkill unavailable.")
        return 0

    def restart(self) -> int:
        self.stop()
        time.sleep(1)
        return self.start()

    # -- Block 3: Status snapshot, logs & anytype-specific verbs ----------------
    def status(self) -> DaemonStatus:
        print("==========================================")
        print(" Anytype Headless Daemon Status")
        print("==========================================")
        container_state = "N/A"
        if _has_podman():
            if _container_running():
                container_state = "RUNNING"
                print(" Container: RUNNING")
            elif _container_exists():
                container_state = "STOPPED (exists)"
                print(" Container: STOPPED (exists)")
            else:
                container_state = "NOT FOUND"
                print(" Container: NOT FOUND")
        api_ready = self._api_ready(timeout=10)
        if api_ready:
            print(f" API: OK (http://127.0.0.1:{self._port})")
        else:
            print(" API: not ready")
        return DaemonStatus(
            container_state=container_state,
            service_state="none",
            api_ready=api_ready,
            data_dir=str(self._data_dir),
            ok=api_ready or container_state == "RUNNING",
        )

    def logs(self) -> int:
        if _has_podman() and _container_exists():
            return _run(["podman", "logs", "-f", "--tail", "200", CONTAINER_NAME]).returncode
        log = self._data_root / "daemon.log"
        if log.exists():
            return _run(["tail", "-f", "-n", "200", str(log)]).returncode
        print("Anytype daemon is not running.")
        return 1

    def _exec_anytype(self, args: list[str]) -> int:
        if _has_podman() and _container_running():
            return _run(["podman", "exec", CONTAINER_NAME, "anytype", *args]).returncode
        anytype_bin = self._local_bin / "anytype"
        if anytype_bin.exists():
            return _run([str(anytype_bin), *args]).returncode
        print("Error: Anytype daemon not running and local binary not found.", file=sys.stderr)
        return 1

    def auth_create(self, name: str = "agent") -> int:
        """'auth create <name>' (anytype-cli >=0.3; was 'account create --name')."""
        return self._exec_anytype(["auth", "create", name])

    def auth_key(self, name: str = "arwaky-agent-key") -> int:
        """Generate an API key and update .env with ANYTYPE_API_KEY."""
        if _has_podman() and _container_running():
            result = subprocess.run(  # noqa: S603
                ["podman", "exec", CONTAINER_NAME, "anytype", "auth", "apikey", "create", name],
                capture_output=True, text=True, check=False,
            )
        elif (self._local_bin / "anytype").exists():
            result = subprocess.run(  # noqa: S603
                [str(self._local_bin / "anytype"), "auth", "apikey", "create", name],
                capture_output=True, text=True, check=False,
            )
        else:
            print("Error: Anytype daemon not running and local binary not found.", file=sys.stderr)
            return 1
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return result.returncode
        api_key = self._extract_api_key(result.stdout)
        if not api_key:
            print("Error: could not extract API key from daemon output.", file=sys.stderr)
            return 1
        env_candidates = [
            agents_arwaky_config_dir() / "anytype.env",
            self._root / "tools/config/anytype.env",
        ]
        for env_path in env_candidates:
            env_path.parent.mkdir(parents=True, exist_ok=True)
            update_env_file(env_path, "ANYTYPE_API_KEY", api_key)
            print(f"  \u2713 Updated ANYTYPE_API_KEY in {env_path}")
        print(f"  \u2713 API key generated: {name}")
        return 0

    def space_join(self, link: str) -> int:
        if not link:
            print("Error: Missing invite link.", file=sys.stderr)
            return 1
        return self._exec_anytype(["space", "join", link])

    def space_list(self) -> int:
        return self._exec_anytype(["space", "list"])

    def service_install(self) -> int:
        if not _has_podman():
            print("Error: Podman is required to install the systemd container service.", file=sys.stderr)
            return 1
        self._unit_dir.mkdir(parents=True, exist_ok=True)
        src = self._script_dir / "anytype-daemon.service"
        if src.exists():
            shutil.copy2(src, self._unit_file)
        _run(["systemctl", "--user", "daemon-reload"])
        _run(["systemctl", "--user", "enable", "--now", "anytype-daemon.service"])
        print(">>> Anytype daemon installed and started as user systemd service: anytype-daemon.service")
        return 0

    def service_status(self) -> int:
        return _run(["systemctl", "--user", "status", "anytype-daemon.service"]).returncode

    def help(self) -> int:
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
