"""9Router daemon manager capability — port of tools/daemons/ninerouter_daemon.py."""
from __future__ import annotations

import os
import secrets
import shutil
import string
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from modules.shared.src.common.taxonomy_core_constant import IMAGE_NAME, PORT
from modules.shared.src.daemon.contract_daemon_protocol import IDaemonManager
from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus
from modules.shared.src.envfile.utility_envfile import update_env_file
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.xdg.utility_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
    data_home,
)

CONTAINER_NAME = "9router"
WEAK_PASSWORDS = {"change-me-to-a-strong-password", "", "password", "admin"}


def _run(cmd: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, **kw)  # noqa: S603


def _out(cmd: list[str], **kw: object) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kw).stdout.strip()  # noqa: S603


def _get_engine() -> str | None:
    for engine in ("podman", "docker"):
        if shutil.which(engine):
            return engine
    return None


def _container_running() -> bool:
    engine = _get_engine()
    if not engine:
        return False
    return _out([engine, "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME]) == "true"


def _container_exists() -> bool:
    engine = _get_engine()
    if not engine:
        return False
    return _out([engine, "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"]) == CONTAINER_NAME


def _api_ready(timeout: int = 90) -> bool:
    url = f"http://127.0.0.1:{PORT}/v1/models"
    deadline = time.time() + timeout
    delay = 1.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status < 400:
                    return True
        except (OSError, ValueError):
            pass
        time.sleep(delay)
        delay = min(delay * 2, 10.0)
    return False


def _service_installed(unit_file: Path) -> bool:
    return unit_file.exists()


def _service_active() -> bool:
    return _out(["systemctl", "--user", "is-active", "9router.service"]) == "active"


class PodmanDaemonManager(IDaemonManager):
    """Manage the 9Router podman container (+ optional systemd user service).

    # Block 1: Configuration & credential handling
    # Block 2: Container / service lifecycle verbs
    # Block 3: Status snapshot & auxiliary verbs
    """

    # -- Block 1: Configuration & credential handling --------------------------
    def __init__(self) -> None:
        self._root = repo_root()
        self._image_name = os.environ.get("NINEROUTER_IMAGE", IMAGE_NAME)
        self._port = os.environ.get("NINEROUTER_PORT", PORT)
        self._data_dir = data_home() / "9router" / "data"
        self._unit_dir = config_home() / "systemd/user"
        self._unit_file = self._unit_dir / "9router.service"

    def _read_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        secret_dir = config_home() / "9router"
        for candidate in (
            agents_arwaky_config_dir() / "ninerouter.env",
            secret_dir / "ninerouter.env",
            secret_dir / ".env",
            self._root / "tools/config/ninerouter.env",
        ):
            if candidate.exists():
                for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip().strip('"').strip("'")
                break
        pwd = env.get("INITIAL_PASSWORD", "")
        if pwd in WEAK_PASSWORDS:
            print("  \u26a0 Warning: INITIAL_PASSWORD is a known-weak/placeholder value.", file=sys.stderr)
            print("    Set a strong password (min 16 chars, mixed case + digits + symbols) in", file=sys.stderr)
            print("    $XDG_CONFIG_HOME/9router/ninerouter.env", file=sys.stderr)
        return env

    def _generate_password(self, length: int = 24) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _ensure_initial_password(self, env: dict[str, str] | None = None) -> str:
        """Generate a strong INITIAL_PASSWORD if unset/weak and persist it (0600)."""
        env = env if env is not None else self._read_env()
        current = env.get("INITIAL_PASSWORD", "")
        weak = WEAK_PASSWORDS | {
            "123456", "12345678", "password123", "qwerty", "your-password",
            "your-secure-password", "change-me", "changeme",
        }
        if current and current not in weak and len(current) >= 16:
            return current
        password = self._generate_password(24)
        env_file = agents_arwaky_config_dir() / "ninerouter.env"
        update_env_file(env_file, "INITIAL_PASSWORD", password)
        try:
            env_file.chmod(0o600)
        except OSError:
            pass
        print(">>> Generated a strong INITIAL_PASSWORD for 9Router dashboard login.")
        print(f">>>   Stored in: {env_file} (mode 0600)")
        print(f">>>   Retrieve with: grep '^INITIAL_PASSWORD=' {env_file}")
        return password

    def _write_container_env(self, env: dict[str, str]) -> Path | None:
        """Write the INITIAL_PASSWORD to a 0600 file, zeroing the in-memory copy."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        env_file = self._data_dir / "container.env"
        lines: list[str] = []
        password = env.get("INITIAL_PASSWORD", "")
        if password:
            if "\n" in password or "\r" in password:
                raise ValueError("INITIAL_PASSWORD must not contain newline characters")
            lines.append(f"INITIAL_PASSWORD={password}")
        env["INITIAL_PASSWORD"] = ""
        if not lines:
            env_file.unlink(missing_ok=True)
            return None
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        env_file.chmod(0o600)
        return env_file

    # -- Block 2: Container / service lifecycle verbs --------------------------
    def start(self) -> int:
        if _service_installed(self._unit_file):
            print(">>> Starting 9Router via systemd service (9router.service)...")
            _run(["systemctl", "--user", "start", "9router.service"])
            print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{self._port}...")
            if _api_ready():
                print(">>> [OK] 9Router daemon is active and healthy!")
                print(f">>> Web Dashboard: http://localhost:{self._port}")
                return 0
            print("Warning: 9Router service started but API health check timed out.", file=sys.stderr)
            return 2
        engine = _get_engine()
        if not engine:
            print("Error: Neither podman nor docker was found. Please install podman.", file=sys.stderr)
            return 1
        if _container_running():
            print(f">>> 9Router daemon container '{CONTAINER_NAME}' is already running.")
            self.status()
            return 0
        env = self._read_env()
        env["INITIAL_PASSWORD"] = self._ensure_initial_password(env)
        env_args: list[str] = []
        try:
            env_file = self._write_container_env(env)
            if env_file:
                env_args += ["--env-file", str(env_file)]
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if _container_exists():
            print(f">>> Starting existing container '{CONTAINER_NAME}' with {engine}...")
            _run([engine, "start", CONTAINER_NAME])
        if not _container_running():
            print(f">>> Starting 9Router container '{CONTAINER_NAME}' ({self._image_name}) on port {self._port}...")
            self._data_dir.mkdir(parents=True, exist_ok=True)
            _run([engine, "run", "-d", "--name", CONTAINER_NAME, "-p", f"{self._port}:20128",
                  "-v", f"{self._data_dir}:/app/data:Z", "-e", "DATA_DIR=/app/data",
                  "-e", "PORT=20128", "-e", "HOSTNAME=0.0.0.0", *env_args,
                  "--restart", "unless-stopped", self._image_name])
        print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{self._port}...")
        if _api_ready():
            print(">>> [OK] 9Router daemon is active and healthy!")
            return 0
        print("Warning: API health check timed out. Check 'aa 9router logs'.", file=sys.stderr)
        return 2

    def stop(self) -> int:
        if _service_installed(self._unit_file):
            print(">>> Stopping 9Router via systemd service...")
            _run(["systemctl", "--user", "stop", "9router.service"])
            print(">>> 9Router service stopped.")
            return 0
        engine = _get_engine()
        if not engine:
            print("Error: No container engine found.", file=sys.stderr)
            return 1
        if _container_running():
            print(f">>> Stopping 9Router container '{CONTAINER_NAME}'...")
            _run([engine, "stop", CONTAINER_NAME])
            print(">>> 9Router stopped.")
        else:
            print(">>> 9Router is not running.")
        return 0

    def restart(self) -> int:
        self.stop()
        time.sleep(2)
        return self.start()

    # -- Block 3: Status snapshot & auxiliary verbs ------------------------------
    def status(self) -> DaemonStatus:
        engine = _get_engine()
        print("9Router Status:")
        if engine and _container_running():
            container_state = "RUNNING"
            print("  Container: RUNNING")
        elif engine and _container_exists():
            container_state = "STOPPED (exists)"
            print("  Container: STOPPED (exists)")
        else:
            container_state = "NOT FOUND"
            print("  Container: NOT FOUND")
        service_state = "none"
        if _service_installed(self._unit_file):
            service_state = "ACTIVE" if _service_active() else "INACTIVE"
            print(f"  systemd: {service_state} (9router.service)")
        api_ready = _api_ready(timeout=10)
        if api_ready:
            print(f"  API: OK (http://127.0.0.1:{self._port})")
        else:
            print("  API: not ready")
        print(f"  Data: {self._data_dir}")
        return DaemonStatus(
            container_state=container_state,
            service_state=service_state,
            api_ready=api_ready,
            data_dir=str(self._data_dir),
            ok=api_ready or service_state == "ACTIVE" or container_state == "RUNNING",
        )

    def logs(self) -> int:
        if _service_installed(self._unit_file):
            return _run(["systemctl", "--user", "status", "9router.service", "-n", "200"]).returncode
        engine = _get_engine()
        if engine and _container_exists():
            return _run([engine, "logs", "-f", "--tail", "200", CONTAINER_NAME]).returncode
        print("9Router is not installed/running.")
        return 1

    def models(self) -> int:
        url = f"http://127.0.0.1:{self._port}/v1/models"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                print(resp.read().decode("utf-8", errors="replace"))
            return 0
        except (OSError, ValueError) as exc:
            print(f"Error fetching models: {exc}", file=sys.stderr)
            return 1

    def service_install(self) -> int:
        if not shutil.which("podman"):
            print("Error: Podman is required to install the systemd container service.", file=sys.stderr)
            return 1
        self._unit_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_initial_password()
        src = self._root / "tools/deploy" / "ninerouter.service"
        if src.exists():
            shutil.copy2(src, self._unit_file)
        if shutil.which("loginctl"):
            _run(["loginctl", "enable-linger", os.environ.get("USER", "raka")])
        if _container_running() and not _service_active():
            engine = _get_engine()
            print(">>> Stopping existing standalone container '9router'...")
            _run([engine, "stop", CONTAINER_NAME])
            _run([engine, "rm", CONTAINER_NAME])
        _run(["systemctl", "--user", "daemon-reload"])
        _run(["systemctl", "--user", "enable", "--now", "9router.service"])
        print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{self._port}...")
        if _api_ready():
            print(">>> [OK] 9Router daemon installed and active: 9router.service")
            print(f">>> Web Dashboard: http://localhost:{self._port}")
            return 0
        print(">>> [WARN] Service enabled, but API is still initializing. Check 'aa 9router logs'.", file=sys.stderr)
        return 2

    def service_status(self) -> int:
        if _service_installed(self._unit_file):
            return _run(["systemctl", "--user", "status", "9router.service"]).returncode
        print("9Router systemd service is not installed (run 'aa 9router service-install').")
        return 0

    def service_uninstall(self) -> int:
        if self._unit_file.exists():
            print(">>> Disabling and stopping 9router.service...")
            _run(["systemctl", "--user", "disable", "--now", "9router.service"])
            self._unit_file.unlink(missing_ok=True)
            _run(["systemctl", "--user", "daemon-reload"])
            print(">>> 9Router systemd user service removed.")
        else:
            print(">>> 9Router systemd service is not installed.")
        return 0

    def help(self) -> int:
        print("Usage: aa 9router <command> [args...]")
        print()
        print("Commands:")
        print("  start              Start 9Router daemon")
        print("  stop               Stop 9Router daemon")
        print("  restart            Restart 9Router daemon")
        print("  status             Show container status and API health")
        print("  logs               Show container/service logs")
        print("  models             List available AI models")
        print("  service-install    Enable 24/7 systemd user service")
        print("  service-status     Show systemd service status")
        print("  service-uninstall  Disable and remove systemd user service")
        print("  help               Show this help")
        return 0
