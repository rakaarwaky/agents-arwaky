"""Context7 adapter (pnpm workspace) — port of tools/install/install_context7.py.

@upstash/context7 is a pnpm workspace (MCP server + CLI). pnpm blocks
postinstall deps by default, so the copied pnpm-workspace.yaml is patched with
`dangerouslyAllowAllBuilds: true`. Runtime is installed in-place to
$XDG_DATA_HOME/context7; launchers point at packages/{mcp,cli}/dist/index.js.
"""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.taxonomy_xdg_paths import data_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec
from modules.installer.src.utility_adapter_base import AdapterBase, ROOT

SRC_REL = "vendor/context7"
APP_DIR = data_home() / "context7"
# Vendor artifacts that must not be included: stale node_modules (may contain
# broken symlinks), git, old build output, etc.
IGNORES = [
    "node_modules", ".git", ".old_modules*", "__pycache__", "mcpb",
    "dist", "target", "*.egg-info", ".venv", "venv", ".next", ".turbo",
]

LAUNCHERS = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}


class Context7Adapter(AdapterBase):
    """Install vendor/context7 (pnpm workspace) into XDG data, build, write launchers."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "context7-mcp").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src = self.ensure_source(root, SRC_REL)
        if not (src / "pnpm-workspace.yaml").exists():
            raise FileNotFoundError(f"context7 source not found (submodule not initialized): {src}")
        if not self.require("pnpm", "context7 is a pnpm workspace"):
            raise FileNotFoundError("pnpm is required (context7 is a pnpm workspace).")

        print(f">>> Installing context7 (pnpm workspace) into {APP_DIR}...")
        self.copy_app(src, APP_DIR, IGNORES)

        # pnpm blocks postinstall deps by default -> allow in this copy only
        ws = APP_DIR / "pnpm-workspace.yaml"
        if "dangerouslyAllowAllBuilds" not in ws.read_text(encoding="utf-8", errors="replace"):
            with ws.open("a", encoding="utf-8") as f:
                f.write("\ndangerouslyAllowAllBuilds: true\n")

        self.run(["pnpm", "install", "--frozen-lockfile"], APP_DIR)
        self.run(["pnpm", "run", "build"], APP_DIR)

        artifacts: list[Path] = []
        for name, entry in LAUNCHERS.items():
            target = APP_DIR / entry
            if not target.exists():
                print(f"  Warning: entry not found {target}", file=sys.stderr)
                continue
            artifacts.append(self.write_node_launcher(name, target))

        self.finish_bin()
        print(">>> Successfully installed context7")
        return artifacts
