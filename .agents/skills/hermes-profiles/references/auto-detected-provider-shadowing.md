# Auto-detected CLI providers shadow your model (the `opencode-free` 401)

## Symptom
A model name that works in the default profile 401s in another profile:
```
── Hermes error details ──
provider: opencode-free
model: free
error: HTTP 401: Model free is not supported
```

## Root cause
Hermes auto-detects installed CLI coding tools (e.g. `opencode` at `~/.opencode/bin/opencode`)
and registers a provider named after the CLI. That provider **claims the bare model name**
`free` (because the CLI's model list includes `opencode/...:free` entries). When you request
model `free`, Hermes prefers the auto-detected provider over your intended one (e.g. `free`
→ 9Router at `http://localhost:20128/v1`), so the request hits the CLI's API, which has no
`free` model → 401.

This is **profile-specific**: it only happens in profiles whose `serve` process was started in
an environment where the CLI binary is on PATH. That's why the default profile (started in a
different PATH context) worked while `currie` did not.

## Diagnosis
1. Read the error's `provider:` field — if it's `<cli>-free` (e.g. `opencode-free`), it's shadowing.
2. Confirm the CLI is installed: `command -v opencode` → `/home/raka/.opencode/bin/opencode`.
3. Confirm your intended provider works via raw curl with the profile's key:
   ```bash
   CK=$(grep -i '^HERMES_CUSTOM_VISION_API_KEY=' ~/.hermes/profiles/<name>/.env | head -1 | cut -d= -f2-)
   curl -s -m 20 -X POST http://localhost:20128/v1/chat/completions \
     -H "Content-Type: application/json" -H "Authorization: Bearer $CK" \
     -d '{"model":"free","messages":[{"role":"user","content":"reply ok"}],"max_tokens":10,"stream":false}'
   # HTTP 200 + "ok" proves the upstream is fine and the key is correct.
   ```

## Fix
Disable the toolset so Hermes never registers that provider:
- Append `- <cli>` (e.g. `- opencode`) to `agent.disabled_toolsets` in the **profile**
  `config.yaml` (`~/.hermes/profiles/<name>/config.yaml`). Profile configs ARE patchable.
- Then restart that profile's serve process (see below).

Do NOT do any of these (they do not work):
- `hermes config unset providers.opencode` → "Config key not set" (auto-detected providers are
  not config keys).
- `hermes gateway restart` alone → only restarts the gateway, not profile serve processes.
- Claiming "it's an upstream error" → the default profile working proves the upstream is fine.

## Restarting a profile serve process
Per-profile `serve` processes are children of `hermes desktop`, NOT the gateway. Apply config
changes by killing the serve process; the desktop respawns it with the new config.
```bash
pid=$(pgrep -f "hermes_cli.main --profile <name> serve" | head -1); kill $pid
sleep 7
pgrep -af "hermes_cli.main --profile <name> serve"   # confirm NEW pid + start time
```
Verify the change took: compare serve PID start time (`ps -o lstart= -p <pid>`) to your edit
time (`stat -c %y ~/.hermes/profiles/<name>/config.yaml`). A PID older than the edit = still
running stale config.

## Also required for auth to actually attach
`model.key_env` AND `providers.<name>.key_env` must both reference the var. If the provider
block lacks `key_env`, requests go out unauthenticated → 401. Set it with
`hermes config set providers.<name>.key_env HERMES_CUSTOM_VISION_API_KEY` (the allowed way to
edit the main config, which patch cannot touch).

## Config-write permissions
- Main `~/.hermes/config.yaml`: PATCH BLOCKED. Use `hermes config set/get/unset`.
  `hermes config set <key>[+]` (array append) is NOT recognized — saves a junk key.
- Profile `config.yaml`: PATCH ALLOWED.
