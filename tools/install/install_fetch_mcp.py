#!/usr/bin/env python3
"""Installer fetch-mcp (Python, shared node installer + dual launcher)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from utility_node_installer import install_node_tool  # type: ignore[import-not-found]

# Dual MCP/CLI launcher khusus fetch (D-3: custom_launcher_content)
FETCH_LAUNCHER = """#!/usr/bin/env python3
import os, sys
from pathlib import Path
data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "fetch-mcp"
cli = {"html","markdown","readable","txt","json","youtube","--help","-h","--version","-v"}
script = data / "dist" / ("cli.js" if (len(sys.argv) > 1 and sys.argv[1] in cli) else "index.js")
env = os.environ.copy()
env["NODE_PATH"] = str(data / "node_modules") + os.pathsep + env.get("NODE_PATH", "")
os.execvpe("node", ["node", str(script), *sys.argv[1:]], env)
"""


def main() -> int:
    return install_node_tool(
        tool_name="fetch-mcp",
        vendor_subpath="vendor/fetch-mcp",
        aliases=["fetch-mcp", "mcp-fetch"],
        entry_point="index.js",
        custom_launcher_content=FETCH_LAUNCHER,
    )


if __name__ == "__main__":
    raise SystemExit(main())
