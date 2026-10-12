---
name: hermes-shell-hooks
description: Set up Hermes shell hooks per profile, keep them firing.
metadata:
  version: 1.0.0
  author: hermes-agent
  license: MIT
  tags:
    - hermes
    - hooks
    - shell-hooks
    - guardrails
    - profiles
  related_skills:
    - hermes-agent
---

# Hermes Shell-Script Hooks

## When to Use

Load this skill when you need to: (a) register a new shell hook in a profile,
(b) understand why a configured hook isn't firing, (c) port an external
agent's hook scripts (Grok/Claude-Code style) to Hermes, or (d) maintain the
consent allowlist / mtime stamps that keep headless hooks alive.

Shell hooks let a profile run any script (Bash/Python/...) at plugin-hook events:
`pre_tool_call` (can BLOCK or modify a tool call), `post_tool_call`, `pre_verify`,
`pre_llm_call`, `subagent_stop`, session lifecycle, and more. Declared in the
profile's `config.yaml`, run as subprocesses with a JSON payload on stdin, JSON
decision on stdout. They register at CLI AND gateway startup — so config changes
take effect on the next session/gateway start, not live.

Two distinct things, keep them separate:
- **Gateway event hooks** (`HOOK.yaml` + `handler.py` under `~/.hermes/hooks/<name>/`):
  Python, in-process, gateway-only. NOT shell hooks, NOT a way to run scripts.
- **Shell hooks** (`hooks:` block in profile `config.yaml`): the thing this skill
  covers. `~/.hermes/hooks/` is the wrong place for scripts; scripts live wherever
  you put them (convention `~/.hermes/agent-hooks/` or `~/.hermes/scripts/`) and
  are referenced by absolute path in the config.

## Registering a hook (all profiles)

Shell hooks are PER PROFILE — there is no global hook file (Grok's global
`hooks/*.json` has no Hermes equivalent). Each profile's own `config.yaml` must
carry the `hooks:` block, and the subprocess runs with that profile's
`HERMES_HOME`.

Use the CLI, never hand-edit YAML (config.yaml must go through the ruamel-safe
writer):

```bash
hermes -p <profile> config set --force 'hooks.pre_tool_call' \
  '[{"matcher":"terminal|write_file|patch","command":"/abs/path/guard.sh","timeout":10,"fail_closed":true}]'
hermes -p <profile> config set --force 'hooks.post_tool_call' \
  '[{"matcher":"terminal|write_file|patch","command":"/abs/path/revert.sh","timeout":15}]'
hermes -p <profile> config set --force 'hooks.pre_verify' \
  '[{"command":"/abs/path/verify.sh","timeout":60}]'
```

- `--force` is needed because `hooks` is not always a recognized key in the
  running version; verify with `hermes -p <profile> config get hooks --json`.
- `matcher` is a REGEX that must FULLY match `tool_name` (`fullmatch`) and is
  honored ONLY for `pre_tool_call`/`post_tool_call`. Omit it for other events.
- `timeout` default 60, capped 300. `fail_closed: true` only meaningful on
  `pre_tool_call` (block if the script itself errors); ignored elsewhere.
- One JSON array literal per event; multiple entries = multiple scripts, run in
  order.

New profile later? Re-run the three `config set` commands with `-p <new>`, then
pre-approve (below).

## Consent / allowlist (the silent-kill gotcha)

Each `(event, command)` pair needs first-use consent recorded in the profile's
`shell-hooks-allowlist.json` (default profile: `~/.hermes/`, sub-profiles:
`~/.hermes/profiles/<name>/`). If a pair is not allowlisted:
- TTY run: interactive prompt on next start.
- NON-TTY run (gateway, cron, `hermes chat -q`): the hook is **silently
  skipped** — no error, just inactive. This is why "I configured the hook but
  it never fires" is almost always a missing allowlist entry, not a config bug.

Ways to satisfy consent:
- Interactive: run the surface once in a TTY and approve the prompt.
- `hermes -p <profile> hooks doctor` — reports `✗ not allowlisted` vs `✓`.
- Pre-approve (script, non-interactive): write the allowlist JSON directly, one
  entry per pair, with `script_mtime_at_approval` equal to the script's CURRENT
  mtime (ISO-8601 UTC `...Z`). This is the right move when registering hooks
  headlessly for a profile that cannot prompt.

## mtime drift (the second silent-kill)

The allowlist records `script_mtime_at_approval`; if the script's mtime is NEWER
than that, the hook is treated as modified: TTY re-prompts, non-TTY skips.
After ANY edit to a hook script, refresh the mtime stamp in every profile's
allowlist that references it, or the hook silently dies on gateway runs.
`hermes hooks doctor` shows `script unchanged since approval` vs a drift line.

