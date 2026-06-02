import os
import subprocess
import sys

def bump_version(current_version):
    parts = current_version.split('.')
    if len(parts) == 3:
        try:
            parts[2] = str(int(parts[2]) + 1)
            return '.'.join(parts)
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
    version_file = os.path.join(os.path.dirname(__file__), "..", "VERSION")
    if not os.path.exists(version_file):
        old_version = "1.0.0"
        print(f"Creating VERSION file with {old_version}")
    else:
        with open(version_file, 'r') as f:
            old_version = f.read().strip()
    
    new_version = bump_version(old_version)
    
    with open(version_file, 'w') as f:
        f.write(new_version)
    
    print(f"Bumped version: {old_version} -> {new_version}")
    
    # Also update main.go if it exists
    main_go_path = os.path.join(os.path.dirname(__file__), "..", "cmd", "github-mcp-server", "main.go")
    if os.path.exists(main_go_path):
        with open(main_go_path, 'r') as f:
            content = f.read()
        import re
        content = re.sub(r'var version = ".*?"', f'var version = "{new_version}"', content)
        with open(main_go_path, 'w') as f:
            f.write(content)
        run_command(["git", "add", main_go_path])

    # Git operations
    run_command(["git", "add", version_file])
    status = run_command(["git", "status", "--porcelain"])
    if status.stdout.strip():
        run_command(["git", "commit", "--no-verify", "-m", f"chore: bump version to {new_version}"])
        run_command(["git", "push"])
    else:
        print("No changes to commit")

if __name__ == "__main__":
    main()
