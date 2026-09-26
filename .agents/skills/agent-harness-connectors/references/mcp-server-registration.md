# Registering an MCP server in Hermes — the traps

Load this when adding an external MCP server (stdio or HTTP) to a Hermes profile
and the first attempt does not clearly work. The config schema, transports,
env-var filtering and generic troubleshooting live in the `hermes-agent` skill
(`references/native-mcp.md`); the curated CLI list is `hermes mcp catalog` /
`hermes mcp add NAME --url|--command | remove | list | test NAME`
(the `hermes-agent` skill's `references/cli-reference.md`). This file only records
what those do not.

## Order of operations

Check the catalog first (`hermes mcp catalog`, or the `setup_mcp` consent card) —
if the server is curated, install it instead of hand-writing config. Verify the
prerequisites independently *before* registering (the binary builds/runs, the
endpoint answers to `curl`), so that a later connection failure has one possible
cause. `hermes mcp add --help` before typing flags: they are not Claude Code's.
Tools only surface in **new** sessions, so a missing tool right after a
successful add is expected, not a failure.

## `--env` must come before `--command` / `--args`

`hermes mcp add` parses with argparse, and the `--args` collector is greedy.
`--env KEY=VALUE` placed **after** `--args` is swallowed into the args list and
passed to the server as an argument; the spawned process then dies with
something like `Unknown command "--env"`, which you only see in
`~/.hermes/logs/mcp-stderr.log` — the add command itself reports no error.

```bash
# right
hermes mcp add foo --env TOKEN=xyz --command npx --args -y @some/server
# wrong — TOKEN never becomes an env var
hermes mcp add foo --command npx --args -y @some/server --env TOKEN=xyz
```

Symptom to recognise: the server connects when you run it by hand but every tool
call fails at startup, and `mcp-stderr.log` shows the server complaining about an
unknown `--env` argument.

## A saved entry is not a working entry

When the connect attempt fails, `hermes mcp add` still offers to save the config
**disabled**. Answering yes produces a plausible-looking `mcp_servers.foo` block
that Hermes ignores. Never treat a successful add as proof:

```bash
hermes mcp test foo        # must report Connected + N tools discovered
hermes mcp list            # and check it is not disabled
```

`test` is also the command to re-run after moving a server's binary or wrapper
script — the config stores the path, not a resolved target.

## Debug stdio with raw JSON-RPC on stdin

Bypass the client entirely to split "server broken" from "registration broken":

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}' \
  | timeout 15 <the exact command and args from the config, with env exported>
```

Expect a single JSON line back containing `serverInfo` and `capabilities`. If
that works but Hermes fails, the server is fine and the fault is in the
registered command/args/env — re-check the ordering rule above and the
`env` block (Hermes passes only a safe baseline environment to stdio
subprocesses; every secret must be listed explicitly).

## A 429 is not a config error

`HTTP 429 upstream capacity` from the model provider is provider saturation, not
a broken MCP server. Evidence lives in `~/.hermes/logs/agent.log`: compare the
`cache=<n>/<total>` percentages between a working session and a failing one
(98%+ cached vs a cold prompt). Read the logs before theorising about payload
size or tool count — those assumptions have been wrong here before.
