---
name: mcp-server-setup
description: Register an MCP server into Hermes; wrapper conventions.
version: 1.0.0
---

# Setting up MCP servers in Hermes

Use when connecting an external MCP server to this Hermes instance (stdio or HTTP).

## Procedure

1. Check the built-in catalog first: `setup_mcp` tool or `hermes mcp catalog`. If absent there,
   register manually with the CLI (`hermes mcp add --help` first — flags differ from Claude Code's).
2. Verify prerequisites independently of the config step (server binary builds, API reachable
   with curl, etc.) BEFORE registering, so connection failures are debuggable.
3. Register, then verify: `hermes mcp test <name>` must report Connected + tools discovered.
4. Tools only appear in NEW sessions — tell the user to start a fresh session.

## Pitfalls

- **`--env` flag order matters**: `hermes mcp add` uses argparse. Put `--env KEY=VALUE` BEFORE
  `--command`/`--args`. If placed after `--args`, it gets swallowed INTO the args list and the
  spawned server dies with errors like `Unknown command "--env"` (visible in ~/.hermes/logs/mcp-stderr.log).
- When `hermes mcp add` fails to connect it still offers to save the config as disabled — a saved
  disabled entry is NOT success. Always follow with `hermes mcp test <name>`.
- Debug stdio servers by piping a raw JSON-RPC initialize line into the command manually; if that
  works but Hermes fails, the problem is arg/env parsing, not the server.
- Prefer a locally built server binary over `npx -y` when a maintained local clone exists (faster
  startup, pinned version); point config at the build output (`dist/...`).

## Diagnosing provider 429s (not config errors)

`HTTP 429 upstream capacity` from the model provider is NOT an MCP/setup failure. Evidence lives
in `~/.hermes/logs/agent.log`: compare `cache=<n>/<total>` percentages between working sessions
(98%+ cached) and failing ones (cold prompt). Read logs before theorizing about payload size or
tool count — assumptions there have been wrong before.

## References

- `references/agents-arwaky-conventions.md` — user's personal MCP tool collection layout & wrapper rules.
