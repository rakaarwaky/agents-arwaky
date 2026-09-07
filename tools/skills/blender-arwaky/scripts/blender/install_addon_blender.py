#!/usr/bin/env python3
"""Install the Blender Arwaky addon into a Blender installation.

Cross-platform: works on Windows, macOS, and Linux. On Linux, supports both
user-level (``~/.config/blender/<ver>/extensions/user_default``) and
system-wide (``/usr/share/blender/<ver>/scripts/addons``) installs.

Usage:
    # Auto-detect Blender and install for current user:
    uv run python scripts/blender/install_addon_blender.py

    # System-wide install (Linux only, requires sudo):
    uv run python scripts/blender/install_addon_blender.py --system

    # Skip auto-enable (Blender 5.x extensions are auto-discovered anyway):
    uv run python scripts/blender/install_addon_blender.py --no-enable
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def candidate_blender_paths() -> list[str]:
    """Return platform-specific Blender executable candidates."""
    env_path = os.environ.get("BLENDER_EXECUTABLE")
    if IS_WINDOWS:
        return [
            env_path,
            r"C:\Program Files\Blender Foundation\Blender\blender.exe",
            r"C:\Program Files (x86)\Blender Foundation\Blender\blender.exe",
            "blender.exe",
            "blender",
        ]
    if IS_MACOS:
        return [
            env_path,
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/usr/local/bin/blender",
            "blender",
        ]
    return [
        env_path,
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/snap/bin/blender",
        "blender",
    ]


def find_blender_path() -> str | None:
    """Find the Blender executable on the system."""
    for path in candidate_blender_paths():
        if not path:
            continue
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    return None


def run_blender_subprocess(blender_path: str, args: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    """Run a Blender subprocess with cross-platform display hints."""
    env = os.environ.copy()
    if IS_LINUX:
        # Improves stability when Blender runs without a real display server.
        env.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    return subprocess.run(
        [blender_path, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


def get_blender_scripts_path(blender_path: str) -> Path:
    """Get Blender's user scripts directory via ``bpy.utils.user_resource``."""
    result = run_blender_subprocess(
        blender_path,
        [
            "--background",
            "--python-expr",
            "import bpy; print('SCRIPTS_PATH=' + bpy.utils.user_resource('SCRIPTS'))",
        ],
        timeout=10,
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.strip().startswith("SCRIPTS_PATH="):
                path_str = line.strip().split("=", 1)[1].strip()
                if path_str:
                    return Path(path_str)

    # Fallback: derive from the highest version directory under config_base
    home = Path.home()
    config_base = home / ".config" / "blender"
    if config_base.exists():
        versions = sorted(
            (d for d in config_base.iterdir() if d.is_dir() and d.name[:1].isdigit()),
            reverse=True,
        )
        if versions:
            return config_base / versions[0].name / "scripts"
    return home / ".config" / "blender" / "5.1" / "scripts"


def find_blender_version(blender_path: str) -> str:
    """Return the short Blender version (``major.minor``)."""
    result = run_blender_subprocess(blender_path, ["--version"], timeout=10)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.strip().startswith("Blender"):
                parts = line.split()
                if len(parts) >= 2:
                    version_parts = parts[1].split(".")
                    if len(version_parts) >= 2:
                        return f"{version_parts[0]}.{version_parts[1]}"
    return "5.1"


def enable_addon(blender_path: str) -> bool:
    """Permanently enable the addon via Blender preferences."""
    enable_code = """
import bpy

try:
    bpy.ops.preferences.addon_enable(module="blender_mcp_addon")
    print("Blender Arwaky addon enabled successfully")
except Exception as e:
    print(f"Failed to enable addon: {e}")

try:
    bpy.ops.wm.save_userpref()
    print("User preferences saved")
except Exception as e:
    print(f"Failed to save preferences: {e}")
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(enable_code)
        temp_script = f.name
    try:
        result = run_blender_subprocess(
            blender_path,
            ["--background", "--python", temp_script],
            timeout=15,
        )
        print("Enable output:", result.stdout)
        if result.stderr:
            print("Enable errors:", result.stderr[:500])
        return result.returncode == 0
    finally:
        with contextlib.suppress(OSError):
            os.unlink(temp_script)


def install_addon(
    blender_path: str, addon_source_path: Path, *, user_install: bool = True, auto_enable: bool = True
) -> bool:
    """Install the addon to Blender (cross-platform)."""
    if not blender_path:
        print("ERROR: Blender not found. Please install Blender first.")
        return False
    if not addon_source_path.exists():
        print(f"ERROR: Addon source not found at {addon_source_path}")
        return False

    version = find_blender_version(blender_path)
    print(f"Blender version: {version}")

    if user_install:
        # Blender 5.x uses extensions; older versions fall back to addons/.
        home = Path.home()
        extensions_path = home / ".config" / "blender" / version / "extensions" / "user_default"
        addons_path = extensions_path
        print(f"Target extensions directory: {addons_path}")
    else:
        if not IS_LINUX:
            print("ERROR: System-wide install is only supported on Linux.")
            return False
        addons_path = Path(f"/usr/share/blender/{version}/scripts/addons")
        print(f"Target addons directory: {addons_path}")

    try:
        addons_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"ERROR: Cannot create directory {addons_path}. Permission denied.")
        if not user_install:
            print("Try running with sudo for system-wide install, or use user install (default).")
        return False

    addon_dest = addons_path / "blender_mcp_addon"
    try:
        if addon_dest.exists():
            print(f"Removing existing addon at {addon_dest}")
            shutil.rmtree(addon_dest)

        print(f"Copying addon from {addon_source_path} to {addon_dest}")
        shutil.copytree(addon_source_path, addon_dest)

        for root, dirs, files in os.walk(addon_dest):
            for d in dirs:
                os.chmod(Path(root) / d, 0o755)
            for f in files:
                os.chmod(Path(root) / f, 0o644)

        print(f"\nSUCCESS: Addon installed to {addon_dest}")

        if auto_enable:
            version_major = int(version.split(".")[0])
            if version_major >= 5:
                print("\nBlender 5.x detected: extension will be auto-discovered.")
                print("Enable it in: Edit > Preferences > Extensions > search 'Blender Arwaky'")
            elif enable_addon(blender_path):
                print("\nAddon is now ENABLED and will be active every time you open Blender.")
            else:
                print("\nWARNING: Auto-enable failed. Enable manually:")
                print("  Edit > Preferences > Add-ons > search 'Blender Arwaky' > check the box")
        else:
            print("\nManual enable required:")
            print("  Edit > Preferences > Extensions > search 'Blender Arwaky' > enable")

        print("\nDone! You can now start Blender and use Blender Arwaky.")
        return True
    except (OSError, shutil.Error) as e:
        print(f"ERROR during installation: {e}")
        return False


def parse_args(argv: list[str]) -> tuple[bool, bool]:
    """Parse CLI flags. Returns ``(user_install, auto_enable)``."""
    user_install = "--system" not in argv and "--system-wide" not in argv
    auto_enable = "--no-enable" not in argv and "--disable-auto-enable" not in argv
    return user_install, auto_enable


def main() -> int:
    addon_path = Path(__file__).parent.parent.parent / "blender_mcp_addon"

    print("=" * 60)
    print("Blender Arwaky Addon Installer")
    print("=" * 60)
    print()

    print("Searching for Blender...")
    blender_path = find_blender_path()
    if not blender_path:
        print("ERROR: Blender not found in PATH or common locations.")
        print("Set the BLENDER_EXECUTABLE environment variable to override.")
        print("Download Blender from https://www.blender.org/download/")
        return 1

    print(f"Found Blender at: {blender_path}")
    print()

    user_install, auto_enable = parse_args(sys.argv[1:])
    print(f"Mode: {'User installation' if user_install else 'System-wide installation (Linux only)'}")
    print(f"Auto-enable: {'ON' if auto_enable else 'OFF'}")
    print()

    success = install_addon(
        blender_path,
        addon_path,
        user_install=user_install,
        auto_enable=auto_enable,
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
