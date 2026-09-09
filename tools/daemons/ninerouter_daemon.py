#!/usr/bin/env python3
"""9Router daemon manager (Python) — replaces 9router-daemon.sh."""
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from ui import info, ok, warn, err, sub  # type: ignore[import-not-found]
from xdg import (  # type: ignore[import-untyped]
    agents_arwaky_config_dir,
    config_home,
    data_home,
)

CONTAINER_NAME = "9router"
IMAGE_NAME = os.environ.get("NINEROUTER_IMAGE", "ghcr.io/decolua/9router:latest")
PORT = os.environ.get("NINEROUTER_PORT", "20128")
DATA_DIR = data_home() / "9router" / "data"
SCRIPT_DIR = ROOT / "tools/deploy"
UNIT_DIR = config_home() / "systemd/user"
UNIT_FILE = UNIT_DIR / "9router.service"


def run(cmd, **kw):
    return subprocess.run(cmd, check=False, **kw)


def out(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kw).stdout.strip()


def get_engine():
    for e in ("podman", "docker"):
        if shutil.which(e):
            return e
    return None


def container_running():
    e = get_engine()
    if not e:
        return False
    return out([e, "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME]) == "true"


def container_exists():
    e = get_engine()
    if not e:
        return False
    return out([e, "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"]) == CONTAINER_NAME


def api_ready(timeout=90):
    url = f"http://127.0.0.1:{PORT}/v1/models"
    deadline = time.time() + timeout
    delay = 1.0
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status < 400:
                    return True
        except (OSError, ValueError):
            pass
        # Exponential backoff: 1s, 2s, 4s, 8s... capped at 10s
        time.sleep(delay)
        delay = min(delay * 2, 10.0)
    return False


def service_installed():
    return UNIT_FILE.exists()


def service_active():
    return out(["systemctl", "--user", "is-active", "9router.service"]) == "active"


WEAK_PASSWORDS = {"change-me-to-a-strong-password", "", "password", "admin"}


def read_env():
    env = {}
    secret_dir = config_home() / "9router"
    for cand in (
        agents_arwaky_config_dir() / "ninerouter.env",
        secret_dir / "ninerouter.env",
        secret_dir / ".env",
        ROOT / "tools/config/ninerouter.env",
    ):
        if cand.exists():
            for line in cand.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    pwd = env.get("INITIAL_PASSWORD", "")
    if pwd in WEAK_PASSWORDS:
        print("  \u26a0 Warning: INITIAL_PASSWORD is a known-weak/placeholder value.", file=sys.stderr)
        print("    Set a strong password (min 16 chars, mixed case + digits + symbols) in", file=sys.stderr)
        print("    $XDG_CONFIG_HOME/9router/ninerouter.env", file=sys.stderr)
    return env


def generate_password(length: int = 24) -> str:
    """Generate a cryptographically strong password (mixed case + digits + symbols)."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def ensure_initial_password(env: dict | None = None) -> str:
    """Generate a strong INITIAL_PASSWORD if unset/weak and persist it.

    Writes to $XDG_CONFIG_HOME/agents-arwaky/ninerouter.env (0600) —
    never inside the repository tree.
    """
    env = env if env is not None else read_env()
    current = env.get("INITIAL_PASSWORD", "")
    weak = WEAK_PASSWORDS | {
        "123456", "12345678", "password123", "qwerty", "your-password",
        "your-secure-password", "change-me", "changeme",
    }
    if current and current not in weak and len(current) >= 16:
        return current  # sudah kuat; pertahankan kredensial yang ada

    password = generate_password(24)
    env_file = agents_arwaky_config_dir() / "ninerouter.env"
    lines = []
    replaced = False
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("INITIAL_PASSWORD="):
                lines.append(f'INITIAL_PASSWORD="{password}"')
                replaced = True
            else:
                lines.append(line)
    if not replaced:
        lines.append(f'INITIAL_PASSWORD="{password}"')
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        env_file.chmod(0o600)
    except OSError:
        pass
    print(">>> Generated a strong INITIAL_PASSWORD for 9Router dashboard login.")
    print(f">>>   Stored in: {env_file} (mode 0600)")
    print(f">>>   Retrieve with: grep '^INITIAL_PASSWORD=' {env_file}")
    return password


def cmd_service_install():
    if not shutil.which("podman"):
        print("Error: Podman is required to install the systemd container service.", file=sys.stderr)
        return 1
    UNIT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_initial_password()
    src = SCRIPT_DIR / "ninerouter.service"
    if src.exists():
        shutil.copy2(src, UNIT_FILE)
    if shutil.which("loginctl"):
        run(["loginctl", "enable-linger", os.environ.get("USER", "raka")])
    if container_running() and not service_active():
        e = get_engine()
        print(">>> Stopping existing standalone container '9router'...")
        run([e, "stop", CONTAINER_NAME])
        run([e, "rm", CONTAINER_NAME])
    run(["systemctl", "--user", "daemon-reload"])
    run(["systemctl", "--user", "enable", "--now", "9router.service"])
    print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{PORT}...")
    if api_ready():
        print(">>> [OK] 9Router daemon installed and active: 9router.service")
        print(f">>> Web Dashboard: http://localhost:{PORT}")
        return 0
    print(">>> [WARN] Service enabled, but API is still initializing. Check 'aa 9router logs'.", file=sys.stderr)
    return 2


def cmd_service_uninstall():
    if UNIT_FILE.exists():
        print(">>> Disabling and stopping 9router.service...")
        run(["systemctl", "--user", "disable", "--now", "9router.service"])
        UNIT_FILE.unlink(missing_ok=True)
        run(["systemctl", "--user", "daemon-reload"])
        print(">>> 9Router systemd user service removed.")
    else:
        print(">>> 9Router systemd service is not installed.")
    return 0


def cmd_service_status():
    if service_installed():
        return run(["systemctl", "--user", "status", "9router.service"]).returncode
    print("9Router systemd service is not installed (run 'aa 9router service-install').")
    return 0


def write_container_env(env: dict):
    """Write container env to a 0600 file (avoid secrets on CLI).

    Secret is zeroed from the in-memory dict after writing (S-1).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    env_file = DATA_DIR / "container.env"
    lines = []
    password = env.get("INITIAL_PASSWORD", "")
    if password:
        if "\n" in password or "\r" in password:
            raise ValueError("INITIAL_PASSWORD must not contain newline characters")
        lines.append(f"INITIAL_PASSWORD={password}")
    # Zero out in-memory secret immediately (avoid core-dump / debug exposure)
    env["INITIAL_PASSWORD"] = ""
    if not lines:
        env_file.unlink(missing_ok=True)
        return None
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    env_file.chmod(0o600)
    return env_file


def cmd_start():
    if service_installed():
        print(">>> Starting 9Router via systemd service (9router.service)...")
        run(["systemctl", "--user", "start", "9router.service"])
        print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{PORT}...")
        if api_ready():
            print(">>> [OK] 9Router daemon is active and healthy!")
            print(f">>> Web Dashboard: http://localhost:{PORT}")
            return 0
        print("Warning: 9Router service started but API health check timed out.", file=sys.stderr)
        return 2
    engine = get_engine()
    if not engine:
        print("Error: Neither podman nor docker was found. Please install podman.", file=sys.stderr)
        return 1
    if container_running():
        print(f">>> 9Router daemon container '{CONTAINER_NAME}' is already running.")
        return cmd_status()
    env = read_env()
    env["INITIAL_PASSWORD"] = ensure_initial_password(env)
    env_args = []
    try:
        env_file = write_container_env(env)
        if env_file:
            env_args += ["--env-file", str(env_file)]
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if container_exists():
        print(f">>> Starting existing container '{CONTAINER_NAME}' with {engine}...")
        run([engine, "start", CONTAINER_NAME])
    if not container_running():
        print(f">>> Starting 9Router container '{CONTAINER_NAME}' ({IMAGE_NAME}) on port {PORT}...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        run([engine, "run", "-d", "--name", CONTAINER_NAME, "-p", f"{PORT}:20128",
             "-v", f"{DATA_DIR}:/app/data:Z", "-e", "DATA_DIR=/app/data",
             "-e", "PORT=20128", "-e", "HOSTNAME=0.0.0.0", *env_args,
             "--restart", "unless-stopped", IMAGE_NAME])
    print(f">>> Waiting for 9Router API to be ready at http://127.0.0.1:{PORT}...")
    if api_ready():
        print(">>> [OK] 9Router daemon is active and healthy!")
        return 0
    print("Warning: API health check timed out. Check 'aa 9router logs'.", file=sys.stderr)
    return 2


def cmd_stop():
    if service_installed():
        print(">>> Stopping 9Router via systemd service...")
        run(["systemctl", "--user", "stop", "9router.service"])
        print(">>> 9Router service stopped.")
        return 0
    engine = get_engine()
    if not engine:
        print("Error: No container engine found.", file=sys.stderr)
        return 1
    if container_running():
        print(f">>> Stopping 9Router container '{CONTAINER_NAME}'...")
        run([engine, "stop", CONTAINER_NAME])
        print(">>> 9Router stopped.")
    else:
        print(">>> 9Router is not running.")
    return 0


def cmd_restart():
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_status():
    engine = get_engine()
    print("9Router Status:")
    if engine and container_running():
        print("  Container: RUNNING")
    elif engine and container_exists():
        print("  Container: STOPPED (exists)")
    else:
        print("  Container: NOT FOUND")
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
        return run(["systemctl", "--user", "status", "9router.service", "-n", "200"]).returncode
    engine = get_engine()
    if engine and container_exists():
        return run([engine, "logs", "-f", "--tail", "200", CONTAINER_NAME]).returncode
    print("9Router is not installed/running.")
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
