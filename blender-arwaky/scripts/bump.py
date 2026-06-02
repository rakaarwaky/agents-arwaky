import os
import re
import subprocess
import sys


def bump_version(current_version):
    parts = current_version.split(".")
    if len(parts) == 3:
        try:
            parts[2] = str(int(parts[2]) + 1)
            return ".".join(parts)
        except ValueError:
            pass
    return current_version + ".1"


def run_command(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result


def main():
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "blender_mcp_addon", "blender_manifest.toml")

    if not os.path.exists(pyproject_path):
        print("pyproject.toml not found")
        sys.exit(1)

    with open(pyproject_path) as f:
        content = f.read()

    match = re.search(r'^version\s*=\s*"(.*?)"', content, re.MULTILINE)
    if not match:
        print("Could not find version in pyproject.toml")
        sys.exit(1)

    old_version = match.group(1)
    new_version = bump_version(old_version)

    new_content = re.sub(r'^version\s*=\s*".*?"', f'version = "{new_version}"', content, count=1, flags=re.MULTILINE)
    with open(pyproject_path, "w") as f:
        f.write(new_content)

    print(f"Bumped pyproject.toml version: {old_version} -> {new_version}")

    # Also bump blender_manifest.toml if it exists
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest_content = f.read()

        manifest_match = re.search(r'^version\s*=\s*"(.*?)"', manifest_content, re.MULTILINE)
        if manifest_match:
            old_manifest_version = manifest_match.group(1)
            new_manifest_content = re.sub(
                r'^version\s*=\s*".*?"', f'version = "{new_version}"', manifest_content, count=1, flags=re.MULTILINE
            )
            with open(manifest_path, "w") as f:
                f.write(new_manifest_content)
            print(f"Bumped blender_manifest.toml version: {old_manifest_version} -> {new_version}")
            run_command(["git", "add", manifest_path])
        else:
            print("Could not find version in blender_manifest.toml")
    else:
        print("blender_manifest.toml not found, skipping manifest bump")

    # Build addon and copy to root
    build_res = run_command([sys.executable, os.path.join(os.path.dirname(__file__), "build_addon.py")])
    if build_res.returncode == 0:
        import shutil
        root_zip = os.path.join(os.path.dirname(__file__), "..", "blender_mcp_addon.zip")
        dist_zip = os.path.join(os.path.dirname(__file__), "..", "dist", "blender_mcp_addon.zip")
        if os.path.exists(dist_zip):
            shutil.copy2(dist_zip, root_zip)
            print(f"Copied built addon to repository root: {root_zip}")
            run_command(["git", "add", root_zip])
        else:
            print("Warning: Built zip file not found in dist/")
    else:
        print("Error: Failed to build addon ZIP")
        sys.exit(1)

    # Git operations
    run_command(["git", "add", pyproject_path])
    status = run_command(["git", "status", "--porcelain"])
    if status.stdout.strip():
        run_command(["git", "commit", "--no-verify", "-m", f"chore: bump version to {new_version}"])
        run_command(["git", "tag", f"v{new_version}"])
        run_command(["git", "push"])
        run_command(["git", "push", "origin", f"v{new_version}"])
    else:
        print("No changes to commit")


if __name__ == "__main__":
    main()

