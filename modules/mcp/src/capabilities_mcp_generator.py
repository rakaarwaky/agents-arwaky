"""MCP config generator — port of the legacy ``tools/mcp/generate_config.py`` body.

The original module exposes a single ``main()`` function honouring
``sys.argv[1]`` as an explicit target (defaulting to the repo-root
``mcp_servers.generated.json``). This capability adapts that as-is body
behind the single-method ``IMcpProtocol.execute`` dispatcher while
keeping ``generate`` / ``list_servers`` / ``show_server`` as concrete
internal methods the orchestrator drives directly.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from modules.shared.src.contract_mcp_protocol import IMcpProtocol
from modules.shared.src.taxonomy_common_vo import (
    agents_arwaky_config_dir,
    config_home,
)
from modules.shared.src.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpServerId,
    McpServerInfo,
)
from modules.shared.src.utility_envfile_parser import load_first_env
from modules.shared.src.utility_paths_resolver import repo_root


# ─── Block 1: Class Definition & Constructor ──────────────
class McpConfigGenerator(IMcpProtocol):
    """Read the manifest + env files and write mcp_servers.generated.json."""

    def __init__(self) -> None:
        self._root = repo_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "McpConfigGenerator()"

    def generate(self, output: Path) -> ExitCode:
        """Write the unified MCP client config to *output*; return exit code.

        Delegates to the unchanged original ``main()`` body, passing
        *output* as the explicit target (the original honours
        ``sys.argv[1]`` exactly this way).
        """
        original_argv = list(sys.argv)
        sys.argv = [sys.argv[0], str(output)]
        try:
            return ExitCode(main())
        finally:
            sys.argv = original_argv

    def list_servers(self) -> list[McpServerInfo]:
        """MCP-enabled tools from the manifest (read-only)."""
        manifest_path = self._root / "config" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        servers = []
        for tool in manifest.get("tools", []):
            if not tool.get("isMcp", False):
                continue
            servers.append(McpServerInfo(
                id=tool["id"],
                category=tool.get("category", ""),
                description=tool.get("description", ""),
            ))
        return servers

    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        """Show the generated config (no id) or probe one server's help/schema."""
        if server_id is None:
            generated = self._root / "mcp_servers.generated.json"
            if not generated.exists():
                print("Configuration file not found. Generating now...")
                self.generate(generated)
            if generated.exists():
                print(f"Path: {generated}")
                print()
                print(generated.read_text(encoding="utf-8"))
                return ExitCode(0)
            print("Failed to generate MCP configuration.", file=sys.stderr)
            return ExitCode(1)
        return self._probe_server(McpServerId(server_id))

    def _probe_server(self, server_id: McpServerId) -> ExitCode:
        """Bounded, read-only help/schema probe for one registered MCP server."""
        manifest_path = self._root / "config" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        tool = next(
            (t for t in manifest.get("tools", [])
             if t.get("id") == server_id and t.get("isMcp", False)),
            None,
        )
        if tool is None:
            print(f"Server '{server_id}' is not registered as an MCP server.", file=sys.stderr)
            return ExitCode(1)
        binary = tool.get("mcpBinary") or tool.get("binary", "")
        args = list(tool.get("mcpArgs", []))
        print(f"Server: {server_id}")
        print(f"Command: {binary} {' '.join(args)}".rstrip())
        if tool.get("description"):
            print(f"Description: {tool['description']}")
        try:
            proc = subprocess.run(
                [binary, *args, "--help"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            help_text = (proc.stdout or proc.stderr or "").strip()
            print()
            if help_text:
                print(help_text)
            else:
                print("(no help output)")
        except FileNotFoundError:
            print("(help probe failed: binary not found)", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("(help probe failed: timed out)", file=sys.stderr)
        except OSError as exc:
            print(f"(help probe failed: {exc})", file=sys.stderr)
        return ExitCode(0)

    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode:
        """Write an alias-qualified client config (I/O lives here)."""
        print(f"Generating alias config '{alias}' -> {output}")
        return self.generate(output)

    def validate(self, output: Path | None = None) -> ExitCode:
        """Parse the generated config at *output* and report validity (I/O lives here)."""
        path = output if output is not None else self._root / "mcp_servers.generated.json"
        if not path.is_file():
            print(f"Config not found: {path}", file=sys.stderr)
            return ExitCode(1)
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in {path}: {exc}", file=sys.stderr)
            return ExitCode(1)
        print(f"Valid config: {path}")
        return ExitCode(0)


def main() -> int:
    """CLI entry point that generates the unified MCP client configuration file."""
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else repo_root() / "mcp_servers.generated.json"
    print("Generating unified MCP client configuration...")
    print(f"Target: {output}")

    env = load_first_env([
        agents_arwaky_config_dir() / "anytype.env",
        config_home() / "anytype-mcp/.env",
        repo_root() / "config/anytype.env",
        repo_root() / ".env",
    ])
    anytype_base = env.get("ANYTYPE_API_BASE_URL", "http://127.0.0.1:31012")
    anytype_key = env.get("ANYTYPE_API_KEY", "<YOUR_API_KEY>")
    if not anytype_key or anytype_key in ("<YOUR_API_KEY>", "change-me", "<YOUR_ANYTYPE_API_KEY>", ""):
        print("  ⚠ Warning: ANYTYPE_API_KEY is not set or is a placeholder.", file=sys.stderr)
        print("    Run 'aa anytype auth-key' to generate a valid key.", file=sys.stderr)
        anytype_key = "<YOUR_API_KEY>"

    # Single source of truth: manifest.json (Traceability fix — hapus hardcoded dict)
    manifest_path = repo_root() / "config" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config: dict = {"mcpServers": {}}
    for tool in manifest.get("tools", []):
        if not tool.get("isMcp", False):
            continue
        tool_id = tool["id"]
        # An MCP server often exposes a dedicated stdio binary that differs
        # from the CLI binary (e.g. vision-arwaky -> vision-arwaky-mcp).
        binary = tool.get("mcpBinary") or tool["binary"]
        entry: dict = {"command": binary}
        if tool.get("mcpArgs"):
            entry["args"] = list(tool["mcpArgs"])
        if tool_id == "anytype":
            entry["env"] = {
                "ANYTYPE_API_BASE_URL": anytype_base,
                "OPENAPI_MCP_HEADERS": json.dumps(
                    {"Authorization": f"Bearer {anytype_key}", "Anytype-Version": "2025-11-08"},
                    ensure_ascii=False,
                ),
            }
        config["mcpServers"][tool_id] = entry
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        output.chmod(0o600)
    except OSError:
        print("Warning: could not set 0600 permissions on generated MCP config.", file=sys.stderr)
    print(f"Generated valid JSON configuration at {output}")
    return 0