```bash
# refresh all profiles' mtime stamps after editing scripts
python3 - <<'EOF'
import json, os, datetime
def mt(p):
    return datetime.datetime.fromtimestamp(os.path.getmtime(p),
        tz=datetime.timezone.utc).isoformat().replace('+00:00','Z')
for p in ['shell-hooks-allowlist.json'] + [f'profiles/{x}/shell-hooks-allowlist.json'
        for x in os.listdir('profiles') if os.path.isdir(f'profiles/{x}')]:
    fp = os.path.join(os.path.expanduser('~/.hermes'), p)
    if not os.path.exists(fp): continue
    d = json.load(open(fp)); n = 0
    for e in d.get('approvals', []):
        if e.get('command') and os.path.exists(e['command']) and e.get('script_mtime_at_approval') != mt(e['command']):
            e['script_mtime_at_approval'] = mt(e['command']); n += 1
    json.dump(d, open(fp, 'w'), indent=2, sort_keys=True)
    open(fp, 'a').write('\n')
    print(p, n, 'refreshed')
EOF
```

## Payload wire protocol (porting external hooks)

What the script receives on stdin (Hermes shape — differs from Claude Code /
Grok shape, which is the #1 porting bug):

```json
{
  "hook_event_name": "pre_tool_call",
  "tool_name": "terminal",
  "tool_input": {"command": "..."},
  "session_id": "sess_...",
  "cwd": "/abs/project",
  "profile": "default",
  "extra": {"task_id": "...", "tool_call_id": "...", "result": "..."}
}
```

- Hermes tool names are NOT the Grok/Claude names: `terminal` (not
  `run_terminal_command`), `patch` (not `search_replace`), `write_file` (not
  `write`). A ported hook that matches tool names must map these.
- `tool_input` is the tool's args dict; for `post_tool_call` the result lives
  under `extra` (e.g. `extra.result`), not `toolResult`.
- Non-tool events (`pre_llm_call`, `subagent_stop`, session lifecycle) have
  `tool_name`/`tool_input` null.

What the script may print on stdout (both canonical + Claude-Code forms
accepted; anything else = no-op):
- Block: `{"action":"block","message":"..."}` or `exit 2` (Claude-Code style)
  — `pre_tool_call` only.
- Modify args: `{"action":"modify","args":{...}}`.
- Inject context: `{"context":"..."}` (`pre_llm_call`).
- Keep-going at verify gate: `{"action":"continue","message":"..."}` (`pre_verify`).

Cleanest port strategy: keep the external scripts' logic intact and add a small
payload normalizer in the shared lib that (a) maps Hermes JSON fields onto the
external shape the logic reads, and (b) maps tool names. Never rewrite the guard
logic — only the wire adapter.

## Verification checklist (do all, in order)

1. `bash -n` every script (syntax).
2. Pipe a synthetic payload into each coordinator script and check exit codes:
   blocking event must `exit 2` on a deny, `exit 0` on allow. (Write the
   payload to a file first; avoid `printf | bash` pipes that trip the scanner.)
3. `hermes -p <profile> hooks doctor` → every hook `✓ script exists`,
   `✓ allowlisted`, `✓ script unchanged since approval`.
4. Confirm the allowlist entry mtime matches (see drift section).
5. Confirm `hermes -p <profile> config get hooks --json` prints the expected
   array(s) — not a scalar (the comma-vs-JSON-array-literal trap).
6. Hooks activate on the NEXT session/gateway start; a live run won't pick
   them up mid-session.

## Standing rules (this user's setup)

- Custom hook scripts live under `~/.hermes/scripts/` (user layer). NEVER inside
  `~/.hermes/hermes-agent/` — that directory is upstream source, read-only,
  and `git status` there must stay clean.
- Guard/allowlist scripts use a per-repo opt-in manifest (`hook-allowlist.txt`)
  and fail open for non-listed workspaces.
- Every profile (default + each sub-profile) gets its own `hooks:` block and its
  own `shell-hooks-allowlist.json`; one shared set of scripts serves all.
- After editing any hook script, ALWAYS refresh mtime stamps in every profile's
  allowlist, then run `hermes hooks doctor`.

## Pitfalls

- "Configured but not firing" = missing allowlist entry OR mtime drift, not a
  config typo. Check `hermes hooks doctor` before touching config.
- Forgetting `-p` writes to the DEFAULT profile; sub-profiles need their own.
- `matcher` that doesn't fullmatch the exact tool name never fires; test the
  regex against the real `tool_name` string.
- A `post_tool_call` script that calls `git clean -fd` on a repo will delete
  legitimately untracked files (e.g. new skill files under a symlinked
  `skills/` dir). Clean only the paths you intend, and exempt known-writable
  source dirs (skill curation writes in place to the source-of-truth repo, not
  into an Orca worktree).
- A `~/.hermes/<dir>` that is a SYMLINK to a git repo means the guard acts on
  the symlink TARGET's repo, not on `~/.hermes` itself — resolve symlinks when
  reasoning about which repo is "immutable".
