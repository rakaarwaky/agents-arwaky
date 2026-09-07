#!/usr/bin/env python3
"""Generate unified MCP client config (pengganti tools/mcp/generate-config.sh)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from envfile import load_first_env  # noqa: E402
from xdg import config_home  # noqa: E402


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "mcp_servers.generated.json"
    print("Generating unified MCP client configuration...")
    print(f"Target: {output}")

    env = load_first_env([
        ROOT / "tools/anytype-mcp/.env",
        config_home() / "anytype-mcp/.env",
        ROOT / ".env",
    ])
    anytype_base = env.get("ANYTYPE_API_BASE_URL", "http://127.0.0.1:31012")
    anytype_key = env.get("ANYTYPE_API_KEY", "<YOUR_API_KEY>")

    config = {
        "mcpServers": {
            "context7": {"command": "context7-mcp"},
            "fetch": {"command": "fetch-mcp"},
            "ponytail": {"command": "ponytail-mcp"},
            "anytype": {
                "command": "anytype-mcp",
                "env": {
                    "ANYTYPE_API_BASE_URL": anytype_base,
                    "OPENAPI_MCP_HEADERS": json.dumps(
                        {"Authorization": f"Bearer {anytype_key}", "Anytype-Version": "2025-11-08"},
                        ensure_ascii=False,
                    ),
                },
            },
            "codegraph": {"command": "codegraph-mcp", "args": ["serve", "--mcp"]},
            "vision": {"command": "vision-arwaky-mcp"},
            "qwen-web": {"command": "qwen-web-mcp"},
            "blender": {"command": "blender-mcp"},
            "lint": {"command": "lint-arwaky-mcp"},
            "workspace": {"command": "workspace-mcp"},
            "mnemosyne": {"command": "mnemosyne-mcp"},
        }
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated valid JSON configuration at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
