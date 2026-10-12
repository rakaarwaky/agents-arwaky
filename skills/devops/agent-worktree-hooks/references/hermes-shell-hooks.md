# Hermes Shell Hooks — Wire Shape, Registration, and Multi-Profile Wiring

The guard scripts (`guard-main-pre.sh`, `guard-main-revert.sh`,
`verify-workflow.sh`) read the Grok/Claude-Code payload shape
(`{toolName, toolInput, toolResult, cwd, workspaceRoot, ...}`). Hermes
shell hooks send a different shape. This reference covers how to make
them talk.

## Wire shape difference

Hermes pipes this JSON to a shell hook's stdin:

```json
{
  "hook_event_name": "pre_tool_call",
  "tool_name":       "terminal",
  "tool_input":      {"command": "git commit -m x", "description": "..."},
  "session_id":      "sess_abc",
  "cwd":             "/abs/path",
  "profile":         "default",
  "extra":           {"result": "...", "task_id": "...", "tool_call_id": "..."}
}
```

Key facts:
- There is **no `workspaceRoot`** in the Hermes payload — the script must
  derive the workspace from `cwd`.
- The exit-code-2-block contract is the same as Grok's deny.
- Shell hooks block only `pre_tool_call`; `post_tool_call` and
  `pre_verify` are observer-only (their directives are ignored).
- `fail_closed` is honored only on `pre_tool_call`.
- A `matcher` is a regex **fullmatch** on the tool name (not a substring),
  and only `pre_tool_call` / `post_tool_call` honor it.

## Payload bridge (in `lib.sh read_hook_input`)

Map Hermes fields onto the Grok shape once, at the top of
`read_hook_input`, and republish as `$INPUT` (downstream scripts re-read
`$INPUT` with their own jq). Also map tool names so the guard `case` /
string comparisons line up:

| Hermes `tool_name` | Grok `TOOL_NAME` used by guards |
|---|---|
| `terminal` | `run_terminal_command` |
| `patch` | `search_replace` |
| `write_file` | `write` |

Native Grok payloads (already carrying `.toolName`) pass through
untouched — the bridge keys off the absence of `.toolName`.

## Config registration (per profile)

Hermes reads shell hooks from the `hooks:` block in each profile's
`config.yaml`, **not** from any `~/.hermes/hooks/*.json`. There is no
Hermes equivalent of Grok's `worktree-enforce.json` — do not copy that
file into `~/.hermes/hooks/` and expect it to load; the `~/.hermes/hooks/`
directory is for Python **gateway** event hooks (`HOOK.yaml` +
`handler.py`), a different system.

Register for every profile the guards must protect, because each
profile resolves its own `config.yaml`:

```bash
# default profile
hermes config set --force 'hooks.pre_tool_call'  '[{"matcher":"terminal|write_file|patch","command":"/home/raka/.hermes/scripts/guard-main-pre.sh","timeout":10,"fail_closed":true}]'
hermes config set --force 'hooks.post_tool_call' '[{"matcher":"terminal|write_file|patch","command":"/home/raka/.hermes/scripts/guard-main-revert.sh","timeout":15}]'
hermes config set --force 'hooks.pre_verify'      '[{"command":"/home/raka/.hermes/scripts/verify-workflow.sh","timeout":60}]'

# each sub-profile: repeat with -p <name>
hermes -p agents-arwaky config set --force 'hooks.pre_tool_call' '[...same...]'  # + post_tool_call, pre_verify
```

- `hermes config set` uses the ruamel-safe writer (comment/order
  preserving). Never hand-edit `config.yaml` for this — use the CLI.
- `--force` is needed because `hooks` is an accepted section but the
  dotted leaf path may be unknown to the running version; the notice is
  harmless.
- Event name mapping: Grok `PreToolUse` → `pre_tool_call`, Grok
  `PostToolUse` → `post_tool_call`, Grok `Stop` → `pre_verify` (the
  verify-gate is the closest Hermes equivalent; it can nudge the agent
  to keep going, which is what the Stop nudge hooks are for).

## Consent (allowlist)

Each (event, command) pair must be allowlisted in
`<profile home>/shell-hooks-allowlist.json`, or Hermes prompts at the TTY
on first run and **silently skips the hook on non-TTY runs** (gateway,
cron, desktop background). Pre-approve by writing the file:

```json
{
  "approvals": [
    {
      "event": "pre_tool_call",
      "command": "/home/raka/.hermes/scripts/guard-main-pre.sh",
      "approved_at": "<ISO8601 UTC>",
      "script_mtime_at_approval": "<ISO8601 UTC>"
    }
  ]
}
```

- `script_mtime_at_approval` is the script file's mtime in ISO-8601 UTC.
  If the script changes after approval, the entry is flagged as
  "mtime drift" and the hook re-prompts — re-record the approval after
  editing the script.
- The default profile's file lives at `~/.hermes/shell-hooks-allowlist.json`;
  each sub-profile's at `~/.hermes/profiles/<name>/shell-hooks-allowlist.json`.
- Alternatives to hand-writing: run once with `--accept-hooks`, set env
  `HERMES_ACCEPT_HOOKS=1`, or set `hooks_auto_accept: true` in the
  profile's `config.yaml`.

## Verify

```bash
hermes hooks list            # shows each hook + whether it's allowlisted
hermes hooks doctor          # exec bit, allowlist, mtime drift, synthetic run
hermes -p <name> hooks doctor  # per sub-profile
```

All-green doctor output + a `hermes hooks test pre_tool_call` synthetic
run is the confirmation that the wiring is live. The hooks themselves
only attach to a running process at start, so a live session needs a
restart before the guards actually block.

## Pitfalls specific to this wiring

- **Gate fallback**: `hook_repo_allowed` in `lib.sh` must resolve the
  workspace from `WORKSPACE_ROOT` (payload) then `OPERATING_DIR` (the
  tool's CWD) then the agent home. Keying it off an unset env var makes
  the gate silently fail-open — the allowlist then never gates and no
  guard can deny. Confirm by testing a non-allowlisted CWD (expect exit
  0) and an allowlisted one (expect exit 2 on a deny).
- **`~/.hermes` is a tracked git repo**: a post-hook `git clean`/revert
  that runs inside it will delete newly-added `~/.hermes/scripts/`
  files. The guard scripts and allowlist manifest must be exempt from
  any in-repo revert, or the tooling wipes itself out. Confirm with
  `git -C ~/.hermes status` after a hook run.
- **Upstream stays clean**: `~/.hermes/hermes-agent/` is the upstream
  checkout and must remain unmodified (`git -C ~/.hermes/hermes-agent
  status` clean). All custom guard code lives in the user home layer
  (`~/.hermes/scripts/`, `config.yaml`, the allowlist files), never in
  `hermes-agent/`.
