#!/usr/bin/env python3
"""Generate unified MCP client config (pengganti tools/mcp/generate-config.sh)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from envfile import load_first_env
from xdg import config_home


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "mcp_servers.generated.json"
    print("Generating unified MCP client configuration...")
    print(f"Target: {output}")

    secret_home = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "agents-arwaky/config"
    env = load_first_env([
        secret_home / "anytype.env",
        config_home() / "anytype-mcp/.env",
        ROOT / "tools/config/anytype.env",
        ROOT / ".env",
    ])
    anytype_base = env.get("ANYTYPE_API_BASE_URL", "http://127.0.0.1:31012")
    anytype_key = env.get("ANYTYPE_API_KEY", "<YOUR_API_KEY>")
    if not anytype_key or anytype_key in ("<YOUR_API_KEY>", "change-me", "<YOUR_ANYTYPE_API_KEY>", ""):
        print("  \u26a0 Warning: ANYTYPE_API_KEY is not set or is a placeholder.", file=sys.stderr)
        print("    Run 'aa anytype auth-key' to generate a valid key.", file=sys.stderr)
        anytype_key = "<YOUR_API_KEY>"

    # Single source of truth: manifest.json (Traceability fix — hapus hardcoded dict)
    manifest_path = ROOT / "tools/config/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = {"mcpServers": {}}
    for tool in manifest.get("tools", []):
        if not tool.get("isMcp", False):
            continue
        tool_id = tool["id"]
        binary = tool["binary"]
        if tool_id == "anytype":
            config["mcpServers"]["anytype"] = {
                "command": binary,
                "env": {
                    "ANYTYPE_API_BASE_URL": anytype_base,
                    "OPENAPI_MCP_HEADERS": json.dumps(
                        {"Authorization": f"Bearer {anytype_key}", "Anytype-Version": "2025-11-08"},
                        ensure_ascii=False,
                    ),
                },
            }
        elif tool_id == "codegraph":
            config["mcpServers"]["codegraph"] = {"command": binary, "args": ["serve", "--mcp"]}
        else:
            config["mcpServers"][tool_id] = {"command": binary}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        output.chmod(0o600)
    except OSError:
        print("Warning: could not set 0600 permissions on generated MCP config.", file=sys.stderr)
    print(f"Generated valid JSON configuration at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
