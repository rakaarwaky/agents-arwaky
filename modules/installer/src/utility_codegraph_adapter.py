"""Codegraph adapter (npm) — verbatim port of tools/install/install_codegraph.py.

@colbymchenry/codegraph is a TypeScript project built with npm. Lockfile
package-lock.json -> `npm ci`; build `npm run build` (tsc + copy-assets +
build:ui) produces dist/bin/codegraph.js. Launchers codegraph-mcp &
codegraph both point at dist/bin/codegraph.js (tool dispatches mode via args).
"""
from __future__ import annotations

from pathlib import Path

from modules.installer.src.utility_adapter_base import AdapterBase, ROOT, NODE_IGNORES

SRC_REL = "vendor/codegraph"
ENTRY = "dist/bin/codegraph.js"
LAUNCHERS = ["codegraph-mcp", "codegraph"]


class CodegraphAdapter(AdapterBase):
    """Install vendor/codegraph (npm) into XDG data, build, write launchers."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "codegraph-mcp").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_paths import data_home

        root = root or ROOT
        src = self.ensure_source(root, SRC_REL)
        if not (src / "package.json").exists():
            raise FileNotFoundError(f"codegraph source not found (submodule not initialized): {src}")
        if not self.require("npm", "codegraph requires npm (https://nodejs.org)"):
            raise FileNotFoundError("npm is required (https://nodejs.org).")

        app_dir = data_home() / "codegraph"
        print(f">>> Installing codegraph into {app_dir}...")
        self.copy_app(src, app_dir, NODE_IGNORES)

        self.run(["npm", "ci", "--no-audit", "--no-fund"], app_dir)
        self.run(["npm", "run", "build"], app_dir)

        entry = app_dir / ENTRY
        if not entry.exists():
            raise FileNotFoundError(f"entry not found {entry}")

        # codegraph-mcp + codegraph both forward to the same entry binary.
        from modules.installer.src.utility_launcher_writer import symlink_alias
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        artifacts = [self.write_node_launcher(LAUNCHERS[0], entry)]
        artifacts += [symlink_alias(name, bin_home() / LAUNCHERS[0]) for name in LAUNCHERS[1:]]
        self.finish_bin()
        print(">>> Successfully installed codegraph")
        return artifacts
