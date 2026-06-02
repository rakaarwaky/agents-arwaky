#!/usr/bin/env python3
"""
Install Blender MCP addon to Blender 5.1 on Fedora.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_blender_path():
    """Find the Blender executable path."""
    possible_paths = [
        "/home/raka/SharedData/App/Blender/blender",  # Primary: correct path
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "blender",  # in PATH
    ]

    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return path
        except Exception:
            continue

    return None


def get_blender_scripts_path(blender_path):
    """Get Blender's scripts directory path."""
    # Set environment for stability
    env = os.environ.copy()
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"

    try:
        # Run Blender to get the scripts directory
        # Using a marker to reliably extract the path from noisy output
        result = subprocess.run(
            [
                blender_path,
                "--background",
                "--python-expr",
                "import bpy; print('SCRIPTS_PATH=' + bpy.utils.user_resource('SCRIPTS'))",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.strip().startswith("SCRIPTS_PATH="):
                    path_str = line.strip().split("=", 1)[1]
                    if path_str:
                        return Path(path_str)
    except Exception as e:
        print(f"Error getting Blender scripts path: {e}")

    # Fallback to common Fedora paths
    home = Path.home()

    # Try to detect version from installed files
    config_base = home / ".config" / "blender"
    if config_base.exists():
        versions = sorted(
            [d for d in config_base.iterdir() if d.is_dir() and d.name[0].isdigit()],
            reverse=True,
        )
        if versions:
            return config_base / versions[0].name / "scripts"

    return home / ".config" / "blender" / "5.2" / "scripts"


def find_blender_version(blender_path):
    """Get the installed Blender version."""
    try:
        result = subprocess.run(
            [blender_path, "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            for line in lines:
                if line.strip().startswith("Blender"):
                    # Example: "Blender 5.1.0 (sub 0)"
                    parts = line.split()
                    if len(parts) >= 2:
                        version_str = parts[1]
                        # Convert "5.1.0" to "5.1"
                        version_parts = version_str.split(".")
                        if len(version_parts) >= 2:
                            return f"{version_parts[0]}.{version_parts[1]}"
    except Exception as e:
        print(f"Error getting Blender version: {e}")

    return "5.1"  # Default fallback


def enable_addon(blender_path):
    """Enable the addon permanently in Blender preferences."""
    import tempfile

    enable_code = """
import bpy

# Enable the addon
try:
    bpy.ops.preferences.addon_enable(module="blender_mcp_addon")
    print("Blender MCP addon enabled successfully")
except Exception as e:
    print(f"Failed to enable addon: {e}")

# Save user preferences
try:
    bpy.ops.wm.save_userpref()
    print("User preferences saved")
except Exception as e:
    print(f"Failed to save preferences: {e}")
"""

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(enable_code)
        temp_script = f.name

    # Set environment for stability
    env = os.environ.copy()
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"

    try:
        result = subprocess.run(
            [blender_path, "--background", "--python", temp_script],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        print("Enable output:", result.stdout)
        if result.stderr:
            print("Enable errors:", result.stderr[:500])  # Truncate long stderr
        return result.returncode == 0
    except Exception as e:
        print(f"Error enabling addon: {e}")
        return False
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_script)
        except Exception:
            pass


def install_addon(blender_path, addon_source_path, user_install=True, auto_enable=True):
    """Install the addon to Blender."""
    if not blender_path:
        print("ERROR: Blender not found. Please install Blender first.")
        return False

    if not addon_source_path.exists():
        print(f"ERROR: Addon source not found at {addon_source_path}")
        return False

    # Get Blender version and scripts path
    version = find_blender_version(blender_path)
    scripts_path = get_blender_scripts_path(blender_path)

    if user_install:
        # User-specific installation
        addons_path = scripts_path / "addons"
    else:
        # System-wide installation (requires sudo)
        addons_path = Path(f"/usr/share/blender/{version}/scripts/addons")

    print(f"Blender version: {version}")

    if user_install:
        # Blender 5.x uses extensions system
        home = Path.home()
        extensions_path = (
            home / ".config" / "blender" / version / "extensions" / "user_default"
        )
        addons_path = extensions_path
        print(f"Target extensions directory: {addons_path}")
    else:
        scripts_path = get_blender_scripts_path(blender_path)
        addons_path = Path(f"/usr/share/blender/{version}/scripts/addons")
        print(f"Target addons directory: {addons_path}")

    # Create addons directory if it doesn't exist
    try:
        addons_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"ERROR: Cannot create directory {addons_path}. Permission denied.")
        if not user_install:
            print(
                "Try running with sudo for system-wide install, or use user install (default)."
            )
        return False

    # Copy addon files
    addon_dest = addons_path / "blender_mcp_addon"
    try:
        if addon_dest.exists():
            print(f"Removing existing addon at {addon_dest}")
            shutil.rmtree(addon_dest)

        print(f"Copying addon from {addon_source_path} to {addon_dest}")
        shutil.copytree(addon_source_path, addon_dest)

        # Set permissions (readable by all)
        for root, dirs, files in os.walk(addon_dest):
            for d in dirs:
                os.chmod(Path(root) / d, 0o755)
            for f in files:
                os.chmod(Path(root) / f, 0o644)

        print(f"\nSUCCESS: Addon installed to {addon_dest}")

        if auto_enable:
            # Blender 5.x: extensions are auto-discovered via blender_manifest.toml
            # No need to call bpy.ops.preferences.addon_enable in background mode
            version_major = int(version.split(".")[0])
            if version_major >= 5:
                print("\nBlender 5.x detected: extension will be auto-discovered.")
                print(
                    "Enable it in: Edit > Preferences > Extensions > search 'Blender MCP'"
                )
            else:
                print("\nEnabling addon automatically...")
                if enable_addon(blender_path):
                    print(
                        "\nAddon is now ENABLED and will be active every time you open Blender."
                    )
                else:
                    print("\nWARNING: Auto-enable failed. Enable manually:")
                    print(
                        "  Edit > Preferences > Add-ons > search 'Blender MCP' > check the box"
                    )
        else:
            print("\nManual enable required:")
            print("  Edit > Preferences > Extensions > search 'Blender MCP' > enable")

        print("\nDone! You can now start Blender and use Blender MCP.")
        return True

    except Exception as e:
        print(f"ERROR during installation: {e}")
        return False


def main():
    script_dir = Path(__file__).parent.parent.resolve()
    addon_path = script_dir / "blender_mcp_addon"

    print("=" * 60)
    print("Blender MCP Addon Installer for Fedora")
    print("=" * 60)
    print()

    # Find Blender
    print("Searching for Blender...")
    blender_path = find_blender_path()

    if not blender_path:
        print("ERROR: Blender not found in PATH or common locations.")
        print("Please install Blender 5.1 or ensure it's in your PATH.")
        print("You can download Blender from https://www.blender.org/download/")
        sys.exit(1)

    print(f"Found Blender at: {blender_path}")
    print()

    # Check flags
    user_install = True
    auto_enable = True

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ["--system", "--system-wide"]:
                user_install = False
            elif arg in ["--no-enable", "--disable-auto-enable"]:
                auto_enable = False

    if user_install:
        print("Mode: User installation (no admin rights needed)")
    else:
        print("Mode: System-wide installation (requires sudo)")

    if auto_enable:
        print("Auto-enable: ON (addon will be enabled automatically)")
    else:
        print("Auto-enable: OFF (you must enable manually in Blender)")

    print()

    # Install
    success = install_addon(
        blender_path, addon_path, user_install=user_install, auto_enable=auto_enable
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
