"""Skills-design MCP adapter (AES surface layer).

MCP adapter exposing every ``sac`` skill command as an MCP tool with
1:1 CLI equivalence. Each MCP tool delegates to the composed
``ISkillsAggregate.execute`` path — the same path the CLI uses — and
therefore triggers the same telemetry view recording on success.
"""
