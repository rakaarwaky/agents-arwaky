"""Ponytail adapter (npm, no build) — verbatim port of tools/install/install_ponytail.py.

@dietrichgebert/ponytail has NO build script and no lockfile — just copy
source to $XDG_DATA_HOME/ponytail and install ponytail-mcp dependencies
(@modelcontextprotocol/sdk, zod) via npm. Entry MCP = ponytail-mcp/index.js.
"""
from __future__ import annotations

from pathlib import Path

from modules.installer.src.utility_adapter_base import AdapterBase, ROOT

SRC_REL = "vendor/ponytail"
APP_DIR_REL = "ponytail"
ENTRY = "ponytail-mcp/index.js"

# Old node_modules in vendor are not copied (may be stale); deps are reinstalled
# with npm --prefix inside APP_DIR/ponytail-mcp.
IGNORES = ["node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv"]


class PonytailAdapter(AdapterBase):
    """Install vendor/ponytail (npm, no build) into XDG data, write MCP launcher."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "ponytail-mcp").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_paths import data_home

        root = root or ROOT
        src = self.ensure_source(root, SRC_REL)
        if not (src / "package.json").exists():
            raise FileNotFoundError(f"ponytail source not found (submodule not initialized): {src}")
        if not self.require("npm", "ponytail requires npm (https://nodejs.org)"):
            raise FileNotFoundError("npm is required (https://nodejs.org).")

        app_dir = data_home() / APP_DIR_REL
        print(f">>> Installing ponytail (no build) into {app_dir}...")
        self.copy_app(src, app_dir, IGNORES)

        mcp_dir = app_dir / "ponytail-mcp"
        if (mcp_dir / "package.json").exists():
            self.run(["npm", "ci", "--no-audit", "--no-fund"], mcp_dir)

        entry = app_dir / ENTRY
        if not entry.exists():
            raise FileNotFoundError(f"entry not found {entry}")

        launcher = self.write_node_launcher("ponytail-mcp", entry)
        self.finish_bin()
        print(">>> Successfully installed ponytail")
        return [launcher]
