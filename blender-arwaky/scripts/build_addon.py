#!/usr/bin/env python3
import os
import zipfile
import sys
from pathlib import Path

def build_addon():
    # Setup paths relative to this script
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    addon_dir = project_root / "blender_mcp_addon"
    dist_dir = project_root / "dist"

    if not addon_dir.exists():
        print(f"Error: Addon directory '{addon_dir}' does not exist.")
        sys.exit(1)

    # Ensure dist directory exists
    dist_dir.mkdir(exist_ok=True)
    zip_path = dist_dir / "blender_mcp_addon.zip"

    print("Building Blender MCP Addon ZIP...")
    print(f"Source: {addon_dir}")
    print(f"Output: {zip_path}")

    # Files or directories to ignore
    ignore_patterns = {
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".git",
        ".DS_Store",
    }

    ignore_extensions = {
        ".pyc",
        ".pyo",
    }

    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(addon_dir):
            # Convert root to a Path object
            root_path = Path(root)
            
            # Prune directories we want to ignore in-place
            # (os.walk allows modifying dirs in-place to avoid traversing them)
            dirs[:] = [d for d in dirs if d not in ignore_patterns]

            for file in files:
                file_path = root_path / file
                
                # Skip files matching ignore rules
                if file in ignore_patterns:
                    continue
                if file_path.suffix in ignore_extensions:
                    continue
                # Skip config.py if it's ignored or contains secret local values
                if file == "config.py" and not (addon_dir / "config.py").exists():
                    continue

                # Calculate path relative to project root so the folder inside the ZIP is blender_mcp_addon
                arcname = file_path.relative_to(project_root)
                
                print(f"  Adding: {arcname}")
                zipf.write(file_path, arcname)
                count += 1

    # Verify the ZIP exists and print its size
    if zip_path.exists():
        size_kb = zip_path.stat().st_size / 1024
        print(f"\nSuccess! Built addon package with {count} files.")
        print(f"Package Size: {size_kb:.2f} KB")
        return True
    else:
        print("\nError: Failed to create ZIP file.")
        return False

if __name__ == "__main__":
    if build_addon():
        sys.exit(0)
    else:
        sys.exit(1)
