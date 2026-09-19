"""Codegraph adapter (npm) — unified install + update + teardown.

@colbymchenry/codegraph is a TypeScript project built with npm. Lockfile
package-lock.json -> `npm ci`; build `npm run build` (tsc + copy-assets +
build:ui) produces dist/bin/codegraph.js. Launchers codegraph-mcp &
codegraph both point at dist/bin/codegraph.js (tool dispatches mode via args).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import bin_home, data_home
from modules.tools.src.utility_adapter_base import AdapterBase, ROOT, NODE_IGNORES
from modules.tools.src.utility_launcher_writer import symlink_alias

SRC_REL = "vendor/codegraph"
ENTRY = "dist/bin/codegraph.js"
LAUNCHERS = ["codegraph-mcp", "codegraph"]


class CodegraphAdapter(AdapterBase):
    """Install/update vendor/codegraph (npm) into XDG data, build, write launchers."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "codegraph-mcp").exists()

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
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
        artifacts = [self.write_node_launcher(LAUNCHERS[0], entry)]
        artifacts += [symlink_alias(name, bin_home() / LAUNCHERS[0]) for name in LAUNCHERS[1:]]
        self.finish_bin()
        print(">>> Successfully installed codegraph")
        return artifacts

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "npm workspace (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule

        source = root / SRC_REL
        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
        if not (source / "package.json").exists():
            raise ToolUpdateError("codegraph source not found (submodule not initialized)")
        if not self.require("npm", "codegraph requires npm (https://nodejs.org)"):
            raise ToolUpdateError("codegraph requires npm (https://nodejs.org)")

        app_dir = data_home() / "codegraph"
        print(f">>> Updating codegraph into {app_dir}...")
        self.copy_app(source, app_dir, NODE_IGNORES)
        self.run(["npm", "ci", "--no-audit", "--no-fund"], app_dir)
        self.run(["npm", "run", "build"], app_dir)

        entry = app_dir / ENTRY
        if not entry.exists():
            raise ToolUpdateError(f"entry not found {entry}")

        created = [self.write_node_launcher(LAUNCHERS[0], entry)]
        created += [symlink_alias(name, bin_home() / LAUNCHERS[0]) for name in LAUNCHERS[1:]]
        self.finish_bin()
        print(">>> Successfully updated codegraph")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return self.generic_owned(spec, LAUNCHERS)
